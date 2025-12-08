const db = require('../db');

async function listPowders(filter = {}) {
  const powders = await db.list('powders');
  if (!filter || Object.keys(filter).length === 0) return powders;
  return powders.filter(p => {
    return Object.keys(filter).every(k => {
      if (!p.hasOwnProperty(k)) return false;
      const val = String(p[k]).toLowerCase();
      return String(filter[k]).toLowerCase().split(' ').every(tok => val.includes(tok));
    });
  });
}

async function getPowder(id) {
  return db.get('powders', id);
}

async function savePowder(powder) {
  // Basic normalization
  if (powder && powder.name) powder.name = powder.name.trim();
  return db.save('powders', powder);
}

async function deletePowder(id) {
  return db.remove('powders', id);
}

module.exports = { listPowders, getPowder, savePowder, deletePowder };
