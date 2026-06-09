export function Loading() {
  return <div className="border border-line bg-white p-5 text-sm text-slate-600">Loading market model...</div>;
}

export function ErrorState({ message }) {
  return <div className="border border-red-200 bg-red-50 p-5 text-sm text-red-700">{message}</div>;
}
