import { HashRouter, Routes, Route, NavLink } from 'react-router-dom';
import Venues from './pages/Venues';
import Events from './pages/Events';
import Ticketmaster from './pages/Ticketmaster';
import Help from './pages/Help';
// Hidden troubleshooting dialogs: Ctrl+Shift+L (logs), Ctrl+Shift+D (database).
// To remove them from the UI, delete this import and <DiagnosticsDialogs /> below.
import DiagnosticsDialogs from './components/DiagnosticsDialogs';
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
            <li>
              <NavLink to="/help" className={({ isActive }) => isActive ? 'active' : ''}>
                ❓ Help
              </NavLink>
            </li>
          </ul>
        </nav>
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Ticketmaster />} />
            <Route path="/events" element={<Events />} />
            <Route path="/venues" element={<Venues />} />
            <Route path="/help" element={<Help />} />
          </Routes>
        </main>
      </div>
      <DiagnosticsDialogs />
    </HashRouter>
  );
}
