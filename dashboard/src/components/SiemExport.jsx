import { useState } from "react";
import { fetchSiemExport } from "../services/api.js";

export default function SiemExport() {
  const [payload, setPayload] = useState("");
  const [error, setError] = useState("");

  async function load() {
    setError("");
    try {
      const result = await fetchSiemExport();
      setPayload(JSON.stringify(result, null, 2));
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  return (
    <section className="rounded-lg border border-line bg-paper p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-bold">SIEM JSON Export</h2>
        <button className="rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white" onClick={load}>
          Generate export
        </button>
      </div>
      {error ? <p className="mt-3 text-sm text-alert">{error}</p> : null}
      {payload ? (
        <pre className="mt-4 max-h-96 overflow-auto rounded border border-line bg-neutral-100 p-4 text-xs">
          {payload}
        </pre>
      ) : null}
    </section>
  );
}

