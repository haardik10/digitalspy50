import React, { useState } from "react";
import { Link } from "react-router-dom";
import "./Trending.css";

const NAV_ITEMS = [
  { label: "Home", to: "/" },
  { label: "Trending News", to: "/trending" },
  { label: "About Us", to: "/about" },
];

function safeText(value, fallback = "") {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function normalizeArticles(data) {
  if (!Array.isArray(data)) return [];

  return data.map((article) => ({
    title: safeText(article?.title, "Untitled Article"),
    url: safeText(article?.url, "#"),
    source: safeText(article?.source, "Unknown Source"),
    image: safeText(article?.image, ""),
    summary: safeText(article?.summary, ""),
  }));
}

function TrendingArticleCard({ article }) {
  return (
    <article className="trending-article-card">
      {article.image ? (
        <img
          src={article.image}
          alt={article.title}
          className="trending-article-image"
          loading="lazy"
          onError={(e) => {
            e.currentTarget.style.display = "none";
          }}
        />
      ) : null}

      <h4>{article.title}</h4>

      <div className="trending-article-source">
        Source: <strong>{article.source}</strong>
      </div>

      {article.summary ? (
        <p className="trending-article-summary">{article.summary}</p>
      ) : null}

      <a
        href={article.url}
        target="_blank"
        rel="noopener noreferrer"
        className="trending-read-link"
      >
        Read source
      </a>
    </article>
  );
}

export default function DigitalSpyTrendingPage() {
  const [articles, setArticles] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadTrendingNews() {
    setIsLoading(true);
    setError("");

    try {
      const res = await fetch("http://127.0.0.1:5000/api/trending-news");

      if (!res.ok) {
        throw new Error(`HTTP error: ${res.status}`);
      }

      const data = await res.json();
      const normalized = normalizeArticles(data?.articles || []);
      setArticles(normalized);
    } catch (err) {
      setArticles([]);
      setError(err instanceof Error ? err.message : "Failed to load trending news.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="trending-page">
      <header className="trending-header">
        <div className="trending-header-inner">
          <Link to="/" className="trending-brand-link">
            <div className="trending-brand-icon">🕵️</div>
            <div className="trending-brand-text">
              <h1>DigitalSpy</h1>
              <p>Advanced verification intelligence for news workflows</p>
            </div>
          </Link>

          <nav className="trending-nav-links">
            {NAV_ITEMS.map((item) => (
              <Link key={item.label} to={item.to}>
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>

      <main className="trending-main">
        <section className="trending-hero-card">
          <div className="trending-hero-pill">Live news stream</div>

          <h2>Track trending stories Now!</h2>

          <p>
            Fetch the latest and trending articles from credible US based news sources.
          </p>

          <div className="trending-hero-actions">
            <button
              type="button"
              onClick={loadTrendingNews}
              disabled={isLoading}
              className="trending-primary-btn"
            >
              {isLoading ? "Loading..." : "Load Trending News"}
            </button>

            <div className="trending-secondary-pill">Global News</div>
            <div className="trending-secondary-pill">latest Events</div>
            <div className="trending-secondary-pill">Credible Sources</div>
          </div>
        </section>

        <section className="trending-feed-wrapper">
          <div className="trending-feed-header">
            <div>
              <h3>Trending Feed</h3>
              <p>
                Latest articles appear below with source attribution and summary.
              </p>
            </div>

            <div className="trending-metric-pill">
              {articles.length} Article{articles.length !== 1 ? "s" : ""}
            </div>
          </div>

          {isLoading ? (
            <div className="trending-status trending-status-warning">
              Loading trending articles
            </div>
          ) : null}

          {!isLoading && !error && articles.length === 0 ? (
            <div className="trending-empty-state">
              <div className="trending-status trending-status-neutral">
                Waiting for action
              </div>
              <p>Click Load Trending News to fetch the latest article stream.</p>
            </div>
          ) : null}

          {error ? (
            <div className="trending-error-box">{error}</div>
          ) : null}

          {!isLoading && !error && articles.length > 0 ? (
            <div className="trending-articles-grid">
              {articles.map((article, index) => (
                <TrendingArticleCard key={`${article.url}-${index}`} article={article} />
              ))}
            </div>
          ) : null}
        </section>
      </main>

      <footer className="trending-footer">
        DigitalSpy trending page optimized for a lighter professional reading experience.
      </footer>
    </div>
  );
}