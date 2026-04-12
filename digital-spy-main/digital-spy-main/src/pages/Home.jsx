import { useEffect, useState } from "react";
import Hero from "../components/Hero";
import axios from "axios";
import "./Home.css";

export default function Home() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const API_URL = "http://127.0.0.1:5000/api/fetch-and-classify";

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const res = await axios.get(API_URL);

        const formatted = (res.data || []).map((article) => ({
  title: article.title || "Untitled",
  source: article.source || "Unknown Source",
  url: article.url || "#",
  summary: article.summary || "",
  confidence: typeof article.confidence === "number" ? article.confidence : 0,
  image: article.image || "https://via.placeholder.com/400x250?text=No+Image",
}));

        setArticles(formatted);
      } catch (err) {
        console.error("Error fetching classified news:", err);
        setError("Failed to load classified news. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchNews();
  }, []);

  return (
    <>
      <Hero />

      <section className="trending news-page">
        <div className="news-section">
          <h2>Trending News</h2>
          <p>Stay informed with the latest classified news.</p>

          {loading && <p className="loading">Loading news...</p>}
          {error && <p className="error">{error}</p>}

          <div className="news-grid">
            {!loading &&
              !error &&
              articles.map((news, i) => {
                const isReal = news.confidence >= 0.5;

                return (
                  <div className="news-card" key={i}>
                    <img
                      src={news.image}
                      alt={news.title}
                      className="news-image"
                      onError={(e) => {
                        e.target.src =
                          "https://via.placeholder.com/400x250?text=No+Image";
                      }}
                    />

                    <h5>{news.title}</h5>
                    <p className="news-source">{news.source}</p>

                    <a
                      href={news.url}
                      target="_blank"
                      rel="noreferrer"
                      className="news-link"
                    >
                      Read source
                    </a>

                    <div className="news-status">
                      <span className={isReal ? "dot-real" : "dot-fake"}></span>
                      <p className="news-confidence">
                        Confidence: {(news.confidence * 100).toFixed(1)}%
                      </p>
                    </div>

                    {news.summary && (
                      <p className="news-summary">{news.summary}</p>
                    )}
                  </div>
                );
              })}
          </div>
        </div>
      </section>
    </>
  );
}