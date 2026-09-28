CREATE TABLE administrators (
    id char(36) PRIMARY KEY,
    full_name varchar(150) NOT NULL,
    email varchar(320) NOT NULL UNIQUE,
    password_hash varchar(255) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at datetime(6) DEFAULT CURRENT_TIMESTAMP(6) NOT NULL,
    updated_at datetime(6) DEFAULT CURRENT_TIMESTAMP(6) NOT NULL,
    last_login_at datetime(6)
);
CREATE TABLE companies (
    id char(36) PRIMARY KEY,
    name varchar(200) NOT NULL,
    address varchar(300), city varchar(120), postal_code varchar(30), country varchar(120),
    tax_identifier varchar(80), website varchar(300), notes text,
    is_archived boolean DEFAULT false NOT NULL,
    created_at datetime(6) DEFAULT CURRENT_TIMESTAMP(6) NOT NULL,
    updated_at datetime(6) DEFAULT CURRENT_TIMESTAMP(6) NOT NULL
);
CREATE UNIQUE INDEX ix_companies_name ON companies (name);
CREATE TABLE company_contacts (
    id char(36) PRIMARY KEY,
    company_id char(36) NOT NULL,
    full_name varchar(200) NOT NULL, email varchar(320), phone varchar(50), job_title varchar(150),
    is_primary boolean DEFAULT false NOT NULL,
    created_at datetime(6) DEFAULT CURRENT_TIMESTAMP(6) NOT NULL,
    updated_at datetime(6) DEFAULT CURRENT_TIMESTAMP(6) NOT NULL,
    primary_guard tinyint GENERATED ALWAYS AS (IF(is_primary, 1, NULL)) STORED,
    CONSTRAINT fk_company_contacts_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
);
CREATE UNIQUE INDEX uq_company_contacts_primary ON company_contacts(company_id, primary_guard);
