import { useState, useEffect, useCallback } from 'react';
import dayjs from 'dayjs';

// Use relative URLs for Docker deployment (nginx will proxy to backend)
// In development, this will work because of Vite proxy or direct connection

const API_BASE = 'http://127.0.0.1:8002/api';

export default function Ticketmaster() {
  const [events, setEvents] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [totalEvents, setTotalEvents] = useState(0);
  const [region, setRegion] = useState('saint_louis');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Filter options from API
  const [filterOptions, setFilterOptions] = useState({
    days_of_week: [],
    days_abbreviated: [],
    classifications: []
  });
  
  // Venues list
  const [venues, setVenues] = useState([]);
  
  // Selected filters
  const [keyword, setKeyword] = useState('');
  const [classification, setClassification] = useState('');

 const [venue, setVenue] = useState('');
 const [venueId, setVenueId] = useState('');
 const [venueScraper, setVenueScraper] = useState('');
 const [venueMode, setVenueMode] = useState('all');

  const [dayOfWeek, setDayOfWeek] = useState('');
  const [daysAhead, setDaysAhead] = useState(90);

  // Load filter options and venues on mount
  useEffect(() => {
    fetch(`${API_BASE}/ticketmaster/filters`)
      .then(res => res.json())
      .then(data => setFilterOptions(data))
      .catch(err => console.error('Failed to load filter options:', err));
    
    fetch(`${API_BASE}/venues/`)
      .then(res => res.json())
      .then(data => setVenues(data))
      .catch(err => console.error('Failed to load venues:', err));
  }, []);

  // Save event to My Events
  const saveEvent = async (event) => {
    try {
      const res = await fetch(`${API_BASE}/my-events/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ticketmaster_id: event.ticketmaster_id,
          title: event.title,
          event_date: event.event_date,
          event_time: event.event_time,
          day_of_week: event.day_of_week,
          venue_name: event.venue_name,
          category: event.category,
          event_url: event.event_url,
          image_url: event.image_url,
          price_min: event.price_min,
          price_max: event.price_max,
          description: event.description
        })
      });
      
      if (res.ok) {
        alert(`Saved: ${event.title}`);
      } else {
        const err = await res.json();
        alert(err.detail || 'Failed to save event');
      }
    } catch (err) {
      alert('Error saving event: ' + err.message);
    }
  };

  // Search function
 // Search function with pagination
const searchEvents = useCallback(async (pageToLoad = currentPage) => {
  setLoading(true);
  setError(null);

  const params = new URLSearchParams();
  params.append('region', region);

  if (keyword) params.append('keyword', keyword);
  if (classification) params.append('classification', classification);
  
  params.append('venue_mode', venueMode);

  if (venue) params.append('venue', venue);
  if (venueId) params.append('venue_id', venueId);
  if (venueScraper) params.append('scraper', venueScraper);

  if (dayOfWeek) params.append('day_of_week', dayOfWeek);

  params.append('days_ahead', daysAhead);
  params.append('size', 50);
  params.append('page', pageToLoad);

  try {
    const res = await fetch(`${API_BASE}/ticketmaster/search?${params}`);

    if (!res.ok) throw new Error(`API error: ${res.status}`);

    const data = await res.json();

    setEvents(data.events || []);
    setHasSearched(true);
    setCurrentPage(data.page ?? pageToLoad);
    setTotalPages(data.total_pages || 0);
    setTotalEvents(data.total || 0);

  } catch (err) {
    setError(err.message);
  } finally {
    setLoading(false);
  }
}, [region, keyword, classification, venue, venueId, venueScraper, venueMode, dayOfWeek, daysAhead, currentPage]);

   const clearFilters = () => {
    setKeyword('');
    setClassification('');
    setVenue('');
    setVenueId('');
    setVenueMode('all');
    setVenueScraper('');
    setDayOfWeek('');
    setDaysAhead(90);
    setHasSearched(false);
    setEvents([]);
    setCurrentPage(0);
    setTotalPages(0);
    setTotalEvents(0);
  };


  return (
    <div>
      <div className="page-header">
        <h1>🎵 Ticketmaster - {region === 'saint_louis' ? 'Saint Louis' : 'Chicago'}</h1>
        <button className="btn btn-secondary" onClick={clearFilters}>
          Clear Filters
        </button>

        <button
          className="btn btn-primary"
          onClick={() => searchEvents(0)}
          disabled={loading}
        >
           {loading ? 'Searching...' : 'Search Events'}
        </button>  
      </div>

      {/* Filter Controls */}
      <div className="filters-row" style={{ marginBottom: 20 }}>
        <select
            value={region}
            onChange={e => {
            setRegion(e.target.value);
          }}
        style={{ width: 180 }}
        >     
          <option value="saint_louis">Saint Louis Metro</option>
          <option value="chicago">Chicago Metro</option>
        </select>
        <input
          type="text"
          placeholder="Search artist or event..."
          value={keyword}
          onChange={e => setKeyword(e.target.value)}
          style={{ width: 200 }}
        />
        
       
         {/* Venue selection */}
        <select
          value={venueMode === 'my_venues' ? '__my_venues__' : venueId}
          onChange={e => {
            const value = e.target.value;

            if (value === '__my_venues__') {
              setVenueMode('my_venues');
              setVenueId('');
              setVenue('');
              setVenueScraper('');
            } else if (value === '') {
              setVenueMode('all');
              setVenueId('');
              setVenue('');
              setVenueScraper('');
            } else {
              const selected = venues.find(
                v => String(v.id) === value
              );

              setVenueMode('individual');
              setVenueId(value);
              setVenue(selected ? selected.name : '');
              setVenueScraper(selected ? selected.scraper_type : '');
            }

            setCurrentPage(0);
          }}
          style={{ width: 200 }}
        >
          <option value="">All Venues</option>
          <option value="__my_venues__">My Venues Only</option>

          {venues.map(v => (
            <option key={v.id} value={String(v.id)}>
              {v.name}
            </option>
          ))}
        </select>

       
        <select 
          value={classification} 
          onChange={e => setClassification(e.target.value)}
          style={{ width: 150 }}
        >
          <option value="">All Categories</option>
          {filterOptions.classifications.map(c => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>

        <select 
          value={dayOfWeek} 
          onChange={e => setDayOfWeek(e.target.value)}
          style={{ width: 130 }}
        >
          <option value="">Any Day</option>
          {filterOptions.days_of_week.map((day, i) => (
            <option key={day} value={filterOptions.days_abbreviated[i]}>
              {day}
            </option>
          ))}
        </select>

        <select 
          value={daysAhead} 
          onChange={e => setDaysAhead(Number(e.target.value))}
          style={{ width: 130 }}
        >
          <option value={30}>Next 30 days</option>
          <option value={60}>Next 60 days</option>
          <option value={90}>Next 90 days</option>
        </select>
      </div>

      {error && (
        <div className="error-msg" style={{ marginBottom: 20 }}>
          Error: {error}
        </div>
      )}

       {loading ? (
        <div className="loading">Searching Ticketmaster...</div>
      ) : events.length === 0 ? (
        <div className="empty-state">
          {!hasSearched ? (
            <p>
              Ready to search? Select your filters and click Search Events.
            </p>
          ) : (
            <>
              <p>No events found matching your filters.</p>
              <p>Try adjusting your search criteria.</p>
            </>
          )}
        </div>
      ) : (
        <>
          <p style={{ marginBottom: 20, color: '#888' }}>
            Found {events.length} events in {region === 'saint_louis' ? 'Saint Louis' : 'Chicago'} Metro
          </p>
          <div className="cards-grid">
            {events.map(event => (
              <div key={event.ticketmaster_id || event.id} className="card event-card">
                {event.image_url && (
                  <img 
                    src={event.image_url} 
                    alt={event.title} 
                    className="event-image"
                    onError={e => e.target.style.display = 'none'}
                  />
                )}
                <div className="event-info">
                  <div className="event-title">{event.title}</div>
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
                  {event.event_url && (
                    <div style={{ marginTop: 12, display: 'flex', gap: 8 }}>
                      <button 
                        className="btn btn-secondary btn-sm"
                        onClick={() => saveEvent(event)}
                      >
                        💾 Save to My Events
                      </button>
                      <a 
                        href={event.event_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="btn btn-primary btn-sm"
                      >
                        🎟️ Get Tickets
                      </a>
                    </div>
                  )}
                </div>
              </div>
            ))}

       </div>

          {totalPages > 1 && (
            <div style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              gap: 16,
              margin: '25px 0',
              flexWrap: 'wrap'
            }}>
              <button
                className="btn btn-secondary"
                onClick={() => searchEvents(currentPage - 1)}
                disabled={currentPage === 0 || loading}
              >
                ← Previous
              </button>

              <span style={{ color: '#888' }}>
                Page {currentPage + 1} of {totalPages}
                {' '}({totalEvents} Ticketmaster events)
              </span>

              <button
                className="btn btn-secondary"
                onClick={() => searchEvents(currentPage + 1)}
                disabled={currentPage >= totalPages - 1 || loading}
              >
                Next →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );

}
