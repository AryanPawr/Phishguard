export default function RiskDistribution({ summary }) {
  const safe = summary?.safe || 0;
  const suspicious = summary?.suspicious || 0;
  const phishing = summary?.phishing || 0;
  const total = Math.max(safe + suspicious + phishing, 1);
  const rows = [
    ["Safe", safe, "bg-guard"],
    ["Suspicious", suspicious, "bg-amber"],
    ["Phishing", phishing, "bg-alert"]
  ];

  return (
    <section className="rounded-lg border border-line bg-paper p-5">
      <h2 className="text-lg font-bold">Risk Distribution</h2>
      <div className="mt-5 space-y-4">
        {rows.map(([label, value, color]) => (
          <div key={label}>
            <div className="mb-1 flex justify-between text-sm">
              <span>{label}</span>
              <span>{value}</span>
            </div>
            <div className="h-3 overflow-hidden rounded bg-neutral-200">
              <div className={`h-full ${color}`} style={{ width: `${(value / total) * 100}%` }} />
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

