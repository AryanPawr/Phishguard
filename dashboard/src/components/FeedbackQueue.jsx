import { dateTime, percent, shortHash } from "../lib/format.js";

const FEEDBACK_LABELS = {
  mark_not_risky: "Marked not risky",
  report_risky: "Reported risky"
};

export default function FeedbackQueue({ feedback }) {
  return (
    <section className="rounded-lg border border-line bg-paper p-5">
      <h2 className="text-lg font-bold">User Feedback Queue</h2>
      <p className="mt-1 text-sm text-neutral-600">
        Feedback is stored for review and is not used for training automatically.
      </p>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[780px] text-left text-sm">
          <thead className="border-b border-line text-neutral-600">
            <tr>
              <th className="py-2">Sample</th>
              <th className="py-2">Domain</th>
              <th className="py-2">Feedback</th>
              <th className="py-2">Status</th>
              <th className="py-2">Risk</th>
              <th className="py-2">Time</th>
            </tr>
          </thead>
          <tbody>
            {(feedback || []).map((item) => (
              <tr key={item.id} className="border-b border-neutral-200 last:border-0">
                <td className="py-3 font-mono text-xs">{shortHash(item.sample_hash)}</td>
                <td className="py-3">{item.domain || "unknown"}</td>
                <td className="py-3">{FEEDBACK_LABELS[item.user_feedback] || item.user_feedback}</td>
                <td className="py-3 capitalize">{item.review_status}</td>
                <td className="py-3">{percent(item.current_risk_score)}</td>
                <td className="py-3">{dateTime(item.created_at)}</td>
              </tr>
            ))}
            {!feedback?.length ? (
              <tr>
                <td className="py-4 text-neutral-600" colSpan="6">
                  No user feedback yet.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}
