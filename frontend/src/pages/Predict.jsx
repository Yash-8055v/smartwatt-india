import { useState } from 'react'
import { api } from '../services/api'
import { PageWrap, Card, SectionTitle } from '../components/ui'

// ── Constants ─────────────────────────────────────────────────────────────────
const HOUSEHOLDS = Array.from({ length: 19 }, (_, i) => i + 1)

const HOURS = Array.from({ length: 24 }, (_, i) => ({
  value: i,
  label: `${String(i).padStart(2, '0')}:00`,
}))

const DAYS = [
  { value: 1, label: 'Monday' },
  { value: 2, label: 'Tuesday' },
  { value: 3, label: 'Wednesday' },
  { value: 4, label: 'Thursday' },
  { value: 5, label: 'Friday' },
  { value: 6, label: 'Saturday' },
  { value: 7, label: 'Sunday' },
]

const MONTHS = [
  { value: 1, label: 'January' }, { value: 2, label: 'February' },
  { value: 3, label: 'March' }, { value: 4, label: 'April' },
  { value: 5, label: 'May' }, { value: 6, label: 'June' },
  { value: 7, label: 'July' }, { value: 8, label: 'August' },
  { value: 9, label: 'September' }, { value: 10, label: 'October' },
  { value: 11, label: 'November' }, { value: 12, label: 'December' },
]

// ── Field component ───────────────────────────────────────────────────────────
function Field({ label, hint, error, children }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-400 uppercase tracking-wide mb-1.5">
        {label}
        {hint && <span className="ml-1.5 text-gray-600 normal-case font-normal">{hint}</span>}
      </label>
      {children}
      {error && <p className="mt-1 text-xs text-red-400">{error}</p>}
    </div>
  )
}

// ── Select control (styled) ───────────────────────────────────────────────────
function StyledSelect({ id, value, onChange, children }) {
  return (
    <select
      id={id}
      value={value}
      onChange={onChange}
      className="w-full bg-[#22263a] border border-[#2e3347] rounded-lg px-3 py-2.5 text-sm text-gray-200
                 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 transition-colors"
    >
      {children}
    </select>
  )
}

// ── Number input ──────────────────────────────────────────────────────────────
function StyledInput({ id, value, onChange, min, max, step = '0.1', placeholder }) {
  return (
    <input
      id={id}
      type="number"
      value={value}
      onChange={onChange}
      min={min}
      max={max}
      step={step}
      placeholder={placeholder}
      className="w-full bg-[#22263a] border border-[#2e3347] rounded-lg px-3 py-2.5 text-sm text-gray-200
                 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/30 transition-colors
                 placeholder-gray-600"
    />
  )
}

