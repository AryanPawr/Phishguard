import { percent } from "../lib/format.js";

export default function BrandTable({ brands }) {
  return (
    <section className="rounded-lg border border-line bg-paper p-5">
      <h2 className="text-lg font-bold">Impersonated Brands</h2>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-80 text-left text-sm">
          <thead className="border-b border-line text-neutral-600">
            <tr>
              <th className="py-2">Brand</th>
              <th className="py-2">Events</th>
              <th className="py-2">Risk</th>
            </tr>
          </thead>
          <tbody>
            {(brands || []).map((brand) => (
              <tr key={brand.brand} className="border-b border-neutral-200 last:border-0">
                <td className="py-3 font-semibold">{brand.brand}</td>
                <td className="py-3">{brand.count}</td>
                <td className="py-3">{percent(brand.average_risk)}</td>
              </tr>
            ))}
            {!brands?.length ? (
              <tr>
                <td className="py-4 text-neutral-600" colSpan="3">
                  No impersonation events yet.
                </td>
              </tr>
            ) : null}
          </tbody>
        </table>
      </div>
    </section>
  );
}

