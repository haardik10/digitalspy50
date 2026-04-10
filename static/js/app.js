document.getElementById('fetchBtn').addEventListener('click', async () => {
  const btn = document.getElementById('fetchBtn');
  btn.disabled = true;
  btn.innerText = 'Fetching...';

  const res = await fetch('http://127.0.0.1:5000/api/fetch-and-classify');
  const data = await res.json();
  const cont = document.getElementById('results');
  cont.innerHTML = '';

  if (data.length === 0) {
    cont.innerHTML = '<div class="alert alert-warning">No articles found.</div>'
  }

  data.forEach(a => {
    const col = document.createElement('div');
    col.className = 'col-12';
    const card = document.createElement('div');
    card.className = 'card p-3';

    let badge = '<span class="badge badge-secondary">Model not loaded</span>';
    if (a.prediction === 'Real') badge = '<span class="badge-real">Real</span>';
    if (a.prediction === 'Fake') badge = '<span class="badge-fake">Fake</span>';

    card.innerHTML = `<h5>${a.title} <small class="text-muted">(${a.source || ''})</small></h5>
                      <p><a href="${a.url}" target="_blank">Read source</a></p>
                      <p>${badge} ${a.confidence !== null ? ' Confidence: ' + (a.confidence ? a.confidence.toFixed(3) : 0) : ''}</p>`;

    col.appendChild(card);
    cont.appendChild(col);
  });

  btn.disabled = false;
  btn.innerText = 'Fetch & Classify';
});
