// Renderer helpers: client-side validation + user feedback
// This script is resilient: it checks for the presence of `window.api` exposed by preload.js

function byId(id) { return document.getElementById(id); }

function showMessage(text, type='info', timeout=5000) {
  let container = document.getElementById('app-messages');
  if (!container) {
    container = document.createElement('div');
    container.id = 'app-messages';
    container.style.position = 'fixed';
    container.style.right = '12px';
    container.style.top = '12px';
    container.style.zIndex = 9999;
    document.body.appendChild(container);
  }
  const el = document.createElement('div');
  el.className = `msg msg-${type}`;
  el.style.margin = '6px';
  el.style.padding = '10px 14px';
  el.style.borderRadius = '6px';
  el.style.boxShadow = '0 2px 6px rgba(0,0,0,0.12)';
  el.style.background = type === 'error' ? '#ffdddd' : (type === 'success' ? '#ddffdf' : '#f0f4ff');
  el.textContent = text;
  container.appendChild(el);
  setTimeout(() => { el.remove(); }, timeout);
}

async function savePowderHandler(ev) {
  ev && ev.preventDefault && ev.preventDefault();
  const name = byId('powder-name') ? byId('powder-name').value.trim() : '';
  const vendor = byId('powder-vendor') ? byId('powder-vendor').value.trim() : '';
  const notes = byId('powder-notes') ? byId('powder-notes').value.trim() : '';
  if (!name) return showMessage('Powder name is required', 'error');
  if (!window.api || !window.api.savePowder) return showMessage('App API not available', 'error');
  try {
    const saved = await window.api.savePowder({ name, vendor, notes });
    if (saved && saved.id) {
      showMessage('Powder saved', 'success');
      // If the save returned merged existing item, notify user
      if (saved._merged) showMessage('Duplicate found — merged with existing record', 'info');
      refreshPowders && refreshPowders();
    } else {
      showMessage('Save returned unexpected result', 'error');
    }
  } catch (err) {
    showMessage('Failed to save powder: ' + (err.message || err), 'error');
    console.error(err);
  }
}

async function saveBulletHandler(ev) {
  ev && ev.preventDefault && ev.preventDefault();
  const name = byId('bullet-name') ? byId('bullet-name').value.trim() : '';
  const caliber = byId('bullet-caliber') ? byId('bullet-caliber').value.trim() : '';
  const notes = byId('bullet-notes') ? byId('bullet-notes').value.trim() : '';
  if (!name) return showMessage('Bullet name is required', 'error');
  if (!caliber) return showMessage('Bullet caliber is recommended', 'error');
  if (!window.api || !window.api.saveBullet) return showMessage('App API not available', 'error');
  try {
    const saved = await window.api.saveBullet({ name, caliber, notes });
    if (saved && saved.id) {
      showMessage('Bullet saved', 'success');
      if (saved._merged) showMessage('Duplicate found — merged with existing record', 'info');
      refreshBullets && refreshBullets();
    } else {
      showMessage('Save returned unexpected result', 'error');
    }
  } catch (err) {
    showMessage('Failed to save bullet: ' + (err.message || err), 'error');
    console.error(err);
  }
}

function attachHandlers() {
  const powderForm = byId('powder-form');
  if (powderForm) powderForm.addEventListener('submit', savePowderHandler);
  const bulletForm = byId('bullet-form');
  if (bulletForm) bulletForm.addEventListener('submit', saveBulletHandler);

  // import button
  const importBtn = byId('import-grt-button');
  if (importBtn) {
    importBtn.addEventListener('click', async () => {
      const area = byId('import-grt-text');
      if (!area) return showMessage('Import textarea not found', 'error');
      const text = area.value || '';
      if (!text.trim()) return showMessage('Paste GRT datasheet text before importing', 'error');
      if (!window.api || !window.api.importGRTText) return showMessage('Import API not available', 'error');
      try {
        const result = await window.api.importGRTText(text);
        if (result && result.added) showMessage(`Imported ${result.added.powders || 0} powders, ${result.added.bullets || 0} bullets`, 'success');
        else showMessage('Import finished', 'success');
        refreshPowders && refreshPowders();
        refreshBullets && refreshBullets();
      } catch (err) {
        showMessage('Import failed: ' + (err.message || err), 'error');
        console.error(err);
      }
    });
  }
}

// Wait for DOM ready
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', attachHandlers);
else attachHandlers();

