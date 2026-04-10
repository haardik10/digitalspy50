import { useEffect, useState } from "react";
import Hero from "../components/Hero";
import NewsCard from "../components/NewsCard";
import axios from "axios";
import "./Home.css";

export default function Home() {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const API_KEY = process.env.REACT_APP_GNEWS_API_KEY; // Replace with your GNews API key
  const API_URL = `https://gnews.io/api/v4/top-headlines?country=in&lang=en&token=${API_KEY}&max=10`;

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const res = await axios.get(API_URL);

        const formatted = res.data.articles
          .filter((a) => a.title && a.description && a.image)
          .map((article) => ({
            category: article.source?.name || "General",
            title: article.title,
            description: article.description,
            source: article.source?.name || "Unknown",
            image: article.image || "https://via.placeholder.com/400x250?text=No+Image",
            url: article.url,
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
  }, [API_URL]);

  return (
    <>
      <Hero />

      <section className="trending">
        <h2>Trending News</h2>
        <p>Stay informed with the latest verified news.</p>

        {loading && <p className="loading">Loading news...</p>}
        {error && <p className="error">{error}</p>}

        <div className="news-grid">
          {!loading &&
            !error &&
            articles.map((news, i) => <NewsCard key={i} {...news} />)}
        </div>
      </section>
    </>
  );
}
