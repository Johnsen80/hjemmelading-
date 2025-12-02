const db = require('../db');

async function listWeapons(filter = {}) {
  const weapons = await db.list('weapons');
  if (!filter || Object.keys(filter).length === 0) return weapons;
  return weapons.filter(w => Object.keys(filter).every(k => String(w[k] || '').toLowerCase().includes(String(filter[k]).toLowerCase())));
}

async function getWeapon(id) { return db.get('weapons', id); }

async function saveWeapon(weapon) {
  if (weapon && weapon.name) weapon.name = weapon.name.trim();
  return db.save('weapons', weapon);
}

async function deleteWeapon(id) { return db.remove('weapons', id); }

module.exports = { listWeapons, getWeapon, saveWeapon, deleteWeapon };
