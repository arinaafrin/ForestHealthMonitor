const STYLES_BY_STATUS = {
  healthy: "bg-forest text-white",
  moderate_stress: "bg-stress text-white",
  severe_stress: "bg-severe text-white",
  unknown: "bg-gray-400 text-white",
};

/** Small, single-purpose component: takes a status string, renders a colored pill. */
export default function StatusBadge({ status }) {
  const style = STYLES_BY_STATUS[status] || STYLES_BY_STATUS.unknown;
  const label = status.replace("_", " ");
  return (
    <span
      className={`inline-block px-3 py-1 rounded-full text-sm font-semibold capitalize ${style}`}
      data-testid="status-badge"
    >
      {label}
    </span>
  );
}
