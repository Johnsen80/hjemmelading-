const db = require('../db');

async function listBullets(filter = {}) {
  const bullets = await db.list('bullets');
  if (!filter || Object.keys(filter).length === 0) return bullets;
  return bullets.filter(b => {
    return Object.keys(filter).every(k => {
      if (!b.hasOwnProperty(k)) return false;
      const val = String(b[k]).toLowerCase();
      return String(filter[k]).toLowerCase().split(' ').every(tok => val.includes(tok));
    });
  });
}

async function getBullet(id) {
  return db.get('bullets', id);
}

async function saveBullet(bullet) {
  if (bullet && bullet.name) bullet.name = bullet.name.trim();
  return db.save('bullets', bullet);
}

async function deleteBullet(id) {
  return db.remove('bullets', id);
}

module.exports = { listBullets, getBullet, saveBullet, deleteBullet };
