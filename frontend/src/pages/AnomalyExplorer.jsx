import { useState, useMemo } from 'react'
import { useFetch } from '../hooks/useFetch'
import { api } from '../services/api'
import {
  PageWrap, Card, SectionTitle, Spinner, ErrorMsg, Empty, Select,
} from '../components/ui'
import AnomalyTable from '../components/AnomalyTable'

// ── Detection method explanations (non-technical) ──────────────────────────────
const METHODS = [
  {
    label: 'Global Z-score',
    tag: 'Z-score',
    color: '#4f8ef7',
    icon: '📊',
    short: 'Far from the long-run average',
    plain: (
      <>
        This hour's consumption is much <em>higher or lower</em> than the household's
        typical level across the whole study period. The model flags readings that fall
        more than 3 standard deviations from the household's own long-run mean.
      </>
    ),
    note: 'Statistically unusual relative to the household\'s modelled long-run baseline. Not a sign of any fault or theft.',
  },
  {
    label: 'IQR Fence',
    tag: 'IQR',
    color: '#a78bfa',
    icon: '📐',
    short: 'Extreme spike on the kWh scale',
    plain: (
      <>
        Consumption exceeded the upper fence defined by the interquartile range (IQR) — a
        standard statistical method that is robust to outliers. Only the most extreme
        readings (beyond Q3 + 3 × IQR) are flagged.
      </>
    ),
    note: 'Robust outlier detection on raw kWh. Large spikes flagged here are unusual even compared with other high readings.',
  },
  {
    label: '7-Day Rolling Z',
    tag: 'Rolling',
    color: '#34d399',
    icon: '📈',
    short: 'Unusual vs recent history',
    plain: (
      <>
        This hour is unusual relative to the <em>past 7 days</em> of the household's own
        consumption — not its long-term average. The rolling baseline adapts over time,
        so seasonal shifts or gradual changes in habits do not trigger false flags.
      </>
    ),
    note: 'Context-sensitive: a reading may be unusual relative to recent behaviour even if it is within the household\'s overall range.',
  },
  {
    label: 'Residual Z',
    tag: 'Residual',
    color: '#fb923c',
    icon: '🔍',
    short: 'More than the model expected',
    plain: (
      <>
        The Ridge regression model predicted how much electricity this household should
        use at this hour, given the time of day, day of week, month, and temperature.
        The actual consumption differed by more than 3 standard deviations from the
        model's expectation.
      </>
    ),
    note: 'Accounts for context (hour, temperature, weekday, season). A residual flag means the gap between actual and model-expected consumption is unusually large.',
  },
]

/**
 * Anomaly Explorer page — browse all anomalies across all or one household.
 * Supports household filter and min-methods severity filter (inside AnomalyTable).
 * T019: improved detection method explanations for non-technical users.
 */
