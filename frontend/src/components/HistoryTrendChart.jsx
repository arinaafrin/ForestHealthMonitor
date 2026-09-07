import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS, LineElement, PointElement,
  CategoryScale, LinearScale, Tooltip, Legend,
} from "chart.js";

ChartJS.register(LineElement, PointElement, CategoryScale, LinearScale, Tooltip, Legend);

export default function HistoryTrendChart({ history }) {
  if (!history?.length) return null;

  const labels = history.map((h) => new Date(h.checked_on).toLocaleDateString());
  const data = {
    labels,
    datasets: [
      { label: "Greenness (NDVI)", data: history.map((h) => h.greenness_score), borderColor: "#2d6a4f", tension: 0.2 },
      { label: "Moisture (NDMI)", data: history.map((h) => h.moisture_stress_score), borderColor: "#1d4ed8", tension: 0.2 },
      { label: "Burn severity (NBR)", data: history.map((h) => h.burn_severity_score), borderColor: "#b91c1c", tension: 0.2 },
    ],
  };
  const options = { responsive: true, scales: { y: { min: -1, max: 1 } } };

  return <Line data={data} options={options} data-testid="history-trend-chart" />;
}