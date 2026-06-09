export default function SignalPill({ signal }) {
  const styles = {
    buy: "bg-emerald-100 text-emerald-800 border-emerald-200",
    hold: "bg-blue-100 text-blue-800 border-blue-200",
    reduce: "bg-amber-100 text-amber-800 border-amber-200",
    sell: "bg-red-100 text-red-800 border-red-200"
  };

  return (
    <span className={`inline-flex min-w-20 justify-center border px-2 py-1 text-xs font-semibold uppercase ${styles[signal] || styles.hold}`}>
      {signal}
    </span>
  );
}
