// Simple Express server to allow multiple users to connect to the same DB
const express = require('express');
const bodyParser = require('body-parser');
const cors = require('cors');
const path = require('path');
const multer = require('multer');
const upload = multer({ dest: path.join(__dirname, 'uploads') });

const app = express();
app.use(cors());
app.use(bodyParser.json({ limit: '10mb' }));

// Simple health
app.get('/api/health', (req, res) => res.json({ status: 'ok' }));

// Endpoint to upload GRT datasheet file
app.post('/api/import/grt', upload.single('file'), (req, res) => {
  // TODO: parse file server-side and insert into DB
  res.json({ ok: true, file: req.file });
});

// Static serve for optional client (if needed)
app.use('/', express.static(path.join(__dirname, 'public')));

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));
