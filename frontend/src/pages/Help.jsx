import { Link } from 'react-router-dom';

// In-app guide: what the application does and how to use each feature.
// Static content only - no API calls.

const sectionStyle = { padding: 24, marginBottom: 20 };
const h2Style = { fontSize: '1.3rem', margin: '0 0 12px', color: '#7c3aed' };
const h3Style = { fontSize: '1.05rem', margin: '18px 0 8px' };
const listStyle = { margin: '0 0 0 20px', lineHeight: 1.7 };
const muted = { color: '#888' };

const ButtonSample = ({ children, kind = 'secondary' }) => (
  <span
    className={`btn btn-${kind} btn-sm`}
    style={{ cursor: 'default', display: 'inline-block', margin: '2px 0' }}
    aria-hidden="true"
  >
    {children}
  </span>
);

export default function Help() {
  return (
    <div style={{ maxWidth: 900 }}>
      <div className="page-header">
        <h1>❓ How to Use EventsManager</h1>
      </div>

      {/* Overview */}
      <section className="card" style={sectionStyle} aria-labelledby="help-overview">
        <h2 id="help-overview" style={h2Style}>What this app does</h2>
        <p style={{ lineHeight: 1.7 }}>
          EventsManager finds concerts, sports, theatre and family events in the Saint Louis and
          Chicago metro areas (within 50 miles of each city center). Most events come from
          Ticketmaster; venues that sell their own tickets - City Winery and MetroTix venues such as
          The Sheldon and Jazz at the Bistro - are included too. You can follow your favorite venues,
          save events you're interested in, buy tickets, and preview performers on YouTube.
        </p>

        <h3 style={h3Style}>The three pages</h3>
        <ul style={listStyle}>
          <li><Link to="/">🎫 Ticketmaster</Link> - search for events and save the ones you like.</li>
          <li><Link to="/events">📅 My Events</Link> - your saved events, grouped by month.</li>
          <li><Link to="/venues">🏛️ Venues</Link> - find venues and keep a list of your favorites.</li>
        </ul>

        <h3 style={h3Style}>Quick start</h3>
        <ol style={listStyle}>
          <li>Open <strong>Ticketmaster</strong>, pick a region and click <ButtonSample kind="primary">Search Events</ButtonSample>.</li>
          <li>Click <ButtonSample>💾 Save to My Events</ButtonSample> on anything that looks good.</li>
          <li>Open <strong>My Events</strong> to see everything you saved, in date order.</li>
        </ol>
      </section>

      {/* Ticketmaster search */}
      <section className="card" style={sectionStyle} aria-labelledby="help-search">
        <h2 id="help-search" style={h2Style}>🎫 Searching for events</h2>
        <p style={{ lineHeight: 1.7 }}>
          Choose your filters, then click <ButtonSample kind="primary">Search Events</ButtonSample>.
          The search only runs when you click the button, so you can set several filters first.
        </p>

        <h3 style={h3Style}>While a search is running</h3>
        <ul style={listStyle}>
          <li>A progress panel shows a spinner, how many seconds have passed, and what the app is doing.</li>
          <li>You can still change the filters. Click <ButtonSample kind="primary">🔄 Search Again</ButtonSample> to replace the running search with your new filters.</li>
          <li><ButtonSample kind="danger">✖ Cancel</ButtonSample> stops the search right away.</li>
          <li>A search that takes longer than 60 seconds stops by itself, with a tip on how to make it faster.</li>
          <li style={muted}><em>My Venues Only</em> checks every saved venue, so it can take a few seconds - especially the first search after starting the app.</li>
        </ul>

        <h3 style={h3Style}>Filters</h3>
        <ul style={listStyle}>
          <li><strong>Region</strong> - Saint Louis Metro or Chicago Metro (50-mile radius).</li>
          <li><strong>Search artist or event</strong> - a name or word, e.g. <em>Three Days Grace</em>, <em>Blues</em>, <em>comedy</em>.</li>
          <li>
            <strong>Venue</strong>:
            <ul style={listStyle}>
              <li><em>All Venues</em> - every venue in the selected region.</li>
              <li><em>My Venues Only</em> - only the venues saved on the Venues page (Ticketmaster, City Winery and MetroTix venues together, in one date-sorted list).</li>
              <li><em>A single venue</em> - just that venue's events, even outside the selected region.</li>
            </ul>
          </li>
          <li><strong>Category</strong> - Music, Sports, Arts &amp; Theatre, Film or Miscellaneous.</li>
          <li><strong>Day</strong> - only events on a given weekday, e.g. Saturdays.</li>
          <li><strong>Date range</strong> - next 30, 60 or 90 days.</li>
        </ul>
        <p style={{ marginTop: 10 }}>
          <ButtonSample>Clear Filters</ButtonSample> resets everything back to the defaults.
        </p>

        <h3 style={h3Style}>Results</h3>
        <ul style={listStyle}>
          <li>Results are sorted by date, soonest first, across all pages.</li>
          <li>50 events per page. Use <ButtonSample>← Previous</ButtonSample> and <ButtonSample>Next →</ButtonSample> at the bottom.</li>
          <li style={muted}>
            Tip: with a Day filter, some pages show fewer than 50 events, because other days are left out.
          </li>
          <li style={muted}>
            MetroTix venues show the door time, and some (like Jazz at the Bistro) list a date without a time.
            City Winery and MetroTix use their own genre names, so the Category filter is a close match rather than exact.
          </li>
        </ul>

        <h3 style={h3Style}>Buttons on each event</h3>
        <ul style={listStyle}>
          <li><ButtonSample>💾 Save to My Events</ButtonSample> - adds the event to My Events. A message confirms it, or tells you it was already saved.</li>
          <li><ButtonSample>▶ YouTube</ButtonSample> - opens the performer's YouTube channel, or a YouTube search when there is no channel.</li>
          <li><ButtonSample kind="primary">🎟️ Get Tickets</ButtonSample> - opens the event's ticket page (Ticketmaster, City Winery or MetroTix).</li>
        </ul>
      </section>

      {/* My Events */}
      <section className="card" style={sectionStyle} aria-labelledby="help-myevents">
        <h2 id="help-myevents" style={h2Style}>📅 My Events</h2>
        <ul style={listStyle}>
          <li>Shows only the events you saved, grouped by month and sorted by date.</li>
          <li>
            Highlights:{' '}
            <span className="badge badge-active">TODAY!</span> for events happening today, and{' '}
            <span className="badge badge-pending">UPCOMING</span> for events in the next 7 days.
          </li>
          <li>Past events are removed automatically when you open the page.</li>
          <li>Each event has <ButtonSample kind="primary">🎟️ Get Tickets</ButtonSample>, <ButtonSample>▶ YouTube</ButtonSample> and <ButtonSample kind="danger">🗑️ Remove</ButtonSample>. Remove asks you to confirm first.</li>
          <li style={muted}>Removing a venue from My Venues does not remove saved events.</li>
        </ul>
      </section>

      {/* Venues */}
      <section className="card" style={sectionStyle} aria-labelledby="help-venues">
        <h2 id="help-venues" style={h2Style}>🏛️ Venues</h2>

        <h3 style={{ ...h3Style, marginTop: 0 }}>Discover Venues</h3>
        <ol style={listStyle}>
          <li>Open the <strong>Discover Venues</strong> tab.</li>
          <li>Pick a metro region. You can also type a keyword like <em>Theatre</em> or <em>Arena</em>.</li>
          <li>Click <ButtonSample kind="primary">🔍 Search Ticketmaster</ButtonSample>.</li>
          <li>Click <ButtonSample kind="primary">+ Add to My Venues</ButtonSample> on venues you like. Search results aren't kept until you add them.</li>
        </ol>

        <h3 style={h3Style}>My Venues</h3>
        <ul style={listStyle}>
          <li>
            <ButtonSample kind="primary">🔄 Fetch Events</ButtonSample> - checks how many upcoming events
            the venue has. Click <ButtonSample kind="primary">📅 View Events</ButtonSample> in the message to see
            them on the Ticketmaster page, already filtered to that venue.
          </li>
          <li><ButtonSample kind="ticketmaster">🎟 Ticketmaster</ButtonSample> - opens the venue's own events page (Ticketmaster, City Winery or MetroTix).</li>
          <li><ButtonSample>✏️ Edit</ButtonSample> - change the name, address, website, event source or notes.</li>
          <li><ButtonSample kind="danger">Remove</ButtonSample> - asks you to confirm, then removes the venue from your list. Your saved events are kept.</li>
          <li><ButtonSample kind="primary">+ Add Venue</ButtonSample> (top of the page) - add a venue by hand.</li>
        </ul>

        <h3 style={h3Style}>Where a venue's events come from</h3>
        <p style={{ lineHeight: 1.7, marginBottom: 8 }}>
          When adding or editing a venue, pick its <strong>Scraper Type</strong> (event source):
        </p>
        <ul style={listStyle}>
          <li><strong>Ticketmaster</strong> - venues found with Discover Venues. Set automatically.</li>
          <li><strong>City Winery (St. Louis / Chicago)</strong> - website: <code>https://citywinery.com/pages/events/st-louis</code> or <code>.../chicago</code>.</li>
          <li><strong>MetroTix</strong> - for venues that sell through MetroTix, like The Sheldon or Jazz at the Bistro. Website: the venue's MetroTix page, e.g. <code>https://www.metrotix.com/events/venue/sheldon-the</code>.</li>
          <li style={muted}>If a venue shows 0 events with Fetch Events, it may sell tickets somewhere else - try a different source.
            Avoid adding the same venue twice from two sources, or its shows can appear twice.</li>
        </ul>
      </section>

      {/* Tips */}
      <section className="card" style={sectionStyle} aria-labelledby="help-tips">
        <h2 id="help-tips" style={h2Style}>💡 Tips and troubleshooting</h2>
        <ul style={listStyle}>
          <li><strong>No events found?</strong> Remove a filter or two, choose a longer date range, or try another region.</li>
          <li><strong>Search is slow or stopped after 60 seconds?</strong> Choose a shorter date range, one venue instead of <em>My Venues Only</em>, or add a keyword, then search again.</li>
          <li><strong>"Could not reach the search service"?</strong> The app's background service isn't running. Close and reopen the app.</li>
          <li><strong>Want everything at your favorite places?</strong> Add them on the Venues page, then search with <em>My Venues Only</em>.</li>
          <li><strong>Search error or "API key not configured"?</strong> The Ticketmaster key is set in the file
            <code style={{ marginLeft: 4 }}>%APPDATA%\search-events-manager\.env</code>.</li>
          <li><strong>"Rate limit exceeded"?</strong> Ticketmaster limits how many searches you can make. Wait a moment and try again.</li>
          <li>Links like Get Tickets and YouTube open in your normal web browser.</li>
        </ul>
      </section>
    </div>
  );
}
