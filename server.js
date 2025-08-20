import express from 'express';
import { config } from 'dotenv';
import { spawnSync } from 'child_process';
import OpenAI from 'openai';
import path from 'path';
import { fileURLToPath } from 'url';

config();

const app = express();
const port = process.env.PORT || 3000;
const client = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

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
app.use(express.json({ limit: '10mb' }));

app.get('/text', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'text.html'));
});

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

app.post('/api/photo', async (req, res) => {
  const { image } = req.body;
  if (!image) {
    return res.status(400).json({ error: 'No image provided' });
  }

  try {
    const resp = await client.responses.create({
      model: process.env.OPENAI_MODEL || 'gpt-5',
      input: [
        {
          role: 'user',
          content: [
            {
              type: 'input_text',
              text: 'The image contains a question that may be multiple choice (single or multiple answers) or true/false. Research on the internet and look at the provided document even if you think you know the answer. Respond only with letters (e.g., "B" or "A,C,D") or "True"/"False" with no explanation.'
            },
            { type: 'input_image', image_url: image }
          ]
        }
      ]
    });
    const answer = resp.output_text.trim();
    res.json({ answer });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Failed to fetch response' });
  }
});

app.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});
