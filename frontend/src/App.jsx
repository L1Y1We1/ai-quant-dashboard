import { Activity, BarChart3, Briefcase, Gauge, List } from "lucide-react";
import { useState } from "react";
import Dashboard from "./pages/Dashboard";
import Portfolio from "./pages/Portfolio";
import Signals from "./pages/Signals";
import Risk from "./pages/Risk";
import Watchlist from "./pages/Watchlist";
import VirtualPortfolio from "./pages/VirtualPortfolio";

const pages = [
  { id: "dashboard", label: "Dashboard", icon: Activity, component: Dashboard },
  { id: "portfolio", label: "Portfolio", icon: Briefcase, component: Portfolio },
  { id: "signals", label: "Signals", icon: BarChart3, component: Signals },
  { id: "risk", label: "Risk", icon: Gauge, component: Risk },
  { id: "watchlist", label: "Watchlist", icon: List, component: Watchlist },
  { id: "virtual", label: "虚拟盘", icon: Briefcase, component: VirtualPortfolio }
];

export default function App() {
  const [active, setActive] = useState("dashboard");
  const page = pages.find((item) => item.id === active) || pages[0];
  const Page = page.component;

  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-4">
          <div>
            <div className="text-lg font-semibold">Quant Foundry</div>
            <div className="text-xs uppercase tracking-wide text-slate-500">AI Infrastructure Portfolio Engine</div>
          </div>
          <nav className="flex flex-wrap gap-1">
            {pages.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActive(id)}
                className={`inline-flex items-center gap-2 border px-3 py-2 text-sm font-medium ${
                  active === id ? "border-ink bg-ink text-white" : "border-line bg-white text-slate-700 hover:border-ink"
                }`}
                title={label}
              >
                <Icon size={16} />
                <span>{label}</span>
              </button>
            ))}
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6">
        <Page />
      </main>
    </div>
  );
}
