import { useState } from 'react'
import { useFetch } from '../hooks/useFetch'
import { api } from '../services/api'
import {
  Card, KpiCard, PageWrap, SectionTitle, Spinner, ErrorMsg, Empty, Select,
} from '../components/ui'
import ConsumptionChart from '../components/ConsumptionChart'
import AnomalyTable from '../components/AnomalyTable'
import { fmtNum } from '../utils/format'

export default function Dashboard() {
  const [aptId, setAptId] = useState(1)    // default: apt 1 per T020
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const { data: meta, loading: metaLoading, error: metaErr } = useFetch(
    () => api.metadata(), []
  )
  const { data: summary, loading: summLoading } = useFetch(
    () => api.summary(), []
  )
  const { data: households, loading: hhLoading } = useFetch(
    () => api.households(), []
  )
  const { data: ts, loading: tsLoading, error: tsErr } = useFetch(
    () => api.timeseries(aptId, { dateFrom: dateFrom || undefined, dateTo: dateTo || undefined }),
    [aptId, dateFrom, dateTo]
  )
  const { data: anomaliesData, loading: anomLoading, error: anomErr } = useFetch(
    () => api.anomalies(aptId),
    [aptId]
  )

  const hhStats = households?.households?.find((h) => h.apt_id === aptId)

  if (metaLoading) return <PageWrap><Spinner text="Loading project data…" /></PageWrap>
  if (metaErr) return <PageWrap><ErrorMsg message={metaErr} /></PageWrap>

  return (
    <PageWrap>
      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-100 mb-1">Consumption Dashboard</h1>
        <p className="text-sm text-gray-400">
          Context-aware anomaly detection — Delhi residential dataset (
          {meta?.date_start?.slice(0, 10)} → {meta?.date_end?.slice(0, 10)})
        </p>
      </div>

      {/* Global KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <KpiCard
          label="Households"
          value={meta?.n_households ?? '—'}
          sub={`${(meta?.n_observations ?? 0).toLocaleString()} hourly obs.`}
        />
        <KpiCard
          label="Total Anomalies"
          value={(meta?.n_anomalies ?? 0).toLocaleString()}
          sub={`${meta?.anomaly_rate_pct ?? '—'}% of all readings`}
          accent="#f87171"
        />
        <KpiCard
          label="Model RMSE"
          value={fmtNum(meta?.model_test_rmse, 4)}
          sub={`R² = ${fmtNum(meta?.model_test_r2, 3)} · ${meta?.selected_model}`}
          accent="#4f8ef7"
        />
        <KpiCard
          label="Model MAE"
          value={fmtNum(meta?.model_test_mae, 4)}
          sub="log(kWh) units"
          accent="#4f8ef7"
        />
      </div>

      {/* Household selector + date filters */}
      <Card className="mb-6">
        <div className="flex flex-col sm:flex-row flex-wrap gap-4 items-start sm:items-end">
          <div className="w-full sm:w-auto">
            <label className="block text-xs text-gray-400 mb-1">Household</label>
            {hhLoading ? <div className="text-gray-500 text-sm">Loading…</div> : (
              <Select value={aptId} onChange={(e) => setAptId(Number(e.target.value))} className="w-full sm:w-auto">
                {households?.households?.map((h) => (
                  <option key={h.apt_id} value={h.apt_id}>
                    Apt {h.apt_id} — {h.n_observations.toLocaleString()} obs, {h.n_anomalies} anomalies
                  </option>
                ))}
              </Select>
            )}
          </div>
          <div className="w-full sm:w-auto">
            <label className="block text-xs text-gray-400 mb-1">From date</label>
            <input
              type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)}
              min="2013-08-01" max="2014-05-12"
              className="w-full sm:w-auto bg-[#22263a] border border-[#2e3347] rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-blue-500"
            />
          </div>
          <div className="w-full sm:w-auto">
            <label className="block text-xs text-gray-400 mb-1">To date</label>
            <input
              type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)}
              min="2013-08-01" max="2014-05-12"
              className="w-full sm:w-auto bg-[#22263a] border border-[#2e3347] rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-blue-500"
            />
          </div>
          {(dateFrom || dateTo) && (
            <button
              onClick={() => { setDateFrom(''); setDateTo('') }}
              className="px-3 py-2 text-xs text-gray-400 hover:text-gray-200 hover:bg-white/5 rounded-lg transition-colors"
            >
              Clear dates
            </button>
          )}
        </div>

        {/* Household quick stats */}
        {hhStats && (
          <div className="mt-4 flex flex-wrap gap-6 text-sm border-t border-[#2e3347] pt-4">
            <Stat label="Mean usage" value={`${fmtNum(hhStats.mean_kwh, 3)} kWh`} />
            <Stat label="Median usage" value={`${fmtNum(hhStats.median_kwh, 3)} kWh`} />
            <Stat label="Std dev" value={`${fmtNum(hhStats.std_kwh, 3)} kWh`} />
            <Stat label="Anomalies" value={`${hhStats.n_anomalies} (${hhStats.anomaly_rate_pct}%)`} accent="#f87171" />
            <Stat label="Period" value={`${hhStats.date_start?.slice(0, 10)} → ${hhStats.date_end?.slice(0, 10)}`} />
          </div>
        )}
      </Card>

      {/* Consumption chart */}
      <Card className="mb-6">
        <SectionTitle>Hourly Consumption — Apt {aptId}</SectionTitle>
        {tsLoading ? <Spinner text="Loading timeseries…" /> : tsErr ? <ErrorMsg message={tsErr} /> : (
          ts?.data?.length
            ? <ConsumptionChart data={ts.data} />
            : <Empty text="No data for this date range." />
        )}
        <p className="mt-2 text-xs text-gray-500">
          Blue line = actual consumption · Dashed area = Ridge regression baseline · Coloured dots = unusual readings
          (yellow = 1 method, orange = 2, red = 3+)
        </p>
      </Card>

      {/* Anomaly table */}
      <Card>
        <SectionTitle>Unusual Readings — Apt {aptId}</SectionTitle>
        {anomLoading ? <Spinner text="Loading anomalies…" /> : anomErr ? <ErrorMsg message={anomErr} /> : (
          <AnomalyTable anomalies={anomaliesData?.data ?? []} />
        )}
      </Card>

      {/* Method breakdown */}
      {summary && !summLoading && (
        <Card className="mt-6">
          <SectionTitle>Anomaly Method Breakdown (all households)</SectionTitle>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <MethodStat label="IQR Extreme" value={summary.by_method.iqr_extreme} color="#a78bfa" />
            <MethodStat label="Rolling Spike" value={summary.by_method.rolling_spike} color="#34d399" />
            <MethodStat label="Residual Z>3" value={summary.by_method.residual_z_gt3} color="#fb923c" />
            <MethodStat label="Global Z>3" value={summary.by_method.global_zscore_hi} color="#4f8ef7" />
          </div>
          <p className="mt-3 text-xs text-gray-500">
            A row is flagged as unusual if at least one method identifies it as statistically anomalous relative to that household's own historical baseline.
          </p>
        </Card>
      )}
    </PageWrap>
  )
}

function Stat({ label, value, accent }) {
  return (
    <div>
      <div className="text-xs text-gray-400">{label}</div>
      <div className="font-medium" style={{ color: accent || '#e8eaf0' }}>{value}</div>
    </div>
  )
}

function MethodStat({ label, value, color }) {
  return (
    <div className="p-3 rounded-lg bg-[#22263a]">
      <div className="text-xs text-gray-400 mb-1">{label}</div>
      <div className="text-lg font-bold" style={{ color }}>{(value ?? 0).toLocaleString()}</div>
    </div>
  )
}
