function escapeHtml(str) {
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function normalizeConfidence(value) {
    const num = Number(value);
    return Number.isFinite(num) ? num : 0;
}

function formatConfidence(value) {
    return normalizeConfidence(value).toFixed(3);
}

function getDotClass(color) {
    if (color === "green") return "real";
    if (color === "red") return "fake";
    return "";
}

async function loadTrendingNews() {
    const fetchTrendingBtn = document.getElementById("fetchTrendingBtn");
    const trendingResults = document.getElementById("trendingResults");
    const articleCount = document.getElementById("articleCount");
    const lastRefresh = document.getElementById("lastRefresh");
    const feedStatus = document.getElementById("feedStatus");

    if (!fetchTrendingBtn || !trendingResults) return;

    fetchTrendingBtn.disabled = true;
    fetchTrendingBtn.textContent = "Loading...";
    feedStatus.textContent = "Loading";

    trendingResults.innerHTML = `
        <div class="status-badge status-warning">Loading articles</div>
        <p class="empty-state">Fetching latest items from the backend pipeline...</p>
    `;

    try {
        const res = await fetch("/api/fetch-and-classify");

        if (!res.ok) {
            throw new Error(`HTTP error: ${res.status}`);
        }

        const data = await res.json();

        if (!Array.isArray(data) || data.length === 0) {
            articleCount.textContent = "0";
            feedStatus.textContent = "Empty";
            trendingResults.innerHTML = `
                <div class="status-badge status-warning">No articles found</div>
                <p class="empty-state">The backend returned an empty result.</p>
            `;
            return;
        }

        articleCount.textContent = String(data.length);
        feedStatus.textContent = "Live";
        lastRefresh.textContent = new Date().toLocaleTimeString();

        trendingResults.innerHTML = `
            <div class="articles-grid">
                ${data.map(article => {
                    const confidence = normalizeConfidence(article.confidence);
                    const color = article.color || "gray";
                    const dotClass = getDotClass(color);
                    const source = article.source && article.source.trim() !== ""
                        ? article.source
                        : "Unknown Source";

                    return `
                        <div class="article-card">
                            ${article.image ? `
                                <img
                                    class="article-image"
                                    src="${escapeHtml(article.image)}"
                                    alt="${escapeHtml(article.title || "Untitled Article")}"
                                    loading="lazy"
                                    onerror="this.style.display='none';"
                                >
                            ` : ""}

                            <h4>${escapeHtml(article.title || "Untitled Article")}</h4>

                            <div class="article-meta">
                                Source: <strong>${escapeHtml(source)}</strong>
                            </div>

                            <a
                                class="article-link"
                                href="${escapeHtml(article.url || "#")}"
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                Read source
                            </a>

                            <div class="confidence-row">
                                <span class="confidence-dot ${dotClass}"></span>
                                <span>Confidence: ${formatConfidence(confidence)}</span>
                            </div>

                            ${article.summary ? `
                                <div class="article-meta" style="margin-top: 12px;">
                                    ${escapeHtml(article.summary)}
                                </div>
                            ` : ""}
                        </div>
                    `;
                }).join("")}
            </div>
        `;
    } catch (error) {
        console.error("Trending news fetch error:", error);
        feedStatus.textContent = "Error";
        trendingResults.innerHTML = `
            <div class="status-badge status-danger">Error</div>
            <p class="empty-state">${escapeHtml(error.message)}</p>
        `;
    } finally {
        fetchTrendingBtn.disabled = false;
        fetchTrendingBtn.textContent = "Load Trending News";
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const fetchTrendingBtn = document.getElementById("fetchTrendingBtn");
    if (fetchTrendingBtn) {
        fetchTrendingBtn.addEventListener("click", loadTrendingNews);
    }
});