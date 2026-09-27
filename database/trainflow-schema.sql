--
-- PostgreSQL database dump
--

-- Dumped from database version 12.4
-- Dumped by pg_dump version 12.4

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: activity_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.activity_logs (
    id uuid NOT NULL,
    administrator_id uuid,
    training_case_id uuid,
    action character varying(80) NOT NULL,
    entity_type character varying(80) NOT NULL,
    entity_id uuid,
    details jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: administrators; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.administrators (
    id uuid NOT NULL,
    full_name character varying(150) NOT NULL,
    email character varying(320) NOT NULL,
    password_hash character varying(255) NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    last_login_at timestamp with time zone
);


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: companies; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.companies (
    id uuid NOT NULL,
    name character varying(200) NOT NULL,
    address character varying(300),
    city character varying(120),
    postal_code character varying(30),
    country character varying(120),
    tax_identifier character varying(80),
    website character varying(300),
    notes text,
    is_archived boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: company_contacts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.company_contacts (
    id uuid NOT NULL,
    company_id uuid NOT NULL,
    full_name character varying(200) NOT NULL,
    email character varying(320),
    phone character varying(50),
    job_title character varying(150),
    is_primary boolean DEFAULT false NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: trainer_cvs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.trainer_cvs (
    id uuid NOT NULL,
    trainer_id uuid,
    original_filename character varying(255) NOT NULL,
    storage_filename character varying(255) NOT NULL,
    mime_type character varying(100) NOT NULL,
    file_size integer NOT NULL,
    sha256 character varying(64) NOT NULL,
    uploaded_at timestamp with time zone DEFAULT now() NOT NULL,
    extraction_status character varying(32) DEFAULT 'UPLOADED'::character varying NOT NULL,
    extraction_model character varying(120),
    extraction_duration_ms integer,
    raw_text text,
    parsed_json jsonb,
    extraction_error text,
    extraction_error_code character varying(64),
    CONSTRAINT ck_trainer_cv_extraction_status CHECK (((extraction_status)::text = ANY ((ARRAY['UPLOADED'::character varying, 'TEXT_EXTRACTED'::character varying, 'OCR_REQUIRED'::character varying, 'OCR_COMPLETED'::character varying, 'AI_ANALYSIS_PENDING'::character varying, 'AI_ANALYSIS_COMPLETED'::character varying, 'REVIEW_REQUIRED'::character varying, 'VALIDATED'::character varying, 'FAILED'::character varying])::text[])))
);


--
-- Name: trainers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.trainers (
    id uuid NOT NULL,
    first_name character varying(100),
    last_name character varying(100),
    full_name character varying(200) NOT NULL,
    email character varying(320),
    phone character varying(50),
    company character varying(200),
    job_title character varying(200),
    years_experience integer,
    hourly_rate numeric(12,2),
    daily_rate numeric(12,2),
    city character varying(120),
    country character varying(120),
    linkedin_url character varying(300),
    website character varying(300),
    notes text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    mobile_phone character varying(50),
    birth_date character varying(50),
    birth_place character varying(150),
    address character varying(300),
    employer_address character varying(300),
    CONSTRAINT ck_trainers_daily_rate_non_negative CHECK (((daily_rate IS NULL) OR (daily_rate >= (0)::numeric))),
    CONSTRAINT ck_trainers_hourly_rate_non_negative CHECK (((hourly_rate IS NULL) OR (hourly_rate >= (0)::numeric))),
    CONSTRAINT ck_trainers_years_experience_non_negative CHECK (((years_experience IS NULL) OR (years_experience >= 0)))
);


--
-- Name: training_case_counters; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.training_case_counters (
    year integer NOT NULL,
    next_value integer NOT NULL
);


--
-- Name: training_case_counters_year_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.training_case_counters_year_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: training_case_counters_year_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.training_case_counters_year_seq OWNED BY public.training_case_counters.year;


--
-- Name: training_cases; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.training_cases (
    id uuid NOT NULL,
    reference character varying(20) NOT NULL,
    company_id uuid NOT NULL,
    primary_contact_id uuid,
    theme character varying(250) NOT NULL,
    description text,
    status character varying(40) DEFAULT 'BROUILLON'::character varying NOT NULL,
    desired_start_date date,
    desired_end_date date,
    created_by uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    closed_at timestamp with time zone,
    is_archived boolean DEFAULT false NOT NULL,
    trainer_id uuid,
    CONSTRAINT ck_training_cases_status CHECK (((status)::text = ANY ((ARRAY['BROUILLON'::character varying, 'DEMANDE_RECUE'::character varying, 'RECHERCHE_FORMATEUR'::character varying, 'FORMATEUR_PROPOSE'::character varying, 'FORMATEUR_ACCEPTE'::character varying, 'BESOIN_A_COMPLETER'::character varying, 'BESOIN_COMPLETE'::character varying, 'PROGRAMME_EN_PREPARATION'::character varying, 'PROGRAMME_A_VALIDER'::character varying, 'PROGRAMME_VALIDE'::character varying, 'TARIFICATION_EN_PREPARATION'::character varying, 'TARIFICATION_A_VALIDER'::character varying, 'TARIFICATION_VALIDEE'::character varying, 'DOCUMENTS_A_GENERER'::character varying, 'DOCUMENTS_GENERES'::character varying, 'TERMINE'::character varying, 'ANNULE'::character varying, 'ARCHIVE'::character varying])::text[])))
);


--
-- Name: training_documents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.training_documents (
    id uuid NOT NULL,
    training_case_id uuid NOT NULL,
    document_type character varying(30) NOT NULL,
    status character varying(20) NOT NULL,
    display_name character varying(150) NOT NULL,
    internal_filename character varying(255),
    original_filename character varying(255),
    relative_path character varying(500),
    mime_type character varying(100),
    file_size bigint,
    sha256 character varying(64),
    snapshot_data jsonb,
    generation_error text,
    generated_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_training_documents_status CHECK (((status)::text = ANY ((ARRAY['PENDING'::character varying, 'GENERATED'::character varying, 'FAILED'::character varying])::text[]))),
    CONSTRAINT ck_training_documents_type CHECK (((document_type)::text = ANY ((ARRAY['PROGRAM'::character varying, 'QUOTE'::character varying, 'AGREEMENT'::character varying, 'ATTENDANCE_SHEET'::character varying, 'CERTIFICATE'::character varying])::text[])))
);


--
-- Name: training_needs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.training_needs (
    id uuid NOT NULL,
    training_case_id uuid NOT NULL,
    target_audience character varying(500),
    location character varying(300),
    participant_count integer,
    delivery_mode character varying(20),
    duration_hours numeric(8,2),
    objectives text,
    desired_start_date date,
    desired_end_date date,
    constraints text,
    is_validated boolean DEFAULT false NOT NULL,
    validated_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_training_needs_date_range CHECK (((desired_end_date IS NULL) OR (desired_start_date IS NULL) OR (desired_end_date >= desired_start_date))),
    CONSTRAINT ck_training_needs_delivery_mode CHECK (((delivery_mode IS NULL) OR ((delivery_mode)::text = ANY ((ARRAY['PRESENTIEL'::character varying, 'DISTANCIEL'::character varying, 'HYBRIDE'::character varying])::text[])))),
    CONSTRAINT ck_training_needs_duration_hours_positive CHECK (((duration_hours IS NULL) OR (duration_hours > (0)::numeric))),
    CONSTRAINT ck_training_needs_participant_count_positive CHECK (((participant_count IS NULL) OR (participant_count > 0)))
);


--
-- Name: training_pricings; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.training_pricings (
    id uuid NOT NULL,
    training_case_id uuid NOT NULL,
    currency character varying(3) DEFAULT 'TND'::character varying NOT NULL,
    trainer_cost numeric(15,3) DEFAULT '0'::numeric NOT NULL,
    transport_cost numeric(15,3) DEFAULT '0'::numeric NOT NULL,
    room_cost numeric(15,3) DEFAULT '0'::numeric NOT NULL,
    meal_cost numeric(15,3) DEFAULT '0'::numeric NOT NULL,
    other_cost numeric(15,3) DEFAULT '0'::numeric NOT NULL,
    margin_rate numeric(6,3) DEFAULT '0'::numeric NOT NULL,
    vat_rate numeric(6,3) DEFAULT '19'::numeric NOT NULL,
    vat_exemption_reason text,
    vat_legal_reference character varying(500),
    trainer_daily_rate_snapshot numeric(15,3),
    trainer_hourly_rate_snapshot numeric(15,3),
    program_day_count_snapshot integer NOT NULL,
    program_duration_minutes_snapshot integer NOT NULL,
    trainer_cost_initialization_method character varying(20) NOT NULL,
    is_submitted boolean DEFAULT false NOT NULL,
    submitted_at timestamp with time zone,
    is_validated boolean DEFAULT false NOT NULL,
    validated_at timestamp with time zone,
    returned_at timestamp with time zone,
    return_reason text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_training_pricings_costs_non_negative CHECK (((trainer_cost >= (0)::numeric) AND (transport_cost >= (0)::numeric) AND (room_cost >= (0)::numeric) AND (meal_cost >= (0)::numeric) AND (other_cost >= (0)::numeric))),
    CONSTRAINT ck_training_pricings_currency CHECK (((currency)::text = 'TND'::text)),
    CONSTRAINT ck_training_pricings_initialization_method CHECK (((trainer_cost_initialization_method)::text = ANY ((ARRAY['DAILY_RATE'::character varying, 'HOURLY_RATE'::character varying, 'NONE'::character varying])::text[]))),
    CONSTRAINT ck_training_pricings_margin_rate CHECK (((margin_rate >= (0)::numeric) AND (margin_rate <= (100)::numeric))),
    CONSTRAINT ck_training_pricings_program_snapshots_non_negative CHECK (((program_day_count_snapshot >= 0) AND (program_duration_minutes_snapshot >= 0))),
    CONSTRAINT ck_training_pricings_vat_rate CHECK ((vat_rate = ANY (ARRAY[19.000, 13.000, 7.000, 0.000]))),
    CONSTRAINT ck_training_pricings_zero_vat_justification CHECK (((vat_rate <> (0)::numeric) OR (vat_exemption_reason IS NOT NULL) OR (vat_legal_reference IS NOT NULL)))
);


--
-- Name: training_program_days; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.training_program_days (
    id uuid NOT NULL,
    training_program_id uuid NOT NULL,
    title character varying(250) NOT NULL,
    "position" integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_training_program_days_position_positive CHECK (("position" > 0))
);


--
-- Name: training_program_item_methods; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.training_program_item_methods (
    training_program_item_id uuid NOT NULL,
    method character varying(40) NOT NULL,
    CONSTRAINT ck_training_program_item_methods_method CHECK (((method)::text = ANY ((ARRAY['EXPOSE'::character varying, 'DEMONSTRATION'::character varying, 'EXERCICE_PRATIQUE'::character varying, 'ETUDE_DE_CAS'::character varying, 'MISE_EN_SITUATION'::character varying, 'ECHANGE_COLLECTIF'::character varying, 'EVALUATION'::character varying])::text[])))
);


--
-- Name: training_program_items; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.training_program_items (
    id uuid NOT NULL,
    training_program_day_id uuid NOT NULL,
    parent_id uuid,
    item_type character varying(20) NOT NULL,
    title character varying(250) NOT NULL,
    content text,
    theory_minutes integer DEFAULT 0 NOT NULL,
    practice_minutes integer DEFAULT 0 NOT NULL,
    "position" integer NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_training_program_items_durations_non_negative CHECK (((theory_minutes >= 0) AND (practice_minutes >= 0))),
    CONSTRAINT ck_training_program_items_parent_by_type CHECK (((((item_type)::text = 'MODULE'::text) AND (parent_id IS NULL)) OR (((item_type)::text = 'SUBMODULE'::text) AND (parent_id IS NOT NULL)))),
    CONSTRAINT ck_training_program_items_position_positive CHECK (("position" > 0)),
    CONSTRAINT ck_training_program_items_type CHECK (((item_type)::text = ANY ((ARRAY['MODULE'::character varying, 'SUBMODULE'::character varying])::text[])))
);


--
-- Name: training_programs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.training_programs (
    id uuid NOT NULL,
    training_case_id uuid NOT NULL,
    title character varying(250) NOT NULL,
    general_objectives text,
    evaluation_method text,
    is_submitted boolean DEFAULT false NOT NULL,
    submitted_at timestamp with time zone,
    is_validated boolean DEFAULT false NOT NULL,
    validated_at timestamp with time zone,
    returned_at timestamp with time zone,
    return_reason text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    prerequisites text
);


--
-- Name: training_case_counters year; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_case_counters ALTER COLUMN year SET DEFAULT nextval('public.training_case_counters_year_seq'::regclass);


--
-- Name: activity_logs activity_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity_logs
    ADD CONSTRAINT activity_logs_pkey PRIMARY KEY (id);


--
-- Name: administrators administrators_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.administrators
    ADD CONSTRAINT administrators_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: companies companies_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.companies
    ADD CONSTRAINT companies_pkey PRIMARY KEY (id);


--
-- Name: company_contacts company_contacts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.company_contacts
    ADD CONSTRAINT company_contacts_pkey PRIMARY KEY (id);


--
-- Name: trainer_cvs trainer_cv_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trainer_cvs
    ADD CONSTRAINT trainer_cv_pkey PRIMARY KEY (id);


--
-- Name: trainer_cvs trainer_cv_sha256_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trainer_cvs
    ADD CONSTRAINT trainer_cv_sha256_key UNIQUE (sha256);


--
-- Name: trainer_cvs trainer_cv_storage_filename_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trainer_cvs
    ADD CONSTRAINT trainer_cv_storage_filename_key UNIQUE (storage_filename);


--
-- Name: trainers trainers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trainers
    ADD CONSTRAINT trainers_pkey PRIMARY KEY (id);


--
-- Name: training_case_counters training_case_counters_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_case_counters
    ADD CONSTRAINT training_case_counters_pkey PRIMARY KEY (year);


--
-- Name: training_cases training_cases_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_cases
    ADD CONSTRAINT training_cases_pkey PRIMARY KEY (id);


--
-- Name: training_cases training_cases_reference_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_cases
    ADD CONSTRAINT training_cases_reference_key UNIQUE (reference);


--
-- Name: training_documents training_documents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_documents
    ADD CONSTRAINT training_documents_pkey PRIMARY KEY (id);


--
-- Name: training_needs training_needs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_needs
    ADD CONSTRAINT training_needs_pkey PRIMARY KEY (id);


--
-- Name: training_pricings training_pricings_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_pricings
    ADD CONSTRAINT training_pricings_pkey PRIMARY KEY (id);


--
-- Name: training_program_days training_program_days_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_program_days
    ADD CONSTRAINT training_program_days_pkey PRIMARY KEY (id);


--
-- Name: training_program_item_methods training_program_item_methods_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_program_item_methods
    ADD CONSTRAINT training_program_item_methods_pkey PRIMARY KEY (training_program_item_id, method);


--
-- Name: training_program_items training_program_items_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_program_items
    ADD CONSTRAINT training_program_items_pkey PRIMARY KEY (id);


--
-- Name: training_programs training_programs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_programs
    ADD CONSTRAINT training_programs_pkey PRIMARY KEY (id);


--
-- Name: training_documents uq_training_documents_case_type; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_documents
    ADD CONSTRAINT uq_training_documents_case_type UNIQUE (training_case_id, document_type);


--
-- Name: training_program_days uq_training_program_days_program_position; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_program_days
    ADD CONSTRAINT uq_training_program_days_program_position UNIQUE (training_program_id, "position");


--
-- Name: ix_activity_logs_training_case_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_activity_logs_training_case_id ON public.activity_logs USING btree (training_case_id);


--
-- Name: ix_administrators_email; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_administrators_email ON public.administrators USING btree (email);


--
-- Name: ix_companies_city; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_companies_city ON public.companies USING btree (city);


--
-- Name: ix_companies_country; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_companies_country ON public.companies USING btree (country);


--
-- Name: ix_companies_is_archived; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_companies_is_archived ON public.companies USING btree (is_archived);


--
-- Name: ix_companies_lower_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_companies_lower_name ON public.companies USING btree (lower((name)::text));


--
-- Name: ix_company_contacts_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_company_contacts_company_id ON public.company_contacts USING btree (company_id);


--
-- Name: ix_trainer_cvs_sha256; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_trainer_cvs_sha256 ON public.trainer_cvs USING btree (sha256);


--
-- Name: ix_trainer_cvs_trainer_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_trainer_cvs_trainer_id ON public.trainer_cvs USING btree (trainer_id);


--
-- Name: ix_trainers_company; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_trainers_company ON public.trainers USING btree (company);


--
-- Name: ix_trainers_email; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_trainers_email ON public.trainers USING btree (email);


--
-- Name: ix_trainers_full_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_trainers_full_name ON public.trainers USING btree (full_name);


--
-- Name: ix_training_cases_company_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_training_cases_company_id ON public.training_cases USING btree (company_id);


--
-- Name: ix_training_cases_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_training_cases_created_at ON public.training_cases USING btree (created_at);


--
-- Name: ix_training_cases_is_archived; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_training_cases_is_archived ON public.training_cases USING btree (is_archived);


--
-- Name: ix_training_cases_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_training_cases_status ON public.training_cases USING btree (status);


--
-- Name: ix_training_cases_theme; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_training_cases_theme ON public.training_cases USING btree (theme);


--
-- Name: ix_training_cases_trainer_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_training_cases_trainer_id ON public.training_cases USING btree (trainer_id);


--
-- Name: ix_training_documents_training_case_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_training_documents_training_case_id ON public.training_documents USING btree (training_case_id);


--
-- Name: ix_training_needs_training_case_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_training_needs_training_case_id ON public.training_needs USING btree (training_case_id);


--
-- Name: ix_training_pricings_training_case_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_training_pricings_training_case_id ON public.training_pricings USING btree (training_case_id);


--
-- Name: ix_training_program_days_training_program_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_training_program_days_training_program_id ON public.training_program_days USING btree (training_program_id);


--
-- Name: ix_training_program_items_day_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_training_program_items_day_id ON public.training_program_items USING btree (training_program_day_id);


--
-- Name: ix_training_program_items_parent_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_training_program_items_parent_id ON public.training_program_items USING btree (parent_id);


--
-- Name: ix_training_programs_training_case_id; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_training_programs_training_case_id ON public.training_programs USING btree (training_case_id);


--
-- Name: uq_company_contacts_primary; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_company_contacts_primary ON public.company_contacts USING btree (company_id) WHERE (is_primary IS TRUE);


--
-- Name: uq_training_program_modules_day_position; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_training_program_modules_day_position ON public.training_program_items USING btree (training_program_day_id, "position") WHERE (parent_id IS NULL);


--
-- Name: uq_training_program_submodules_parent_position; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_training_program_submodules_parent_position ON public.training_program_items USING btree (parent_id, "position") WHERE (parent_id IS NOT NULL);


--
-- Name: activity_logs activity_logs_administrator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity_logs
    ADD CONSTRAINT activity_logs_administrator_id_fkey FOREIGN KEY (administrator_id) REFERENCES public.administrators(id) ON DELETE SET NULL;


--
-- Name: activity_logs activity_logs_training_case_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.activity_logs
    ADD CONSTRAINT activity_logs_training_case_id_fkey FOREIGN KEY (training_case_id) REFERENCES public.training_cases(id) ON DELETE CASCADE;


--
-- Name: company_contacts company_contacts_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.company_contacts
    ADD CONSTRAINT company_contacts_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id) ON DELETE CASCADE;


--
-- Name: training_cases fk_training_cases_trainer_id; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_cases
    ADD CONSTRAINT fk_training_cases_trainer_id FOREIGN KEY (trainer_id) REFERENCES public.trainers(id) ON DELETE SET NULL;


--
-- Name: trainer_cvs trainer_cv_trainer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.trainer_cvs
    ADD CONSTRAINT trainer_cv_trainer_id_fkey FOREIGN KEY (trainer_id) REFERENCES public.trainers(id) ON DELETE SET NULL;


--
-- Name: training_cases training_cases_company_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_cases
    ADD CONSTRAINT training_cases_company_id_fkey FOREIGN KEY (company_id) REFERENCES public.companies(id);


--
-- Name: training_cases training_cases_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_cases
    ADD CONSTRAINT training_cases_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.administrators(id);


--
-- Name: training_cases training_cases_primary_contact_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_cases
    ADD CONSTRAINT training_cases_primary_contact_id_fkey FOREIGN KEY (primary_contact_id) REFERENCES public.company_contacts(id) ON DELETE SET NULL;


--
-- Name: training_documents training_documents_training_case_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_documents
    ADD CONSTRAINT training_documents_training_case_id_fkey FOREIGN KEY (training_case_id) REFERENCES public.training_cases(id) ON DELETE CASCADE;


--
-- Name: training_needs training_needs_training_case_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_needs
    ADD CONSTRAINT training_needs_training_case_id_fkey FOREIGN KEY (training_case_id) REFERENCES public.training_cases(id) ON DELETE CASCADE;


--
-- Name: training_pricings training_pricings_training_case_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_pricings
    ADD CONSTRAINT training_pricings_training_case_id_fkey FOREIGN KEY (training_case_id) REFERENCES public.training_cases(id) ON DELETE CASCADE;


--
-- Name: training_program_days training_program_days_training_program_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_program_days
    ADD CONSTRAINT training_program_days_training_program_id_fkey FOREIGN KEY (training_program_id) REFERENCES public.training_programs(id) ON DELETE CASCADE;


--
-- Name: training_program_item_methods training_program_item_methods_training_program_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_program_item_methods
    ADD CONSTRAINT training_program_item_methods_training_program_item_id_fkey FOREIGN KEY (training_program_item_id) REFERENCES public.training_program_items(id) ON DELETE CASCADE;


--
-- Name: training_program_items training_program_items_parent_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_program_items
    ADD CONSTRAINT training_program_items_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.training_program_items(id) ON DELETE CASCADE;


--
-- Name: training_program_items training_program_items_training_program_day_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_program_items
    ADD CONSTRAINT training_program_items_training_program_day_id_fkey FOREIGN KEY (training_program_day_id) REFERENCES public.training_program_days(id) ON DELETE CASCADE;


--
-- Name: training_programs training_programs_training_case_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.training_programs
    ADD CONSTRAINT training_programs_training_case_id_fkey FOREIGN KEY (training_case_id) REFERENCES public.training_cases(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

