import "./NewsCard.css";

export default function NewsCard({
  title,
  source,
  url,
  image_url,
  prediction,
  confidence,
}) {
  const badgeColor =
    prediction === "Real"
      ? "badge-real"
      : prediction === "Fake"
      ? "badge-fake"
      : "badge-secondary";

  return (
    <div className="news-card">
      {/* ✅ Image Section */}
      <img
        src={
          image_url && image_url.startsWith("http")
            ? image_url
            : "https://via.placeholder.com/400x250?text=No+Image"
        }
        alt={title}
        className="news-image"
        onError={(e) => {
          e.target.onerror = null;
          e.target.src = "https://via.placeholder.com/400x250?text=No+Image";
        }}
      />

      {/* ✅ Content Section */}
      <div className="news-content">
        <h4 className="news-title">{title}</h4>
        <p className="news-source">{source}</p>
        <a href={url} target="_blank" rel="noopener noreferrer">
          Read source
        </a>
        <p className="prediction">
          <span className={`badge ${badgeColor}`}>{prediction}</span>{" "}
          {confidence !== null &&
            confidence !== undefined &&
            `Confidence: ${confidence.toFixed(3)}`}
        </p>
      </div>
    </div>
  );
}
