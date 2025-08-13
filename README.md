# GPT-5 Express Example

This project demonstrates a minimal Express.js server with a single-page frontend that queries the OpenAI API.

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```
2. Copy `.env.example` to `.env` and set your OpenAI API key:
   ```bash
   cp .env.example .env
   # then edit .env
   ```
3. Start the server:
   ```bash
   npm start
   ```
4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Notes
- The API call uses model `gpt-5` as requested. If this model is unavailable, update `server.js` with a supported model.
