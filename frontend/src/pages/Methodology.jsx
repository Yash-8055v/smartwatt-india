import { useFetch } from '../hooks/useFetch'
import { api } from '../services/api'
import { PageWrap, Card, SectionTitle, KpiCard, Spinner, ErrorMsg } from '../components/ui'
import { fmtNum } from '../utils/format'

/**
 * Methodology page — explains the statistical/ML approach with
 * plain language, formulas, and dataset provenance.
 * No API calls needed for the static content; model metrics fetched live.
 */
export default function Methodology() {
  const { data: meta, loading, error } = useFetch(() => api.metadata(), [])

  return (
    <PageWrap>
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-100 mb-1">Methodology</h1>
        <p className="text-sm text-gray-400">
          How SmartWatt India detects statistically unusual electricity consumption.
        </p>
      </div>

      {/* Dataset */}
      <Card className="mb-6">
        <SectionTitle>Dataset</SectionTitle>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-4">
          <Info label="Source" value="IIIT-Delhi Residential Field Experiment" />
          <Info label="DOI" value="10.7910/DVN/7MEXN4 (Harvard Dataverse)" />
          <Info label="Location" value="New Delhi, India" />
          <Info label="Households" value="19 apartments" />
          <Info label="Resolution" value="Hourly" />
          <Info label="Period" value="Aug 2013 – May 2014 (~9.5 months)" />
        </div>
        <p className="text-xs text-gray-400 leading-relaxed">
          The dataset is from a randomised controlled field experiment. Households received either financial
          or health-framing electricity-conservation tips. The dataset records hourly electricity consumption
          in kWh (as the natural log <code className="text-blue-300">lnenergy</code>), outdoor temperature,
          and treatment indicators. Coverage averages ~80% of hourly slots due to measurement gaps.
        </p>
      </Card>

      {/* Core idea */}
      <Card className="mb-6">
        <SectionTitle>Core Idea: Household-Specific Baselines</SectionTitle>
        <div className="mb-3 p-4 rounded-lg bg-blue-900/20 border border-blue-800/40">
          <p className="text-sm text-blue-200 font-medium">
            "Don't ask whether consumption is high. Ask whether it is unusually high <em>for this household.</em>"
          </p>
        </div>
        <p className="text-xs text-gray-400 leading-relaxed mb-3">
          Household consumption varies enormously. The 19 apartments have mean usage ranging from 0.09 kWh to
          1.04 kWh per hour — a 12× range. Coefficient of Variation (CV) ranges from 79% to 208% within
          individual households. A fixed threshold of "2 kWh = anomaly" would miss low-use anomalies and
          over-flag high-use households.
        </p>
        <p className="text-xs text-gray-400 leading-relaxed">
          All four detection methods compute anomaly signals <strong className="text-gray-300">relative to each
          household's own historical distribution</strong>, not a global average.
        </p>
      </Card>

      {/* Methods */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <Card>
          <SectionTitle>Method 1 — Global Z-score (lnenergy)</SectionTitle>
          <Formula text="Z = (lnenergy − μ_apt) / σ_apt" />
          <p className="text-xs text-gray-400 leading-relaxed mt-3">
            The natural log of hourly kWh (<code className="text-blue-300">lnenergy</code>) is approximately
            log-normally distributed (skewness ≈ −0.22 on log scale). Z-scores are computed against the
            household's full-period mean and std. Readings with <code className="text-yellow-300">|Z| &gt; 3</code> are
            flagged — roughly 0.5% of observations.
          </p>
        </Card>

        <Card>
          <SectionTitle>Method 2 — IQR Fence (energy_kwh)</SectionTitle>
          <Formula text="Upper fence = Q75 + 3 × IQR" />
          <p className="text-xs text-gray-400 leading-relaxed mt-3">
            Tukey's outer fence on raw kWh (not log scale) per household. This is robust to extreme outliers
            and catches large spikes that may not be visible in log space. The 3×IQR "extreme" tier flags
            ~5% of observations and corresponds to genuinely large consumption events.
          </p>
        </Card>

        <Card>
          <SectionTitle>Method 3 — 7-Day Rolling Z-score</SectionTitle>
          <Formula text="Z_rolling = (kWh − μ_168h) / σ_168h" />
          <p className="text-xs text-gray-400 leading-relaxed mt-3">
            Rolling 168-observation window (7 days × 24 hours) per household. The current observation is
            <strong className="text-gray-300"> excluded from its own window</strong> (closed="left") to prevent
            self-leakage. Requires min. 48 prior observations before computing — the first 48 rows of each
            household have no rolling flag. This method adapts to seasonal shifts in usage.
          </p>
        </Card>

        <Card>
          <SectionTitle>Method 4 — Ridge Regression Residual</SectionTitle>
          <Formula text="residual = lnenergy − ŷ_ridge" />
          <p className="text-xs text-gray-400 leading-relaxed mt-3">
            A Ridge regression (α=100, chosen by 5-fold chronological cross-validation) predicts expected
            log-consumption from: time-of-day, day-of-week, month, outdoor temperature, household identity,
            treatment group, and cubic time trend. The residual captures what cannot be explained by context.
            The residual Z-score is standardised per-household using <em>training-period</em> residual
            statistics to avoid test leakage.
          </p>
        </Card>
      </div>

      {/* Why combined */}
      <Card className="mb-6">
        <SectionTitle>Why Multiple Signals?</SectionTitle>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Comparison
            title="Global Z-score"
            pro="Stable; uses full household history"
            con="Insensitive to recent pattern shifts"
          />
          <Comparison
            title="IQR Fence"
            pro="Robust to skewed distribution; easy to explain"
            con="Does not account for time-of-day or season"
          />
          <Comparison
            title="Rolling Z-score"
            pro="Adapts to recent behaviour; season-aware"
            con="Undefined for first 48 observations per household"
          />
          <Comparison
            title="Residual Z-score"
            pro="Accounts for hour, temperature, and season"
            con="Depends on model quality (R²=0.27 on test set)"
          />
        </div>
        <p className="mt-4 text-xs text-gray-400 leading-relaxed">
          A reading flagged by multiple independent methods is more likely to be genuinely unusual.
          The composite anomaly count (0–4) serves as a severity indicator, not a definitive classification.
        </p>
      </Card>

      {/* Model metrics live */}
      <Card className="mb-6">
        <SectionTitle>Ridge Model Performance</SectionTitle>
        {loading ? <Spinner text="Loading metrics…" /> : error ? <ErrorMsg message={error} /> : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard label="Test R²" value={fmtNum(meta?.model_test_r2, 3)} sub="Chronological 20% holdout" />
            <KpiCard label="Test RMSE" value={fmtNum(meta?.model_test_rmse, 4)} sub="log(kWh) units" />
            <KpiCard label="Test MAE" value={fmtNum(meta?.model_test_mae, 4)} sub="log(kWh) units" />
            <KpiCard label="Model" value={meta?.selected_model ?? '—'} sub={`α=100 (RidgeCV)`} />
          </div>
        )}
        <p className="mt-4 text-xs text-gray-400 leading-relaxed">
          R²=0.27 means the model explains 27% of variance in hourly log-consumption on the test set.
          This is <strong className="text-gray-300">expected and acceptable</strong>: hourly residential
          electricity is highly variable due to occupant behaviour, appliance heterogeneity, and measurement
          noise. The model's residuals are the signal — not the R² itself.
        </p>
      </Card>

      {/* Limitations */}
      <Card>
        <SectionTitle>Limitations &amp; Caveats</SectionTitle>
        <ul className="space-y-2 text-xs text-gray-400">
          <li className="flex gap-2">
            <span className="text-yellow-400 shrink-0">⚠</span>
            <span><strong className="text-gray-300">Not a causal diagnosis.</strong> An unusual reading does not mean theft, appliance failure, or any specific cause. It means the consumption was statistically unexpected for that household at that time.</span>
          </li>
          <li className="flex gap-2">
            <span className="text-yellow-400 shrink-0">⚠</span>
            <span><strong className="text-gray-300">Temporal gaps.</strong> Average hourly coverage is ~80%. Rolling windows span more calendar time when gaps exist. First 48 observations of each household have no rolling statistics.</span>
          </li>
          <li className="flex gap-2">
            <span className="text-yellow-400 shrink-0">⚠</span>
            <span><strong className="text-gray-300">Small dataset.</strong> 19 households in one city over 9.5 months. Results may not generalise to other Indian cities or climates.</span>
          </li>
          <li className="flex gap-2">
            <span className="text-yellow-400 shrink-0">⚠</span>
            <span><strong className="text-gray-300">No ground truth.</strong> There are no verified "true" anomaly labels. The detection is based on statistical deviation from modelled baselines.</span>
          </li>
          <li className="flex gap-2">
            <span className="text-yellow-400 shrink-0">⚠</span>
            <span><strong className="text-gray-300">No real-time operation.</strong> This is a batch retrospective analysis on a fixed historical dataset, not a live monitoring system.</span>
          </li>
        </ul>
        <div className="mt-4 pt-4 border-t border-[#2e3347] text-xs text-gray-500">
          Dataset: Sudarshan, A. et al. (2017). "Nudging Electricity Consumers". IIIT-Delhi.{' '}
          <a
            href="https://doi.org/10.7910/DVN/7MEXN4"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:underline"
          >
            doi:10.7910/DVN/7MEXN4
          </a>
        </div>
      </Card>
    </PageWrap>
  )
}

function Formula({ text }) {
  return (
    <div className="mt-2 px-4 py-2 rounded bg-[#22263a] font-mono text-blue-300 text-sm">
      {text}
    </div>
  )
}

function Info({ label, value }) {
  return (
    <div>
      <div className="text-xs text-gray-500">{label}</div>
      <div className="text-sm text-gray-200">{value}</div>
    </div>
  )
}

function Comparison({ title, pro, con }) {
  return (
    <div className="p-3 rounded-lg bg-[#22263a] border border-[#2e3347]">
      <div className="text-xs font-semibold text-gray-200 mb-2">{title}</div>
      <div className="flex gap-1 mb-1">
        <span className="text-green-400 shrink-0 text-xs">✓</span>
        <span className="text-xs text-gray-400">{pro}</span>
      </div>
      <div className="flex gap-1">
        <span className="text-yellow-400 shrink-0 text-xs">−</span>
        <span className="text-xs text-gray-400">{con}</span>
      </div>
    </div>
  )
}
