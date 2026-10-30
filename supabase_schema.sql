-- ========================================================
-- SGNIA: SINDH GOVERNMENT NOTIFICATION ISSUING AUTHORITY
-- SUPABASE POSTGRESQL SCHEMA WITH ROW LEVEL SECURITY (RLS)
-- ========================================================

-- 1. DEPARTMENTS TABLE
CREATE TABLE IF NOT EXISTS public.departments (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    short_name TEXT,
    code VARCHAR(32) UNIQUE,
    parent_id BIGINT REFERENCES public.departments(id) ON DELETE SET NULL,
    overview TEXT,
    key_functions TEXT,
    governance_hierarchy TEXT,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);

-- 2. USERS (STAFF ACCOUNTS) TABLE
CREATE TABLE IF NOT EXISTS public.users (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    email VARCHAR(254) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(32) NOT NULL,
    department VARCHAR(160) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON public.users(role);

-- 3. NOTIFICATIONS TABLE
CREATE TABLE IF NOT EXISTS public.notifications (
    id BIGSERIAL PRIMARY KEY,
    reference VARCHAR(64) NOT NULL UNIQUE,
    title VARCHAR(240) NOT NULL,
    category VARCHAR(80) NOT NULL DEFAULT 'Notification',
    department VARCHAR(160) NOT NULL,
    department_code VARCHAR(32),
    subject VARCHAR(500) NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    document_date DATE,
    official_reference VARCHAR(120),
    pdf_url TEXT,
    pdf_path VARCHAR(500),
    pdf_sha256 VARCHAR(64),
    status VARCHAR(32) NOT NULL DEFAULT 'Draft',
    portal_listing_number INTEGER,
    source_url TEXT,
    created_by_id BIGINT REFERENCES public.users(id) ON DELETE SET NULL,
    reviewed_by_id BIGINT REFERENCES public.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now())
);
CREATE INDEX IF NOT EXISTS idx_notifications_status ON public.notifications(status);
CREATE INDEX IF NOT EXISTS idx_notifications_reference ON public.notifications(reference);
CREATE INDEX IF NOT EXISTS idx_notifications_doc_date ON public.notifications(document_date DESC);

-- 4. NOTIFICATION VERSIONS TABLE
CREATE TABLE IF NOT EXISTS public.notification_versions (
    id BIGSERIAL PRIMARY KEY,
    notification_id BIGINT NOT NULL REFERENCES public.notifications(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL DEFAULT 1,
    title VARCHAR(240) NOT NULL,
    category VARCHAR(80) NOT NULL DEFAULT 'Notification',
    department VARCHAR(160) NOT NULL,
    subject VARCHAR(500) NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    document_date DATE,
    official_reference VARCHAR(120),
    pdf_url TEXT,
    pdf_path VARCHAR(500),
    pdf_sha256 VARCHAR(64),
    signature VARCHAR(128),
    signature_key_id VARCHAR(64),
    signature_signed_at TIMESTAMPTZ,
    change_summary VARCHAR(500) NOT NULL DEFAULT '',
    status VARCHAR(32) NOT NULL DEFAULT 'Draft',
    created_by_id BIGINT REFERENCES public.users(id) ON DELETE SET NULL,
    reviewed_by_id BIGINT REFERENCES public.users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    CONSTRAINT uq_notification_version UNIQUE (notification_id, version_number)
);

-- 5. SIGNING KEYS TABLE
CREATE TABLE IF NOT EXISTS public.signing_keys (
    key_id VARCHAR(64) PRIMARY KEY,
    public_key VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    active BOOLEAN NOT NULL DEFAULT true
);

-- 6. AUDIT LOGS TABLE
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id BIGSERIAL PRIMARY KEY,
    actor_id BIGINT REFERENCES public.users(id) ON DELETE SET NULL,
    action VARCHAR(80) NOT NULL,
    target_type VARCHAR(80) NOT NULL,
    target_id VARCHAR(80),
    details VARCHAR(500) NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc'::text, now()),
    previous_hash VARCHAR(64),
    entry_hash VARCHAR(64) UNIQUE
);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON public.audit_logs(created_at DESC);

-- ========================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ========================================================
ALTER TABLE public.departments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notification_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.signing_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow public read active departments" ON public.departments;
DROP POLICY IF EXISTS "Allow public read published notifications" ON public.notifications;
DROP POLICY IF EXISTS "Allow public read published versions" ON public.notification_versions;
DROP POLICY IF EXISTS "Allow public read active signing keys" ON public.signing_keys;

