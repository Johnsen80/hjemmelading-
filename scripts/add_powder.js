const readline = require('readline');
const db = require('../db');

async function promptAndSave() {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const question = (q) => new Promise(res => rl.question(q, ans => res(ans)));
  try {
    const name = (await question('Powder name: ')).trim();
    const burn = (await question('Burn rate (e.g. fast, medium, slow): ')).trim();
    const notes = (await question('Notes: ')).trim();
    rl.close();
    await db.init();
    const saved = await db.save('powders', { name, burn_rate: burn, notes });
    console.log('Saved powder:', saved);
  } catch (err) {
    rl.close();
    console.error(err);
  }
}

promptAndSave();
