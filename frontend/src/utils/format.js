/** Shared UI utilities */

/** Severity level from anomaly_method_count */
export function severity(count) {
  if (count >= 3) return 'critical'
  if (count === 2) return 'high'
  if (count === 1) return 'medium'
  return 'normal'
}

export const SEVERITY_COLOR = {
  critical: '#f87171',
  high: '#fb923c',
  medium: '#fbbf24',
  normal: '#34d399',
}

export const SEVERITY_BG = {
  critical: 'bg-red-900/30 text-red-400 border border-red-800',
  high: 'bg-orange-900/30 text-orange-400 border border-orange-800',
  medium: 'bg-yellow-900/30 text-yellow-400 border border-yellow-800',
  normal: 'bg-green-900/30 text-green-400 border border-green-800',
}

/** Format ISO timestamp to "Aug 12, 2013 14:00" */
export function fmtTs(ts) {
  if (!ts) return '—'
  return new Date(ts).toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit', hour12: false,
  })
}

/** Format to 3 decimal places, fallback dash */
export function fmtNum(v, decimals = 3) {
  if (v == null || isNaN(v)) return '—'
  return Number(v).toFixed(decimals)
}

/** Which method flags were active on an anomaly row */
export function methodLabels(row) {
  const labels = []
  if (row.flag_zscore_hi) labels.push('Z-score')
  if (row.flag_iqr_extreme) labels.push('IQR')
  if (row.flag_rolling_spike) labels.push('Rolling')
  if (row.residual_z_flagged) labels.push('Residual')
  return labels
}
