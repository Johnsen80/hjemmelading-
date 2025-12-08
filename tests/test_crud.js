const db = require('../db');

async function run() {
  console.log('Initializing DB...');
  await db.init();

  // clean collections for test
  const collections = ['powders', 'bullets', 'weapons'];
  for (const c of collections) {
    const items = await db.list(c);
    for (const it of items) await db.remove(c, it.id);
  }

  console.log('Saving powder A...');
  const p1 = await db.save('powders', { name: 'IMR 4064', vendor: 'IMR', notes: 'Test powder' });
  console.log('Saved:', p1.id);

  console.log('Saving duplicate powder (name only)...');
  const p2 = await db.save('powders', { name: 'IMR 4064' });
  console.log('Result id (should match previous):', p2.id);

  const powders = await db.list('powders');
  console.log('Powder count (should be 1):', powders.length);

  if (powders.length !== 1) {
    console.error('Deduplication failed for powders');
    process.exit(2);
  }

  console.log('Saving bullet A...');
  const b1 = await db.save('bullets', { name: 'MatchKing', caliber: '6.5mm' });
  console.log('Saved bullet id:', b1.id);

  console.log('Saving duplicate bullet with same name+caliber...');
  const b2 = await db.save('bullets', { name: 'MatchKing', caliber: '6.5mm', weight: '140gr' });
  console.log('Result bullet id (should match previous):', b2.id);

  const bullets = await db.list('bullets');
  console.log('Bullet count (should be 1):', bullets.length);
  if (bullets.length !== 1) {
    console.error('Deduplication failed for bullets');
    process.exit(3);
  }

  console.log('All tests passed.');
  process.exit(0);
}

run().catch(err => {
  console.error('Test run failed:', err);
  process.exit(1);
});
