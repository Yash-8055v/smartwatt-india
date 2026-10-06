import { useState, useEffect, useCallback } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, Legend,
} from 'recharts'
import { api } from '../services/api'
import { fmtNum } from '../utils/format'
import { PageWrap, Spinner, ErrorMsg, Card, SectionTitle } from '../components/ui'

// ── Household colour palette (up to 5 households) ────────────────────────────
const PALETTE = ['#60a5fa', '#34d399', '#f472b6', '#fbbf24', '#a78bfa']

// ── Multi-select checkbox component ──────────────────────────────────────────
function HouseholdCheckbox({ household, checked, onChange, color, disabled }) {
  return (
    <label
      className={`flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer border transition-all text-sm
        ${checked
          ? 'border-opacity-60 bg-white/5'
          : 'border-[#2e3347] hover:border-[#404669] hover:bg-white/3'
        }
        ${disabled && !checked ? 'opacity-40 cursor-not-allowed' : ''}
      `}
      style={checked ? { borderColor: color + '80' } : {}}
    >
      <input
        type="checkbox"
        className="sr-only"
        checked={checked}
        disabled={disabled && !checked}
        onChange={() => onChange(household.apt_id)}
      />
      <span
        className="w-3 h-3 rounded-sm flex-shrink-0 border-2 flex items-center justify-center"
        style={checked
          ? { backgroundColor: color, borderColor: color }
          : { borderColor: '#4b5563' }
        }
      >
        {checked && (
          <svg className="w-2 h-2 text-white" viewBox="0 0 8 8" fill="none">
            <path d="M1 4l2 2 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        )}
      </span>
      <span style={checked ? { color } : {}} className="font-medium">
        Apt {household.apt_id}
      </span>
      <span className="text-gray-500 text-xs ml-auto">
        {fmtNum(household.mean_kwh, 2)} kWh avg
      </span>
    </label>
  )
}

// ── Comparison metrics table ──────────────────────────────────────────────────
function ComparisonTable({ selected, colorMap }) {
  if (!selected.length) return null

  const cols = [
    { key: 'apt_id', label: 'Household', fmt: (v) => `Apt ${v}` },
    { key: 'n_observations', label: 'Observations', fmt: (v) => v.toLocaleString('en-IN') },
    { key: 'mean_kwh', label: 'Avg Consumption', fmt: (v) => `${fmtNum(v, 3)} kWh` },
    { key: 'median_kwh', label: 'Median', fmt: (v) => `${fmtNum(v, 3)} kWh` },
    { key: 'std_kwh', label: 'Std Dev', fmt: (v) => `${fmtNum(v, 3)} kWh` },
    { key: 'n_anomalies', label: 'Anomalies', fmt: (v) => v.toLocaleString('en-IN') },
    { key: 'anomaly_rate_pct', label: 'Anomaly Rate', fmt: (v) => `${fmtNum(v, 2)}%` },
  ]

  // Identify min/max for highlighting
  const means = selected.map(h => h.mean_kwh)
  const rates = selected.map(h => h.anomaly_rate_pct)
  const maxMean = Math.max(...means)
  const minMean = Math.min(...means)
  const maxRate = Math.max(...rates)
  const minRate = Math.min(...rates)

  return (
    <div className="overflow-x-auto rounded-xl border border-[#2e3347]">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[#2e3347] bg-[#13161f]">
            {cols.map(c => (
              <th
                key={c.key}
                className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wide whitespace-nowrap"
              >
                {c.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {selected.map((h, i) => (
            <tr
              key={h.apt_id}
              className="border-b border-[#2e3347] last:border-0 hover:bg-white/2 transition-colors"
            >
              {cols.map(c => {
                const val = h[c.key]
                let extra = ''
                if (c.key === 'mean_kwh') {
                  if (val === maxMean && selected.length > 1) extra = ' text-orange-400'
                  if (val === minMean && selected.length > 1) extra = ' text-green-400'
                }
                if (c.key === 'anomaly_rate_pct') {
                  if (val === maxRate && selected.length > 1) extra = ' text-red-400'
                  if (val === minRate && selected.length > 1) extra = ' text-green-400'
                }
                return (
                  <td key={c.key} className={`px-4 py-3 ${extra}`}>
                    {c.key === 'apt_id' ? (
                      <span className="flex items-center gap-2">
                        <span
                          className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                          style={{ backgroundColor: colorMap[h.apt_id] }}
                        />
                        <span className="font-medium text-gray-200">
                          {c.fmt(val)}
                        </span>
                      </span>
                    ) : (
                      <span className={`text-gray-300${extra}`}>{c.fmt(val)}</span>
                    )}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── Custom bar chart tooltip ──────────────────────────────────────────────────
function ChartTooltip({ active, payload, label, unit = '' }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-[#1a1d27] border border-[#2e3347] rounded-lg px-3 py-2 text-xs shadow-xl">
      <div className="text-gray-400 mb-1">{label}</div>
      {payload.map(p => (
        <div key={p.name} className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: p.fill }} />
          <span className="text-gray-200 font-medium">
            {typeof p.value === 'number' ? p.value.toFixed(3) : p.value}{unit}
          </span>
        </div>
      ))}
    </div>
  )
}

// ── Main Compare page ─────────────────────────────────────────────────────────
export default function Compare() {
  const [allHouseholds, setAllHouseholds] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedIds, setSelectedIds] = useState(new Set([1, 2]))

  useEffect(() => {
    setLoading(true)
    api.households()
      .then(d => {
        setAllHouseholds(d.households)
        setLoading(false)
      })
      .catch(e => {
        setError(e.message)
        setLoading(false)
      })
  }, [])

  const toggleHousehold = useCallback((id) => {
    setSelectedIds(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        if (next.size < 5) next.add(id)
      }
      return next
    })
  }, [])

  const selectAll = () => {
    const first5 = allHouseholds.slice(0, 5).map(h => h.apt_id)
    setSelectedIds(new Set(first5))
  }

  const clearAll = () => setSelectedIds(new Set())

  if (loading) return <PageWrap><Spinner text="Loading household data…" /></PageWrap>
  if (error) return <PageWrap><ErrorMsg message={error} /></PageWrap>

  // Build colorMap: selected IDs in sorted order → colours
  const sortedSelected = Array.from(selectedIds).sort((a, b) => a - b)
  const colorMap = Object.fromEntries(
    sortedSelected.map((id, i) => [id, PALETTE[i % PALETTE.length]])
  )

  const selected = allHouseholds.filter(h => selectedIds.has(h.apt_id))
  const atMax = selectedIds.size >= 5

  // Chart data
  const avgConsumptionData = selected.map(h => ({
    name: `Apt ${h.apt_id}`,
    value: h.mean_kwh,
    fill: colorMap[h.apt_id],
  }))

  const anomalyRateData = selected.map(h => ({
    name: `Apt ${h.apt_id}`,
    value: h.anomaly_rate_pct,
    fill: colorMap[h.apt_id],
  }))

  const anomalyCountData = selected.map(h => ({
    name: `Apt ${h.apt_id}`,
    value: h.n_anomalies,
    fill: colorMap[h.apt_id],
  }))

  return (
    <PageWrap>
      {/* Page header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-100 mb-1">Household Comparison</h1>
        <p className="text-gray-500 text-sm">
          Select 2–5 households to compare consumption and anomaly behaviour side-by-side.
        </p>
      </div>

      {/* Selection panel */}
      <Card className="mb-8">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
          <SectionTitle>Select Households</SectionTitle>
          <div className="flex flex-wrap items-center gap-3 text-xs">
            <span className="text-gray-500">
              {selectedIds.size} selected{atMax ? ' (max 5)' : ''}
            </span>
            <button
              onClick={selectAll}
              className="text-blue-400 hover:text-blue-300 transition-colors disabled:opacity-40"
              disabled={atMax}
            >
              Select first 5
            </button>
            <span className="text-gray-600">·</span>
            <button
              onClick={clearAll}
              className="text-gray-400 hover:text-gray-300 transition-colors"
            >
              Clear all
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2">
          {allHouseholds.map((h, i) => (
            <HouseholdCheckbox
              key={h.apt_id}
              household={h}
              checked={selectedIds.has(h.apt_id)}
              onChange={toggleHousehold}
              color={colorMap[h.apt_id] || PALETTE[i % PALETTE.length]}
              disabled={atMax}
            />
          ))}
        </div>

        {atMax && (
          <p className="mt-3 text-xs text-amber-400/80">
            Maximum 5 households selected. Deselect one to add another.
          </p>
        )}
      </Card>

      {/* Empty state */}
      {selected.length === 0 && (
        <div className="flex flex-col items-center justify-center py-24 text-gray-500">
          <div className="text-4xl mb-4">🏠</div>
          <div className="text-base font-medium mb-1">No households selected</div>
          <div className="text-sm">Check at least one household above to start comparing.</div>
        </div>
      )}

      {/* Single household hint */}
      {selected.length === 1 && (
        <div className="flex items-center gap-2 bg-blue-950/30 border border-blue-800/40 rounded-lg px-4 py-3 text-sm text-blue-400 mb-6">
          <span>💡</span>
          <span>Select at least 2 households to see a meaningful comparison.</span>
        </div>
      )}

      {selected.length >= 1 && (
        <>
          {/* Metrics table */}
          <div className="mb-8">
            <SectionTitle>Metrics Comparison</SectionTitle>
            <ComparisonTable selected={selected} colorMap={colorMap} />
            <p className="text-xs text-gray-600 mt-2">
              <span className="text-orange-400">Orange</span> = highest value ·{' '}
              <span className="text-green-400">Green</span> = lowest value (when 2+ households selected)
            </p>
          </div>

          {/* Charts row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Average consumption bar chart */}
            <Card>
              <SectionTitle>Average Consumption (kWh/hr)</SectionTitle>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart
                  data={avgConsumptionData}
                  margin={{ top: 4, right: 16, bottom: 4, left: 0 }}
                  barCategoryGap="35%"
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#2e3347" vertical={false} />
                  <XAxis
                    dataKey="name"
                    tick={{ fill: '#9ca3af', fontSize: 12 }}
                    axisLine={{ stroke: '#2e3347' }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: '#9ca3af', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    width={55}
                    tickFormatter={v => `${v.toFixed(2)}`}
                  />
                  <Tooltip
                    content={<ChartTooltip unit=" kWh" />}
                    cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                  />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {avgConsumptionData.map((entry) => (
                      <Cell key={entry.name} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>

            {/* Anomaly rate bar chart */}
            <Card>
              <SectionTitle>Anomaly Rate (%)</SectionTitle>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart
                  data={anomalyRateData}
                  margin={{ top: 4, right: 16, bottom: 4, left: 0 }}
                  barCategoryGap="35%"
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#2e3347" vertical={false} />
                  <XAxis
                    dataKey="name"
                    tick={{ fill: '#9ca3af', fontSize: 12 }}
                    axisLine={{ stroke: '#2e3347' }}
                    tickLine={false}
                  />
                  <YAxis
                    tick={{ fill: '#9ca3af', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    width={45}
                    tickFormatter={v => `${v.toFixed(1)}%`}
                  />
                  <Tooltip
                    content={<ChartTooltip unit="%" />}
                    cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                  />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {anomalyRateData.map((entry) => (
                      <Cell key={entry.name} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>
          </div>

          {/* Anomaly count chart (full width) */}
          <Card className="mb-8">
            <SectionTitle>Total Anomaly Count</SectionTitle>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart
                data={anomalyCountData}
                margin={{ top: 4, right: 16, bottom: 4, left: 0 }}
                barCategoryGap="40%"
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#2e3347" vertical={false} />
                <XAxis
                  dataKey="name"
                  tick={{ fill: '#9ca3af', fontSize: 12 }}
                  axisLine={{ stroke: '#2e3347' }}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#9ca3af', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  width={50}
                  tickFormatter={v => v.toLocaleString('en-IN')}
                />
                <Tooltip
                  content={({ active, payload, label }) => {
                    if (!active || !payload?.length) return null
                    const h = selected.find(s => `Apt ${s.apt_id}` === label)
                    return (
                      <div className="bg-[#1a1d27] border border-[#2e3347] rounded-lg px-3 py-2 text-xs shadow-xl">
                        <div className="text-gray-400 mb-1">{label}</div>
                        <div className="flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: payload[0].fill }} />
                          <span className="text-gray-200 font-medium">{payload[0].value} anomalies</span>
                        </div>
                        {h && (
                          <div className="text-gray-500 mt-0.5">
                            Rate: {h.anomaly_rate_pct}%
                          </div>
                        )}
                      </div>
                    )
                  }}
                  cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {anomalyCountData.map((entry) => (
                    <Cell key={entry.name} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Data note */}
          <p className="text-xs text-gray-600 text-center">
            Metrics derived from{' '}
            <code className="text-gray-500">/api/v1/households</code>. Anomaly detection uses
            combined Z-score, IQR, rolling, and residual signals.
          </p>
        </>
      )}
    </PageWrap>
  )
}
