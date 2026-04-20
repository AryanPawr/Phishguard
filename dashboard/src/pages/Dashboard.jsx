import { useEffect, useState } from "react";
import BrandTable from "../components/BrandTable.jsx";
import FeedbackQueue from "../components/FeedbackQueue.jsx";
import RecentFlaggedEmails from "../components/RecentFlaggedEmails.jsx";
import RiskDistribution from "../components/RiskDistribution.jsx";
import SiemExport from "../components/SiemExport.jsx";
import StatCard from "../components/StatCard.jsx";
import TrendGraph from "../components/TrendGraph.jsx";
import { fetchBrands, fetchFeedback, fetchRecent, fetchSummary, fetchTrends } from "../services/api.js";
import { percent } from "../lib/format.js";

export default function Dashboard({ onLogout, shield }) {
  const [summary, setSummary] = useState(null);
  const [recent, setRecent] = useState([]);
  const [trends, setTrends] = useState([]);
  const [brands, setBrands] = useState([]);
  const [feedback, setFeedback] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const [summaryData, recentData, trendsData, brandData, feedbackData] = await Promise.all([
          fetchSummary(),
          fetchRecent(),
          fetchTrends(),
          fetchBrands(),
          fetchFeedback()
        ]);
        if (mounted) {
          setSummary(summaryData);
          setRecent(recentData);
          setTrends(trendsData);
          setBrands(brandData);
          setFeedback(feedbackData);
        }
      } catch (requestError) {
        if (mounted) setError(requestError.message);
      }
    }
    load();
    const timer = window.setInterval(load, 30000);
    return () => {
      mounted = false;
      window.clearInterval(timer);
    };
  }, []);

  return (
    <main className="min-h-screen bg-neutral-100 text-ink">
      <header className="border-b border-line bg-paper">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-4">
          <div className="flex min-w-0 items-center gap-3">
            <img src={shield} alt="PhishGuard shield" className="h-11 w-11 rounded" />
            <div className="min-w-0">
              <h1 className="truncate text-xl font-bold">PhishGuard</h1>
              <p className="text-sm text-neutral-600">Threat analytics</p>
            </div>
          </div>
          <button className="rounded-md border border-line px-3 py-2 text-sm font-semibold" onClick={onLogout}>
            Sign out
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-5 py-6">
        {error ? <div className="mb-5 rounded-lg border border-alert bg-white p-4 text-alert">{error}</div> : null}

        <section className="grid gap-4 md:grid-cols-4">
          <StatCard label="Events" value={summary?.total_events ?? 0} />
          <StatCard label="Phishing" value={summary?.phishing ?? 0} tone="alert" />
          <StatCard label="Suspicious" value={summary?.suspicious ?? 0} tone="amber" />
          <StatCard label="Average risk" value={percent(summary?.average_risk ?? 0)} tone="guard" />
        </section>

        <section className="mt-6 grid gap-5 lg:grid-cols-[1fr_1fr]">
          <RiskDistribution summary={summary} />
          <TrendGraph trends={trends} />
        </section>

        <section className="mt-6 grid gap-5 lg:grid-cols-[1fr_1.2fr]">
          <BrandTable brands={brands} />
          <RecentFlaggedEmails recent={recent} />
        </section>

        <section className="mt-6">
          <FeedbackQueue feedback={feedback} />
        </section>

        <section className="mt-6">
          <SiemExport />
        </section>
      </div>
    </main>
  );
}
