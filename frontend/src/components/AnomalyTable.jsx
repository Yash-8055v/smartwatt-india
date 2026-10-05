import { useState, useMemo } from 'react'
import { fmtTs, fmtNum, methodLabels } from '../utils/format'
import { SeverityBadge, MethodTag, Empty } from './ui'

/**
 * Anomaly data table with client-side sort and severity filter.
 * Props: anomalies – array of AnomalyPoint from API; showHousehold – bool
 */
export default function AnomalyTable({ anomalies = [], showHousehold = false }) {
  const [minMethods, setMinMethods] = useState(1)
  const [sortKey, setSortKey] = useState('timestamp')
  const [sortDir, setSortDir] = useState('desc')

  const filtered = useMemo(() => {
    const f = anomalies.filter((a) => a.anomaly_method_count >= minMethods)
    return [...f].sort((a, b) => {
      let av = a[sortKey], bv = b[sortKey]
      if (typeof av === 'string') av = av.localeCompare(bv)
      else av = (av ?? 0) - (bv ?? 0)
      return sortDir === 'asc' ? av : -av
    })
  }, [anomalies, minMethods, sortKey, sortDir])

  function toggleSort(key) {
    if (sortKey === key) setSortDir((d) => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('desc') }
  }

  const Th = ({ k, children }) => (
    <th
      onClick={() => toggleSort(k)}
      className="px-3 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wide cursor-pointer select-none hover:text-gray-200 whitespace-nowrap"
    >
      {children} {sortKey === k ? (sortDir === 'asc' ? '↑' : '↓') : ''}
    </th>
  )

  if (!anomalies.length) return <Empty text="No anomalies detected for this selection." />

  return (
    <div>
      {/* Filter bar */}
      <div className="flex flex-wrap gap-3 mb-4 items-center">
        <span className="text-xs text-gray-400">Min. methods flagged:</span>
        {[1, 2, 3, 4].map((n) => (
          <button
            key={n}
            onClick={() => setMinMethods(n)}
            className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
              minMethods === n
                ? 'bg-blue-700 text-white'
                : 'bg-[#22263a] text-gray-400 hover:bg-[#2e3347]'
            }`}
          >
            ≥{n}
          </button>
        ))}
        <span className="text-xs text-gray-500 ml-auto">{filtered.length.toLocaleString()} rows</span>
      </div>

      <div className="overflow-x-auto rounded-lg border border-[#2e3347]">
        <table className="w-full text-sm">
          <thead className="bg-[#22263a]">
            <tr>
              {showHousehold && <Th k="apt_id">Apt</Th>}
              <Th k="timestamp">Timestamp</Th>
              <Th k="energy_kwh">Actual kWh</Th>
              <Th k="lnenergy_predicted">Expected (ln)</Th>
              <Th k="feat_zscore_global">Global Z</Th>
              <Th k="feat_rolling_zscore">Rolling Z</Th>
              <Th k="residual_zscore">Residual Z</Th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-400 uppercase tracking-wide">Methods</th>
              <Th k="anomaly_method_count">Severity</Th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#2e3347]">
            {filtered.map((row, i) => {
              const labels = methodLabels(row)
              return (
                <tr
                  key={i}
                  className="hover:bg-[#22263a]/60 transition-colors"
                >
                  {showHousehold && (
                    <td className="px-3 py-2 text-gray-300">{row.apt_id}</td>
                  )}
                  <td className="px-3 py-2 text-gray-300 whitespace-nowrap">{fmtTs(row.timestamp)}</td>
                  <td className="px-3 py-2 text-blue-300 font-mono">{fmtNum(row.energy_kwh, 4)}</td>
                  <td className="px-3 py-2 text-green-400 font-mono">{fmtNum(row.lnenergy_predicted, 3)}</td>
                  <td className="px-3 py-2 font-mono text-right">
                    <ZScore value={row.feat_zscore_global} />
                  </td>
                  <td className="px-3 py-2 font-mono text-right">
                    <ZScore value={row.feat_rolling_zscore} />
                  </td>
                  <td className="px-3 py-2 font-mono text-right">
                    <ZScore value={row.residual_zscore} />
                  </td>
                  <td className="px-3 py-2">
                    {labels.map((l) => <MethodTag key={l} label={l} />)}
                  </td>
                  <td className="px-3 py-2">
                    <SeverityBadge count={row.anomaly_method_count} />
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <p className="mt-3 text-xs text-gray-500">
        ⚠ "Unusual consumption" means the reading deviates significantly from this household's own historical pattern. It does not imply theft, appliance failure, or any specific cause.
      </p>
    </div>
  )
}

function ZScore({ value }) {
  if (value == null) return <span className="text-gray-600">—</span>
  const abs = Math.abs(value)
  const color = abs > 3 ? '#f87171' : abs > 2 ? '#fbbf24' : '#7c8299'
  return <span style={{ color }}>{fmtNum(value, 2)}</span>
}
