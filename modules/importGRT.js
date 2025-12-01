// Importmodul for GordonsReloadingTool-data til hjemmeladingssystemet
// Henter ut kaliber, krutt og kuledata fra datasheet og loads

class GRTImporter {
    constructor() {
        this.supportedStandards = ['SAAMI', 'CIP'];
    }

    // Parse datasheet text (PNG/JPG må OCR, TXT/CSV kan leses direkte)
    parseDatasheet(text) {
        // Eksempel: Finn kaliber, trykk, mål, standard
        const result = {};
        const lines = text.split(/\r?\n/);
        lines.forEach(line => {
            // Caliber (simple contains check)
            if (/winchester/i.test(line)) result.caliber = line.trim();

            // Standard (SAAMI or CIP)
            let m = line.match(/Standard\s*:\s*(SAAMI|CIP)/i);
            if (m) result.standard = m[1].toUpperCase();

            // Pmax (pressure) - tolerant for spaces and units
            m = line.match(/Pmax\s*=\s*([0-9,.]+)\s*(bar|psi)?/i);
            if (m) {
                // Replace comma with dot if present
                const num = parseFloat(m[1].replace(',', '.'));
                if (!Number.isNaN(num)) result.maxPressureBar = num;
            }

            // L6 / max length in mm
            m = line.match(/L6\s*=\s*([0-9,.]+)\s*mm/i);
            if (m) {
                const num = parseFloat(m[1].replace(',', '.'));
                if (!Number.isNaN(num)) result.maxLengthMM = num;
            }
            // ... flere felter kan parses her
        });
        return result;
    }

    // Parse loads file (krutt/kule data)
    parseLoads(text) {
        // Eksempel: Finn krutt, kule, vekt, BC, start/max
        const loads = [];
        const lines = text.split(/\r?\n/);
        let current = null;
        lines.forEach(rawLine => {
            const line = rawLine.trim();
            if (!line) return; // skip empty lines

            let m = line.match(/^Bullet\s*:\s*(.+)$/i);
            if (m) {
                if (current && Object.keys(current).length) loads.push(current);
                current = { bullet: m[1].trim() };
                return;
            }

            if (!current) current = {}; // start a new entry if we see other fields first

            m = line.match(/^Powder\s*:\s*(.+)$/i);
            if (m) { current.powder = m[1].trim(); return; }

            m = line.match(/^Weight\s*:\s*([0-9,.]+)/i);
            if (m) { const v = parseFloat(m[1].replace(',', '.')); if (!Number.isNaN(v)) current.weight = v; return; }

            m = line.match(/^BC\s*:\s*([0-9,.]+)/i);
            if (m) { const v = parseFloat(m[1].replace(',', '.')); if (!Number.isNaN(v)) current.bc = v; return; }

            m = line.match(/^Start\s*:\s*([0-9,.]+)/i);
            if (m) { const v = parseFloat(m[1].replace(',', '.')); if (!Number.isNaN(v)) current.start = v; return; }

            m = line.match(/^Max\s*:\s*([0-9,.]+)/i);
            if (m) { const v = parseFloat(m[1].replace(',', '.')); if (!Number.isNaN(v)) current.max = v; return; }

            // If line contains a colon but didn't match known keys, store raw key/value
            m = line.match(/^([^:]+)\s*:\s*(.+)$/);
            if (m) {
                const key = m[1].trim().toLowerCase().replace(/\s+/g, '_');
                const val = m[2].trim();
                current[key] = val;
            }
        });
        if (current && Object.keys(current).length) loads.push(current);
        return loads;
    }

    // Autofyll våpenmodul
    autofillWeaponModule(data) {
        // Her kan du koble til våpenmodulens inputfelter
        // Eksempel:
        // document.getElementById('caliber').value = data.caliber;
        // document.getElementById('maxPressure').value = data.maxPressureBar;
        // document.getElementById('maxLength').value = data.maxLengthMM;
    }

    // Autofyll kruttmodul
    autofillPowderModule(loads) {
        // Fyll inn kruttdata
        // ...
    }

    // Autofyll kulemodul
    autofillBulletModule(loads) {
        // Fyll inn kuledata
        // ...
    }
}

window.GRTImporter = new GRTImporter();
