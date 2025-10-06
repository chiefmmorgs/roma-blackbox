#!/usr/bin/env python3
import os

files = {
    'schema.sql': '''-- Database schema for roma-blackbox PostgreSQL storage
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

CREATE TABLE IF NOT EXISTS audit_log (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    reason TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);
''',
    'README.md': '''# roma-blackbox

Privacy-first monitoring for ROMA agents.

## Installation
```bash
pip install roma-blackbox