CREATE POLICY "Allow public read active departments"
ON public.departments FOR SELECT TO anon, authenticated
USING (active = true);

CREATE POLICY "Allow public read published notifications"
ON public.notifications FOR SELECT TO anon, authenticated
USING (status = 'Published');

CREATE POLICY "Allow public read published versions"
ON public.notification_versions FOR SELECT TO anon, authenticated
USING (status = 'Published');

CREATE POLICY "Allow public read active signing keys"
ON public.signing_keys FOR SELECT TO anon, authenticated
USING (active = true);

-- ========================================================
-- SEED DATA: 43 SINDH DEPARTMENTS WITH PROFILES
-- ========================================================
INSERT INTO public.departments (name, short_name, code, overview, key_functions, governance_hierarchy) VALUES
('Agriculture, Supply & Prices Department', 'Agriculture & Supply', 'ASP', 'The Agriculture, Supply & Prices Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Auqaf Religious Affairs Zakat & Ushr Department', 'Auqaf, Religious Affairs & Zakat', 'ARAZU', 'The Auqaf Religious Affairs Zakat & Ushr Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Board of Revenue (BOR)', 'Board of Revenue', 'BOR', 'The Board of Revenue (BOR) operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Chief Minister''s Secretariat & Inspection Team', 'CM Secretariat', 'CMSIT', 'The Chief Minister''s Secretariat & Inspection Team operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('College Education Department', 'College Education', 'CED', 'The College Education Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Cooperative Department', 'Cooperative', 'COOP', 'The Cooperative Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Culture, Tourism & Antiquities Department', 'Culture & Tourism', 'CTA', 'The Culture, Tourism & Antiquities Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Department of Empowerment of Persons with Disabilities', 'Empowerment of Persons with Disabilities', 'DEPD', 'The Department of Empowerment of Persons with Disabilities operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Energy Department', 'Energy', 'ENERGY', 'The Energy Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Enquiries & Anti-Corruption Establishment', 'Anti-Corruption Establishment', 'EACE', 'The Enquiries & Anti-Corruption Establishment operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Environment, Climate Change & Coastal Development Department', 'Environment & Climate Change', 'ECCD', 'The Environment, Climate Change & Coastal Development Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Excise, Taxation & Narcotics Control Department', 'Excise & Taxation', 'ETNC', 'The Excise, Taxation & Narcotics Control Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Finance Department', 'Finance', 'FIN', 'The Finance Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Food Department & Sindh Food Authority', 'Food & Food Authority', 'FD-SFA', 'The Food Department & Sindh Food Authority operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Forest & Wildlife Department', 'Forest & Wildlife', 'FW', 'The Forest & Wildlife Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Health Department', 'Health', 'HEALTH', 'The Health Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Home Department & Sindh Police', 'Home & Police', 'HOME-POL', 'The Home Department & Sindh Police operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Human Rights Department', 'Human Rights', 'HRD', 'The Human Rights Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Industries & Commerce Department', 'Industries & Commerce', 'IC', 'The Industries & Commerce Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Information Department', 'Information', 'INFO', 'The Information Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Inter Provincial Coordination Department', 'Inter Provincial Coordination', 'IPCD', 'The Inter Provincial Coordination Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Investment Department', 'Investment', 'INVEST', 'The Investment Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Irrigation Department', 'Irrigation', 'IRR', 'The Irrigation Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Labour & Human Resources Department', 'Labour & Human Resources', 'LHR', 'The Labour & Human Resources Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Law Department & Prosecutor General', 'Law & Prosecution', 'LDPG', 'The Law Department & Prosecutor General operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Livestock & Fisheries Department', 'Livestock & Fisheries', 'LF', 'The Livestock & Fisheries Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Local Government & Housing Town Planning Department', 'Local Government & Housing', 'LGHTP', 'The Local Government & Housing Town Planning Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Mines & Mineral Development Department', 'Mines & Minerals', 'MMD', 'The Mines & Mineral Development Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Minorities Affairs Department', 'Minorities Affairs', 'MA', 'The Minorities Affairs Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Planning & Development Department', 'Planning & Development', 'P&D', 'The Planning & Development Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Population Welfare Department', 'Population Welfare', 'PWD', 'The Population Welfare Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Public Health Engineering & Rural Development Department', 'Public Health Engineering', 'PHERDD', 'The Public Health Engineering & Rural Development Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Rehabilitation Department', 'Rehabilitation', 'REHAB', 'The Rehabilitation Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('School Education & Literacy Department', 'School Education & Literacy', 'SELD', 'The School Education & Literacy Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Science & Information Technology Department', 'Science & Information Technology', 'SIT', 'The Science & Information Technology Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Services, General Administration & Coordination Department (SGA&CD)', 'Services & General Administration', 'SGA-CD', 'The Services, General Administration & Coordination Department (SGA&CD) operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Sindh Higher Education Commission (Sindh HEC)', 'Sindh HEC', 'SHEC', 'The Sindh Higher Education Commission (Sindh HEC) operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Social Welfare Department', 'Social Welfare', 'SWD', 'The Social Welfare Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Sports & Youth Affairs Department', 'Sports & Youth Affairs', 'SYA', 'The Sports & Youth Affairs Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Transport & Mass Transit Department', 'Transport & Mass Transit', 'TMT', 'The Transport & Mass Transit Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Universities & Boards Department', 'Universities & Boards', 'UBD', 'The Universities & Boards Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Women Development Department', 'Women Development', 'WDD', 'The Women Development Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Works & Services Department', 'Works & Services', 'W&S', 'The Works & Services Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and developmental administration within its respective sector.', '• Formulation and execution of provincial policies and strategic directives.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.')
ON CONFLICT (name) DO UPDATE SET
  short_name = EXCLUDED.short_name,
  code = EXCLUDED.code,
  overview = EXCLUDED.overview,
  key_functions = EXCLUDED.key_functions,
  governance_hierarchy = EXCLUDED.governance_hierarchy;

-- ========================================================
-- SEED DATA: 55 OFFICIAL NOTIFICATIONS
-- ========================================================
INSERT INTO public.notifications (
    reference, portal_listing_number, title, category, department,
    department_code, document_date, official_reference, pdf_url, source_url, status
) VALUES
('SGNIA-ARCH-001', 1, 'Hosting of Government Websites in Pakistan', 'Notification', 'Science, Information Technology (IS&T) Department', 'SIT', '2026-09-18', NULL, 'https://www.sindh.gov.pk/storage/notification/EKqqtUqbPsT2rzrihJBD1SKaTTULTY8iJ6GAz0qC.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-002', 2, 'SACM Seher Gul Bhatti', 'Notification', 'Services, General Administration & Coordination Department (SGA&CD)', 'SGA-CD', '2026-07-04', 'SOVI(SGA&CD)4(24)/2026', 'https://www.sindh.gov.pk/storage/notification/86dsQGIzx6TEL44K6s6omIhBiQAIhqqXXU47f5Ak.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-003', 3, 'Advisory', 'Advisory', 'Science, Information Technology (IS&T) Department', 'SIT', '2026-07-14', NULL, 'https://www.sindh.gov.pk/storage/notification/DbGhPMQtBJt1JOq52LyFtLcmeNZT0ncrxDZ4TfWC.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-004', 4, 'Advisory', 'Advisory', 'Science, Information Technology (IS&T) Department', 'SIT', '2026-07-14', 'DG-II/CERT/4/124/2023/P-I', 'https://www.sindh.gov.pk/storage/notification/M84iJKsEcTGj51hnKADLK5K7xPyFejWeelyESCi0.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-005', 5, 'Holidays for Hindu Community for the Occasion of Dulhandi and Holi', 'Notification', 'Services, General Administration & Coordination Department (SGA&CD)', 'SGA-CD', '2026-03-02', 'CTC(SGA&CD)27(2)2010', 'https://www.sindh.gov.pk/storage/notification/Vpw4dnkKmZwHMYjMtcwJNt4v25ijmfXkhm8fahxo.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-007', 7, 'CYBER SECURITY ADVISORY ON ANDROID ZERO-DAY EXPLOIT IMMEDIATE ACTION', 'Advisory', 'Science, Information Technology (IS&T) Department', 'SIT', '2026-01-28', NULL, 'https://www.sindh.gov.pk/storage/notification/E2QyNbOlj1rEnKDpqVw7JlDP0UnjM4HiW1igdL4U.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-008', 8, 'Cyber Security Advisory on Prevention Against Exploitation of Video Conferencing Applications (Zoom, Google Meet etc)', 'Advisory', 'Science, Information Technology (IS&T) Department', 'SIT', '2025-12-19', NULL, 'https://www.sindh.gov.pk/storage/notification/91KSd8M00WHlXe2XWYRwtj5fVedPprKvFEcyM6cs.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-009', 9, 'Cyber Security Advisory on Risks Associated With Smart / Internet-Enabled IPTV Devices in Sensitive Premises Immediate Mitigation Measures', 'Advisory', 'Science, Information Technology (IS&T) Department', 'SIT', '2025-12-17', NULL, 'https://www.sindh.gov.pk/storage/notification/gwaa6YnZGMHo6OewaO59AJAmEanfZ4zVcf0YgWg6.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-010', 10, 'Cyber Security Advisory on Immediate Mitigation of Multiple Critical Vulnerabilities', 'Advisory', 'Science, Information Technology (IS&T) Department', 'SIT', '2025-11-13', NULL, 'https://www.sindh.gov.pk/storage/notification/TwZbR1JIFggsYiahHppGvjOEzVasz1tE8Ar2bQQC.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-011', 11, 'Cyber Security Advisory on Risks of Hosting Government Email Infrastructure Outside National Jurisdiction', 'Advisory', 'Science, Information Technology (IS&T) Department', 'SIT', '2025-11-13', NULL, 'https://www.sindh.gov.pk/storage/notification/YxH9l13VG7LvTHt3PnkiMNwiDWpX0ihLe6bXGpsK.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-013', 13, 'Mr. Muhammad Ismail Rahoo', 'Notification', 'Services, General Administration & Coordination Department (SGA&CD)', 'SGA-CD', '2025-09-26', 'SOVI(SGA&CD)2(1)/2024', 'https://www.sindh.gov.pk/storage/notification/kNJvWyfI1e96lAK8AAeGe2O4hGlyZwyj4w1dGvXA.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-014', 14, 'Allocate and Re allocate portfolios of Minister', 'Notification', 'Services, General Administration & Coordination Department (SGA&CD)', 'SGA-CD', '2025-09-26', 'SOVI(SGA&CD)2(1)/2024', 'https://www.sindh.gov.pk/storage/notification/NUBVPC7Mf2Xqiv8Ko4orXyRM0KDYMeMxBTNuDyUC.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-015', 15, 'Cyber Security Advisory -Revamping CS Postures of Government Websites', 'Advisory', 'Science, Information Technology (IS&T) Department', 'SIT', '2025-08-08', NULL, 'https://www.sindh.gov.pk/storage/notification/tvQLHxleLzEm25SLnY41DcNc9XO6ksqu3NInaVaD.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-016', 16, 'IRRIGATION DEPARTMENT ORDER', 'Order', 'Irrigation Department', 'IRR', '2025-08-07', NULL, 'https://www.sindh.gov.pk/storage/notification/AQTZAGE1ut3sOfOLd1pfyyQD5byktE8LHXHXury1.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-017', 17, 'CYBER SECURITY ADVISORY -IVANTI ZERO DAY ATTACK ON TELECOM IT NETWORK', 'Advisory', 'Science, Information Technology (IS&T) Department', 'SIT', '2025-08-04', NULL, 'https://www.sindh.gov.pk/storage/notification/s4hVYcCYTwnH2kHUFURlk6u5eeIGlOnRGu6fjti5.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-018', 18, 'Advisory', 'Advisory', 'Science, Information Technology (IS&T) Department', 'SIT', '2025-07-11', NULL, 'https://www.sindh.gov.pk/storage/notification/I9lOUpkcrcER8s13gchRUDnjKa7kv6mQO8XKIqlS.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-019', 19, 'Advisory', 'Advisory', 'Science, Information Technology (IS&T) Department', 'SIT', '2025-07-11', NULL, 'https://www.sindh.gov.pk/storage/notification/erumRCNOtWxObnr7hKhV3yaj5hV0W0kspE6ydIGX.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-020', 20, 'Advisory', 'Advisory', 'Science, Information Technology (IS&T) Department', 'SIT', '2025-07-11', NULL, 'https://www.sindh.gov.pk/storage/notification/NbyZkt5RJNNSoqQdNWkV9TBYtORzNFCIS6pBQKIy.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-021', 21, 'Advisory', 'Advisory', 'Science, Information Technology (IS&T) Department', 'SIT', '2025-07-11', NULL, 'https://www.sindh.gov.pk/storage/notification/Rf6VocBpvvb1XdxhTMKqPPMejgnDeCnDvKamujhK.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-022', 22, 'Advisory', 'Advisory', 'Science, Information Technology (IS&T) Department', 'SIT', '2025-07-10', NULL, 'https://www.sindh.gov.pk/storage/notification/RsAy4INAhviDaEfAS0tIQ9EDIXEnsYaTyj2yYkSL.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-023', 23, 'Advisory', 'Advisory', 'Science, Information Technology (IS&T) Department', 'SIT', '2025-07-10', NULL, 'https://www.sindh.gov.pk/storage/notification/7Z0eo3GDDwHdwrH0lSwPROqetq9ivUFe51V1mnzF.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-024', 24, 'Energy Department', 'Notification', 'Energy Department', 'ENERGY', '2025-06-23', NULL, 'https://www.sindh.gov.pk/storage/notification/68o4x8AUg1I3xgiDA0pfKxCCKVj34n5h9tAG358x.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-025', 25, 'Energy Department', 'Notification', 'Energy Department', 'ENERGY', '2025-06-23', NULL, 'https://www.sindh.gov.pk/storage/notification/GBSHc96r1ESVEfos8iBVEhY7T65tIM4vVmNE6Hx7.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-026', 26, 'Cyber Security Advisory Fortinet Farewell', 'Advisory', 'Science, Information Technology (IS&T) Department', 'SIT', '2025-05-27', NULL, 'https://www.sindh.gov.pk/storage/notification/Qso0DAjyl2N7X4PmhHgHoTWz8d8YbR3gHnXOoEP3.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-027', 27, 'Cyber Security Advisory Malicious Apps found on Google Play Store', 'Advisory', 'Science, Information Technology (IS&T) Department', 'SIT', '2025-05-27', NULL, 'https://www.sindh.gov.pk/storage/notification/2tgvRuFU0BAxiFXQaLQ6d6tfjmhUh6I72yUlmjnu.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-028', 28, 'Cyber Security Advisory Apple Patches Actively Exploited Web-kit Zero Day', 'Advisory', 'Science, Information Technology (IS&T) Department', 'SIT', '2025-05-27', NULL, 'https://www.sindh.gov.pk/storage/notification/vhwXShZd83cmLGQhivZEfiyf8wYo8Vj1iWA0LeOm.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-029', 29, 'Promotion', 'Notification', 'Services, General Administration & Coordination Department (SGA&CD)', 'SGA-CD', '2025-03-24', 'SOII(SGA&CD)7-1/2025', 'https://www.sindh.gov.pk/storage/notification/onT7XxArZeXgFYjwqLjEg0cIwoHIWqFQkpWIONzN.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-030', 30, 'Critical Information Infrastructure Protection', 'Notification', 'Science, Information Technology (IS&T) Department', 'SIT', '2025-02-25', NULL, 'https://www.sindh.gov.pk/storage/notification/q0giNQ04xecwAd3O4j0Ek4bdpCuYDQq8UpQV1Yhw.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-031', 31, 'National Computer Emergency Response Team', 'Notification', 'Science, Information Technology (IS&T) Department', 'SIT', '2025-02-25', NULL, 'https://www.sindh.gov.pk/storage/notification/dhRz7I11vmxmsoNZdcMLddmNLtry9DIusVgd2N8y.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-032', 32, 'Cyber Security Advisory', 'Advisory', 'Science, Information Technology (IS&T) Department', 'SIT', '2025-01-31', NULL, 'https://www.sindh.gov.pk/storage/notification/1m6J7NFR8a3EGRhwEFhrn2qms5DvYHAwuUZUE6hK.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-033', 33, 'Reply of Awarness Drive about Benami Transcation', 'Notification', 'Science, Information Technology (IS&T) Department', 'SIT', '2025-01-23', NULL, 'https://www.sindh.gov.pk/storage/notification/npJyTdhGr3ZJWoXADd81pdQCK2qlWSQfS31HwGL5.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-034', 34, 'Awarness Drive about Benami Transication', 'Notification', 'Finance Department', 'FIN', '2025-01-23', NULL, 'https://www.sindh.gov.pk/storage/notification/M6ZJVZ2We2ffgTSbzKvoFDDOwYGPqwmimIubxKyW.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-035', 35, 'Appointment of Spokesperson', 'Notification', 'Services, General Administration & Coordination Department (SGA&CD)', 'SGA-CD', '2025-01-13', 'SOVI(SGA&CD)5(1)/2025', 'https://www.sindh.gov.pk/storage/notification/m6SZan2cRJxE7P99oCyewfrxobZAnwxTE8yRWG3T.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-036', 36, 'Appointment of Special Assistant to CM Sindh', 'Notification', 'Services, General Administration & Coordination Department (SGA&CD)', 'SGA-CD', '2025-01-13', 'SOVI(SGA&CD)4(1)/2025', 'https://www.sindh.gov.pk/storage/notification/3XQobJRfEyd2S3PdVLuZospS0j7Qft3BuBgZWXGC.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-037', 37, 'Amendments in the Sindh Government Rules of Business 1986', 'Notification', 'Services, General Administration & Coordination Department (SGA&CD)', 'SGA-CD', '2025-01-03', NULL, 'https://www.sindh.gov.pk/storage/notification/Vb12RChHGzU3T1FUuqpXkK2oRY5fSZntzKEXZEfu.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-038', 38, 'EXPRESSION OF INTEREST', 'Notice', 'Services, General Administration & Coordination Department (SGA&CD)', 'SGA-CD', '2025-01-09', 'SO(T)(SGA&CD)77/2024', 'https://www.sindh.gov.pk/storage/notification/2FhFjVb5nFWwHXxZS2cFmgxru44CJtvnNeCjsRcy.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-039', 39, 'Notification', 'Notification', 'Energy Department', 'ENERGY', '2025-01-02', 'ED/SO(Admn)/12-6/AEI/2014(13)', 'https://www.sindh.gov.pk/storage/notification/zyklgpBFsbWK2qO02D0LgqGzDCbZUkqNrLFK7TvF.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-040', 40, 'Sindh Civil Servants Act 1973', 'Legislation', 'Services, General Administration & Coordination Department (SGA&CD)', 'SGA-CD', '2024-12-19', 'SORI(SGA&CD)2-25/2024', 'https://www.sindh.gov.pk/storage/notification/8Wh8bi1ZLKr61rnfZ9l7xFuFRv8VVAMM4FLYuHGD.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-041', 41, 'Cyber Security Implications of wearable devices', 'Notification', 'Science, Information Technology (IS&T) Department', 'SIT', '2024-11-26', NULL, 'https://www.sindh.gov.pk/storage/notification/CUp49cULvVZnh0ycxXP2nbeJ1aw4KC9sZs1hw2R9.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-042', 42, 'Cyber Security Advisory Strengthening " Know your Client KYC process for cyber security compliance and threat mitigation', 'Advisory', 'Science, Information Technology (IS&T) Department', 'SIT', '2024-11-26', NULL, 'https://www.sindh.gov.pk/storage/notification/JhqAuLHR5XuhkFc3mghVLvYR3fadCMrJHZm1j4iA.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-043', 43, 'Cyber Security Advisory Securing Sensitive Digital Documents Confidential Files', 'Advisory', 'Science, Information Technology (IS&T) Department', 'SIT', '2024-11-26', NULL, 'https://www.sindh.gov.pk/storage/notification/kBU6WAiLS1CD27Ui6ZZOywE3a51YKEWrL3Xyqep1.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-044', 44, 'Advisory', 'Advisory', 'Science, Information Technology (IS&T) Department', 'SIT', '2024-08-27', 'DG-II/Cyber Advisory/4/111/2023', 'https://www.sindh.gov.pk/storage/notification/VSdaNnl7oe4xxOsTpyeJ8RpjBH8Wnp0u02BoRP3b.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-045', 45, 'Cyber Security Advisory', 'Advisory', 'Science, Information Technology (IS&T) Department', 'SIT', '2024-08-13', NULL, 'https://www.sindh.gov.pk/storage/notification/QzdF8Z4eqDT8TH3HElzk65LkhHbW0k6q00ehmFN8.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-046', 46, 'Blacklisted', 'Notification', 'Services, General Administration & Coordination Department (SGA&CD)', 'SGA-CD', '2024-05-24', NULL, 'https://www.sindh.gov.pk/storage/notification/eWMuxAxiTDNgSKTpCMo4pyfEmj9Fri5pB0ZYwrcc.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-047', 47, 'Cabinet Committee on Finance', 'Notification', 'Finance Department', 'FIN', '2024-05-12', NULL, 'https://www.sindh.gov.pk/storage/notification/WqMOjIgVuaafrIMmnOwop8O1LKUvke6G90odjDXM.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-048', 48, 'INFORMATION SCIENCE & TECHNOLOGY DEPARTMENT ADVISORY', 'Advisory', 'Science, Information Technology (IS&T) Department', 'SIT', '2024-03-06', NULL, 'https://www.sindh.gov.pk/storage/notification/RnIKYfzovNTGcp0En65dDLQSrLwb6gPqmiVq3Hf8.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-049', 49, 'Caretaker Minister''s Order Notification', 'Order', 'Services, General Administration & Coordination Department (SGA&CD)', 'SGA-CD', '2023-08-21', NULL, 'https://www.sindh.gov.pk/storage/notification/HryZVQXNl6QwHEpzgHrGOpBuboOLirRWuq1r0ohM.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-050', 50, 'Serives General Administration & coordination Department', 'Notification', 'Services, General Administration & Coordination Department (SGA&CD)', 'SGA-CD', '2023-05-19', NULL, 'https://www.sindh.gov.pk/storage/notification/lByNMw8LO0xXHdp1FH0465mFFQ3hdGKQSc29iz5j.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-051', 51, 'Government of Sindh , Services General Administration and Coordination Department', 'Notification', 'Services, General Administration & Coordination Department (SGA&CD)', 'SGA-CD', '2022-10-06', NULL, 'https://www.sindh.gov.pk/storage/notification/2JtBqKpJ8DwAV4YopbbXY8jPqPQf9bUI8FKpBXJB.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-052', 52, 'Services General Administration & Coordination Department', 'Notification', 'Services, General Administration & Coordination Department (SGA&CD)', 'SGA-CD', '2022-05-20', NULL, 'https://www.sindh.gov.pk/storage/notification/eyXQ289ihxGGjoiaxY6RdiyWAtI34it0a9dPnL6e.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-053', 53, 'Services General Administration & Coordination Department', 'Notification', 'Services, General Administration & Coordination Department (SGA&CD)', 'SGA-CD', '2022-05-20', NULL, 'https://www.sindh.gov.pk/storage/notification/7gRVJd6FiEHrA8elv9cZqTIGMH1w6L54qZrrwM8r.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-054', 54, 'GOVERNMENT OF SINDH, SERVICES GENERAL ADMINISTRATION & COORDINATION DEPARTMENT', 'Notification', 'Services, General Administration & Coordination Department (SGA&CD)', 'SGA-CD', '2021-11-10', NULL, 'https://www.sindh.gov.pk/storage/notification/GVJps0jIandvqxl3NeB8i6uTZhiWg4ur5CqBEOye.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-055', 55, 'GOVERNMENT OF SINDH, SERVICES GENERAL ADMINISTRATION & COORDINATION DEPARTMENT CABINET SECTION (UPDATED)', 'Notification', 'Services, General Administration & Coordination Department (SGA&CD)', 'SGA-CD', '2021-08-10', NULL, 'https://www.sindh.gov.pk/storage/notification/h2pV26oHPEytPUjfuDBB3VtNWx8sDKe3JDgxdLjR.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-056', 56, 'GOVERNMENT OF SINDH, SERVICES GENERAL ADMINISTRATION & COORDINATION DEPARTMENT', 'Notification', 'Services, General Administration & Coordination Department (SGA&CD)', 'SGA-CD', '2019-03-11', NULL, 'https://www.sindh.gov.pk/storage/notification/wWDJhcvak1INBlUxJO6IG9XrOqFyORS7fugcRgoQ.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published'),
('SGNIA-ARCH-057', 57, 'GOVERNMENT OF SINDH, ENERGY DEPARTMENT', 'Notification', 'Energy Department', 'ENERGY', '2019-03-08', NULL, 'https://www.sindh.gov.pk/storage/notification/2EJP6Iiy05zWRp6658jSHPLSTFwMx15KHBVgl8Bi.pdf', 'https://www.sindh.gov.pk/notifications?show=notification', 'Published')
ON CONFLICT (reference) DO NOTHING;
