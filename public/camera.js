const video = document.getElementById('camera');
const canvas = document.getElementById('canvas');
const overlay = document.getElementById('overlay');
const captureBtn = document.getElementById('capture-btn');

navigator.mediaDevices.getUserMedia({ video: true })
  .then(stream => {
    video.srcObject = stream;
  })
  .catch(err => {
    overlay.textContent = 'Camera access denied';
    overlay.classList.remove('hidden');
  });

captureBtn.addEventListener('click', async () => {
  const ctx = canvas.getContext('2d');
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  ctx.drawImage(video, 0, 0);
  const dataUrl = canvas.toDataURL('image/png');
  overlay.textContent = 'Loading...';
  overlay.classList.remove('hidden');
  try {
    const res = await fetch('/api/photo', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image: dataUrl })
    });
    const data = await res.json();
    overlay.textContent = data.answer || data.error || 'No response';
  } catch (err) {
    overlay.textContent = 'Error: ' + err.message;
  }
});
