import { useState, useMemo } from 'react'
import { useFetch } from '../hooks/useFetch'
import { api } from '../services/api'
import {
  PageWrap, Card, SectionTitle, Spinner, ErrorMsg, Empty, Select,
} from '../components/ui'
import AnomalyTable from '../components/AnomalyTable'

/**
 * Anomaly Explorer page — browse all anomalies across all or one household.
 * Supports household filter and min-methods severity filter (inside AnomalyTable).
 */
export default function AnomalyExplorer() {
  const [aptId, setAptId] = useState('all')

  const { data: households } = useFetch(() => api.households(), [])

  // Fetch anomalies from all households when "all" selected,
  // otherwise fetch from the selected one only.
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
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-100 mb-1">Anomaly Explorer</h1>
        <p className="text-sm text-gray-400">
          Hourly observations flagged as statistically unusual relative to the household's own historical baseline.
          These are <strong className="text-gray-300">not</strong> labels for theft, appliance failure, or any cause.
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
              <span className="text-gray-200 font-medium">{anomalies.length.toLocaleString()}</span> unusual readings
              {aptId === 'all' && (
                <span className="text-gray-500"> across {aptCount} households</span>
              )}
            </div>
          )}
        </div>
      </Card>

      {/* Evidence legend */}
      <Card className="mb-6">
        <SectionTitle>Detection Methods</SectionTitle>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MethodCard
            label="Global Z-score"
            color="#4f8ef7"
            desc="Hourly lnenergy deviates >3σ from this household's long-run mean. Flags persistently high or low readings."
          />
          <MethodCard
            label="IQR Fence"
            color="#a78bfa"
            desc="energy_kwh exceeds Q75 + 3×IQR for this household. Robust to outliers; catches extreme spikes on the kWh scale."
          />
          <MethodCard
            label="7-Day Rolling Z"
            color="#34d399"
            desc="Hourly consumption deviates >3σ from the past 168-observation rolling mean. Context-sensitive; adapts over time."
          />
          <MethodCard
            label="Residual Z"
            color="#fb923c"
            desc="Ridge regression residual (actual − expected) exceeds 3σ. Accounts for time-of-day, temperature, and seasonal patterns."
          />
        </div>
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

function MethodCard({ label, color, desc }) {
  return (
    <div className="p-3 rounded-lg bg-[#22263a] border border-[#2e3347]">
      <div className="text-xs font-semibold mb-1" style={{ color }}>{label}</div>
      <p className="text-xs text-gray-400 leading-relaxed">{desc}</p>
    </div>
  )
}
