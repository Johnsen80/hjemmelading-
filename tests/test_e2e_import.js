const db = require('../db');

// Simple simulated GRT text for e2e test
const sample = `
Datasheet: 6.5mm Match
Powder: IMR 4064
Powder vendor: IMR
Bullet: MatchKing, Caliber: 6.5mm

Datasheet: .308 Factory
Powder: Varget
Powder vendor: Hodgdon
Bullet: MatchKing, Caliber: 6.5mm
Bullet: Sierra MatchKing, Caliber: .308
`;

function parseSimpleGRT(text) {
  const lines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
  const powders = [];
  const bullets = [];
  for (const l of lines) {
    const mPow = l.match(/^Powder:\s*(.+)$/i);
    if (mPow) {
      powders.push({ name: mPow[1].trim() });
      continue;
    }
    const mPowV = l.match(/^Powder vendor:\s*(.+)$/i);
    if (mPowV && powders.length) {
      powders[powders.length-1].vendor = mPowV[1].trim();
      continue;
    }
    const mBull = l.match(/^Bullet:\s*(.+?)(?:,\s*Caliber:\s*(.+))?$/i);
    if (mBull) {
      bullets.push({ name: mBull[1].trim(), caliber: mBull[2] ? mBull[2].trim() : undefined });
      continue;
    }
  }
  return { powders, bullets };
}

async function run() {
  console.log('Initializing DB...');
  await db.init();

  const parsed = parseSimpleGRT(sample);
  console.log('Parsed powders:', parsed.powders);
  console.log('Parsed bullets:', parsed.bullets);

  const added = { powders: 0, bullets: 0 };

  for (const p of parsed.powders) {
    const saved = await db.save('powders', p);
    if (saved && saved._merged) console.log('Powder merged:', saved.name);
    else added.powders++;
  }

  for (const b of parsed.bullets) {
    const saved = await db.save('bullets', b);
    if (saved && saved._merged) console.log('Bullet merged:', saved.name, saved.caliber || '');
    else added.bullets++;
  }

  console.log('Import result:', added);
  const powders = await db.list('powders');
  const bullets = await db.list('bullets');
  console.log('DB powders count:', powders.length);
  console.log('DB bullets count:', bullets.length);
  process.exit(0);
}

run().catch(err => { console.error(err); process.exit(1); });
