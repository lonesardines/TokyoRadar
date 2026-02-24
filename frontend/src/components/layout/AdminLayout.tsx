import { NavLink, Outlet } from 'react-router-dom';
import { Package, Activity, AlertTriangle, ArrowLeft } from 'lucide-react';

const navItems = [
  { to: '/admin/items', label: 'Items', icon: Package },
  { to: '/admin/scrape-jobs', label: 'Scrape Jobs', icon: Activity },
  { to: '/admin/flagged', label: 'Flagged Items', icon: AlertTriangle },
];

export default function AdminLayout() {
  return (
    <div className="min-h-screen flex bg-neutral-50">
      <aside className="w-56 bg-neutral-900 text-white flex flex-col">
        <div className="px-4 py-5 border-b border-neutral-700">
          <h1 className="text-sm font-bold tracking-wider uppercase">TokyoRadar</h1>
          <p className="text-[10px] text-neutral-400 mt-0.5">Admin Dashboard</p>
        </div>
        <nav className="flex-1 py-4">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                  isActive
                    ? 'bg-neutral-800 text-white font-medium'
                    : 'text-neutral-400 hover:text-white hover:bg-neutral-800/50'
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="px-4 py-4 border-t border-neutral-700">
          <NavLink
            to="/"
            className="flex items-center gap-2 text-xs text-neutral-500 hover:text-white transition-colors"
          >
            <ArrowLeft size={14} />
            Back to site
          </NavLink>
        </div>
      </aside>
      <main className="flex-1 overflow-auto">
        <div className="p-6 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
