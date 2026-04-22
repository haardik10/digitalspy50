import { Link } from "react-router-dom";
import "./Hero.css";

export default function Hero() {
  return (
    <section className="hero">
      <h1>🕵DigitalSpy</h1>
      <p className="subtitle">News Aggregation using deep learning</p>
      <p className="description">

      </p>
      <Link to="/detect">
        <button className="get-started-btn">Get Started</button>
      </Link>
    </section>
  );
}