export default function AnomalyExplorer() {
  const [aptId, setAptId] = useState(1)
  const [expandedMethod, setExpandedMethod] = useState(null)

  const { data: households } = useFetch(() => api.households(), [])
  const allAptIds = households?.households?.map((h) => h.apt_id) ?? []

  const { data: anomalies, loading, error } = useFetch(() => {
    if (aptId === 'all') {
      return Promise.all(allAptIds.map((id) => api.anomalies(id))).then((results) =>
        results.flatMap((r, i) =>
          (r?.data ?? []).map((a) => ({ ...a, apt_id: allAptIds[i] }))
        )
      )
    }
    return api.anomalies(Number(aptId)).then((r) =>
      (r?.data ?? []).map((a) => ({ ...a, apt_id: Number(aptId) }))
    )
  }, [aptId, allAptIds.length])

  const aptCount = anomalies
    ? new Set(anomalies.map((a) => a.apt_id)).size
    : 0

  return (
    <PageWrap>
      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-100 mb-1">Anomaly Explorer</h1>
        <p className="text-sm text-gray-400 max-w-3xl leading-relaxed">
          Hourly observations that are statistically unusual relative to a household's
          own modelled baseline. Each reading was assessed by up to four independent
          statistical methods.{' '}
          <span className="text-gray-500">
            These flags are <strong className="text-gray-400">not</strong> evidence of
            theft, appliance failure, or any specific cause — they indicate statistical
            deviation only.
          </span>
        </p>
      </div>

      {/* Controls */}
      <Card className="mb-6">
        <div className="flex flex-wrap gap-4 items-end">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Household</label>
            <Select value={aptId} onChange={(e) => setAptId(e.target.value)}>
              <option value="all">All households</option>
              {households?.households?.map((h) => (
                <option key={h.apt_id} value={h.apt_id}>
                  Apt {h.apt_id} ({h.n_anomalies} anomalies)
                </option>
              ))}
            </Select>
          </div>

          {anomalies && (
            <div className="ml-auto text-sm text-gray-400">
              <span className="text-gray-200 font-medium">{anomalies.length.toLocaleString()}</span>{' '}
              unusual readings
              {aptId === 'all' && (
                <span className="text-gray-500"> across {aptCount} households</span>
              )}
            </div>
          )}
        </div>
      </Card>

      {/* Detection method explanations */}
      <Card className="mb-6">
        <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
          <SectionTitle>How was this detected?</SectionTitle>
          <span className="text-xs text-gray-600">Click a method to expand its explanation</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {METHODS.map((m) => (
            <MethodCard
              key={m.tag}
              method={m}
              expanded={expandedMethod === m.tag}
              onToggle={() => setExpandedMethod(expandedMethod === m.tag ? null : m.tag)}
            />
          ))}
        </div>

        {/* Expanded detail panel */}
        {expandedMethod && (() => {
          const m = METHODS.find(x => x.tag === expandedMethod)
          if (!m) return null
          return (
            <div
              className="mt-4 p-4 rounded-lg border border-[#2e3347] bg-[#13161f] transition-all"
            >
              <div className="flex items-start gap-3">
                <span className="text-2xl">{m.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold mb-2" style={{ color: m.color }}>
                    {m.label} — {m.short}
                  </div>
                  <p className="text-sm text-gray-300 leading-relaxed mb-3">
                    {m.plain}
                  </p>
                  <p className="text-xs text-gray-500 border-l-2 pl-3 leading-relaxed" style={{ borderColor: m.color + '60' }}>
                    ⚠️ {m.note}
                  </p>
                </div>
              </div>
            </div>
          )
        })()}
      </Card>

      {/* Table */}
      <Card>
        <SectionTitle>Flagged Observations</SectionTitle>
        {loading ? (
          <Spinner text="Loading anomalies…" />
        ) : error ? (
          <ErrorMsg message={error} />
        ) : (
          <AnomalyTable anomalies={anomalies ?? []} showHousehold={aptId === 'all'} />
        )}
      </Card>
    </PageWrap>
  )
}

// ── Method card (compact, clickable) ─────────────────────────────────────────
function MethodCard({ method, expanded, onToggle }) {
  return (
    <button
      onClick={onToggle}
      className={`text-left p-3 rounded-lg border transition-all w-full
        ${expanded
          ? 'border-opacity-60 bg-white/5'
          : 'border-[#2e3347] bg-[#22263a] hover:border-[#404669] hover:bg-[#22263a]/80'
        }
      `}
      style={expanded ? { borderColor: method.color + '80' } : {}}
    >
      <div className="flex items-center gap-2 mb-1.5">
        <span className="text-base">{method.icon}</span>
        <span className="text-xs font-semibold" style={{ color: method.color }}>
          {method.label}
        </span>
        <span className="ml-auto text-gray-600 text-xs">{expanded ? '▲' : '▼'}</span>
      </div>
      <p className="text-xs text-gray-400 leading-snug">{method.short}</p>
    </button>
  )
}
