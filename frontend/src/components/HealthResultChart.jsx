import { Bar } from "react-chartjs-2";
import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
} from "chart.js";

// Chart.js requires each piece it uses to be explicitly registered.
// Registering only what we use (not chart.js's full bundle) keeps the
// production build smaller.
ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip);

export default function HealthResultChart({ result }) {
  const data = {
    labels: ["Greenness", "Burn Severity", "Moisture Stress", "Canopy Density"],
    datasets: [
      {
        label: "Index value (-1 to 1)",
        data: [
          result.greenness_score,
          result.burn_severity_score,
          result.moisture_stress_score,
          result.canopy_density_score,
        ],
        backgroundColor: "#2d6a4f",
        borderRadius: 4,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: { legend: { display: false } },
    scales: { y: { min: -1, max: 1 } },
  };

  return <Bar data={data} options={options} data-testid="results-chart" />;
}
