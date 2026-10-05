import {
  ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceDot, Legend,
} from 'recharts'
import { fmtTs, fmtNum, SEVERITY_COLOR } from '../utils/format'

/**
 * Consumption timeseries chart showing actual vs predicted energy.
 * Anomaly points are rendered as red reference dots.
 *
 * Props:
 *   data: array of TimeseriesPoint from API
 *   maxPoints: max data points to render (default 500 for performance)
 */
export default function ConsumptionChart({ data = [], maxPoints = 500 }) {
  // Thin the data for performance if too many points
  const step = Math.max(1, Math.floor(data.length / maxPoints))
  const thinned = data.filter((_, i) => i % step === 0)

  const chartData = thinned.map((d) => ({
    ts: d.timestamp,
    actual: +(d.energy_kwh?.toFixed(4) ?? 0),
    expected: d.energy_kwh_predicted != null ? +(d.energy_kwh_predicted.toFixed(4)) : null,
    anomaly: d.is_anomaly ? d.energy_kwh : null,
    methods: d.anomaly_method_count,
  }))

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null
    const d = payload[0]?.payload
    return (
      <div className="bg-[#1a1d27] border border-[#2e3347] rounded-lg p-3 text-xs shadow-lg min-w-[200px]">
        <div className="text-gray-400 mb-2">{fmtTs(label)}</div>
        <div className="text-blue-300">Actual: {fmtNum(d.actual, 4)} kWh</div>
        {d.expected != null && (
          <div className="text-green-400">Expected: {fmtNum(d.expected, 4)} kWh</div>
        )}
        {d.anomaly != null && (
          <div className="text-red-400 font-medium mt-1">
            ⚠ Unusual ({d.methods} method{d.methods > 1 ? 's' : ''})
          </div>
        )}
      </div>
    )
  }

  const anomalyPoints = chartData.filter((d) => d.anomaly != null)

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ComposedChart data={chartData} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2e3347" />
        <XAxis
          dataKey="ts"
          tick={{ fill: '#7c8299', fontSize: 11 }}
          tickFormatter={(v) => new Date(v).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}
          interval="preserveStartEnd"
        />
        <YAxis tick={{ fill: '#7c8299', fontSize: 11 }} tickFormatter={(v) => `${v}kW`} width={48} />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          wrapperStyle={{ fontSize: 12, color: '#7c8299' }}
          formatter={(v) => v === 'actual' ? 'Actual (kWh)' : 'Expected baseline'}
        />
        {/* Expected baseline area */}
        <Area
          dataKey="expected"
          type="monotone"
          fill="#1e3a6e"
          stroke="#4f8ef7"
          strokeWidth={1.5}
          strokeDasharray="4 2"
          dot={false}
          activeDot={false}
          name="expected"
        />
        {/* Actual consumption */}
        <Line
          dataKey="actual"
          type="monotone"
          stroke="#4f8ef7"
          strokeWidth={1.5}
          dot={false}
          activeDot={{ r: 3 }}
          name="actual"
        />
        {/* Anomaly markers */}
        {anomalyPoints.map((d, i) => (
          <ReferenceDot
            key={i}
            x={d.ts}
            y={d.actual}
            r={3}
            fill={d.methods >= 3 ? '#f87171' : d.methods === 2 ? '#fb923c' : '#fbbf24'}
            stroke="none"
          />
        ))}
      </ComposedChart>
    </ResponsiveContainer>
  )
}
