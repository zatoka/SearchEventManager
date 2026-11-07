import { useState, useEffect, useCallback } from 'react';
import dayjs from 'dayjs';

// Use relative URLs for Docker deployment (nginx will proxy to backend)
// In development, this will work because of Vite proxy or direct connection

const API_BASE = 'http://127.0.0.1:8002/api';

// My Events: shows only events the user explicitly saved.
// Venue search results are shown on the Ticketmaster page instead.
export default function Events() {

  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadEvents = useCallback(async () => {
    try {
      setLoading(true);

      const res = await fetch(`${API_BASE}/my-events/`);
      if (!res.ok) throw new Error('Failed to load events');
      const data = await res.json();

      setEvents(data);
    } catch (err) {
      console.error('Failed to load events:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadEvents(); }, [loadEvents]);

  // Remove dialog (replaces browser confirm/alert boxes)
  // type: 'confirm' -> ask first, 'error' -> show failure
  const [removeDialog, setRemoveDialog] = useState(null);
  const [removing, setRemoving] = useState(false);

  const handleRemove = (id, title) => {
    setRemoveDialog({ type: 'confirm', id, title });
  };

  const confirmRemove = async () => {
    if (!removeDialog) return;
    const { id, title } = removeDialog;
    setRemoving(true);

    try {
      const res = await fetch(`${API_BASE}/my-events/${id}`, {
        method: 'DELETE'
      });

      if (res.ok) {
        setRemoveDialog(null);
        loadEvents();
      } else {
        setRemoveDialog({ type: 'error', title, message: 'Failed to remove event.' });
      }
    } catch (err) {
      setRemoveDialog({ type: 'error', title, message: 'Error: ' + err.message });
    } finally {
      setRemoving(false);
    }
  };

  const closeRemoveDialog = () => {
    if (!removing) setRemoveDialog(null);
  };

  // Group events by month for better organization
  const groupedEvents = events.reduce((groups, event) => {
    const month = event.event_date ? dayjs(event.event_date).format('MMMM YYYY') : 'No Date';
    if (!groups[month]) groups[month] = [];
    groups[month].push(event);
    return groups;
  }, {});

  // Check if event is upcoming (within 7 days)
  const isUpcoming = (eventDate) => {
    if (!eventDate) return false;
    const eventDay = dayjs(eventDate);
    const today = dayjs();
    const diff = eventDay.diff(today, 'day');
    return diff >= 0 && diff <= 7;
  };

  // Check if event is today
  const isToday = (eventDate) => {
    if (!eventDate) return false;
    return dayjs(eventDate).isSame(dayjs(), 'day');
  };

  if (loading) return <div className="loading">Loading My Events...</div>;

  return (
    <div>
      <div className="page-header">
        <h1>📅 My Events</h1>
            <span style={{ color: '#888' }}>
                 {events.length} saved events
            </span>
      </div>

      {events.length === 0 ? (
        <div className="empty-state">
          <p>No saved events yet.</p>
          <p>Go to <strong>Ticketmaster</strong> to search and save events you're interested in.</p>
        </div>
      ) : (
        Object.entries(groupedEvents).map(([month, monthEvents]) => (
          <div key={month} style={{ marginBottom: 30 }}>
            <h2 style={{ 
              fontSize: '1.2rem', 
              marginBottom: 15, 
              color: '#7c3aed',
              borderBottom: '1px solid #2a2a2a',
              paddingBottom: 8
            }}>
              {month}
            </h2>
            <div className="cards-grid">
              {monthEvents.map(event => (
                <div key={event.id} className="card event-card" style={{
                  border: isToday(event.event_date) ? '2px solid #10b981' : 
                          isUpcoming(event.event_date) ? '2px solid #f59e0b' : undefined
                }}>
                  {event.image_url && (
                    <img 
                      src={event.image_url} 
                      alt={event.title} 
                      className="event-image"
                      onError={e => e.target.style.display = 'none'}
                    />
                  )}
                  <div className="event-info">
                    <div className="event-title">
                      {event.title}
                      {isToday(event.event_date) && (
                        <span style={{ 
                          marginLeft: 8, 
                          background: '#10b981', 
                          color: 'white',
                          padding: '2px 8px',
                          borderRadius: 4,
                          fontSize: '0.7rem'
                        }}>
                          TODAY!
                        </span>
                      )}
                      {isUpcoming(event.event_date) && !isToday(event.event_date) && (
                        <span style={{ 
                          marginLeft: 8, 
                          background: '#f59e0b', 
                          color: 'black',
                          padding: '2px 8px',
                          borderRadius: 4,
                          fontSize: '0.7rem'
                        }}>
                          UPCOMING
                        </span>
                      )}
                    </div>
                    <div className="event-meta">
                      {event.venue_name && (
                        <p className="event-venue">{event.venue_name}</p>
                      )}
                      {event.event_date && (
                        <p>
                          📅 {dayjs(event.event_date).format('MMM D, YYYY')} 
                          {event.day_of_week && ` (${event.day_of_week})`}
                          {event.event_time && ` at ${event.event_time}`}
                        </p>
                      )}
                      {event.category && <p>🏷️ {event.category}</p>}
                      {event.price_min != null && (
                        <p className="event-price">
                          ${event.price_min.toFixed(0)}
                          {event.price_max && event.price_max !== event.price_min && 
                            ` - $${event.price_max.toFixed(0)}`}
                        </p>
                      )}
                    </div>
                    <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
                      {event.event_url && (
                        <a 
                          href={event.event_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="btn btn-primary btn-sm"
                        >
                          🎟️ Get Tickets
                        </a>
                      )}
                      <button 
                        className="btn btn-danger btn-sm"
                        onClick={() => handleRemove(event.id, event.title)}
                      >
                        🗑️ Remove
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))
      )}

      {/* Remove event dialog (same style as Fetch Events dialog) */}
      {removeDialog && (
        <div className="modal-overlay" onClick={closeRemoveDialog}>
          <div
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="remove-dialog-title"
            onClick={e => e.stopPropagation()}
          >
            <div className="modal-header">
              <h2 id="remove-dialog-title">
                {removeDialog.type === 'confirm'
                  ? '🗑️ Remove Event'
                  : '⚠️ Remove Failed'}
              </h2>

              <button
                className="modal-close"
                aria-label="Close"
                onClick={closeRemoveDialog}
                disabled={removing}
              >
                ×
              </button>
            </div>

            <div style={{ textAlign: 'center', padding: 20 }}>
              <h3>{removeDialog.title}</h3>

              <p style={{ margin: '20px 0' }}>
                {removeDialog.type === 'confirm'
                  ? 'Remove this event from My Events?'
                  : removeDialog.message}
              </p>
            </div>

            {/* All dialog buttons on one row */}
            <div style={{
              display: 'flex',
              justifyContent: 'flex-end',
              alignItems: 'center',
              gap: 10,
              padding: '0 20px 20px'
            }}>
              {removeDialog.type === 'confirm' && (
                <button
                  className="btn btn-danger"
                  onClick={confirmRemove}
                  disabled={removing}
                >
                  {removing ? 'Removing...' : '🗑️ Remove'}
                </button>
              )}

              <button
                className="btn btn-secondary"
                autoFocus
                onClick={closeRemoveDialog}
                disabled={removing}
              >
                {removeDialog.type === 'confirm' ? 'Cancel' : 'Close'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
