import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:8002/api',
  timeout: 60000,
});

// ── Venues ──────────────────────────────────────────────────────────────────
export const getVenues = () => api.get('/venues/').then(r => r.data);

// ── My Venues (Selected Venues) ────────────────────────────────────────────
export const getMyVenues = () =>
  api.get('/venues/my').then(r => r.data);

export const addMyVenue = (venueId) =>
  api.post(`/venues/my/${venueId}`).then(r => r.data);

export const removeMyVenue = (venueId) =>
  api.delete(`/venues/my/${venueId}`);

// ── Regions and Cities ─────────────────────────────────────────────────────
export const getRegions = () =>
  api.get('/regions/').then(r => r.data);

export const searchTicketmasterVenues = (params) =>
  api.get('/venues/ticketmaster/search', { params }).then(r => r.data);

export const searchTicketmasterVenuesByRegion = (params) =>
  api.get('/venues/ticketmaster/search-by-region', { params }).then(r => r.data);

export const createVenue = (data) => api.post('/venues/', data).then(r => r.data);
export const updateVenue = (id, data) => api.put(`/venues/${id}`, data).then(r => r.data);
export const deleteVenue = (id) => api.delete(`/venues/${id}`);
export const fetchVenueEvents = (venueId) => api.post(`/venues/${venueId}/fetch`).then(r => r.data);

// ── Events ──────────────────────────────────────────────────────────────────
export const getEvents = (params) => api.get('/events/', { params }).then(r => r.data);
export const getEvent = (id) => api.get(`/events/${id}`).then(r => r.data);
export const deleteEvent = (id) => api.delete(`/events/${id}`);
export const deleteVenueEvents = (venueId) => api.delete(`/venues/${venueId}/events`);

// ── Ticketmaster Search ─────────────────────────────────────────────────────
export const searchTicketmaster = (params) => api.get('/ticketmaster/search', { params }).then(r => r.data);
export const getTicketmasterFilters = () => api.get('/ticketmaster/filters').then(r => r.data);

// ── My Events (Saved Events) ────────────────────────────────────────────────
export const getMyEvents = () => api.get('/my-events/').then(r => r.data);
export const saveMyEvent = (event) => api.post('/my-events/', event).then(r => r.data);
export const deleteMyEvent = (id) => api.delete(`/my-events/${id}`);

export default api;
