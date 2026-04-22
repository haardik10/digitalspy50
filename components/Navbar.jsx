import { Search } from "lucide-react";
import { Link, NavLink } from "react-router-dom";
import "./Navbar.css";

export default function Navbar() {
  return (
    <nav className="navbar">
      <Link to="/" className="logo">
        <Search className="icon" /> DigitalSpy
      </Link>
      <ul className="nav-links">
        <li><NavLink to="/" end>Home</NavLink></li>
        <li><NavLink to="/detect">Detect News</NavLink></li>
        <li><NavLink to="/news">News</NavLink></li>
        
        <li><NavLink to="/dashboard">Dashboard</NavLink></li>
        <li><NavLink to="/about">About</NavLink></li>
        
        
      </ul>
    </nav>
  );
}
