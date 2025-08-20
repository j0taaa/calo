document.getElementById('chat-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const message = document.getElementById('message').value;
  const responseDiv = document.getElementById('response');
  responseDiv.textContent = 'Loading...';

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    const data = await res.json();
    responseDiv.textContent = data.answer || data.error || 'No response';
  } catch (err) {
    responseDiv.textContent = 'Error: ' + err.message;
  }
});
