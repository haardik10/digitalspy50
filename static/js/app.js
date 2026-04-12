function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

async function fetchArticles() {
  const btn = document.getElementById('fetchBtn');
  const cont = document.getElementById('results');

  btn.disabled = true;
  btn.innerText = 'Fetching...';
  cont.innerHTML = '';

  try {
    const res = await fetch('http://127.0.0.1:5000/api/fetch-and-classify');

    if (!res.ok) {
      throw new Error(`HTTP error: ${res.status}`);
    }

    const data = await res.json();
    console.log('Flask response:', data);

    if (!Array.isArray(data) || data.length === 0) {
      cont.innerHTML = `<div class="alert alert-warning">No articles found.</div>`;
      return;
    }

    cont.innerHTML = `
      <div class="articles-grid">
        ${data.map(article => {
          const confidence = Number(article.confidence ?? 0);
          const prediction = String(article.prediction ?? '').toLowerCase().trim();

          let dotClass = '';
          if (prediction.includes('real')) dotClass = 'real';
          else if (prediction.includes('fake')) dotClass = 'fake';

          return `
            <div class="article-card">
              <img
                class="article-image"
                src="${article.image || '/static/no-image.png'}"
                alt="${escapeHtml(article.title || 'Untitled Article')}"
                onerror="this.src='/static/no-image.png';"
              >

              <h4>${escapeHtml(article.title || 'Untitled Article')}</h4>

              <div class="article-meta">
                ${escapeHtml(article.source || 'Unknown Source')}
              </div>

              <a
                class="article-link"
                href="${article.url || '#'}"
                target="_blank"
                rel="noopener noreferrer"
              >
                Read source
              </a>

              <div class="confidence-row">
                <span class="confidence-dot ${dotClass}"></span>
                <span>Confidence: ${confidence.toFixed(3)}</span>
              </div>

              ${article.summary ? `
                <div class="article-meta" style="margin-top: 12px;">
                  ${escapeHtml(article.summary)}
                </div>
              ` : ''}
            </div>
          `;
        }).join('')}
      </div>
    `;
  } catch (error) {
    console.error('Fetch/classify error:', error);
    cont.innerHTML = `<div class="alert alert-danger">Error: ${escapeHtml(error.message)}</div>`;
  } finally {
    btn.disabled = false;
    btn.innerText = 'Fetch & Classify';
  }
}

document.getElementById('fetchBtn').addEventListener('click', fetchArticles);