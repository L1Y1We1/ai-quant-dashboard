import { api } from "../api";
import { currency, percent, useApi } from "../hooks";
import { ErrorState, Loading } from "../components/DataState";

export default function Portfolio() {
  const { data, error, loading } = useApi(api.portfolio);
  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} />;

  return (
    <section className="border border-line bg-white">
      <div className="border-b border-line px-4 py-3">
        <h1 className="text-xl font-semibold">Portfolio</h1>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-panel text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">Ticker</th>
              <th className="px-4 py-3">Shares</th>
              <th className="px-4 py-3">Price</th>
              <th className="px-4 py-3">Value</th>
              <th className="px-4 py-3">Current</th>
              <th className="px-4 py-3">Target</th>
              <th className="px-4 py-3">Gap</th>
            </tr>
          </thead>
          <tbody>
            {data.holdings.map((row) => (
              <tr key={row.ticker} className="border-t border-line">
                <td className="px-4 py-3 font-semibold">{row.ticker}</td>
                <td className="px-4 py-3">{row.shares}</td>
                <td className="px-4 py-3">{currency(row.price)}</td>
                <td className="px-4 py-3">{currency(row.market_value)}</td>
                <td className="px-4 py-3">{percent(row.current_weight)}</td>
                <td className="px-4 py-3">{percent(row.target_weight)}</td>
                <td className={row.weight_gap >= 0 ? "px-4 py-3 text-gain" : "px-4 py-3 text-loss"}>{percent(row.weight_gap)}</td>
              </tr>
            ))}
            <tr className="border-t border-line bg-panel font-semibold">
              <td className="px-4 py-3">Cash</td>
              <td className="px-4 py-3">--</td>
              <td className="px-4 py-3">--</td>
              <td className="px-4 py-3">{currency(data.cash)}</td>
              <td className="px-4 py-3">{percent(data.cash / data.total_value)}</td>
              <td className="px-4 py-3">{percent(data.target_weights.CASH)}</td>
              <td className="px-4 py-3">{percent(data.target_weights.CASH - data.cash / data.total_value)}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  );
}
