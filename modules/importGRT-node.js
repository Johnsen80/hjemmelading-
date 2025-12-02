// Node-friendly GRT importer (parsing only). Use from scripts to persist to DB.
class GRTImporterNode {
    parseDatasheet(text) {
        const result = {};
        const lines = text.split(/\r?\n/);
        lines.forEach(line => {
            if (/winchester/i.test(line)) result.caliber = line.trim();
            let m = line.match(/Standard\s*:\s*(SAAMI|CIP)/i);
            if (m) result.standard = m[1].toUpperCase();
            m = line.match(/Pmax\s*=\s*([0-9,.]+)\s*(bar|psi)?/i);
            if (m) {
                const num = parseFloat(m[1].replace(',', '.'));
                if (!Number.isNaN(num)) result.maxPressureBar = num;
            }
            m = line.match(/L6\s*=\s*([0-9,.]+)\s*mm/i);
            if (m) {
                const num = parseFloat(m[1].replace(',', '.'));
                if (!Number.isNaN(num)) result.maxLengthMM = num;
            }
        });
        return result;
    }

    parseLoads(text) {
        const loads = [];
        const lines = text.split(/\r?\n/);
        let current = null;
        lines.forEach(rawLine => {
            const line = rawLine.trim();
            if (!line) return;
            let m = line.match(/^Bullet\s*:\s*(.+)$/i);
            if (m) { if (current && Object.keys(current).length) loads.push(current); current = { bullet: m[1].trim() }; return; }
            if (!current) current = {};
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
            m = line.match(/^([^:]+)\s*:\s*(.+)$/);
            if (m) { const key = m[1].trim().toLowerCase().replace(/\s+/g, '_'); current[key] = m[2].trim(); }
        });
        if (current && Object.keys(current).length) loads.push(current);
        return loads;
    }
}

module.exports = new GRTImporterNode();
