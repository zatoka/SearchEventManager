import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';

import {
  getVenues,
  getMyVenues,
  addMyVenue,
  removeMyVenue,
  searchTicketmasterVenuesByRegion,
  createVenue,
  updateVenue,
  fetchVenueEvents
} from '../api/client';

const SCRAPER_TYPES = [
  { value: 'ticketmaster', label: 'Ticketmaster' },
  { value: 'axs', label: 'AXS' },
  { value: 'metrotix', label: 'MetroTix' },
];

export default function Venues() {
  // --------------------------------------------------
  // State
  // --------------------------------------------------
  
  const [activeTab, setActiveTab] = useState('my');
  const navigate = useNavigate();
  const [venues, setVenues] = useState([]);
  const [myVenues, setMyVenues] = useState([]);

  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [fetchingId, setFetchingId] = useState(null);
  const [fetchDialog, setFetchDialog] = useState(null);
  const [addingVenueId, setAddingVenueId] = useState(null);

  const [discoveredVenues, setDiscoveredVenues] = useState([]);

  const [searchRegion, setSearchRegion] = useState('saint_louis');
  const [searchKeyword, setSearchKeyword] = useState('');
  const [searchPage, setSearchPage] = useState(0);
  const [searchTotal, setSearchTotal] = useState(0);
  const [searchTotalPages, setSearchTotalPages] = useState(0);
  const [searchRadius, setSearchRadius] = useState(50);

  const [showModal, setShowModal] = useState(false);
  const [editingVenue, setEditingVenue] = useState(null);

  const [formData, setFormData] = useState({
    name: '',
    url: '',
    address: '',
    scraper_type: '',
    notes: ''
  });

  // --------------------------------------------------
  // Load data
  // --------------------------------------------------

  const loadVenues = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getVenues();
      setVenues(data);
    } catch (err) {
      console.error('Failed to load venues:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadMyVenues = useCallback(async () => {
    try {
      const data = await getMyVenues();
      setMyVenues(data);
    } catch (err) {
      console.error('Failed to load My Venues:', err);
    }
  }, []);

  useEffect(() => {
    loadVenues();
    loadMyVenues();
  }, [loadVenues, loadMyVenues]);

  // --------------------------------------------------
  // Ticketmaster discovery
  // --------------------------------------------------

  const runTicketmasterSearch = async (page = 0) => {
    setSearching(true);

    try {
      const result = await searchTicketmasterVenuesByRegion({
        region: searchRegion,
        keyword: searchKeyword.trim() || undefined,
        size: 100,
        page
      });

      setDiscoveredVenues(result.venues || []);
      setSearchPage(result.page ?? page);
      setSearchTotal(result.total || 0);
      setSearchTotalPages(result.total_pages || 0);
      setSearchRadius(result.radius_miles || 50);
    } catch (err) {
      alert(
        'Ticketmaster search failed: ' +
        (err.response?.data?.detail || err.message)
      );
    } finally {
      setSearching(false);
    }
  };

  const handleSearchTicketmaster = async (e) => {
    e.preventDefault();
    setDiscoveredVenues([]);
    setSearchPage(0);
    setSearchTotal(0);
    setSearchTotalPages(0);
    await runTicketmasterSearch(0);
  };

  const handleSearchPageChange = async (page) => {
    if (page < 0 || page >= searchTotalPages || searching) return;
    await runTicketmasterSearch(page);
  };

  const handleAddDiscoveredVenue = async (venue) => {
    setAddingVenueId(venue.ticketmaster_id);

    try {
      // Check master catalog for an existing Ticketmaster ID.
      let existing = venues.find(
        v => v.ticketmaster_id === venue.ticketmaster_id
      );

      // Create the master record if necessary.
      if (!existing) {
        existing = await createVenue({
          name: venue.name,
          url: venue.url || '',
          address: venue.address || '',
          scraper_type: 'ticketmaster',
          ticketmaster_id: venue.ticketmaster_id,
          postal_code: venue.postal_code || '',
          latitude: venue.latitude,
          longitude: venue.longitude,
          timezone: venue.timezone || ''
        });
      }

      // Add the master record to My Venues.
      await addMyVenue(existing.id);

      await Promise.all([
        loadVenues(),
        loadMyVenues()
      ]);

    } catch (err) {
      alert(
        'Failed to add venue: ' +
        (err.response?.data?.detail || err.message)
      );
    } finally {
      setAddingVenueId(null);
    }
  };

  // --------------------------------------------------
  // My Venues
  // --------------------------------------------------

  const handleRemoveMyVenue = async (venueId) => {
    if (!confirm('Remove this venue from My Venues?')) return;

    try {
      await removeMyVenue(venueId);
      await loadMyVenues();
    } catch (err) {
      alert(
        'Failed to remove venue: ' +
        (err.response?.data?.detail || err.message)
      );
    }
  };

  // --------------------------------------------------
  // Manual venue management
  // --------------------------------------------------

  const handleOpenModal = (venue = null) => {
    if (venue) {
      setEditingVenue(venue);

      setFormData({
        name: venue.name,
        url: venue.url || '',
        address: venue.address || '',
        scraper_type: venue.scraper_type || '',
        notes: venue.notes || ''
      });

    } else {
      setEditingVenue(null);

      setFormData({
        name: '',
        url: '',
        address: '',
        scraper_type: '',
        notes: ''
      });
    }

    setShowModal(true);
  };

  const handleCloseModal = () => {
    setShowModal(false);
    setEditingVenue(null);

    setFormData({
      name: '',
      url: '',
      address: '',
      scraper_type: '',
      notes: ''
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      if (editingVenue) {
        await updateVenue(editingVenue.id, formData);
      } else {
        const createdVenue = await createVenue(formData);
        await addMyVenue(createdVenue.id);
      }

      handleCloseModal();

      await Promise.all([
        loadVenues(),
        loadMyVenues()
      ]);

    } catch (err) {
      alert(
        'Failed to save venue: ' +
        (err.response?.data?.detail || err.message)
      );
    }
  };


  // --------------------------------------------------
  // Fetch events
  // --------------------------------------------------
const handleFetchEvents = async (venueId) => {
  setFetchingId(venueId);

  try {
    const events = await fetchVenueEvents(venueId);

    const venue = [...myVenues, ...venues].find(
      v => String(v.id) === String(venueId)
    );

    setFetchDialog({
      type: 'success',
      venueId,
      venueName: venue?.name || 'Selected Venue',
      count: Array.isArray(events) ? events.length : 0
    });

    console.log('FETCH EVENTS RESPONSE:', events);

  } catch (err) {
    setFetchDialog({
      type: 'error',
      message:
        err.response?.data?.detail ||
        err.message ||
        'Unable to fetch events.'
    });
  } finally {
    setFetchingId(null);
  }
};
  

  // --------------------------------------------------
  // Render and interface
  // --------------------------------------------------

  if (loading) {
    return <div className="loading">Loading venues...</div>;
  }

  // --------------------------------------------------
  // Venue card
  // --------------------------------------------------

  const renderVenueCard = (venue) => (
    <div key={venue.id} className="card venue-card">

      <div className="venue-card-header">
        <div className="venue-name">{venue.name}</div>   
      </div>

      <div className="venue-details">

        {venue.address && (
          <p>📍 {venue.address}</p>
        )}

        {venue.url && (
          <p>
            🔗 <a
              href={venue.url}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#7c3aed' }}
            >
              Website
            </a>
          </p>
        )}

        {venue.notes && (
          <p>📝 {venue.notes}</p>
        )}

      </div>

      <div className="venue-actions">

        <button
          className={`btn btn-primary btn-sm ${
            fetchingId === venue.id ? 'btn-loading' : ''
          }`}
          onClick={() => handleFetchEvents(venue.id)}
          disabled={!venue.scraper_type || fetchingId === venue.id}
        >
          {fetchingId === venue.id
            ? '⏳ Fetching...'
            : '🔄 Fetch Events'}
        </button>
        <button
          className="btn btn-ticketmaster btn-sm"
          onClick={() => window.open(
            venue.url,
            '_blank',
            'noopener,noreferrer'
          )}
          disabled={!venue.ticketmaster_id || !venue.url}
        >
          🎟 Ticketmaster
        </button>

        <button
          className="btn btn-secondary btn-sm"
          onClick={() => handleOpenModal(venue)}
        >
          ✏️ Edit
        </button>

        <button
          className="btn btn-danger btn-sm"
          onClick={() => handleRemoveMyVenue(venue.id)}
        >
          Remove
        </button>


      </div>
    </div>
  );

  // --------------------------------------------------
  // Interface
  // --------------------------------------------------

  return (
    <div>

      <div className="page-header">
        <h1>Venues</h1>

        <button
          className="btn btn-primary"
          onClick={() => handleOpenModal()}
        >
          + Add Venue
        </button>
      </div>

      {/* Navigation tabs */}

      <div style={{
        display: 'flex',
        gap: 10,
        marginBottom: 25,
        borderBottom: '1px solid #ddd',
        paddingBottom: 12
      }}>

        {[
          { id: 'my', label: `My Venues (${myVenues.length})` },
          { id: 'discover', label: 'Discover Venues' }
        ].map(tab => (

          <button
            key={tab.id}
            className={
              activeTab === tab.id
                ? 'btn btn-primary'
                : 'btn btn-secondary'
            }
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>

        ))}

      </div>

      {/* ==========================================
          MY VENUES
      ========================================== */}

      {activeTab === 'my' && (

        <div>

          <h2>My Venues</h2>

          <p>
            These are the venues selected for your event monitoring.
          </p>

          {myVenues.length === 0 ? (

            <div className="empty-state">
              <p>You haven't selected any venues yet.</p>
              <p>
                Open Discover Venues to find venues and add them here.
              </p>
            </div>

          ) : (

            <div className="cards-grid">
              {myVenues.map(venue =>
                renderVenueCard(venue)
              )}
            </div>

          )}

        </div>

      )}

      {/* ==========================================
          DISCOVER VENUES
      ========================================== */}

      {activeTab === 'discover' && (

        <div>

          <h2>Discover Ticketmaster Venues</h2>

          <p>
            Discover Ticketmaster venues within 50 miles of the selected metro
            center. Search results are temporary until you add a venue to My Venues.
          </p>

          <form
            onSubmit={handleSearchTicketmaster}
            className="card"
            style={{
              padding: 20,
              marginBottom: 25
            }}
          >

            <div style={{
              display: 'flex',
              gap: 15,
              flexWrap: 'wrap',
              alignItems: 'end'
            }}>

              <div className="form-group">
                <label>Metro Region *</label>

                <select
                  value={searchRegion}
                  onChange={e => setSearchRegion(e.target.value)}
                >
                  <option value="saint_louis">Saint Louis Metro</option>
                  <option value="chicago">Chicago Metro</option>
                </select>
              </div>

              <div className="form-group">
                <label>Keyword (optional)</label>

                <input
                  value={searchKeyword}
                  onChange={e => setSearchKeyword(e.target.value)}
                  placeholder="Theatre, Arena..."
                />
              </div>

              <button
                type="submit"
                className="btn btn-primary"
                disabled={searching}
              >
                {searching ? 'Searching...' : '🔍 Search Ticketmaster'}
              </button>

            </div>

          </form>

          {discoveredVenues.length > 0 && (

            <div>

              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: 10,
                marginBottom: 15
              }}>
                <h3 style={{ margin: 0 }}>
                  Search Results ({searchTotal.toLocaleString()} total)
                </h3>
                <span style={{ color: '#666' }}>
                  {searchRadius}-mile radius · Page {searchPage + 1} of {searchTotalPages}
                </span>
              </div>

              <div className="cards-grid">

                {discoveredVenues.map(venue => {

                  const existing = venues.find(
                    v => v.ticketmaster_id === venue.ticketmaster_id
                  );

                  const alreadySelected = existing &&
                    myVenues.some(v => v.id === existing.id);

                  return (

                    <div
                      key={venue.ticketmaster_id}
                      className="card venue-card"
                    >

                      <div className="venue-card-header">
                        <div className="venue-name">
                          {venue.name}
                        </div>

                        <span className="badge badge-active">
                          Ticketmaster
                        </span>
                      </div>

                      <div className="venue-details">

                        {venue.address && (
                          <p>📍 {venue.address}</p>
                        )}

                        {(venue.city || venue.state_code) && (
                          <p>🏙️ {[venue.city, venue.state_code].filter(Boolean).join(', ')}</p>
                        )}

                        {typeof venue.distance_miles === 'number' && (
                          <p>📏 {venue.distance_miles.toFixed(2)} miles from metro center</p>
                        )}

                        {venue.postal_code && (
                          <p>ZIP: {venue.postal_code}</p>
                        )}

                        {venue.timezone && (
                          <p>🕒 {venue.timezone}</p>
                        )}

                        {venue.url && (
                          <p>
                            🔗 <a
                              href={venue.url}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              Ticketmaster Website
                            </a>
                          </p>
                        )}

                      </div>

                      <div className="venue-actions">

                        <button
                          className="btn btn-primary btn-sm"
                          disabled={
                            alreadySelected ||
                            addingVenueId === venue.ticketmaster_id
                          }
                          onClick={() => handleAddDiscoveredVenue(venue)}
                        >
                          {alreadySelected
                            ? '✓ Already in My Venues'
                            : addingVenueId === venue.ticketmaster_id
                              ? 'Adding...'
                              : '+ Add to My Venues'}
                        </button>

                      </div>

                    </div>

                  );

                })}

              </div>

              {searchTotalPages > 1 && (
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: 12,
                  marginTop: 20
                }}>
                  <button
                    className="btn btn-secondary"
                    onClick={() => handleSearchPageChange(searchPage - 1)}
                    disabled={searching || searchPage === 0}
                  >
                    ← Previous
                  </button>

                  <span>
                    Page {searchPage + 1} of {searchTotalPages}
                  </span>

                  <button
                    className="btn btn-secondary"
                    onClick={() => handleSearchPageChange(searchPage + 1)}
                    disabled={searching || searchPage >= searchTotalPages - 1}
                  >
                    Next →
                  </button>
                </div>
              )}

            </div>

          )}

          {!searching && discoveredVenues.length === 0 && (

            <div className="empty-state">
              <p>Select a metro region and search Ticketmaster to discover venues.</p>
            </div>

          )}

        </div>

      )}

      {/* ==========================================
          ADD / EDIT VENUE MODAL
      ========================================== */}

      {showModal && (

        <div
          className="modal-overlay"
          onClick={handleCloseModal}
        >

          <div
            className="modal"
            onClick={e => e.stopPropagation()}
          >

            <div className="modal-header">

              <h2>
                {editingVenue ? 'Edit Venue' : 'Add Venue'}
              </h2>

              <button
                className="modal-close"
                onClick={handleCloseModal}
              >
                &times;
              </button>

            </div>

            <form onSubmit={handleSubmit}>

              <div className="form-group">
                <label>Venue Name *</label>

                <input
                  type="text"
                  value={formData.name}
                  onChange={e => setFormData({
                    ...formData,
                    name: e.target.value
                  })}
                  required
                  placeholder="e.g., Fox Theatre"
                />
              </div>

              <div className="form-group">
                <label>Website URL</label>

                <input
                  type="url"
                  value={formData.url}
                  onChange={e => setFormData({
                    ...formData,
                    url: e.target.value
                  })}
                  placeholder="https://..."
                />
              </div>

              <div className="form-group">
                <label>Address</label>

                <input
                  type="text"
                  value={formData.address}
                  onChange={e => setFormData({
                    ...formData,
                    address: e.target.value
                  })}
                  placeholder="123 Main St, St. Louis, MO"
                />
              </div>

              <div className="form-group">
                <label>Scraper Type</label>

                <select
                  value={formData.scraper_type}
                  onChange={e => setFormData({
                    ...formData,
                    scraper_type: e.target.value
                  })}
                >
                  <option value="">-- Select --</option>

                  {SCRAPER_TYPES.map(type => (
                    <option
                      key={type.value}
                      value={type.value}
                    >
                      {type.label}
                    </option>
                  ))}

                </select>
              </div>

              <div className="form-group">
                <label>Notes</label>

                <textarea
                  value={formData.notes}
                  onChange={e => setFormData({
                    ...formData,
                    notes: e.target.value
                  })}
                  rows={2}
                />
              </div>

              <div style={{
                display: 'flex',
                gap: 10,
                justifyContent: 'flex-end',
                marginTop: 20
              }}>

                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={handleCloseModal}
                >
                  Cancel
                </button>

                <button
                  type="submit"
                  className="btn btn-primary"
                >
                  {editingVenue ? 'Update' : 'Add'}
                </button>

              </div>

            </form>

          </div>

        </div>
      )}

      {/* Fetch Events Result Dialog */}
      {fetchDialog && (
        <div className="modal-overlay">
          <div className="modal">
            <div className="modal-header">
              <h2>
                {fetchDialog.type === 'success'
                  ? '✅ Events Retrieved'
                  : '⚠️ Fetch Failed'}
              </h2>

              <button
               className="modal-close"
               onClick={() => setFetchDialog(null)}
              >
                ×
              </button>
            </div>

            {fetchDialog.type === 'success' ? (
              <div style={{ textAlign: 'center', padding: 20 }}>
                <h3>{fetchDialog.venueName}</h3>

                <p style={{ margin: '20px 0' }}>
                  Successfully fetched{' '}
                  <strong style={{ color: '#10b981', fontSize: '1.4rem' }}>
                    {fetchDialog.count} events
                  </strong>
                </p>
              </div>
            ) : (
              <div style={{ padding: 20 }}>
                <p>{fetchDialog.message}</p>
              </div>
            )}

            {/* All dialog buttons on one row */}
            <div style={{
              display: 'flex',
              justifyContent: 'flex-end',
              alignItems: 'center',
              gap: 10,
              padding: '0 20px 20px'
            }}>
              {fetchDialog.type === 'success' && (
                <button
                  className="btn btn-primary"
                  disabled={fetchDialog.count === 0}
                  onClick={() => {
                    // Show this venue's events on the Ticketmaster page,
                    // where they can be browsed and saved to My Events.
                    const url = `/?venue_id=${encodeURIComponent(fetchDialog.venueId)}`;

                    setFetchDialog(null);
                    navigate(url);
                  }}
                >
                  📅 View Events
                </button>
              )}

              <button
                className="btn btn-secondary"
                onClick={() => setFetchDialog(null)}
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