export default function Metric({ label, value, tone = "default" }) {
  const tones = {
    default: "text-ink",
    good: "text-gain",
    bad: "text-loss",
    info: "text-signal"
  };

  return (
    <div className="border border-line bg-white px-4 py-3">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-1 text-2xl font-semibold ${tones[tone]}`}>{value}</div>
    </div>
  );
}
