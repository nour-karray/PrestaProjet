-- TrainFlow AI - MySQL 8.x Flyway schema baseline.
-- Flyway executes this migration for a new empty database. Existing non-empty
-- installations are baselined at this version and keep their current schema.
SET NAMES utf8mb4;
SET time_zone = '+00:00';

CREATE TABLE administrators (
    id CHAR(36) NOT NULL PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(320) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    last_login_at DATETIME(6),
    CONSTRAINT uq_administrators_email UNIQUE (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE companies (
    id CHAR(36) NOT NULL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    address VARCHAR(300),
    city VARCHAR(120),
    postal_code VARCHAR(30),
    country VARCHAR(120),
    tax_identifier VARCHAR(80),
    website VARCHAR(300),
    notes TEXT,
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT uq_companies_name UNIQUE (name),
    INDEX ix_companies_city (city),
    INDEX ix_companies_country (country),
    INDEX ix_companies_is_archived (is_archived)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE trainers (
    id CHAR(36) NOT NULL PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    full_name VARCHAR(200) NOT NULL,
    email VARCHAR(320),
    phone VARCHAR(50),
    mobile_phone VARCHAR(50),
    birth_date VARCHAR(50),
    birth_place VARCHAR(150),
    address VARCHAR(300),
    company VARCHAR(200),
    employer_address VARCHAR(300),
    job_title VARCHAR(200),
    years_experience INT,
    hourly_rate DECIMAL(12,2),
    daily_rate DECIMAL(12,2),
    city VARCHAR(120),
    country VARCHAR(120),
    linkedin_url VARCHAR(300),
    website VARCHAR(300),
    notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT ck_trainers_years_experience_non_negative CHECK (years_experience IS NULL OR years_experience >= 0),
    CONSTRAINT ck_trainers_hourly_rate_non_negative CHECK (hourly_rate IS NULL OR hourly_rate >= 0),
    CONSTRAINT ck_trainers_daily_rate_non_negative CHECK (daily_rate IS NULL OR daily_rate >= 0),
    INDEX ix_trainers_full_name (full_name),
    INDEX ix_trainers_email (email),
    INDEX ix_trainers_company (company)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE training_case_counters (
    year INT NOT NULL PRIMARY KEY,
    next_value INT NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE training_catalog_items (
    id CHAR(36) NOT NULL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    title VARCHAR(250) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT uq_training_catalog_items_title UNIQUE (title),
    INDEX ix_training_catalog_items_active_category (is_active, category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE company_contacts (
    id CHAR(36) NOT NULL PRIMARY KEY,
    company_id CHAR(36) NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    email VARCHAR(320),
    phone VARCHAR(50),
    job_title VARCHAR(150),
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    primary_guard TINYINT GENERATED ALWAYS AS (IF(is_primary, 1, NULL)) STORED,
    CONSTRAINT fk_company_contacts_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    CONSTRAINT uq_company_contacts_primary UNIQUE (company_id, primary_guard),
    INDEX ix_company_contacts_company_id (company_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE trainer_cvs (
    id CHAR(36) NOT NULL PRIMARY KEY,
    trainer_id CHAR(36),
    original_filename VARCHAR(255) NOT NULL,
    storage_filename VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    file_size INT NOT NULL,
    sha256 VARCHAR(64) NOT NULL,
    uploaded_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    extraction_status VARCHAR(32) NOT NULL DEFAULT 'UPLOADED',
    extraction_model VARCHAR(120),
    extraction_duration_ms INT,
    raw_text LONGTEXT,
    parsed_json JSON,
    extraction_error TEXT,
    extraction_error_code VARCHAR(64),
    CONSTRAINT uq_trainer_cvs_storage_filename UNIQUE (storage_filename),
    CONSTRAINT uq_trainer_cvs_sha256 UNIQUE (sha256),
    CONSTRAINT ck_trainer_cv_extraction_status CHECK (extraction_status IN ('UPLOADED','TEXT_EXTRACTED','OCR_REQUIRED','OCR_COMPLETED','AI_ANALYSIS_PENDING','AI_ANALYSIS_COMPLETED','REVIEW_REQUIRED','VALIDATED','FAILED')),
    CONSTRAINT fk_trainer_cvs_trainer FOREIGN KEY (trainer_id) REFERENCES trainers(id) ON DELETE SET NULL,
    INDEX ix_trainer_cvs_trainer_id (trainer_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE training_cases (
    id CHAR(36) NOT NULL PRIMARY KEY,
    reference VARCHAR(20) NOT NULL,
    company_id CHAR(36) NOT NULL,
    primary_contact_id CHAR(36),
    trainer_id CHAR(36),
    theme VARCHAR(250) NOT NULL,
    description TEXT,
    status VARCHAR(40) NOT NULL DEFAULT 'BROUILLON',
    desired_start_date DATE,
    desired_end_date DATE,
    created_by CHAR(36) NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    closed_at DATETIME(6),
    is_archived BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT uq_training_cases_reference UNIQUE (reference),
    CONSTRAINT ck_training_cases_status CHECK (status IN ('BROUILLON','DEMANDE_RECUE','RECHERCHE_FORMATEUR','FORMATEUR_PROPOSE','FORMATEUR_ACCEPTE','BESOIN_A_COMPLETER','BESOIN_COMPLETE','PROGRAMME_EN_PREPARATION','PROGRAMME_A_VALIDER','PROGRAMME_VALIDE','TARIFICATION_EN_PREPARATION','TARIFICATION_A_VALIDER','TARIFICATION_VALIDEE','DOCUMENTS_A_GENERER','DOCUMENTS_GENERES','TERMINE','ANNULE','ARCHIVE')),
    CONSTRAINT fk_training_cases_company FOREIGN KEY (company_id) REFERENCES companies(id),
    CONSTRAINT fk_training_cases_contact FOREIGN KEY (primary_contact_id) REFERENCES company_contacts(id) ON DELETE SET NULL,
    CONSTRAINT fk_training_cases_trainer FOREIGN KEY (trainer_id) REFERENCES trainers(id) ON DELETE SET NULL,
    CONSTRAINT fk_training_cases_creator FOREIGN KEY (created_by) REFERENCES administrators(id),
    INDEX ix_training_cases_company_id (company_id),
    INDEX ix_training_cases_trainer_id (trainer_id),
    INDEX ix_training_cases_status (status),
    INDEX ix_training_cases_theme (theme),
    INDEX ix_training_cases_created_at (created_at),
    INDEX ix_training_cases_is_archived (is_archived)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE activity_logs (
    id CHAR(36) NOT NULL PRIMARY KEY,
    administrator_id CHAR(36),
    training_case_id CHAR(36),
    action VARCHAR(80) NOT NULL,
    entity_type VARCHAR(80) NOT NULL,
    entity_id CHAR(36),
    details JSON NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT fk_activity_logs_administrator FOREIGN KEY (administrator_id) REFERENCES administrators(id) ON DELETE SET NULL,
    CONSTRAINT fk_activity_logs_case FOREIGN KEY (training_case_id) REFERENCES training_cases(id) ON DELETE CASCADE,
    INDEX ix_activity_logs_training_case_id (training_case_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE training_needs (
    id CHAR(36) NOT NULL PRIMARY KEY,
    training_case_id CHAR(36) NOT NULL,
    target_audience VARCHAR(500),
    level VARCHAR(20),
    location VARCHAR(300),
    participant_count INT,
    delivery_mode VARCHAR(20),
    duration_hours DECIMAL(8,2),
    planned_days_count INT,
    objectives TEXT,
    desired_start_date DATE,
    desired_end_date DATE,
    constraints TEXT,
    is_validated BOOLEAN NOT NULL DEFAULT FALSE,
    validated_at DATETIME(6),
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT uq_training_needs_case UNIQUE (training_case_id),
    CONSTRAINT ck_training_needs_participant_count_positive CHECK (participant_count IS NULL OR participant_count > 0),
    CONSTRAINT ck_training_needs_duration_hours_positive CHECK (duration_hours IS NULL OR duration_hours > 0),
    CONSTRAINT ck_training_needs_planned_days_count_positive CHECK (planned_days_count IS NULL OR planned_days_count > 0),
    CONSTRAINT ck_training_needs_delivery_mode CHECK (delivery_mode IS NULL OR delivery_mode IN ('PRESENTIEL','DISTANCIEL','HYBRIDE')),
    CONSTRAINT ck_training_needs_level CHECK (level IS NULL OR level IN ('BEGINNER','INTERMEDIATE','ADVANCED','EXPERT')),
    CONSTRAINT ck_training_needs_date_range CHECK (desired_end_date IS NULL OR desired_start_date IS NULL OR desired_end_date >= desired_start_date),
    CONSTRAINT fk_training_needs_case FOREIGN KEY (training_case_id) REFERENCES training_cases(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE training_programs (
    id CHAR(36) NOT NULL PRIMARY KEY,
    training_case_id CHAR(36) NOT NULL,
    title VARCHAR(250) NOT NULL,
    general_objectives TEXT,
    prerequisites TEXT,
    evaluation_method TEXT,
    is_submitted BOOLEAN NOT NULL DEFAULT FALSE,
    submitted_at DATETIME(6),
    is_validated BOOLEAN NOT NULL DEFAULT FALSE,
    validated_at DATETIME(6),
    returned_at DATETIME(6),
    return_reason TEXT,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT uq_training_programs_case UNIQUE (training_case_id),
    CONSTRAINT fk_training_programs_case FOREIGN KEY (training_case_id) REFERENCES training_cases(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE training_program_days (
    id CHAR(36) NOT NULL PRIMARY KEY,
    training_program_id CHAR(36) NOT NULL,
    title VARCHAR(250) NOT NULL,
    position INT NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT uq_training_program_days_position UNIQUE (training_program_id, position),
    CONSTRAINT ck_training_program_days_position_positive CHECK (position > 0),
    CONSTRAINT fk_training_program_days_program FOREIGN KEY (training_program_id) REFERENCES training_programs(id) ON DELETE CASCADE,
    INDEX ix_training_program_days_program (training_program_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE training_program_items (
    id CHAR(36) NOT NULL PRIMARY KEY,
    training_program_day_id CHAR(36) NOT NULL,
    parent_id CHAR(36),
    item_type VARCHAR(20) NOT NULL,
    title VARCHAR(250) NOT NULL,
    content TEXT,
    theory_minutes INT NOT NULL DEFAULT 0,
    practice_minutes INT NOT NULL DEFAULT 0,
    position INT NOT NULL,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    parent_position_scope CHAR(36) GENERATED ALWAYS AS (COALESCE(parent_id, '')) STORED,
    CONSTRAINT uq_training_program_items_position UNIQUE (training_program_day_id, parent_position_scope, position),
    CONSTRAINT ck_training_program_items_type CHECK (item_type IN ('MODULE','SUBMODULE')),
    CONSTRAINT ck_training_program_items_durations_non_negative CHECK (theory_minutes >= 0 AND practice_minutes >= 0),
    CONSTRAINT ck_training_program_items_position_positive CHECK (position > 0),
    CONSTRAINT ck_training_program_items_parent_by_type CHECK ((item_type = 'MODULE' AND parent_id IS NULL) OR (item_type = 'SUBMODULE' AND parent_id IS NOT NULL)),
    CONSTRAINT fk_training_program_items_day FOREIGN KEY (training_program_day_id) REFERENCES training_program_days(id) ON DELETE CASCADE,
    CONSTRAINT fk_training_program_items_parent FOREIGN KEY (parent_id) REFERENCES training_program_items(id),
    INDEX ix_training_program_items_day (training_program_day_id),
    INDEX ix_training_program_items_parent (parent_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE training_program_item_methods (
    training_program_item_id CHAR(36) NOT NULL,
    method VARCHAR(40) NOT NULL,
    PRIMARY KEY (training_program_item_id, method),
    CONSTRAINT ck_training_program_item_methods_method CHECK (method IN ('EXPOSE','DEMONSTRATION','EXERCICE_PRATIQUE','ETUDE_DE_CAS','MISE_EN_SITUATION','ECHANGE_COLLECTIF','EVALUATION')),
    CONSTRAINT fk_training_program_item_methods_item FOREIGN KEY (training_program_item_id) REFERENCES training_program_items(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE training_pricings (
    id CHAR(36) NOT NULL PRIMARY KEY,
    training_case_id CHAR(36) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'TND',
    trainer_cost DECIMAL(15,3) NOT NULL DEFAULT 0,
    transport_cost DECIMAL(15,3) NOT NULL DEFAULT 0,
    room_cost DECIMAL(15,3) NOT NULL DEFAULT 0,
    meal_cost DECIMAL(15,3) NOT NULL DEFAULT 0,
    other_cost DECIMAL(15,3) NOT NULL DEFAULT 0,
    margin_rate DECIMAL(6,3) NOT NULL DEFAULT 0,
    vat_rate DECIMAL(6,3) NOT NULL DEFAULT 19,
    vat_exemption_reason TEXT,
    vat_legal_reference VARCHAR(500),
    trainer_daily_rate_snapshot DECIMAL(15,3),
    trainer_hourly_rate_snapshot DECIMAL(15,3),
    program_day_count_snapshot INT NOT NULL,
    program_duration_minutes_snapshot INT NOT NULL,
    trainer_cost_initialization_method VARCHAR(20) NOT NULL,
    is_submitted BOOLEAN NOT NULL DEFAULT FALSE,
    submitted_at DATETIME(6),
    is_validated BOOLEAN NOT NULL DEFAULT FALSE,
    validated_at DATETIME(6),
    returned_at DATETIME(6),
    return_reason TEXT,
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT uq_training_pricings_case UNIQUE (training_case_id),
    CONSTRAINT ck_training_pricings_currency CHECK (currency = 'TND'),
    CONSTRAINT ck_training_pricings_costs_non_negative CHECK (trainer_cost >= 0 AND transport_cost >= 0 AND room_cost >= 0 AND meal_cost >= 0 AND other_cost >= 0),
    CONSTRAINT ck_training_pricings_margin_rate CHECK (margin_rate >= 0 AND margin_rate <= 100),
    CONSTRAINT ck_training_pricings_vat_rate CHECK (vat_rate IN (19.000,13.000,7.000,0.000)),
    CONSTRAINT ck_training_pricings_zero_vat_justification CHECK (vat_rate <> 0 OR vat_exemption_reason IS NOT NULL OR vat_legal_reference IS NOT NULL),
    CONSTRAINT ck_training_pricings_snapshots_non_negative CHECK (program_day_count_snapshot >= 0 AND program_duration_minutes_snapshot >= 0),
    CONSTRAINT ck_training_pricings_initialization_method CHECK (trainer_cost_initialization_method IN ('DAILY_RATE','HOURLY_RATE','NONE')),
    CONSTRAINT fk_training_pricings_case FOREIGN KEY (training_case_id) REFERENCES training_cases(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE training_documents (
    id CHAR(36) NOT NULL PRIMARY KEY,
    training_case_id CHAR(36) NOT NULL,
    document_type VARCHAR(30) NOT NULL,
    status VARCHAR(20) NOT NULL,
    display_name VARCHAR(150) NOT NULL,
    internal_filename VARCHAR(255),
    original_filename VARCHAR(255),
    relative_path VARCHAR(500),
    mime_type VARCHAR(100),
    file_size BIGINT,
    sha256 VARCHAR(64),
    snapshot_data JSON,
    generation_error TEXT,
    generated_at DATETIME(6),
    created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    CONSTRAINT uq_training_documents_case_type UNIQUE (training_case_id, document_type),
    CONSTRAINT ck_training_documents_type CHECK (document_type IN ('PROGRAM','QUOTE','AGREEMENT','ATTENDANCE_SHEET','CERTIFICATE')),
    CONSTRAINT ck_training_documents_status CHECK (status IN ('PENDING','GENERATED','FAILED')),
    CONSTRAINT fk_training_documents_case FOREIGN KEY (training_case_id) REFERENCES training_cases(id) ON DELETE CASCADE,
    INDEX ix_training_documents_case (training_case_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
