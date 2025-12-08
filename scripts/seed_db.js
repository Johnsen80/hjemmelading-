const db = require('../db');

async function seed() {
  await db.init();

  const powders = [
    { name: 'Alliant Reloder 15', burn_rate: 'medium', notes: 'Popular for rifle cartridges' },
    { name: 'Hodgdon Varget', burn_rate: 'medium-slow', notes: 'Great for varmint loads and long-range' },
    { name: 'IMR 4064', burn_rate: 'medium', notes: 'Classic match powder' }
  ];

  const bullets = [
    { name: 'Hornady 168gr ELD', caliber: '.308', type: 'spitzer', weight_gr: 168 },
    { name: 'Sierra 155gr MatchKing', caliber: '.308', type: 'spitzer', weight_gr: 155 },
    { name: 'Nosler 150gr AccuBond', caliber: '.308', type: 'spitzer', weight_gr: 150 }
  ];

  for (const p of powders) await db.save('powders', p);
  for (const b of bullets) await db.save('bullets', b);

  console.log('Seed complete. Powders and bullets added.');
}

seed().catch(err => { console.error(err); process.exit(1); });
