import { HashRouter, Routes, Route, NavLink } from 'react-router-dom';
import Venues from './pages/Venues';
import Events from './pages/Events';
import Ticketmaster from './pages/Ticketmaster';
import './App.css';

export default function App() {
  return (
    <HashRouter>
      <div className="app-layout">
        <nav className="sidebar">
          <div className="sidebar-logo">
            <span className="logo-icon">🎵</span>
            <span className="logo-text">EventsManager</span>
          </div>
          <ul className="nav-links">
            <li>
              <NavLink to="/" end className={({ isActive }) => isActive ? 'active' : ''}>
                🎫 Ticketmaster
              </NavLink>
            </li>
            <li>
              <NavLink to="/events" className={({ isActive }) => isActive ? 'active' : ''}>
                📅 My Events
              </NavLink>
            </li>
            <li>
              <NavLink to="/venues" className={({ isActive }) => isActive ? 'active' : ''}>
                🏛️ Venues
              </NavLink>
            </li>
          </ul>
        </nav>
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Ticketmaster />} />
            <Route path="/events" element={<Events />} />
            <Route path="/venues" element={<Venues />} />
          </Routes>
        </main>
      </div>
    </HashRouter>
  );
}
