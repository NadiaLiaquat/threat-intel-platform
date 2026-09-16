import React from 'react'

const TYPE_LABELS = {
  ip: 'IP',
  url: 'URL',
  domain: 'DOMAIN',
  hash_md5: 'MD5',
  hash_sha1: 'SHA1',
  hash_sha256: 'SHA256',
}

// Tailwind's JIT scanner needs complete literal class strings — dynamic
// `text-${accent}` interpolation wouldn't be picked up at build time.
const ACCENT_TEXT = { cyan: 'text-cyan', purple: 'text-purple', pink: 'text-pink' }

export function StatCards({ summary }) {
  if (!summary) return null

  const cards = [
    { label: 'TOTAL_IOCS', value: summary.total_indicators, accent: 'cyan' },
    { label: 'AVG_CONFIDENCE', value: `${summary.avg_confidence}%`, accent: 'purple' },
    { label: 'AVG_SEVERITY', value: `${summary.avg_severity}%`, accent: 'pink' },
  ]

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      {cards.map((c) => (
        <div key={c.label} className="glass rounded-xl border border-white/10 p-4">
          <p className="mono text-[10px] tracking-[0.18em] text-muted">{c.label}</p>
          <p className={`mono mt-2 text-2xl font-bold ${ACCENT_TEXT[c.accent]}`}>{c.value}</p>
        </div>
      ))}

      <div className="glass rounded-xl border border-white/10 p-4 sm:col-span-3">
        <p className="mono mb-3 text-[10px] tracking-[0.18em] text-muted">BY_TYPE</p>
        <div className="flex flex-wrap gap-2">
          {Object.entries(summary.by_type || {}).map(([type, count]) => (
            <span
              key={type}
              className="mono rounded border border-cyan/25 bg-cyan/[0.06] px-2.5 py-1 text-[11px] text-cyan"
            >
              {TYPE_LABELS[type] || type}: {count}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}

export default StatCards
