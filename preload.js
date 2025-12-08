const { contextBridge, ipcRenderer } = require('electron');
const db = require('./db');
const importer = require('./modules/importGRT-node');

contextBridge.exposeInMainWorld('api', {
  listPowders: async () => await db.list('powders'),
  savePowder: async (p) => await db.save('powders', p),
  listBullets: async () => await db.list('bullets'),
  saveBullet: async (b) => await db.save('bullets', b),
  listWeapons: async () => await db.list('weapons'),
  saveWeapon: async (w) => await db.save('weapons', w),
  importGRTText: async (text) => {
    const datasheet = importer.parseDatasheet(text);
    const loads = importer.parseLoads(text);
    // Save powders and bullets found
    for (const l of loads) {
      if (l.powder) await db.save('powders', { name: l.powder });
      if (l.bullet) await db.save('bullets', { name: l.bullet, weight_gr: l.weight || null, bc: l.bc || null });
    }
    return { datasheet, loadsCount: loads.length };
  },
  openFileDialog: async (opts) => await ipcRenderer.invoke('show-open-dialog', opts),
  getAppPath: async () => await ipcRenderer.invoke('app-path')
});
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electron', {
  invoke: (channel, ...args) => ipcRenderer.invoke(channel, ...args),
  on: (channel, listener) => ipcRenderer.on(channel, listener)
});
