import express from 'express';
import { config } from 'dotenv';
import { spawnSync } from 'child_process';

config();

const app = express();
const port = process.env.PORT || 3000;

// Ensure the PDF is downloaded and indexed so the Python agent can use it
try {
  spawnSync('python', [
    '-c',
    "from agent.pdf_rag import ensure_pdf_index; ensure_pdf_index('https://hcip-files.obs.sa-brazil-1.myhuaweicloud.com/HCIP-Cloud%20Service%20Solutions%20Architect%20V3.0%20Training%20Material.pdf')"
  ], { stdio: 'inherit' });
} catch (err) {
  console.error('Failed to prepare PDF index', err);
}

app.use(express.static('public'));
app.use(express.json());

app.post('/api/chat', (req, res) => {
  const { message } = req.body;
  if (!message) {
    return res.status(400).json({ error: 'No message provided' });
  }

  try {
    const py = spawnSync('python', ['run_agent.py', message], {
      encoding: 'utf8',
    });
    if (py.error) throw py.error;
    const answer = py.stdout.trim();
    res.json({ answer });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch response' });
  }
});

app.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});
