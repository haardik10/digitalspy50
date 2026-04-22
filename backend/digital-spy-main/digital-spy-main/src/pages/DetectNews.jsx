import "./DetectNews.css";

export default function DetectNews() {
  return (
    <div className="detect-page">
      <h1>Detect Fake News</h1>
      <p>Paste a news article or link below to verify its authenticity.</p>
      <textarea placeholder="Enter article text or URL..."></textarea>
      <button>Check Authenticity</button>
    </div>
  );
}
