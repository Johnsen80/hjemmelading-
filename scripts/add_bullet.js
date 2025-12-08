const readline = require('readline');
const db = require('../db');

async function promptAndSave() {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const question = (q) => new Promise(res => rl.question(q, ans => res(ans)));
  try {
    const name = (await question('Bullet name: ')).trim();
    const caliber = (await question('Caliber (e.g. .308): ')).trim();
    const weight = parseFloat((await question('Weight (gr): ')).trim()) || null;
    const type = (await question('Type (spitzer, boat-tail, etc): ')).trim();
    rl.close();
    await db.init();
    const saved = await db.save('bullets', { name, caliber, weight_gr: weight, type });
    console.log('Saved bullet:', saved);
  } catch (err) {
    rl.close();
    console.error(err);
  }
}

promptAndSave();
