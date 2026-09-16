import React, { useCallback, useEffect, useState } from 'react'
import api from '../lib/api.js'
import StatCards from '../components/StatCards.jsx'
import RegionMap from '../components/RegionMap.jsx'
import TopList from '../components/TopList.jsx'
import IOCTable from '../components/IOCTable.jsx'

const PAGE_SIZE = 15
const REFRESH_MS = 30_000

export function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [region, setRegion] = useState([])
  const [sources, setSources] = useState([])
  const [families, setFamilies] = useState([])
  const [iocs, setIocs] = useState({ results: [], total: 0 })
  const [filters, setFilters] = useState({ type: '', q: '' })
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [collecting, setCollecting] = useState(false)
  const [error, setError] = useState(null)
  const [lastUpdated, setLastUpdated] = useState(null)

  const loadAll = useCallback(async () => {
    try {
      const [summaryRes, regionRes, sourcesRes, familiesRes, iocsRes] = await Promise.all([
        api.summary(),
        api.byRegion(),
        api.topSources(),
        api.topMalwareFamilies(),
        api.iocs({ type: filters.type, q: filters.q, page, page_size: PAGE_SIZE }),
      ])
      setSummary(summaryRes)
      setRegion(regionRes)
      setSources(sourcesRes)
      setFamilies(familiesRes)
      setIocs(iocsRes)
      setLastUpdated(new Date())
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [filters, page])

  useEffect(() => {
    loadAll()
    const interval = setInterval(loadAll, REFRESH_MS)
    return () => clearInterval(interval)
  }, [loadAll])

  const handleRunNow = async () => {
    setCollecting(true)
    try {
      await api.triggerCollection()
      await loadAll()
    } catch (err) {
      setError(err.message)
    } finally {
      setCollecting(false)
    }
  }

  return (
    <div className="grid-lines min-h-screen bg-bg">
      <header className="sticky top-0 z-10 border-b border-white/10 bg-bg/85 backdrop-blur-xl">
        <div className="mx-auto flex max-w-[1200px] items-center justify-between px-5 py-4">
          <div>
            <p className="mono text-sm font-bold tracking-[0.14em] text-ink">
              <span className="text-cyan">&lt;</span> THREAT_INTEL_PLATFORM <span className="text-cyan">/&gt;</span>
            </p>
            <p className="mono mt-0.5 text-[10px] tracking-[0.12em] text-muted">
              {lastUpdated ? `LAST_UPDATED: ${lastUpdated.toLocaleTimeString()}` : 'LOADING...'}
            </p>
          </div>
          <button
            type="button"
            onClick={handleRunNow}
            disabled={collecting}
            className="mono rounded-md border border-cyan/50 bg-cyan/10 px-4 py-2 text-xs font-semibold tracking-[0.12em] text-cyan transition-colors hover:bg-cyan/20 disabled:opacity-50"
          >
            {collecting ? 'COLLECTING...' : 'RUN_COLLECTION_NOW'}
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-[1200px] space-y-6 px-5 py-8">
        {error && (
          <div className="mono rounded-lg border border-pink/40 bg-pink/[0.06] px-4 py-3 text-xs text-pink">
            ERROR: {error} — is the backend reachable at /api?
          </div>
        )}

        <StatCards summary={summary} />

        <RegionMap data={region} />

        <div className="grid gap-6 sm:grid-cols-2">
          <TopList title="TOP_SOURCES" items={sources} itemKey="source" />
          <TopList title="TOP_MALWARE_FAMILIES" items={families} itemKey="family" />
        </div>

        <IOCTable
          results={iocs.results}
          total={iocs.total}
          page={page}
          pageSize={PAGE_SIZE}
          filters={filters}
          loading={loading}
          onFiltersChange={(f) => {
            setFilters(f)
            setPage(1)
          }}
          onPageChange={setPage}
        />
      </main>
    </div>
  )
}

export default Dashboard