// Export helpers for manual testing in devtools
window.__hl_debug = { showMessage };
document.addEventListener('DOMContentLoaded', () => {
  const powdersList = document.getElementById('powders-list');
  const bulletsList = document.getElementById('bullets-list');
  const powderForm = document.getElementById('powder-form');
  const bulletForm = document.getElementById('bullet-form');
  const importTextarea = document.getElementById('import-text');
  const importBtn = document.getElementById('import-btn');
  const weaponForm = document.getElementById('weapon-form');
  const weaponsList = document.getElementById('weapons-list');

  async function refreshPowders() {
    const powders = await window.api.listPowders();
    powdersList.innerHTML = powders.map(p => `<li>${escapeHtml(p.name || '')} — ${escapeHtml(p.burn_rate || '')}</li>`).join('');
  }

  async function refreshBullets() {
    const bullets = await window.api.listBullets();
    bulletsList.innerHTML = bullets.map(b => `<li>${escapeHtml(b.name || '')} — ${escapeHtml(b.caliber || '')} ${b.weight_gr ? '('+b.weight_gr+' gr)':''}</li>`).join('');
  }

  async function refreshWeapons() {
    const weapons = await window.api.listWeapons();
    weaponsList.innerHTML = weapons.map(w => `<li>${escapeHtml(w.name || '')} — ${escapeHtml(w.caliber || '')} ${w.barrel_length ? '('+w.barrel_length+(w.barrel_unit||'')+')':''}</li>`).join('');
  }

  powderForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('powder-name').value;
    const burn = document.getElementById('powder-burn').value;
    const notes = document.getElementById('powder-notes').value;
    await window.api.savePowder({ name, burn_rate: burn, notes });
    powderForm.reset();
    await refreshPowders();
  });

  bulletForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('bullet-name').value;
    const caliber = document.getElementById('bullet-caliber').value;
    const weight = parseFloat(document.getElementById('bullet-weight').value) || null;
    const type = document.getElementById('bullet-type').value;
    await window.api.saveBullet({ name, caliber, weight_gr: weight, type });
    bulletForm.reset();
    await refreshBullets();
  });

  weaponForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('weapon-name').value;
    const caliber = document.getElementById('weapon-caliber').value;
    let barrel_length = parseFloat(document.getElementById('weapon-barrel-length').value) || null;
    const barrel_unit = document.getElementById('weapon-barrel-unit').value;
    let twist = document.getElementById('weapon-twist').value || null;
    const twist_unit = document.getElementById('weapon-twist-unit').value;

    // Normalize barrel_length to mm for storage
    if (barrel_length && barrel_unit === 'in') barrel_length = +(barrel_length * 25.4).toFixed(2);

    // Normalize twist: store as string (1:10 or mm/turn)
    if (twist && twist_unit === '1/in') {
      // user inputs number like 10 -> store as 1:10
      if (!twist.includes(':')) twist = `1:${twist}`;
    }

    await window.api.saveWeapon({ name, caliber, barrel_length, barrel_unit, twist, twist_unit });
    weaponForm.reset();
    await refreshWeapons();
  });

  importBtn.addEventListener('click', async () => {
    const text = importTextarea.value;
    if (!text) return alert('Paste GRT text into the import box first');
    const res = await window.api.importGRTText(text);
    alert(`Imported: ${res.loadsCount} loads parsed`);
    await refreshPowders();
    await refreshBullets();
    await refreshWeapons();
  });

  // Helpers
  function escapeHtml(s) { return String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c])); }

  // initial load
  refreshPowders();
  refreshBullets();
  refreshWeapons();
});
// Renderer logic for Hjemmelading desktop

document.getElementById('btn-import-grt').addEventListener('click', async () => {
  const res = await window.electron.invoke('show-open-dialog', { properties: ['openFile'], filters: [{ name: 'All Files', extensions: ['txt','csv','json','png','jpg'] }] });
  if (!res || res.canceled) return;
  const file = res.filePaths[0];
  document.getElementById('output').innerText = `Valgt fil: ${file}`;

  // Try to read file via fetch using file:// (Electron allows it from renderer)
  try {
    const data = await fetch(`file://${file}`).then(r => r.arrayBuffer()).then(buf => new TextDecoder('utf-8').decode(buf));
    // Hand off to import module if present
    if (window.GRTImporter && typeof window.GRTImporter.parseDatasheet === 'function') {
      const parsed = window.GRTImporter.parseDatasheet(data);
      document.getElementById('output').innerText = JSON.stringify(parsed, null, 2);
    } else {
      document.getElementById('output').innerText = 'Importmodul ikke funnet i appen.';
    }
  } catch (err) {
    document.getElementById('output').innerText = 'Kunne ikke lese fil: ' + err.message;
  }
});

// Start server mode
document.getElementById('btn-start-server').addEventListener('click', async () => {
  document.getElementById('output').innerText = 'Starter server på port 3000...';
  // Start server process by invoking node server.js via fetch to backend isn't possible here
  // Instead instruct user to run: npm run start-server
  document.getElementById('output').innerText += '\nKjør i terminal: npm run start-server';
});
