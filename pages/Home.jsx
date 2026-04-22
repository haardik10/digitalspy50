import React, { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import "./Home.css";

const NAV_ITEMS = [
  { label: "Home", to: "/" },
  { label: "Trending News", to: "/trending" },
  { label: "About Us", to: "/about" },
];

const DOMAIN_OPTIONS = [
  { label: "General", value: "general" },
  { label: "Politics", value: "politics" },
  { label: "Finance", value: "finance" },
  { label: "Sports", value: "sports" },
  { label: "Cinema", value: "cinema" },
];

function safeText(value, fallback = "") {
  return typeof value === "string" && value.trim() ? value : fallback;
}

function toNumber(value) {
  const num = Number(value);
  return Number.isFinite(num) ? num : 0;
}

function formatConfidence(value) {
  return `${toNumber(value).toFixed(2)}%`;
}

function formatPublishedDate(value) {
  if (!value) return "";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";

  return date.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function normalizeLabel(label) {
  return String(label || "").trim().toUpperCase();
}

function predictionMeta(label) {
  const normalized = normalizeLabel(label);

  if (normalized === "REAL") {
    return {
      dotClass: "dot-green",
    };
  }

  if (normalized === "FAKE") {
    return {
      dotClass: "dot-red",
    };
  }

  return {
    dotClass: "dot-neutral",
  };
}

function overallStatus(groups) {
  if (!groups.length) {
    return {
      title: "Waiting for analysis",
      description:
        "Choose a domain and click Fetch & Analyze to load grouped similar articles.",
      className: "status-pill status-neutral",
    };
  }

  return {
    title: "Grouped comparison ready",
    description:
      "Similar articles from multiple websites are grouped together with both model outputs.",
    className: "status-pill status-success",
  };
}

function ModelSignal({ modelName, result }) {
  const meta = predictionMeta(result?.label);
  const confidence = formatConfidence(result?.confidence);

  return (
    <div className="model-signal-card">
      <div className="model-signal-top">
        <div className="model-label-wrap">
          <span className={`signal-dot ${meta.dotClass}`}></span>
          <span className="model-name">{modelName}</span>
        </div>
      </div>

      <div className="model-confidence">
        Confidence: <strong>{confidence}</strong>
      </div>
    </div>
  );
}

function ArticleCard({ article }) {
  const title = safeText(article?.title, "Untitled Article");
  const source = safeText(article?.source, "Unknown Source");
  const url = safeText(article?.url, "#");
  const image = safeText(article?.image, "");
  const publishedAt = formatPublishedDate(article?.published_at);
  const summary = safeText(article?.summary, "");
  const distilbert = article?.distilbert || {};
  const lstm = article?.lstm || {};

  return (
    <article className="article-card article-card-expanded">
      <div className="article-image-square">
        {image ? (
          <img
            src={image}
            alt={title}
            loading="lazy"
            onError={(e) => {
              e.currentTarget.style.display = "none";
            }}
          />
        ) : (
          <div className="image-fallback">No Image</div>
        )}
      </div>

      <div className="article-body">
        <div className="article-meta-row">
          <span className="article-source">
            Source: <strong>{source}</strong>
          </span>

          {publishedAt ? (
            <span className="article-date">{publishedAt}</span>
          ) : null}
        </div>

        <h4 className="article-title">{title}</h4>

        <div className="dual-model-grid">
          <ModelSignal modelName="DistilBERT" result={distilbert} />
          <ModelSignal modelName="LSTM" result={lstm} />
        </div>

        {summary ? <p className="article-summary">{summary}</p> : null}

        <a
          href={url}
          target="_blank"
          rel="noopener noreferrer"
          className="read-link"
        >
          Read source
        </a>
      </div>
    </article>
  );
}



function GroupCard({ group, index }) {
  const articles = Array.isArray(group?.articles) ? group.articles : [];

  return (
    <section className="group-block group-block-expanded">
      <div className="group-header">
        <div className="group-header-left">
          <div className="section-pill">Similar story cluster</div>
          <h3>Common Section {index + 1}</h3>
          <p className="group-header-desc">
            All related articles for this story are shown together below with both
            DistilBERT and LSTM outputs.
          </p>
        </div>
      </div>

      

      <div className="articles-grid articles-grid-full">
        {articles.slice(0, 3).map((article, articleIndex) => (
          <ArticleCard
            key={`${article?.url || article?.title || "article"}-${articleIndex}`}
            article={article}
          />
        ))}
      </div>
    </section>
  );
}

export default function Home() {
  const [groups, setGroups] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [selectedDomain, setSelectedDomain] = useState("general");

  const status = useMemo(() => overallStatus(groups), [groups]);

  const totalArticles = useMemo(() => {
    return groups.reduce((sum, group) => {
      return sum + (Array.isArray(group?.articles) ? group.articles.length : 0);
    }, 0);
  }, [groups]);

  const totalSources = useMemo(() => {
    const allSources = new Set();

    groups.forEach((group) => {
      const sources = group?.summary?.sources;
      if (Array.isArray(sources)) {
        sources.forEach((source) => allSources.add(source));
      } else if (Array.isArray(group?.articles)) {
        group.articles.forEach((article) => {
          if (article?.source) allSources.add(article.source);
        });
      }
    });

    return allSources.size;
  }, [groups]);

  async function fetchArticles() {
    setIsLoading(true);
    setError("");

    try {
      const url = `/api/analyze?domain=${selectedDomain}&min_sources=2`;
      console.log("Fetching from:", url);

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }

      const data = await response.json();

      if (!data?.success) {
        throw new Error(data?.error || "Backend returned an error.");
      }

      const incomingGroups = Array.isArray(data?.groups) ? data.groups : [];

      const normalizedGroups = incomingGroups
        .map((group) => ({
          ...group,
          articles: Array.isArray(group?.articles)
            ? group.articles.filter((article) => article && article.source)
            : [],
        }))
        .filter((group) => group.articles.length > 0);

      setGroups(normalizedGroups);
    } catch (err) {
      setGroups([]);
      setError(
        err instanceof Error
          ? err.message
          : "Something went wrong while fetching grouped articles."
      );
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="home-page">
      <header className="home-header">
        <div className="home-header-inner">
          <Link to="/" className="brand-link">
            <div className="brand-icon">🕵️</div>
            <div className="brand-text">
              <h1>DigitalSpy</h1>
              <p>Advanced verification intelligence for news workflows</p>
            </div>
          </Link>

          <nav className="nav-links">
            {NAV_ITEMS.map((item) => (
              <Link key={item.label} to={item.to}>
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>

      <main>
        <section className="hero-section">
          <div className="hero-card">
            <div className="hero-pill">AI-powered verification</div>

            <h2>
              Compare all similar articles together and inspect both model outputs
              side by side.
            </h2>

            <p>
              Choose a domain, fetch grouped articles from multiple websites, and
              review each similar article in one common section with DistilBERT and
              LSTM confidence signals.
            </p>

            <div className="hero-actions">
              <a href="#news-verifier" className="primary-btn">
                Live analysis workflow
              </a>
              <div className="secondary-pill">Grouped comparison</div>
              <div className="secondary-pill">Dual model output</div>
              <div className="secondary-pill">Cross-source review</div>
            </div>
          </div>

          <aside className="snapshot-card">
            <h3>System Snapshot</h3>
            <p>
              Built to show grouped similar articles with both model decisions in a
              cleaner review workflow.
            </p>

            <div className="snapshot-grid">
              <div className="metric-card">
                <div className="label">Domain</div>
                <div className="value">{selectedDomain}</div>
              </div>

              <div className="metric-card">
                <div className="label">Groups</div>
                <div className="value">{groups.length}</div>
              </div>

              <div className="metric-card">
                <div className="label">Articles shown</div>
                <div className="value">{totalArticles}</div>
              </div>

              <div className="metric-card">
                <div className="label">Websites checked</div>
                <div className="value">{totalSources}</div>
              </div>
            </div>
          </aside>
        </section>

        <section id="news-verifier" className="verifier-section">
          <div className="verifier-wrapper">
            <div className="verifier-top">
              <div>
                <h3>News Verifier</h3>
                <p>
                  Pull grouped similar stories from the backend and compare all
                  related articles together in one section.
                </p>
              </div>

              <div className="metric-pill">Grouped Dual-Model Workflow</div>
            </div>

            <div className="run-panel">
              <div className="run-panel-top">
                <div>
                  <h4>Run Verification</h4>
                  <p>
                    Select a domain, fetch grouped stories, and inspect each
                    article’s DistilBERT and LSTM confidence output.
                  </p>
                </div>

                <div className="controls-wrap">
                  <select
                    className="domain-select"
                    value={selectedDomain}
                    onChange={(e) => setSelectedDomain(e.target.value)}
                  >
                    {DOMAIN_OPTIONS.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>

                  <button
                    type="button"
                    onClick={fetchArticles}
                    disabled={isLoading}
                    className="primary-btn"
                  >
                    {isLoading ? "Fetching..." : "Fetch & Analyze"}
                  </button>
                </div>
              </div>
            </div>

            <div className="results-panel">
              <h4>Grouped Similar Articles</h4>
              <p>
                Every section below contains related reports grouped together from
                different websites.
              </p>

              <div className={status.className}>
                {isLoading ? "Loading grouped stories" : status.title}
              </div>

              <p>
                {isLoading
                  ? "Fetching latest grouped items from the backend pipeline..."
                  : status.description}
              </p>

              {error ? <div className="error-box">{error}</div> : null}

              {!isLoading && !error && groups.length === 0 ? (
                <div className="empty-state">
                  Choose a domain and click Fetch & Analyze to load grouped similar
                  article outputs.
                </div>
              ) : null}

              <div className="groups-list">
                {groups.map((group, index) => (
                  <GroupCard
                    key={`${group?.group_id ?? "group"}-${index}`}
                    group={group}
                    index={index}
                  />
                ))}
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="home-footer">
        DigitalSpy interface optimized for grouped article comparison and dual-model
        credibility review.
      </footer>
    </div>
  );
}