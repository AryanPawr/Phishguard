const tones = {
  alert: "border-alert",
  amber: "border-amber",
  guard: "border-guard",
  default: "border-line"
};

export default function StatCard({ label, value, tone = "default" }) {
  return (
    <article className={`rounded-lg border ${tones[tone]} bg-paper p-4`}>
      <p className="text-sm text-neutral-600">{label}</p>
      <p className="mt-2 text-3xl font-bold">{value}</p>
    </article>
  );
}

