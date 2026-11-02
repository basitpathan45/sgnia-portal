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
('Agriculture, Supply & Prices Department', 'Agriculture & Supply', 'ASP', 'The Agriculture, Supply & Prices Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in the agricultural, supply, and price regulation domain.' , '• Policy formulation, regulation, and coordination for agriculture, irrigation, and supply chain management.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Auqaf Religious Affairs Zakat & Ushr Department', 'Auqaf, Religious Affairs & Zakat', 'ARAZU', 'The Auqaf Religious Affairs Zakat & Ushr Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in religious, charitable, and zakat-related matters.', '• Policy formulation, regulation, and coordination for religious affairs, Auqaf management, and zakat administration.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Board of Revenue (BOR)', 'Board of Revenue', 'BOR', 'The Board of Revenue (BOR) operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in revenue administration and land-related matters.', '• Policy formulation, regulation, and coordination for revenue administration and land records.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Chief Minister''s Secretariat & Inspection Team', 'CM Secretariat', 'CMSIT', 'The Chief Minister''s Secretariat & Inspection Team operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in governance oversight and strategic coordination.', '• Policy formulation, regulation, and coordination for governance affairs and priority agenda management.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('College Education Department', 'College Education', 'CED', 'The College Education Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in college education and academic development.', '• Policy formulation, regulation, and coordination for college education and higher learning institutions.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Cooperative Department', 'Cooperative', 'COOP', 'The Cooperative Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in cooperative development and rural economic support.', '• Policy formulation, regulation, and coordination for cooperative institutions and development programs.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Culture, Tourism & Antiquities Department', 'Culture & Tourism', 'CTA', 'The Culture, Tourism & Antiquities Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in cultural heritage, tourism, and antiquities preservation.', '• Policy formulation, regulation, and coordination for culture, heritage, tourism, and antiquities management.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Department of Empowerment of Persons with Disabilities', 'Empowerment of Persons with Disabilities', 'DEPD', 'The Department of Empowerment of Persons with Disabilities operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in disability inclusion and welfare services.', '• Policy formulation, regulation, and coordination for disability welfare and inclusion programs.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Energy Department', 'Energy', 'ENERGY', 'The Energy Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in energy generation, transmission, and sustainability.', '• Policy formulation, regulation, and coordination for electricity, energy supply, and infrastructure planning.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Enquiries & Anti-Corruption Establishment', 'Anti-Corruption Establishment', 'EACE', 'The Enquiries & Anti-Corruption Establishment operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in anti-corruption investigations and integrity oversight.', '• Policy formulation, regulation, and coordination for anti-corruption investigation and compliance.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Environment, Climate Change & Coastal Development Department', 'Environment & Climate Change', 'ECCD', 'The Environment, Climate Change & Coastal Development Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in environmental protection and coastal resilience.', '• Policy formulation, regulation, and coordination for environmental protection and climate action.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Excise, Taxation & Narcotics Control Department', 'Excise & Taxation', 'ETNC', 'The Excise, Taxation & Narcotics Control Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in taxation, excise, and narcotics control.', '• Policy formulation, regulation, and coordination for taxation, excise, and narcotics control.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Finance Department', 'Finance', 'FIN', 'The Finance Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in public finance, budgeting, and treasury management.', '• Policy formulation, regulation, and coordination for provincial finance and budget oversight.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Food Department & Sindh Food Authority', 'Food & Food Authority', 'FD-SFA', 'The Food Department & Sindh Food Authority operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in food safety, food security, and regulatory oversight.', '• Policy formulation, regulation, and coordination for food safety and public health governance.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Forest & Wildlife Department', 'Forest & Wildlife', 'FW', 'The Forest & Wildlife Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in forest conservation and wildlife protection.', '• Policy formulation, regulation, and coordination for forest and wildlife conservation.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Health Department', 'Health', 'HEALTH', 'The Health Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in public health and healthcare systems.', '• Policy formulation, regulation, and coordination for health services and public health programs.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Home Department & Sindh Police', 'Home & Police', 'HOME-POL', 'The Home Department & Sindh Police operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in internal security and policing.', '• Policy formulation, regulation, and coordination for internal security and provincial law enforcement.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Human Rights Department', 'Human Rights', 'HRD', 'The Human Rights Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in human rights protection and equality.', '• Policy formulation, regulation, and coordination for human rights and welfare protection.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Industries & Commerce Department', 'Industries & Commerce', 'IC', 'The Industries & Commerce Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in industry, trade, and investment ecosystems.', '• Policy formulation, regulation, and coordination for industrial development and commerce.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Information Department', 'Information', 'INFO', 'The Information Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in public information and communications.', '• Policy formulation, regulation, and coordination for public information and media management.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Inter Provincial Coordination Department', 'Inter Provincial Coordination', 'IPCD', 'The Inter Provincial Coordination Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in intergovernmental coordination and federal-provincial relations.', '• Policy formulation, regulation, and coordination for inter-provincial liaison and coordination.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Investment Department', 'Investment', 'INVEST', 'The Investment Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in attracting and managing investment opportunities.', '• Policy formulation, regulation, and coordination for investment promotion and facilitation.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Irrigation Department', 'Irrigation', 'IRR', 'The Irrigation Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in irrigation management and water resources.', '• Policy formulation, regulation, and coordination for irrigation and water resource management.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Labour & Human Resources Department', 'Labour & Human Resources', 'LHR', 'The Labour & Human Resources Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in labour welfare and workforce development.', '• Policy formulation, regulation, and coordination for labour welfare and human resource governance.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Law Department & Prosecutor General', 'Law & Prosecution', 'LDPG', 'The Law Department & Prosecutor General operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in legal affairs and prosecution.', '• Policy formulation, regulation, and coordination for legal affairs and prosecution management.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Livestock & Fisheries Department', 'Livestock & Fisheries', 'LF', 'The Livestock & Fisheries Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in livestock and fisheries development.', '• Policy formulation, regulation, and coordination for livestock and fisheries development.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Local Government & Housing Town Planning Department', 'Local Government & Housing', 'LGHTP', 'The Local Government & Housing Town Planning Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in urban planning, housing, and local governance.', '• Policy formulation, regulation, and coordination for local government and urban planning.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Mines & Mineral Development Department', 'Mines & Minerals', 'MMD', 'The Mines & Mineral Development Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in mineral development and resource governance.', '• Policy formulation, regulation, and coordination for mineral development and resource management.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Minorities Affairs Department', 'Minorities Affairs', 'MA', 'The Minorities Affairs Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in minority welfare and social inclusion.', '• Policy formulation, regulation, and coordination for minority welfare and social inclusion.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Planning & Development Department', 'Planning & Development', 'P&D', 'The Planning & Development Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in provincial planning and development policy.', '• Policy formulation, regulation, and coordination for planning and development programs.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Population Welfare Department', 'Population Welfare', 'PWD', 'The Population Welfare Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in population welfare and family planning.', '• Policy formulation, regulation, and coordination for population welfare and family planning programs.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Public Health Engineering & Rural Development Department', 'Public Health Engineering', 'PHERDD', 'The Public Health Engineering & Rural Development Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in rural development and water/sanitation infrastructure.', '• Policy formulation, regulation, and coordination for rural development and public health engineering.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Rehabilitation Department', 'Rehabilitation', 'REHAB', 'The Rehabilitation Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in rehabilitation and social reintegration services.', '• Policy formulation, regulation, and coordination for rehabilitation services and social reintegration.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('School Education & Literacy Department', 'School Education & Literacy', 'SELD', 'The School Education & Literacy Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in education access and literacy improvement.', '• Policy formulation, regulation, and coordination for school education and literacy.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Science & Information Technology Department', 'Science & Information Technology', 'SIT', 'The Science & Information Technology Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in digital governance and technology modernization.', '• Policy formulation, regulation, and coordination for digital governance and IT modernization.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Services, General Administration & Coordination Department (SGA&CD)', 'Services & General Administration', 'SGA-CD', 'The Services, General Administration & Coordination Department (SGA&CD) operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in governance coordination and civil administration.', '• Policy formulation, regulation, and coordination for governance administration and civil services.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Sindh Higher Education Commission (Sindh HEC)', 'Sindh HEC', 'SHEC', 'The Sindh Higher Education Commission (Sindh HEC) operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in higher education quality and governance.', '• Policy formulation, regulation, and coordination for higher education oversight and quality assurance.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Social Welfare Department', 'Social Welfare', 'SWD', 'The Social Welfare Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in social protection and welfare services.', '• Policy formulation, regulation, and coordination for social welfare and public assistance.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Sports & Youth Affairs Department', 'Sports & Youth Affairs', 'SYA', 'The Sports & Youth Affairs Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in sports, youth development, and recreational programs.', '• Policy formulation, regulation, and coordination for sports and youth affairs.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Transport & Mass Transit Department', 'Transport & Mass Transit', 'TMT', 'The Transport & Mass Transit Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in transport policy and public mobility.', '• Policy formulation, regulation, and coordination for transport and mass transit.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Universities & Boards Department', 'Universities & Boards', 'UBD', 'The Universities & Boards Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in university governance and board coordination.', '• Policy formulation, regulation, and coordination for higher education governance and boards.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Women Development Department', 'Women Development', 'WDD', 'The Women Development Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in women empowerment and development.', '• Policy formulation, regulation, and coordination for women development and empowerment.
• Supervision, coordination, and administrative control over attached directorates and field offices.
• Budget planning, financial oversight, and resource allocation in liaison with the Finance Department.
• Drafting statutory regulations, departmental guidelines, and ensuring compliance with provincial laws.', '• Minister / Secretary: Head of the department responsible for overall policy execution.
• Additional / Deputy Secretaries: Oversee specific operational wings and administrative units.
• Section Officers / Focal Persons: Manage day-to-day coordination, inter-departmental communication, and public queries.'),
('Works & Services Department', 'Works & Services', 'W&S', 'The Works & Services Department operates under the Government of Sindh framework, entrusted with policy formulation, public service delivery, regulatory enforcement, and administrative leadership in public works and service infrastructure.', '• Policy formulation, regulation, and coordination for public works and provincial services.
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
-- Seeded notification data removed from this file.
-- Use scripts/cleanup_notifications.sql for live database cleanup.
-- ========================================================
