import { useState, useEffect, useCallback, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import dayjs from 'dayjs';

// Use relative URLs for Docker deployment (nginx will proxy to backend)
// In development, this will work because of Vite proxy or direct connection

const API_BASE = 'http://127.0.0.1:8002/api';

// A search that takes longer than this is stopped with a friendly message.
const SEARCH_TIMEOUT_MS = 60000;

export default function Ticketmaster() {
  // A venue can be passed in from the Venues page "View Events" button: /?venue_id=<id>
  const [searchParams, setSearchParams] = useSearchParams();
  const [autoSearch, setAutoSearch] = useState(false);

  // Result dialog for "Save to My Events" (replaces browser alert boxes)
  const [saveDialog, setSaveDialog] = useState(null);


  const [events, setEvents] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);
  const [totalPages, setTotalPages] = useState(0);
  const [totalEvents, setTotalEvents] = useState(0);
  const [region, setRegion] = useState('saint_louis');
  const [loading, setLoading] = useState(false);

  // Search progress / cancel / timeout
  const searchRef = useRef(null);        // { controller, requestId } of the running search
  const requestIdRef = useRef(0);        // increments per search; stale results are ignored
  const [searchStartedAt, setSearchStartedAt] = useState(null);
  const [elapsed, setElapsed] = useState(0);
  const [notice, setNotice] = useState(null);
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
        setSaveDialog({ type: 'success', title: event.title });
      } else {
        const err = await res.json().catch(() => ({}));
        setSaveDialog({
          type: 'error',
          title: event.title,
          message: err.detail || 'Failed to save event'
        });
      }
    } catch (err) {
      setSaveDialog({
        type: 'error',
        title: event.title,
        message: 'Error saving event: ' + err.message
      });
    }
  };

  // ── YouTube link for every event ─────────────────────────────────────────
  const youtubeSearchUrl = (query) =>
    `https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`;

  // Performer's YouTube channel from Ticketmaster when available, otherwise
  // a YouTube search for the performer (or the event title if none is listed).
  const eventYoutubeUrl = (event) => {
    const first = event.attractions?.[0];
    if (first?.youtube_url) return first.youtube_url;
    return youtubeSearchUrl(first?.name || event.title);
  };

  // Search function
 // Search function with pagination.
 // Each search can be cancelled, stops after SEARCH_TIMEOUT_MS, and a newer
 // search replaces an older one (late responses from old searches are ignored).
