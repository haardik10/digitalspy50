import "./NewsCard.css";

export default function NewsCard({
  title,
  source,
  url,
  image_url,
  confidence,
  summary
}) {
  const safeConfidence = typeof confidence === "number" ? confidence : 0;
  const isReal = safeConfidence >= 0.5;

  return (
    <div className="news-card">
      <img
        src={image_url || "https://via.placeholder.com/400x250?text=No+Image"}
        alt={title}
        className="news-image"
        onError={(e) => {
          e.target.src = "https://via.placeholder.com/400x250?text=No+Image";
        }}
      />

      <h5>{title || "Untitled"}</h5>

      <p className="news-source">{source || "Unknown Source"}</p>

      <a
        href={url || "#"}
        target="_blank"
        rel="noreferrer"
        className="news-link"
      >
        Read source
      </a>

      <div className="news-status">
        <span className={isReal ? "dot-real" : "dot-fake"}></span>
        <p className="news-confidence">
          Confidence: {(safeConfidence * 100).toFixed(1)}%
        </p>
      </div>

      {summary && <p className="news-summary">{summary}</p>}
    </div>
  );
}