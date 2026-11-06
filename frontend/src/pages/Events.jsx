import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import dayjs from 'dayjs';
import { fetchVenueEvents } from '../api/client';

// Use relative URLs for Docker deployment (nginx will proxy to backend)
// In development, this will work because of Vite proxy or direct connection

const API_BASE = 'http://127.0.0.1:8002/api';

export default function Events() {

  const [searchParams] = useSearchParams();
  const venueId = searchParams.get('venue_id');
  const venueName = searchParams.get('venue_name');

  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadEvents = useCallback(async () => {
    try {
      setLoading(true);

      let data;

      if (venueId) {
        data = await fetchVenueEvents(venueId);
      } else {
        const res = await fetch(`${API_BASE}/my-events/`);
        if (!res.ok) throw new Error('Failed to load events');
        data = await res.json();
      }

      setEvents(data);
    } catch (err) {
      console.error('Failed to load events:', err);
    } finally {
      setLoading(false);
    }
  }, [venueId]);

  useEffect(() => { loadEvents(); }, [loadEvents]);

  const handleRemove = async (id, title) => {
    if (!confirm(`Remove "${title}" from My Events?`)) return;
    
    try {
      const res = await fetch(`${API_BASE}/my-events/${id}`, {
        method: 'DELETE'
      });
      
      if (res.ok) {
        loadEvents();
      } else {
        alert('Failed to remove event');
      }
    } catch (err) {
      alert('Error: ' + err.message);
    }
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
        <h1>📅 {venueId ? venueName || 'Venue Events' : 'My Events'}</h1>
            <span style={{ color: '#888' }}>
                 {events.length} {venueId ? 'events found' : 'saved events'}
            </span>
      </div>

      {events.length === 0 ? (
        <div className="empty-state">
          {venueId ? (
            <>
              <p>No events found for this venue.</p>
              <p>Try fetching events again later.</p>
            </>
          ) : (
            <>
              <p>No saved events yet.</p>
              <p>Go to <strong>Ticketmaster</strong> to search and save events you're interested in.</p>
            </>
          )}
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
                      {!venueId && (
                        <button 
                          className="btn btn-danger btn-sm"
                          onClick={() => handleRemove(event.id, event.title)}
                        >
                          🗑️ Remove
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}
