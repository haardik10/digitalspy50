import "./About.css";

export default function About() {
  return (
    <div className="about-page">
      <section className="about-section">
        <h1>About Us</h1>
        <p>
          We are a passionate team committed to fighting misinformation using
          cutting-edge AI and data-driven solutions.
        </p>
      </section>

      <section className="team-section">
        <h2>Our Team</h2>
        <div className="team-grid">
          <div className="team-card">
            <img
              src=""
              alt="Devansh Motwani"
            />
            <h3>Devansh Motwani</h3>
            <p>Software Developer</p>
          </div>
          <div className="team-card">
            <img
              src=""
              alt="Mohit Kinger"
            />
            <h3>Mohit Kinger</h3>
            <p>Software Developer</p>
          </div>
          <div className="team-card">
            <img
              src=""
              alt="Devesh Mamtani"
            />
            <h3>Devesh Mamtani</h3>
            <p>Software Developer</p>
          </div>
          <div className="team-card">
            <img
              src=""
              alt="Hardik Manjani"
            />
            <h3>Hardik Manjani</h3>
            <p>Software Developer</p>
          </div>
        </div>
      </section>
    </div>
  );
}
