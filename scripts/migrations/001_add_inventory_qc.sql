-- Migration: add inventory and QC tables
BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS inventory_lots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_type TEXT NOT NULL,
    component_id INTEGER,
    lot_number TEXT,
    quantity_initial INTEGER DEFAULT 0,
    quantity_remaining INTEGER DEFAULT 0,
    purchase_date TEXT,
    supplier TEXT,
    notes TEXT,
    created_date TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_inventory_lots_component ON inventory_lots(component_type, component_id);

CREATE TABLE IF NOT EXISTS measurement_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lot_id INTEGER NOT NULL,
    measured_by TEXT,
    datetime TEXT DEFAULT (datetime('now')),
    sample_size INTEGER,
    measured_all INTEGER DEFAULT 0,
    notes TEXT,
    FOREIGN KEY(lot_id) REFERENCES inventory_lots(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS measurement_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    item_index INTEGER,
    weight_grains REAL,
    length_mm REAL,
    neck_thickness_mm REAL,
    case_weight_gr REAL,
    passed_qc INTEGER,
    notes TEXT,
    FOREIGN KEY(session_id) REFERENCES measurement_sessions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_measurement_session ON measurement_values(session_id);

CREATE TABLE IF NOT EXISTS prep_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    brass_batch_id INTEGER,
    method TEXT,
    anneal_date TEXT,
    trim_mm REAL,
    neck_bushing_size_inches REAL,
    neck_tension_notes TEXT,
    measured_after INTEGER DEFAULT 0,
    notes TEXT,
    created_date TEXT DEFAULT (datetime('now'))
);

COMMIT;
