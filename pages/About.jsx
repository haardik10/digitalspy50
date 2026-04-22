import React from "react";
import { Link } from "react-router-dom";
import "./About.css";

const NAV_ITEMS = [
  { label: "Home", to: "/" },
  { label: "Trending News", to: "/trending" },
  { label: "About Us", to: "/about" },
];

const TEAM_MEMBERS = [
  {
    name: "Devesh Mamtani",
    role: "Software Developer",
    bio: "Focused on implementation quality, backend contribution, and making the verification workflow more stable and dependable.",
    image: "/devesh.jpg",
  },
  {
    name: "Mohit Kinger",
    role: "Software Developer",
    bio: "Works on interface behavior, usability improvements, and keeping the product experience clean and practical.",
    image: "/mohit.jpg",
  },
  {
    name: "Haardik Manjani",
    role: "Software Developer",
    bio: "Supports development across system structure, data flow, feature refinement, and overall project integration.",
    image: "/haardik.jpg",
  },
  {
    name: "Devansh Motwani",
    role: "Software Developer",
    bio: "Contributes to product development, engineering execution, and building reliable software workflows for the platform.",
    image: "devansh.jpg",
  },
];

function TeamCard({ member }) {
  return (
    <article className="about-team-card">
      <img
        src={member.image}
        alt={member.name}
        className="about-team-image"
        onError={(e) => {
  e.currentTarget.src = "/no-image.png";
}}
      />

      <h4>{member.name}</h4>
      <div className="about-team-role">{member.role}</div>
      <p>{member.bio}</p>
    </article>
  );
}

export default function DigitalSpyAboutPage() {
  return (
    <div className="about-page">
      <header className="about-header">
        <div className="about-header-inner">
          <Link to="/" className="about-brand-link">
            <div className="about-brand-icon">🕵️</div>
            <div className="about-brand-text">
              <h1>DigitalSpy</h1>
              <p>Advanced verification intelligence for news workflows</p>
            </div>
          </Link>

          <nav className="about-nav-links">
            {NAV_ITEMS.map((item) => (
              <Link key={item.label} to={item.to}>
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>

      <main className="about-main">
        <section className="about-hero-card">
          <div className="about-hero-pill">Who We Are</div>

          <h2>About DigitalSpy</h2>

          <p>
            DigitalSpy is built to tackle misinformation using intelligent news
            analysis, source tracking, and AI-driven verification workflows.
            The goal is to help users assess content faster, reduce noise, and
            make better judgments about the credibility of what they read online.
          </p>

          <p>
            It combines machine learning, article parsing, feed aggregation,
            and frontend usability into one focused system designed for practical
            verification and faster decision-making.
          </p>

          <div className="about-hero-tags">
            <div className="about-secondary-pill">AI-driven verification</div>
            <div className="about-secondary-pill">Websites credibility comparision</div>
            <div className="about-secondary-pill">Clean UI</div>
            <div className="about-secondary-pill">Dual model integration</div>
          </div>
        </section>

        <section className="about-team-wrapper">
          <div className="about-team-header">
            <div>
              <div className="about-section-pill">Core Team</div>
              <h3>Meet the Team</h3>
              <p>
                The project was developed by a four-member team focused on building
                a cleaner and more reliable news verification platform.
              </p>
            </div>

            <div className="about-metric-pill">4 Team Members</div>
          </div>

          <div className="about-team-grid">
            {TEAM_MEMBERS.map((member) => (
              <TeamCard key={member.name} member={member} />
            ))}
          </div>
        </section>
      </main>

      <footer className="about-footer">
        DigitalSpy about page designed in the same off-white professional style as the rest of the platform.
      </footer>
    </div>
  );
}