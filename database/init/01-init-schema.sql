-- Sophia AI Pay Ready Database Schema
-- Company performance and business intelligence tables

-- Companies table (for Pay Ready data)
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    founded_date DATE,
    headquarters VARCHAR(255),
    website VARCHAR(255),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Financial metrics table
CREATE TABLE IF NOT EXISTS financial_metrics (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    metric_date DATE NOT NULL,
    revenue DECIMAL(15,2),
    profit DECIMAL(15,2),
    expenses DECIMAL(15,2),
    growth_rate DECIMAL(5,2),
    market_share DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer metrics table
CREATE TABLE IF NOT EXISTS customer_metrics (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    metric_date DATE NOT NULL,
    total_customers INTEGER,
    new_customers INTEGER,
    churned_customers INTEGER,
    retention_rate DECIMAL(5,2),
    acquisition_cost DECIMAL(10,2),
    lifetime_value DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Strategic initiatives table
CREATE TABLE IF NOT EXISTS strategic_initiatives (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'planning',
    priority VARCHAR(20) DEFAULT 'medium',
    start_date DATE,
    target_date DATE,
    completion_date DATE,
    progress_percentage INTEGER DEFAULT 0,
    budget DECIMAL(12,2),
    owner VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Competitive analysis table
CREATE TABLE IF NOT EXISTS competitive_analysis (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    competitor_name VARCHAR(255) NOT NULL,
    market_share DECIMAL(5,2),
    strengths TEXT,
    weaknesses TEXT,
    threats TEXT,
    opportunities TEXT,
    analysis_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Operational metrics table
CREATE TABLE IF NOT EXISTS operational_metrics (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    metric_date DATE NOT NULL,
    system_uptime DECIMAL(5,2),
    response_time_ms INTEGER,
    error_rate DECIMAL(5,4),
    transaction_volume INTEGER,
    efficiency_score DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI insights table
CREATE TABLE IF NOT EXISTS ai_insights (
    id SERIAL PRIMARY KEY,
    company_id INTEGER REFERENCES companies(id),
    insight_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    confidence_score DECIMAL(3,2),
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'new',
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    implemented_at TIMESTAMP
);

-- User sessions table (for single user authentication)
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert Pay Ready company data
INSERT INTO companies (name, industry, founded_date, headquarters, website, description) 
VALUES (
    'Pay Ready',
    'Financial Technology',
    '2020-01-01',
    'San Francisco, CA',
    'https://payready.com',
    'Innovative payment processing and financial technology solutions'
) ON CONFLICT DO NOTHING;

-- Insert sample financial metrics for Pay Ready
INSERT INTO financial_metrics (company_id, metric_date, revenue, profit, expenses, growth_rate, market_share)
SELECT 
    c.id,
    DATE '2024-01-01' + (interval '1 month' * generate_series(0, 5)),
    45000 + (generate_series(0, 5) * 3000) + (random() * 5000)::int,
    8000 + (generate_series(0, 5) * 500) + (random() * 1000)::int,
    37000 + (generate_series(0, 5) * 2500) + (random() * 3000)::int,
    12 + (generate_series(0, 5) * 2) + (random() * 5)::int,
    30 + (generate_series(0, 5) * 1) + (random() * 2)::int
FROM companies c WHERE c.name = 'Pay Ready';

-- Insert sample customer metrics
INSERT INTO customer_metrics (company_id, metric_date, total_customers, new_customers, churned_customers, retention_rate, acquisition_cost, lifetime_value)
SELECT 
    c.id,
    DATE '2024-01-01' + (interval '1 month' * generate_series(0, 5)),
    120 + (generate_series(0, 5) * 25) + (random() * 10)::int,
    25 + (random() * 10)::int,
    3 + (random() * 3)::int,
    88 + (random() * 8)::int,
    150 + (random() * 50)::int,
    2500 + (random() * 500)::int
FROM companies c WHERE c.name = 'Pay Ready';

-- Insert sample strategic initiatives
INSERT INTO strategic_initiatives (company_id, title, description, status, priority, start_date, target_date, progress_percentage, budget, owner)
SELECT 
    c.id,
    initiative.title,
    initiative.description,
    initiative.status,
    initiative.priority,
    initiative.start_date,
    initiative.target_date,
    initiative.progress,
    initiative.budget,
    initiative.owner
FROM companies c 
CROSS JOIN (
    VALUES 
    ('Market Expansion', 'Expand into new geographic markets', 'in_progress', 'high', '2024-01-01', '2024-12-31', 75, 500000, 'CEO'),
    ('Product Innovation', 'Develop next-generation payment platform', 'in_progress', 'high', '2024-02-01', '2024-10-31', 60, 750000, 'CTO'),
    ('Customer Retention', 'Implement advanced customer success program', 'in_progress', 'medium', '2024-03-01', '2024-09-30', 85, 200000, 'VP Customer Success')
) AS initiative(title, description, status, priority, start_date, target_date, progress, budget, owner)
WHERE c.name = 'Pay Ready';

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_financial_metrics_company_date ON financial_metrics(company_id, metric_date);
CREATE INDEX IF NOT EXISTS idx_customer_metrics_company_date ON customer_metrics(company_id, metric_date);
CREATE INDEX IF NOT EXISTS idx_strategic_initiatives_company ON strategic_initiatives(company_id);
CREATE INDEX IF NOT EXISTS idx_competitive_analysis_company ON competitive_analysis(company_id);
CREATE INDEX IF NOT EXISTS idx_operational_metrics_company_date ON operational_metrics(company_id, metric_date);
CREATE INDEX IF NOT EXISTS idx_ai_insights_company ON ai_insights(company_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token);

