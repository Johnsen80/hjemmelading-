 
// Lightweight JSON DB using lowdb for easier cross-platform setup during development
const path = require('path');
const fs = require('fs');
const { Low } = require('lowdb');
const { JSONFile } = require('lowdb/node');

const dataDir = path.join(__dirname, 'data');
if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir, { recursive: true });

const file = path.join(dataDir, 'db.json');
const adapter = new JSONFile(file);
// Provide default data to satisfy lowdb's constructor requirements
const defaultData = { weapons: [], bullets: [], powders: [], cases: [], manufacturers: [] };
const db = new Low(adapter, defaultData);

// Initialize with default structure if empty
async function init() {
  await db.read();
  db.data = db.data || { weapons: [], bullets: [], powders: [], cases: [], manufacturers: [] };
  await db.write();
}

// Helper to ensure DB is initialized before use
async function ready() {
  if (!db.data) await init();
  return db;
}

// Generic helpers
async function list(collection) {
  const _db = await ready();
  return _db.data[collection] || [];
}

async function get(collection, id) {
  const _db = await ready();
  return (_db.data[collection] || []).find(x => x.id === id) || null;
}

async function save(collection, item) {
  const _db = await ready();
  _db.data[collection] = _db.data[collection] || [];
  // Basic validation
  if (!item || typeof item !== 'object') throw new Error('Invalid item');
  if (!item.name || String(item.name).trim() === '') throw new Error('Item must have a name');

  // Normalize helper
  const normalize = s => (s || '').toString().trim().toLowerCase();

  // Deduplication rules for powders and bullets: try to find an existing item
  if (!item.id && (collection === 'powders' || collection === 'bullets')) {
    const existing = _db.data[collection].find(x => {
      if (!x || !x.name) return false;
      if (normalize(x.name) === normalize(item.name)) {
        // For bullets, also match caliber if present
        if (collection === 'bullets') {
          if (x.caliber && item.caliber) return normalize(x.caliber) === normalize(item.caliber);
        }
        // For powders, match vendor/manufacturer if available
        if (collection === 'powders') {
          if ((x.vendor || x.manufacturer) && (item.vendor || item.manufacturer)) {
            return normalize(x.vendor || x.manufacturer) === normalize(item.vendor || item.manufacturer);
          }
        }
        // fallback to name-only match
        return true;
      }
      return false;
    });
    if (existing) {
      // merge shallow fields (prefer incoming values when present)
      Object.keys(item).forEach(k => {
        if (item[k] !== undefined && item[k] !== null && item[k] !== '') existing[k] = item[k];
      });
      // ensure id remains
      existing._merged = true;
      item = existing;
    } else {
      // simple id generator
      item.id = Date.now().toString(36) + Math.random().toString(36).slice(2,8);
      _db.data[collection].push(item);
    }
  } else {
    if (!item.id) {
      item.id = Date.now().toString(36) + Math.random().toString(36).slice(2,8);
      _db.data[collection].push(item);
    } else {
      const idx = _db.data[collection].findIndex(x => x.id === item.id);
      if (idx === -1) _db.data[collection].push(item);
      else _db.data[collection][idx] = item;
    }
  }
  try {
    await _db.write();
  } catch (err) {
    // Fallback for environments (OneDrive/locked files) where atomic rename fails.
    // Write file directly as a fallback.
    try {
      fs.writeFileSync(file, JSON.stringify(_db.data, null, 2), { encoding: 'utf8' });
    } catch (err2) {
      // rethrow original error if fallback also fails
      throw err;
    }
  }
  return item;
}

async function remove(collection, id) {
  const _db = await ready();
  _db.data[collection] = (_db.data[collection] || []).filter(x => x.id !== id);
  await _db.write();
  return true;
}

module.exports = {
  init,
  ready,
  list,
  get,
  save,
  remove,
  // expose low-level db for advanced use if needed
  _raw: db
};
