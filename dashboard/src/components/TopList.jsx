import React from 'react'

export function TopList({ title, items, itemKey, countKey = 'count' }) {
  const max = Math.max(1, ...items.map((i) => i[countKey]))

  return (
    <div className="glass rounded-xl border border-white/10 p-4 sm:p-5">
      <h3 className="mono mb-3 text-xs tracking-[0.16em] text-muted">{title}</h3>
      {items.length === 0 ? (
        <p className="mono text-[11px] text-muted/70">NO_DATA_YET</p>
      ) : (
        <ul className="space-y-2">
          {items.map((item) => (
            <li key={item[itemKey]}>
              <div className="mb-1 flex items-center justify-between">
                <span className="mono text-xs text-ink">{item[itemKey]}</span>
                <span className="mono text-xs text-purple">{item[countKey]}</span>
              </div>
              <div className="h-1 w-full overflow-hidden rounded-full bg-white/[0.06]">
                <div
                  className="h-full rounded-full bg-purple"
                  style={{ width: `${(item[countKey] / max) * 100}%` }}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default TopList