// ── Prediction result display ─────────────────────────────────────────────────
function PredictionResult({ result, inputs }) {
  const dayName = DAYS.find(d => d.value === inputs.dayofweek)?.label ?? ''
  const monthName = MONTHS.find(m => m.value === inputs.month)?.label ?? ''
  const hourLabel = HOURS.find(h => h.value === inputs.hour)?.label ?? ''

  // Consumption level indicator
  const kwh = result.predicted_kwh
  let level = 'Normal'
  let levelColor = 'text-green-400'
  let barWidth = '40%'
  if (kwh > 1.5) { level = 'High'; levelColor = 'text-orange-400'; barWidth = '80%' }
  else if (kwh > 0.8) { level = 'Moderate'; levelColor = 'text-yellow-400'; barWidth = '55%' }
  else if (kwh < 0.15) { level = 'Very Low'; levelColor = 'text-blue-400'; barWidth = '15%' }

  return (
    <Card className="border-blue-800/40 bg-blue-950/10">
      {/* Main prediction value */}
      <div className="text-center pb-6 border-b border-[#2e3347] mb-6">
        <div className="text-xs text-gray-500 uppercase tracking-wide mb-2">Predicted Hourly Consumption</div>
        <div className="text-5xl font-bold text-blue-300 mb-1">
          {result.predicted_kwh.toFixed(3)}
        </div>
        <div className="text-lg text-gray-400">kWh / hour</div>
        <div className={`mt-2 text-sm font-medium ${levelColor}`}>{level} consumption</div>
      </div>

      {/* Consumption bar */}
      <div className="mb-6">
        <div className="flex justify-between text-xs text-gray-600 mb-1.5">
          <span>0 kWh</span>
          <span>1 kWh</span>
          <span>2+ kWh</span>
        </div>
        <div className="h-2 bg-[#22263a] rounded-full overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-blue-600 to-blue-400 transition-all duration-700"
            style={{ width: barWidth }}
          />
        </div>
      </div>

      {/* Scenario summary */}
      <div className="bg-[#13161f] rounded-lg p-4 mb-5 text-sm text-gray-400 leading-relaxed">
        Expected consumption for <span className="text-gray-200 font-medium">Apt {inputs.apt}</span>{' '}
        at <span className="text-gray-200 font-medium">{hourLabel}</span> on a{' '}
        <span className="text-gray-200 font-medium">{dayName}</span> in{' '}
        <span className="text-gray-200 font-medium">{monthName}</span> at{' '}
        <span className="text-gray-200 font-medium">{inputs.temp_c}°C</span>.
      </div>

      {/* Technical detail */}
      <div className="grid grid-cols-2 gap-3 mb-5">
        <div className="bg-[#13161f] rounded-lg p-3">
          <div className="text-xs text-gray-600 mb-0.5">ln(kWh)</div>
          <div className="text-sm font-mono text-gray-400">{result.predicted_lnenergy.toFixed(4)}</div>
        </div>
        <div className="bg-[#13161f] rounded-lg p-3">
          <div className="text-xs text-gray-600 mb-0.5">Model</div>
          <div className="text-sm font-mono text-gray-400">Ridge {result.model_version}</div>
        </div>
      </div>

      {/* Disclaimer */}
      <p className="text-xs text-gray-600 leading-relaxed">
        ⚠️ {result.note}
      </p>
    </Card>
  )
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function Predict() {
  const [form, setForm] = useState({
    apt: 1,
    hour: 18,
    dayofweek: 3,
    month: 10,
    temp_c: 25,
  })
  const [tempInput, setTempInput] = useState('25')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [validationErrors, setValidationErrors] = useState({})

  function setField(key, val) {
    setForm(prev => ({ ...prev, [key]: val }))
    setResult(null)
    setError(null)
    setValidationErrors(prev => ({ ...prev, [key]: undefined }))
  }

  function validateTemp(raw) {
    const v = parseFloat(raw)
    if (isNaN(v)) return 'Enter a number.'
    if (v < 5) return 'Minimum 5°C.'
    if (v > 45) return 'Maximum 45°C.'
    return null
  }

  function handleTempChange(e) {
    const raw = e.target.value
    setTempInput(raw)
    const err = validateTemp(raw)
    if (!err) setField('temp_c', parseFloat(raw))
    else setValidationErrors(prev => ({ ...prev, temp_c: err }))
  }

  async function handleSubmit(e) {
    e.preventDefault()

    const tempErr = validateTemp(tempInput)
    if (tempErr) {
      setValidationErrors({ temp_c: tempErr })
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const data = await api.predict({
        apt: Number(form.apt),
        hour: Number(form.hour),
        dayofweek: Number(form.dayofweek),
        month: Number(form.month),
        temp_c: Number(form.temp_c),
      })
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function handleReset() {
    setForm({ apt: 1, hour: 18, dayofweek: 3, month: 10, temp_c: 25 })
    setTempInput('25')
    setResult(null)
    setError(null)
    setValidationErrors({})
  }

  const hasError = Object.values(validationErrors).some(Boolean)

  return (
    <PageWrap>
      {/* Page header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-100 mb-1">Prediction Scenarios</h1>
        <p className="text-gray-500 text-sm max-w-2xl">
          Enter a contextual scenario to get expected hourly electricity consumption from the
          trained Ridge regression model. Adjust household, time of day, and weather to explore
          how context drives expected usage.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Form panel */}
        <div>
          <Card>
            <SectionTitle>Scenario Inputs</SectionTitle>
            <form onSubmit={handleSubmit} noValidate>
              <div className="space-y-5">

                <Field label="Household" hint="(Apt 1–19)">
                  <StyledSelect
                    id="apt"
                    value={form.apt}
                    onChange={e => setField('apt', Number(e.target.value))}
                  >
                    {HOUSEHOLDS.map(id => (
                      <option key={id} value={id}>Apartment {id}</option>
                    ))}
                  </StyledSelect>
                </Field>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Field label="Hour of Day">
                    <StyledSelect
                      id="hour"
                      value={form.hour}
                      onChange={e => setField('hour', Number(e.target.value))}
                    >
                      {HOURS.map(h => (
                        <option key={h.value} value={h.value}>{h.label}</option>
                      ))}
                    </StyledSelect>
                  </Field>

                  <Field label="Day of Week" hint="(ISO 1=Mon)">
                    <StyledSelect
                      id="dayofweek"
                      value={form.dayofweek}
                      onChange={e => setField('dayofweek', Number(e.target.value))}
                    >
                      {DAYS.map(d => (
                        <option key={d.value} value={d.value}>{d.label}</option>
                      ))}
                    </StyledSelect>
                  </Field>
                </div>

                <Field label="Month">
                  <StyledSelect
                    id="month"
                    value={form.month}
                    onChange={e => setField('month', Number(e.target.value))}
                  >
                    {MONTHS.map(m => (
                      <option key={m.value} value={m.value}>{m.label}</option>
                    ))}
                  </StyledSelect>
                </Field>

                <Field
                  label="Temperature"
                  hint="(5–45°C)"
                  error={validationErrors.temp_c}
                >
                  <StyledInput
                    id="temp_c"
                    value={tempInput}
                    onChange={handleTempChange}
                    min="5"
                    max="45"
                    step="0.5"
                    placeholder="e.g. 25"
                  />
                </Field>

                <div className="flex gap-3 pt-2">
                  <button
                    type="submit"
                    disabled={loading || hasError}
                    className="flex-1 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40
                               disabled:cursor-not-allowed text-white text-sm font-medium transition-colors"
                  >
                    {loading ? (
                      <span className="flex items-center justify-center gap-2">
                        <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        Computing…
                      </span>
                    ) : 'Run Scenario'}
                  </button>
                  <button
                    type="button"
                    onClick={handleReset}
                    className="px-4 py-2.5 rounded-lg border border-[#2e3347] text-gray-400
                               hover:text-gray-200 hover:border-[#404669] text-sm transition-colors"
                  >
                    Reset
                  </button>
                </div>
              </div>
            </form>
          </Card>

          {/* Model info card */}
          <Card className="mt-4">
            <div className="text-xs text-gray-500 space-y-2 leading-relaxed">
              <p className="text-gray-400 font-medium text-sm mb-3">About this model</p>
              <p>
                Predictions come from a <strong className="text-gray-300">Ridge Regression (α=100)</strong>{' '}
                model trained on 103,704 hourly observations from 19 Delhi households
                (Aug 2013–May 2014).
              </p>
              <p>
                Inputs used: household identity, hour, day of week, month, and temperature.
                Time-trend variables are held at their dataset median.
              </p>
              <p>
                <strong className="text-gray-300">Test R² = 0.266, RMSE = 0.995</strong>.
                Predictions explain 27% of variance — useful for comparing scenarios
                but not for precise point forecasts.
              </p>
              <p className="text-gray-600">
                This model does NOT imply electricity theft, appliance-level consumption,
                or causal effects.
              </p>
            </div>
          </Card>
        </div>

        {/* Result panel */}
        <div>
          {!result && !loading && !error && (
            <div className="flex flex-col items-center justify-center h-full min-h-[320px]
                            border border-dashed border-[#2e3347] rounded-xl text-gray-600 text-sm text-center px-8">
              <div className="text-4xl mb-4">⚡</div>
              <div className="font-medium text-gray-500 mb-1">No scenario run yet</div>
              <div>Fill in the inputs and click <span className="text-gray-400">Run Scenario</span> to see the prediction.</div>
            </div>
          )}

          {loading && (
            <div className="flex flex-col items-center justify-center h-full min-h-[320px]
                            border border-[#2e3347] rounded-xl text-gray-500 text-sm">
              <div className="w-10 h-10 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mb-4" />
              <div>Computing prediction…</div>
            </div>
          )}

          {error && !loading && (
            <div className="rounded-xl border border-red-800 bg-red-950/30 p-6">
              <div className="text-red-400 font-medium mb-1">Prediction failed</div>
              <div className="text-red-500/70 text-sm">{error}</div>
            </div>
          )}

          {result && !loading && (
            <PredictionResult result={result} inputs={form} />
          )}
        </div>
      </div>
    </PageWrap>
  )
}
