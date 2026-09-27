CREATE TABLE companies (
    id uuid PRIMARY KEY,
    name varchar(200) NOT NULL,
    address varchar(300), city varchar(120), postal_code varchar(30), country varchar(120),
    tax_identifier varchar(80), website varchar(300), notes text,
    is_archived boolean DEFAULT false NOT NULL,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL
);
CREATE UNIQUE INDEX ix_companies_lower_name ON companies (lower(name));
CREATE TABLE company_contacts (
    id uuid PRIMARY KEY,
    company_id uuid NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    full_name varchar(200) NOT NULL, email varchar(320), phone varchar(50), job_title varchar(150),
    is_primary boolean DEFAULT false NOT NULL,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL
);
CREATE UNIQUE INDEX uq_company_contacts_primary ON company_contacts(company_id) WHERE is_primary IS true;
