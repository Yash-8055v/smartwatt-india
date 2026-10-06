import { NavLink } from 'react-router-dom'

const links = [
  { to: '/', label: 'Dashboard' },
  { to: '/anomalies', label: 'Anomaly Explorer' },
  { to: '/compare', label: 'Compare' },
  { to: '/predict', label: 'Predict' },
  { to: '/methodology', label: 'Methodology' },
]

export default function Navbar() {
  return (
    <nav className="sticky top-0 z-40 border-b border-[#2e3347] bg-[#0f1117]/90 backdrop-blur">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-2">
          <span className="text-blue-400 text-lg font-bold tracking-tight">⚡ SmartWatt</span>
          <span className="hidden sm:inline text-gray-500 text-sm">India</span>
        </div>

        {/* Nav links */}
        <ul className="flex items-center gap-1 overflow-x-auto whitespace-nowrap hide-scrollbar pb-1 sm:pb-0">
          {links.map(({ to, label }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `px-3 py-1.5 rounded-lg text-sm transition-colors ${
                    isActive
                      ? 'bg-blue-900/40 text-blue-300 font-medium'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-white/5'
                  }`
                }
              >
                {label}
              </NavLink>
            </li>
          ))}
        </ul>
      </div>
    </nav>
  )
}
