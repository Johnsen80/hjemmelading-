const fs = require('fs');
const path = require('path');
const importer = require('../modules/importGRT-node');
const db = require('../db');

async function importFile(filePath) {
  if (!fs.existsSync(filePath)) { console.error('File not found:', filePath); process.exit(1); }
  const text = fs.readFileSync(filePath, 'utf8');
  const datasheet = importer.parseDatasheet(text);
  const loads = importer.parseLoads(text);
  console.log('Parsed datasheet:', datasheet);
  console.log('Parsed', loads.length, 'load entries');

  await db.init();

  // Save powders and bullets found in loads (simple heuristics)
  for (const l of loads) {
    if (l.powder) {
      await db.save('powders', { name: l.powder });
    }
    if (l.bullet) {
      await db.save('bullets', { name: l.bullet, weight_gr: l.weight || null, bc: l.bc || null });
    }
  }

  console.log('Import complete. Saved powders/bullets to DB.');
}

const arg = process.argv[2];
if (!arg) { console.error('Usage: node import_grt_file.js <path-to-text-file>'); process.exit(1); }
importFile(path.resolve(arg)).catch(err => { console.error(err); process.exit(1); });
