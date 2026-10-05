/** Shared UI primitive components */

/** Loading spinner */
export function Spinner({ text = 'Loading…' }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-gray-400">
      <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
      <span className="text-sm">{text}</span>
    </div>
  )
}

/** Error display */
export function ErrorMsg({ message }) {
  const isColdStart = message?.includes('fetch') || message?.includes('ECONNREFUSED') || message?.includes('network')
  return (
    <div className="rounded-lg border border-red-800 bg-red-950/30 p-6 text-center">
      <div className="text-red-400 font-medium mb-1">
        {isColdStart ? 'Starting analysis service…' : 'Could not load data'}
      </div>
      <div className="text-red-500/70 text-sm">
        {isColdStart
          ? 'The backend is warming up. Please wait a moment and refresh.'
          : message}
      </div>
    </div>
  )
}

/** Empty state */
export function Empty({ text = 'No data available.' }) {
  return (
    <div className="flex items-center justify-center py-16 text-gray-500 text-sm">
      {text}
    </div>
  )
}

/** Card container */
export function Card({ children, className = '' }) {
  return (
    <div
      className={`rounded-xl border bg-[#1a1d27] border-[#2e3347] p-5 ${className}`}
    >
      {children}
    </div>
  )
}

/** Section heading */
export function SectionTitle({ children }) {
  return <h2 className="text-base font-semibold text-gray-200 mb-4">{children}</h2>
}

/** KPI metric card */
export function KpiCard({ label, value, sub, accent }) {
  return (
    <Card>
      <div className="text-xs text-gray-400 uppercase tracking-wide mb-1">{label}</div>
      <div
        className="text-2xl font-bold"
        style={{ color: accent || 'var(--color-text)' }}
      >
        {value}
      </div>
      {sub && <div className="text-xs text-gray-500 mt-1">{sub}</div>}
    </Card>
  )
}

/** Severity badge */
export function SeverityBadge({ count }) {
  const map = {
    0: { label: 'Normal', cls: 'bg-green-900/40 text-green-400' },
    1: { label: 'Medium', cls: 'bg-yellow-900/40 text-yellow-400' },
    2: { label: 'High', cls: 'bg-orange-900/40 text-orange-400' },
    3: { label: 'Critical', cls: 'bg-red-900/40 text-red-400' },
    4: { label: 'Critical', cls: 'bg-red-900/40 text-red-400' },
  }
  const s = map[count] || map[0]
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${s.cls}`}>
      {s.label}
    </span>
  )
}

/** Method flag tag */
export function MethodTag({ label }) {
  const cls = {
    'Z-score': 'bg-blue-900/40 text-blue-300',
    'IQR': 'bg-purple-900/40 text-purple-300',
    'Rolling': 'bg-teal-900/40 text-teal-300',
    'Residual': 'bg-orange-900/40 text-orange-300',
  }
  return (
    <span className={`inline-block px-1.5 py-0.5 rounded text-xs font-medium mr-1 ${cls[label] || 'bg-gray-800 text-gray-400'}`}>
      {label}
    </span>
  )
}

/** Select dropdown */
export function Select({ value, onChange, children, className = '' }) {
  return (
    <select
      value={value}
      onChange={onChange}
      className={`bg-[#22263a] border border-[#2e3347] rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-blue-500 ${className}`}
    >
      {children}
    </select>
  )
}

/** Text input */
export function Input({ ...props }) {
  return (
    <input
      {...props}
      className={`bg-[#22263a] border border-[#2e3347] rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-blue-500 ${props.className || ''}`}
    />
  )
}

/** Page wrapper with max width */
export function PageWrap({ children }) {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
      {children}
    </div>
  )
}
