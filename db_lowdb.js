// Lightweight JSON DB using lowdb for easier cross-platform setup during development
const path = require('path');
const fs = require('fs');
const { Low, JSONFile } = require('lowdb');

const dataDir = path.join(__dirname, 'data');
if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir);

const file = path.join(dataDir, 'db.json');
const adapter = new JSONFile(file);
const db = new Low(adapter);

// Initialize with default structure if empty
async function init() {
  await db.read();
  db.data = db.data || { weapons: [], bullets: [], powders: [], cases: [] };
  await db.write();
}

init();

module.exports = db;
