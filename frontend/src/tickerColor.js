export function getTickerColor(score) {
  if (score === null || score === undefined) return "text-slate-500";
  if (score >= 5) return "text-gain";
  if (score >= 3) return "text-signal";
  if (score >= 1) return "text-amber-700";
  return "text-loss";
}
