import { useCallback, useEffect, useState } from "react";
import MapDrawer from "../components/MapDrawer";
import HealthResultChart from "../components/HealthResultChart";
import StatusBadge from "../components/StatusBadge";
import { regionApi, healthCheckApi, historyApi } from "../api/client";
import { useAsyncAction } from "../hooks/useAsyncAction";
import HistoryTrendChart from "../components/HistoryTrendChart";

export default function DashboardPage() {
  const [boundary, setBoundary] = useState(null);
  const [regionName, setRegionName] = useState("");
  const [regions, setRegions] = useState([]);
  const [selectedRegionId, setSelectedRegionId] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const listAction = useAsyncAction(regionApi.list);
  const createAction = useAsyncAction(regionApi.create);
  const healthCheckAction = useAsyncAction(healthCheckApi.run);
  const historyAction = useAsyncAction(historyApi.get);

  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

  const refreshRegions = useCallback(async () => {
    const list = await listAction.run();
    setRegions(list);
  }, [listAction]);

  useEffect(() => {
    refreshRegions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // load once on mount, not on every refreshRegions identity change

  async function handleSaveRegion() {
    if (!regionName || !boundary) return;
    await createAction.run(regionName, boundary);
    setRegionName("");
    setBoundary(null);
    refreshRegions();
  }

  async function handleRunHealthCheck() {
    if (!selectedRegionId || !startDate || !endDate) return;
    await healthCheckAction.run(selectedRegionId, startDate, endDate);
    await historyAction.run(selectedRegionId);
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-forest text-white px-6 py-3 flex justify-between items-center">
        <h1 className="font-bold">🌲 Forest Health Monitor</h1>
        <a
          href="/about"
          className="group inline-flex items-center gap-2 rounded-lg border border-white/20 bg-transparent px-4 py-2 text-sm font-medium text-white transition-all hover:border-white hover:bg-white/10 active:scale-95 active:bg-white/20"
        >
          <svg
            className="h-4 w-4 transition-transform group-hover:rotate-12"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth="2"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
          </svg>
          <span>Project Details</span>
        </a>
      </header>

      <main className="mx-auto px-60 py-20 space-y-4">
        <section className="bg-white rounded-lg shadow p-5">
          <h2 className="font-semibold mb-1">1. Draw your forest boundary</h2>
          <p className="text-sm text-gray-500 mb-3">
            Search for a forest, park, or reserve to auto-fill its boundary, or use the
            polygon tool on the map to draw one by hand. Then name and save the region.
          </p>
          <MapDrawer onBoundaryDrawn={setBoundary} />
          <input
            className="w-full border rounded px-3 py-2 mt-3 mb-2"
            placeholder="e.g. Redwood Grove"
            value={regionName}
            onChange={(e) => setRegionName(e.target.value)}
            data-testid="region-name-input"
          />
          <button
            className="bg-forest text-white rounded px-4 py-2 disabled:opacity-50"
            onClick={handleSaveRegion}
            disabled={createAction.isLoading || !boundary || !regionName}
            data-testid="save-region-button"
          >
            {createAction.isLoading ? "Saving..." : "Save Forest Region"}
          </button>
          {createAction.error && (
            <p className="text-severe text-sm mt-2">{createAction.error}</p>
          )}
        </section>

        <section className="bg-white rounded-lg shadow p-5">
          <h2 className="font-semibold mb-3">2. Run a health check</h2>
          <select
            className="w-full border rounded px-3 py-2 mb-3"
            value={selectedRegionId}
            onChange={(e) => setSelectedRegionId(e.target.value)}
            data-testid="region-select"
          >
            <option value="">Choose a saved region...</option>
            {regions.map((region) => (
              <option key={region.id} value={region.id}>
                {region.name}
              </option>
            ))}
          </select>
          <div className="grid grid-cols-2 gap-3 mb-3">
            <input
              type="date"
              className="border rounded px-3 py-2"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              data-testid="start-date-input"
            />
            <input
              type="date"
              className="border rounded px-3 py-2"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              data-testid="end-date-input"
            />
          </div>
          <button
            className="bg-forest text-white rounded px-4 py-2 disabled:opacity-50"
            onClick={handleRunHealthCheck}
            disabled={healthCheckAction.isLoading || !selectedRegionId || !startDate || !endDate}
            data-testid="run-health-check-button"
          >
            {healthCheckAction.isLoading ? "Checking..." : "Check Forest Health"}
          </button>
          {healthCheckAction.error && (
            <p className="text-severe text-sm mt-2" data-testid="health-check-error">
              {healthCheckAction.error}
            </p>
          )}
        </section>

        {healthCheckAction.data && (
          <section className="bg-white rounded-lg shadow p-5" data-testid="results-section">
            <h2 className="font-semibold mb-3">3. Result</h2>
            <div className="flex items-center gap-2 mb-4">
              <StatusBadge status={healthCheckAction.data.status} />
              <span className="text-xs text-gray-500" data-testid="cache-note">
                {healthCheckAction.data.came_from_cache ? "(from cache)" : "(freshly computed)"}
              </span>
            </div>
            <HealthResultChart result={healthCheckAction.data} />

            {historyAction.data?.length > 1 && (
              <section className="bg-white rounded-lg shadow p-5 mt-4">
                <h2 className="font-semibold mb-3">Trend over time</h2>
                <HistoryTrendChart history={historyAction.data} />
              </section>
            )}

            <a
              href={`${API_BASE_URL}/regions/${selectedRegionId}/report.pdf`}
              target="_blank"
              rel="noreferrer"
              className="text-sm underline text-forest inline-block mt-4"
            >
              Download PDF report
            </a>
          </section>
        )}
      </main>
    </div>
  );
}