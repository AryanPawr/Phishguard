import { dateTime, percent, shortHash } from "../lib/format.js";

export default function RecentFlaggedEmails({ recent }) {
  return (
    <section className="rounded-lg border border-line bg-paper p-5">
      <h2 className="text-lg font-bold">Recent Flagged Emails</h2>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[880px] text-left text-sm">
          <thead className="border-b border-line text-neutral-600">
            <tr>
              <th className="py-2">Sample</th>
              <th className="py-2">Domain</th>
              <th className="py-2">Source</th>
              <th className="py-2">Risk</th>
              <th className="py-2">Class</th>
              <th className="py-2">Top reason</th>
              <th className="py-2">Time</th>
            </tr>
          </thead>
          <tbody>
            {(recent || []).map((event) => (
              <tr key={event.id} className="border-b border-neutral-200 last:border-0">
                <td className="py-3 font-mono text-xs">{shortHash(event.sample_hash)}</td>
                <td className="py-3">{event.domain || "unknown"}</td>
                <td className="py-3 capitalize">{event.source || "extension"}</td>
                <td className="py-3">{percent(event.risk_score)}</td>
                <td className="py-3 capitalize">{event.classification}</td>
                <td className="max-w-[240px] py-3 text-neutral-600">{event.reasons?.[0] || "No major reason"}</td>
                <td className="py-3">{dateTime(event.created_at)}</td>
              </tr>
            ))}
            {!recent?.length ? (
              <tr>
                <td className="py-4 text-neutral-600" colSpan="7">
                  No analyzed messages yet.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}
