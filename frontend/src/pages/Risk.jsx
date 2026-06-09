import { AlertTriangle, ShieldCheck } from "lucide-react";
import { api } from "../api";
import { percent, useApi } from "../hooks";
import Metric from "../components/Metric";
import { ErrorState, Loading } from "../components/DataState";

export default function Risk() {
  const { data, error, loading } = useApi(api.risk);
  if (loading) return <Loading />;
  if (error) return <ErrorState message={error} />;

  return (
    <div className="space-y-5">
      <div className="grid gap-3 md:grid-cols-4">
        <Metric label="Cash Weight" value={percent(data.summary.cash_weight)} />
        <Metric label="AI Exposure" value={percent(data.summary.ai_theme_exposure)} tone="info" />
        <Metric label="High Beta" value={percent(data.summary.high_beta_exposure)} />
        <Metric label="Crypto" value={percent(data.summary.crypto_exposure)} />
      </div>

      <section className="border border-line bg-white">
        <div className="border-b border-line px-4 py-3">
          <h1 className="text-xl font-semibold">Risk Warnings</h1>
        </div>
        <div className="p-4">
          {data.warnings.length === 0 ? (
            <div className="flex items-center gap-2 text-sm text-gain"><ShieldCheck size={18} /> All limits are currently clear.</div>
          ) : (
            <div className="space-y-3">
              {data.warnings.map((warning, index) => (
                <div key={index} className="flex items-start gap-3 border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
                  <AlertTriangle size={18} className="mt-0.5 shrink-0" />
                  <span>{warning.message}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      <section className="border border-line bg-white p-4">
        <h2 className="font-semibold">Risk Limits</h2>
        <div className="mt-3 grid gap-2 text-sm md:grid-cols-2">
          {Object.entries(data.limits).map(([key, value]) => (
            <div key={key} className="flex justify-between border-b border-line py-2">
              <span className="capitalize text-slate-600">{key.replaceAll("_", " ")}</span>
              <span className="font-semibold">{percent(value)}</span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
