import { useEffect, useState } from "react";
import NewsCard from "../components/NewsCard";
import axios from "axios";
import "./News.css";

export default function News() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const res = await fetch("http://localhost:5000/api/fetch-and-classify"); // ✅ Flask endpoint
        const data = await res.json();

        const formatted = data.map((a) => ({
          title: a.title,
          source: a.source,
          url: a.url,
          image_url:
            a.image_url ||
            a.image ||
            "https://via.placeholder.com/400x250?text=No+Image",
          prediction: a.prediction,
          confidence: a.confidence,
        }));

        setArticles(formatted);
      } catch (err) {
        console.error("Error fetching news:", err);
        setError("Failed to load news. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchNews();
  }, []);

  return (
    <div className="news-page">
      <section className="news-section">
        <h2>Latest News</h2>
        <p>Stay informed with the latest verified news</p>

        {loading && <p className="loading">Loading news...</p>}
        {error && <p className="error">{error}</p>}

        <div className="news-grid">
          {!loading &&
            !error &&
            articles.map((news, i) => <NewsCard key={i} {...news} />)}
        </div>
      </section>
    </div>
  );
}
