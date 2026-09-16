import React from 'react'

const TYPE_OPTIONS = [
  { value: '', label: 'ALL_TYPES' },
  { value: 'ip', label: 'IP' },
  { value: 'url', label: 'URL' },
  { value: 'domain', label: 'DOMAIN' },
  { value: 'hash_md5', label: 'MD5' },
  { value: 'hash_sha1', label: 'SHA1' },
  { value: 'hash_sha256', label: 'SHA256' },
]

export function IOCTable({ results, total, page, pageSize, filters, onFiltersChange, onPageChange, loading }) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize))

  return (
    <div className="glass rounded-xl border border-white/10 p-4 sm:p-5">
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h3 className="mono text-xs tracking-[0.16em] text-muted">INDICATORS ({total})</h3>
        <div className="flex flex-wrap gap-2">
          <input
            type="search"
            value={filters.q}
            onChange={(e) => onFiltersChange({ ...filters, q: e.target.value })}
            placeholder="search indicator..."
            className="mono w-48 rounded border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-ink placeholder:text-muted/50 focus:border-cyan/50 focus:outline-none"
          />
          <select
            value={filters.type}
            onChange={(e) => onFiltersChange({ ...filters, type: e.target.value })}
            className="mono rounded border border-white/10 bg-white/[0.03] px-2 py-1.5 text-xs text-ink focus:border-cyan/50 focus:outline-none"
          >
            {TYPE_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead>
            <tr className="mono border-b border-white/10 text-[10px] tracking-[0.12em] text-muted">
              <th className="pb-2 pr-3">INDICATOR</th>
              <th className="pb-2 pr-3">TYPE</th>
              <th className="pb-2 pr-3">CONFIDENCE</th>
              <th className="pb-2 pr-3">SEVERITY</th>
              <th className="pb-2 pr-3">SOURCES</th>
              <th className="pb-2">FAMILY</th>
            </tr>
          </thead>
          <tbody>
            {results.map((ioc) => (
              <tr key={ioc.id} className="border-b border-white/5 last:border-0">
                <td className="mono max-w-[280px] truncate py-2 pr-3 text-ink" title={ioc.indicator}>
                  {ioc.indicator}
                </td>
                <td className="mono py-2 pr-3 text-cyan">{ioc.type}</td>
                <td className="mono py-2 pr-3 text-muted">{ioc.confidence ?? '—'}</td>
                <td className="mono py-2 pr-3 text-muted">{ioc.severity ?? '—'}</td>
                <td className="mono py-2 pr-3 text-muted">{(ioc.sources || []).join(', ')}</td>
                <td className="mono py-2 text-muted">{ioc.malware_family || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {!loading && results.length === 0 && (
          <p className="mono py-8 text-center text-xs tracking-[0.14em] text-muted">
            NO_INDICATORS_YET — waiting on the first collection run
          </p>
        )}
      </div>

      <div className="mt-4 flex items-center justify-between">
        <button
          type="button"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
          className="mono rounded border border-white/10 px-3 py-1.5 text-[11px] text-muted disabled:opacity-40"
        >
          PREV
        </button>
        <span className="mono text-[11px] text-muted">
          {page} / {totalPages}
        </span>
        <button
          type="button"
          disabled={page >= totalPages}
          onClick={() => onPageChange(page + 1)}
          className="mono rounded border border-white/10 px-3 py-1.5 text-[11px] text-muted disabled:opacity-40"
        >
          NEXT
        </button>
      </div>
    </div>
  )
}

export default IOCTable
