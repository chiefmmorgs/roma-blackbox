-- Database schema for roma-blackbox PostgreSQL storage

CREATE TABLE IF NOT EXISTS outcomes (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(255) UNIQUE NOT NULL,
    input_hash VARCHAR(64),
    output_hash VARCHAR(64),
    status VARCHAR(50) NOT NULL,
    latency_ms INTEGER,
    cost_cents NUMERIC(10, 2),
    created_at TIMESTAMP DEFAULT NOW(),
    attestation JSONB
);

CREATE INDEX idx_request_id ON outcomes(request_id);
CREATE INDEX idx_status ON outcomes(status);
CREATE INDEX idx_created_at ON outcomes(created_at);

CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    reason TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_request_id_audit ON audit_log(request_id);
CREATE INDEX idx_action ON audit_log(action);

COMMENT ON TABLE outcomes IS 'Stores only outcome data (no traces)';
COMMENT ON TABLE audit_log IS 'Audit trail for break-glass activations';
