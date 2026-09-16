import React, { useMemo } from 'react'
import { centroidFor } from '../lib/countryCentroids.js'

/**
 * RegionMap — region-wise threat visualization. Plots one glowing bubble
 * per country at its real lat/lon on an equirectangular grid, sized by
 * threat count (sqrt scale, so area — not radius — is proportional to
 * count, which is the perceptually correct way to encode magnitude).
 *
 * This deliberately does NOT attempt to draw actual coastlines — getting
 * that accurate would mean depending on a topojson world atlas and an
 * ISO alpha-2 -> numeric-ID mapping table neither of which this project
 * wants to risk getting subtly wrong. Real lat/lon positioning on a
 * labeled grid conveys "where" just as clearly, honestly.
 */
const VIEW_W = 960
const VIEW_H = 480

function project(lat, lon) {
  const x = ((lon + 180) / 360) * VIEW_W
  const y = ((90 - lat) / 180) * VIEW_H
  return [x, y]
}

export function RegionMap({ data = [] }) {
  const points = useMemo(() => {
    const withCoords = data
      .map((d) => {
        const c = centroidFor(d.country_code)
        return c ? { ...d, ...c } : null
      })
      .filter(Boolean)

    const maxCount = Math.max(1, ...withCoords.map((d) => d.count))
    return withCoords.map((d) => ({
      ...d,
      radius: 3 + Math.sqrt(d.count / maxCount) * 16,
    }))
  }, [data])

  const ranked = useMemo(() => [...data].sort((a, b) => b.count - a.count).slice(0, 8), [data])

  return (
    <div className="glass rounded-xl border border-white/10 p-4 sm:p-5">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="mono text-xs tracking-[0.16em] text-muted">REGION-WISE THREATS</h3>
        <span className="mono text-[10px] tracking-[0.12em] text-muted/70">
          {data.length} {data.length === 1 ? 'REGION' : 'REGIONS'}
        </span>
      </div>

      <div className="overflow-hidden rounded-lg border border-white/10 bg-[#06070d]">
        <svg viewBox={`0 0 ${VIEW_W} ${VIEW_H}`} className="w-full" role="img" aria-label="World map of threat counts by country">
          <rect width={VIEW_W} height={VIEW_H} fill="#06070d" />
          {/* graticule */}
          {Array.from({ length: 13 }, (_, i) => (
            <line key={`v${i}`} x1={(i * VIEW_W) / 12} y1="0" x2={(i * VIEW_W) / 12} y2={VIEW_H} stroke="rgba(255,255,255,0.05)" />
          ))}
          {Array.from({ length: 7 }, (_, i) => (
            <line key={`h${i}`} x1="0" y1={(i * VIEW_H) / 6} x2={VIEW_W} y2={(i * VIEW_H) / 6} stroke="rgba(255,255,255,0.05)" />
          ))}
          <line x1="0" y1={VIEW_H / 2} x2={VIEW_W} y2={VIEW_H / 2} stroke="rgba(0,245,255,0.12)" strokeDasharray="4 4" />

          {points.map((p) => {
            const [x, y] = project(p.lat, p.lon)
            return (
              <g key={p.country_code}>
                <circle cx={x} cy={y} r={p.radius} fill="rgba(255,43,214,0.14)" />
                <circle cx={x} cy={y} r={Math.max(2, p.radius * 0.45)} fill="#FF2BD6" fillOpacity="0.85" />
                <title>
                  {p.name} ({p.country_code}) — {p.count} indicator{p.count === 1 ? '' : 's'}
                </title>
              </g>
            )
          })}
        </svg>
      </div>

      <ul className="mt-4 grid grid-cols-2 gap-x-4 gap-y-1.5 sm:grid-cols-4">
        {ranked.map((r) => {
          const c = centroidFor(r.country_code)
          return (
            <li key={r.country_code} className="mono flex items-center justify-between text-[11px]">
              <span className="text-muted">{c?.name || r.country_code}</span>
              <span className="text-pink">{r.count}</span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

export default RegionMap
