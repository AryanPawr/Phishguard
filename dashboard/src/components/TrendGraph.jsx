import { percent } from "../lib/format.js";

export default function TrendGraph({ trends }) {
  const points = normalizePoints(trends);
  const width = 640;
  const height = 220;
  const path = points
    .map((point, index) => {
      const x = points.length === 1 ? width / 2 : (index / (points.length - 1)) * width;
      const y = height - point.risk * height;
      return `${index === 0 ? "M" : "L"} ${x} ${y}`;
    })
    .join(" ");

  return (
    <section className="rounded-lg border border-line bg-paper p-5">
      <h2 className="text-lg font-bold">Risk Trend</h2>
      <svg className="mt-4 h-56 w-full" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Risk trend">
        <rect width={width} height={height} fill="#fafafa" rx="8" />
        <path d={path} fill="none" stroke="#0891b2" strokeWidth="5" strokeLinecap="round" />
        {points.map((point, index) => {
          const x = points.length === 1 ? width / 2 : (index / (points.length - 1)) * width;
          const y = height - point.risk * height;
          return <circle key={`${point.label}-${index}`} cx={x} cy={y} r="5" fill="#171717" />;
        })}
      </svg>
      <div className="mt-3 grid gap-2 text-sm text-neutral-600 sm:grid-cols-3">
        {points.slice(-3).map((point, index) => (
          <div key={`${point.label}-${index}`} className="rounded border border-line px-3 py-2">
            <div>{point.label}</div>
            <div className="font-semibold text-ink">{percent(point.risk)}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

function normalizePoints(trends = []) {
  if (!trends.length) {
    return [{ label: "No data", risk: 0 }];
  }
  return trends.map((point, index) => {
    const rawRisk = Number(point.risk_score ?? point.average_risk ?? 0);
    const createdAt = point.created_at ? new Date(point.created_at) : null;
    const label = createdAt && !Number.isNaN(createdAt.getTime())
      ? createdAt.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      : point.day || `Event ${index + 1}`;
    return {
      label,
      risk: Math.min(Math.max(rawRisk, 0), 1)
    };
  });
}
