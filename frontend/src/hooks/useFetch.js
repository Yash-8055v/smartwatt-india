import { useState, useEffect } from 'react'

/**
 * Generic data-fetching hook.
 * Usage: const { data, loading, error } = useFetch(fetchFn, deps)
 * fetchFn: async function that returns data
 * deps: dependency array (re-fetches when changed)
 */
export function useFetch(fetchFn, deps = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    fetchFn()
      .then((d) => { if (!cancelled) { setData(d); setLoading(false) } })
      .catch((e) => { if (!cancelled) { setError(e.message || String(e)); setLoading(false) } })
    return () => { cancelled = true }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { data, loading, error }
}