const searchEvents = useCallback(async (pageToLoad = currentPage) => {
  // Stop any search that is still running.
  if (searchRef.current) searchRef.current.controller.abort('replaced');

  const controller = new AbortController();
  const requestId = (requestIdRef.current += 1);
  const timer = setTimeout(() => controller.abort('timeout'), SEARCH_TIMEOUT_MS);
  searchRef.current = { controller, requestId };

  setLoading(true);
  setError(null);
  setNotice(null);
  setSearchStartedAt(Date.now());

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

  const isCurrent = () => requestIdRef.current === requestId;

  try {
    const res = await fetch(`${API_BASE}/ticketmaster/search?${params}`, {
      signal: controller.signal
    });

    if (!res.ok) {
      // Show the backend's explanation when it sends one.
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Search failed (error ${res.status}). Please try again.`);
    }

    const data = await res.json();
    if (!isCurrent()) return;

    setEvents(data.events || []);
    setHasSearched(true);
    setCurrentPage(data.page ?? pageToLoad);
    setTotalPages(data.total_pages || 0);
    setTotalEvents(data.total || 0);

  } catch (err) {
    if (!isCurrent()) return;  // replaced by a newer search

    if (controller.signal.aborted) {
      const reason = controller.signal.reason;
      if (reason === 'timeout') {
        setError(
          `The search took longer than ${SEARCH_TIMEOUT_MS / 1000} seconds and was stopped. ` +
          'Try a shorter date range, one venue instead of My Venues Only, or add a keyword.'
        );
      } else if (reason === 'cancelled') {
        setNotice('Search cancelled. Change your filters and click Search Events when ready.');
      }
    } else if (err instanceof TypeError) {
      // fetch() network failure: backend not running or unreachable
      setError('Could not reach the search service. Make sure the backend is running, then try again.');
    } else {
      setError(err.message);
    }
  } finally {
    clearTimeout(timer);
    if (isCurrent()) {
      searchRef.current = null;
      setLoading(false);
      setSearchStartedAt(null);
    }
  }
}, [region, keyword, classification, venue, venueId, venueScraper, venueMode, dayOfWeek, daysAhead, currentPage]);

  const cancelSearch = () => {
    if (searchRef.current) searchRef.current.controller.abort('cancelled');
  };

  // Seconds counter for the progress panel.
  useEffect(() => {
    if (!searchStartedAt) {
      setElapsed(0);
      return undefined;
    }
    const tick = setInterval(() => {
      setElapsed(Math.floor((Date.now() - searchStartedAt) / 1000));
    }, 1000);
    return () => clearInterval(tick);
  }, [searchStartedAt]);

  // Stop a running search when leaving the page.
  useEffect(() => () => {
    if (searchRef.current) searchRef.current.controller.abort('replaced');
  }, []);

  const progressMessage = () => {
    if (elapsed < 5) return 'Searching for events...';
    if (elapsed < 15) {
      return venueMode === 'my_venues'
        ? 'Checking each of your saved venues...'
        : 'Still searching...';
    }
    if (elapsed < 30) return 'This is taking longer than usual. You can keep waiting or cancel.';
    return `Almost at the ${SEARCH_TIMEOUT_MS / 1000}-second limit. Cancel and narrow your search if you prefer.`;
  };

  // When opened from Venues -> Fetch Events -> View Events, preselect that
  // venue once the venue list has loaded, then run the search.
  useEffect(() => {
    const incomingVenueId = searchParams.get('venue_id');
    if (!incomingVenueId || venues.length === 0) return;

    const selected = venues.find(v => String(v.id) === incomingVenueId);

    if (selected) {
      setVenueMode('individual');
      setVenueId(String(selected.id));
      setVenue(selected.name);
      setVenueScraper(selected.scraper_type || '');
      setCurrentPage(0);
      setAutoSearch(true);
    } else {
      setError('The selected venue was not found in My Venues.');
    }

    // Remove the parameter so a refresh or later visit does not re-run it.
    setSearchParams({}, { replace: true });
  }, [searchParams, venues, setSearchParams]);

  // Runs after the venue state above has been applied.
  useEffect(() => {
    if (!autoSearch) return;
    setAutoSearch(false);
    searchEvents(0);
  }, [autoSearch, searchEvents]);

   const clearFilters = () => {
    // Stop a running search; its results should not appear after clearing.
    if (searchRef.current) {
      searchRef.current.controller.abort('replaced');
      searchRef.current = null;
      requestIdRef.current += 1;
      setLoading(false);
      setSearchStartedAt(null);
    }
    setError(null);
    setNotice(null);
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

        {/* While searching, filters stay usable: Search again replaces the
            running search, Cancel stops it. */}
        <button
          className="btn btn-primary"
          onClick={() => searchEvents(0)}
        >
          {loading ? '🔄 Search Again' : 'Search Events'}
        </button>

        {loading && (
          <button className="btn btn-danger" onClick={cancelSearch}>
            ✖ Cancel
          </button>
        )}
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
        <div className="error-msg" role="alert" style={{ marginBottom: 20 }}>
          ⚠️ {error}
        </div>
      )}

      {notice && !loading && (
        <div role="status" style={{ marginBottom: 20, color: '#888' }}>
          ℹ️ {notice}
        </div>
      )}

       {loading ? (
        <div
          className="card"
          role="status"
          aria-live="polite"
          style={{ padding: 30, textAlign: 'center', marginBottom: 20 }}
        >
          <div className="search-spinner" aria-hidden="true" />
          <p style={{ margin: '14px 0 6px', fontWeight: 600 }}>{progressMessage()}</p>
          <p style={{ margin: '0 0 6px', color: '#888' }}>
            {elapsed}s elapsed · stops automatically after {SEARCH_TIMEOUT_MS / 1000}s
          </p>
          <p style={{ margin: '0 0 16px', color: '#888', fontSize: '0.85rem' }}>
            You can change the filters and click Search Again at any time.
          </p>
          <button className="btn btn-secondary" onClick={cancelSearch}>
            ✖ Cancel Search
          </button>
        </div>
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
            {venueMode === 'individual' && venue
              ? `Found ${totalEvents || events.length} events at ${venue}`
              : `Found ${events.length} events in ${region === 'saint_louis' ? 'Saint Louis' : 'Chicago'} Metro`}
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
                        className="btn btn-secondary btn-sm"
                        href={eventYoutubeUrl(event)}
                        target="_blank"
                        rel="noopener noreferrer"
                        aria-label={`Watch ${event.title} on YouTube`}
                      >
                        ▶ YouTube
                      </a>
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

      {/* Save to My Events result dialog (same style as Fetch Events dialog) */}
      {saveDialog && (
        <div className="modal-overlay" onClick={() => setSaveDialog(null)}>
          <div
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="save-dialog-title"
            onClick={e => e.stopPropagation()}
          >
            <div className="modal-header">
              <h2 id="save-dialog-title">
                {saveDialog.type === 'success'
                  ? '✅ Event Saved'
                  : '⚠️ Save Failed'}
              </h2>

              <button
                className="modal-close"
                aria-label="Close"
                onClick={() => setSaveDialog(null)}
              >
                ×
              </button>
            </div>

            <div style={{ textAlign: 'center', padding: 20 }}>
              <h3>{saveDialog.title}</h3>

              <p style={{ margin: '20px 0' }}>
                {saveDialog.type === 'success'
                  ? 'This event was added to My Events.'
                  : saveDialog.message}
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
              <button
                className="btn btn-secondary"
                autoFocus
                onClick={() => setSaveDialog(null)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

}
