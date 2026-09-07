import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  timeout: 30_000, // satellite calls can be slow; fail clearly instead of hanging forever
});

// Turns every backend error into one predictable shape, so components, never need to guess whether `error.response.data.detail` exists.
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const friendlyMessage =
      error.response?.data?.detail ||
      (error.code === "ECONNABORTED"
        ? "The request took too long. Please try again."
        : "Something went wrong. Please try again.");
    return Promise.reject(new Error(friendlyMessage));
  }
);

export const regionApi = {
  list: () => apiClient.get("/regions").then((r) => r.data),
  create: (name, boundaryGeoJson) =>
    apiClient
      .post("/regions", { name, border_shape_geojson: boundaryGeoJson })
      .then((r) => r.data),
};

export const healthCheckApi = {
  run: (regionId, startDate, endDate, maxCloudPercent = 20.0) =>
    apiClient
      .post(`/regions/${regionId}/health-check`, {
        start_date: startDate,
        end_date: endDate,
        max_cloud_percent: maxCloudPercent,
      })
      .then((r) => r.data),
};

export const historyApi = {
  get: (regionId) => apiClient.get(`/regions/${regionId}/history`).then((r) => r.data),
};
