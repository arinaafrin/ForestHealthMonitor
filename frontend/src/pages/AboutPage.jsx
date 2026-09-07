export default function AboutPage() {
    return (
        <div className="min-h-screen bg-gray-50">
            <header className="bg-forest text-white px-6 py-3 flex justify-between items-center">
                <h1 className="font-bold">🌲 Forest Health Monitor</h1>
                <a
                    href="/"
                    className="group inline-flex items-center gap-2 rounded-lg border border-white/20 bg-transparent px-4 py-2 text-sm font-medium text-white transition-all hover:border-white hover:bg-white/10 active:scale-95 active:bg-white/20"
                >
                    <svg
                        className="h-4 w-4 transition-transform group-hover:-translate-x-1"
                        fill="none"
                        viewBox="0 0 24 24"
                        strokeWidth="2"
                        stroke="currentColor"
                    >
                        <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
                    </svg>
                    <span>Dashboard</span>
                </a>
            </header>

            <main className="max-w-3xl mx-auto px-6 py-10 space-y-8">
                <section>
                    <h2 className="text-xl font-semibold mb-2">What this project is</h2>
                    <p className="text-gray-700">
                        Forest Health Monitor is a full-stack web app that checks the health of any
                        forest using real satellite data, no site visit needed. Draw a boundary on
                        a map, pick a date range, and the system analyzes recent satellite images to
                        tell you if that forest is healthy, stressed, or showing signs of damage.
                    </p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-2">Example</h2>
                    <p className="text-gray-700">
                        A user draws a boundary around a section of forest and picks the last 3
                        months. The app pulls Sentinel-2 satellite images for that area and date
                        range, calculates four vegetation scores, and returns a status: Healthy,
                        Moderate Stress, or Severe Stress; along with a trend chart showing how
                        those scores have changed over past checks. A conservation team could use
                        this to catch early signs of drought stress or illegal logging without ever
                        visiting the site.
                    </p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-2">The four indices explained</h2>
                    <ul className="list-disc list-inside text-gray-700 space-y-1">
                        <li><b>NDVI (Greenness)</b> — how much healthy vegetation is present.</li>
                        <li><b>NBR (Burn severity)</b> — signs of fire damage.</li>
                        <li><b>NDMI (Moisture)</b> — water content in leaves, an early stress signal.</li>
                        <li><b>EVI (Canopy density)</b> — how thick and full the tree cover is.</li>
                    </ul>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-2">System architecture</h2>
                    <p className="text-gray-700 mb-3">
                        The app is split into independent, containerized services that talk to each
                        other over a private Docker network. Only the frontend is exposed to the
                        internet; the database, cache, and API are reachable only inside the
                        network, not directly from outside.
                    </p>
                    <div className="bg-white border rounded-lg p-4 font-mono text-xs text-gray-700 leading-6 overflow-x-auto">
                        <pre>
                            {`       Browser
          │
          ▼ (Port 80/443)
   ┌─────────────┐       /api/*       ┌──────────────┐
   │  forest_web │ ─────────────────> │  forest_api  │
   │  (Nginx +   │  (Internal HTTP)   │  (FastAPI +  │
   │  React app) │                    │   Uvicorn)   │
   └─────────────┘                    └──────┬───────┘
                                             │
             ┌───────────────────────────────┼───────────────────────────────┐
             │                               │                               │
             ▼                               ▼                               ▼
   ┌──────────────────┐            ┌──────────────────┐            ┌──────────────────┐
   │   forest_cache   │            │ forest_database  │            │   Google Earth   │
   │     (Redis)      │            │ (PostgreSQL +    │            │  Engine (External│
   │                  │            │    PostGIS)      │            │      API)        │
   └──────────────────┘            └──────────────────┘            └──────────────────┘`}
                        </pre>
                    </div>
                    <p className="text-gray-700 mt-3">
                        <b>Request flow:</b> the browser talks only to Nginx, which serves the React
                        app and forwards <code>/api/*</code> calls to FastAPI. FastAPI checks Redis
                        first for a cached result; on a cache miss, it queries Earth Engine for
                        satellite data, runs the vegetation-index math, saves the result to PostGIS,
                        caches it, and returns it — so repeat checks on the same region and date
                        range are near-instant.
                    </p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-2">Tech stack</h2>
                    <ul className="list-disc list-inside text-gray-700 space-y-1">
                        <li><b>Backend:</b> FastAPI (Python), Gunicorn + Uvicorn workers</li>
                        <li><b>Database:</b> PostGIS (Postgres with geospatial extensions) for storing forest boundaries and historical results</li>
                        <li><b>Cache:</b> Redis, keyed by region and date range, to avoid re-querying satellite data</li>
                        <li><b>Satellite data:</b> Google Earth Engine (Sentinel-2 imagery)</li>
                        <li><b>Frontend:</b> React + Vite, interactive map for drawing boundaries, Chart.js for results and trends</li>
                        <li><b>Infrastructure:</b> Docker, with separate images for the API and frontend (Nginx-served), so each can be built, scaled, and deployed independently</li>
                        <li><b>CI/CD:</b> GitHub Actions — runs unit and integration tests, then end-to-end tests against a live Docker Compose stack, before building and publishing images</li>
                    </ul>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-2">Why it's useful</h2>
                    <p className="text-gray-700">
                        Manually checking forest health means physically visiting a site or paying
                        for expensive satellite analysis tools. This app automates that process —
                        anyone can check a forest's condition in seconds, track it over time, and
                        catch problems like drought, fire damage, or deforestation early, at no cost
                        beyond hosting.
                    </p>
                </section>

                <section>
                    <h2 className="text-xl font-semibold mb-2">Future work</h2>
                    <div className="space-y-4 text-gray-700">
                        <div>
                            <h3 className="font-semibold text-sm text-gray-900 mb-1">Finish what's started</h3>
                            <ul className="list-disc list-inside space-y-1">
                                <li>Wire up real user authentication (JWT) — the data models already exist</li>
                                <li>Restrict CORS to the production frontend domain</li>
                                <li>Add an automated deploy step to the CI/CD pipeline</li>
                            </ul>
                        </div>
                        <div>
                            <h3 className="font-semibold text-sm text-gray-900 mb-1">Satellite imagery & alerts</h3>
                            <ul className="list-disc list-inside space-y-1">
                                <li>Capture and store satellite snapshot images for each health check, alongside the numeric scores</li>
                                <li>NDVI heatmap overlay on the map, showing exactly where stress is occurring inside a region</li>
                                <li>A dedicated alerts system that flags and tracks unhealthy regions (with their exact saved location) separately from routine check history</li>
                                <li>Email or webhook notifications when a region's status turns to Moderate or Severe Stress</li>
                            </ul>
                        </div>
                        <div>
                            <h3 className="font-semibold text-sm text-gray-900 mb-1">More analysis features</h3>
                            <ul className="list-disc list-inside space-y-1">
                                <li>Side-by-side comparison of two regions' trend charts</li>
                                <li>Scheduled automatic health checks (weekly/monthly), instead of only on-demand</li>
                                <li>Export region boundaries and results as GeoJSON or Shapefile for use in GIS tools</li>
                            </ul>
                        </div>
                        <div>
                            <h3 className="font-semibold text-sm text-gray-900 mb-1">Reliability & scale</h3>
                            <ul className="list-disc list-inside space-y-1">
                                <li>API rate limiting, since satellite queries aren't free or instant</li>
                                <li>Pagination on region and history endpoints</li>
                                <li>Structured logging in place of print statements, for easier debugging in production</li>
                            </ul>
                        </div>
                    </div>
                </section>
            </main>
        </div>
    );
}