import { motion } from 'framer-motion'
import { Database, Zap } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine, CartesianGrid } from 'recharts'
import { metrics } from '@/data/metrics'

const p95Cards = [
  { load: 'Idle', p95: '~2 ms', note: 'no users, nothing in flight', color: 'blue' },
  { load: 'Steady', p95: '~2–5 ms', note: 'normal traffic, healthy DB', color: 'green' },
  { load: 'Spike (contention)', p95: 'up to 23,200 ms', note: 'SQLite write lock serialization', color: 'red' },
]

const endpoints = ['GET /', 'GET /api/query?type=count', 'GET /api/query?type=stats', 'POST /api/write']

const colorBadge: Record<string, string> = {
  blue: 'bg-blue-100 text-blue-700',
  green: 'bg-green-100 text-green-700',
  red: 'bg-red-100 text-red-700',
}

// Synthesised illustration of the 285-row features_v2.csv p95 column.
// The exact values are recorded in `data/features_v2.csv` and verified by
// the audit script. We pick a deterministic synthetic curve here so the
// chart line never breaks CI when data/features_v2.csv is regenerated.
const p95Synthetic = Array.from({ length: 60 }, (_, i) => {
  const spikeStart = 30
  const spikePeak = 50
  if (i < spikeStart) return { idx: i, p95: 2 + Math.sin(i * 0.2) * 0.5 + i * 0.05 }
  if (i <= spikePeak) {
    const k = (i - spikeStart) / (spikePeak - spikeStart)
    return { idx: i, p95: 2 + k * 14000 + Math.sin(i) * 1200 }
  }
  return { idx: i, p95: 14000 - (i - spikePeak) * 1800 }
})

export function V2Workload() {
  return (
    <section id="v2-workload" className="py-20 md:py-28 lg:py-32 px-6 md:px-12 max-w-6xl mx-auto" aria-labelledby="v2-heading">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        transition={{ duration: 0.6 }}
        className="text-center max-w-3xl mx-auto mb-12"
      >
        <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-teal-50 text-teal-700 text-sm font-medium border border-teal-200 mb-4">
          Day 16: v2 Workload
        </span>
        <h2 id="v2-heading" className="text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary leading-tight mb-6">
          p95 Variability: <span className="text-teal-600">CPU-Blind Bottleneck</span>
        </h2>
        <p className="text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
          Original podinfo had near-constant p95 (~3 ms). Day 16 replaced it with a DB-backed Flask + SQLite service
          ({metrics.offlineReplayRows}-row dataset) where the bottleneck is SQLite write serialization, not CPU,
          so p95 spans <strong>~2 ms idle to 23,200 ms under contention</strong>.
        </p>
      </motion.div>

      <div className="grid md:grid-cols-3 gap-5 mb-10" role="list">
        {p95Cards.map((item, i) => (
          <motion.div
            key={item.load}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ delay: i * 0.1, duration: 0.5 }}
            className="bg-white rounded-xl border border-border p-5 text-center hover:shadow-lg transition-shadow"
            role="listitem"
          >
            <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium ${colorBadge[item.color]}`}>
              {item.load}
            </span>
            <div className="mt-4">
              <div className="text-2xl md:text-3xl font-bold text-text-primary">{item.p95}</div>
              <p className="text-text-secondary text-xs mt-1">{item.note}</p>
            </div>
          </motion.div>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-50px' }}
        transition={{ duration: 0.5 }}
        className="bg-white rounded-2xl border border-border p-5 shadow-sm mb-10"
      >
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-base font-semibold text-text-primary">Illustrative p95 over time</h3>
          <span className="text-xs text-text-muted">synthesised from features_v2.csv shape</span>
        </div>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={p95Synthetic} margin={{ top: 10, right: 16, bottom: 10, left: 0 }}>
              <CartesianGrid stroke="#E2E8F0" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="idx" stroke="#475569" fontSize={12} tickLine={false} axisLine={false} label={{ value: 'time (30-s windows)', position: 'insideBottom', offset: -5, fill: '#94A3B8', fontSize: 11 }} />
              <YAxis stroke="#475569" fontSize={12} tickLine={false} axisLine={false} unit=" ms" />
              <Tooltip
                contentStyle={{ borderRadius: 8, border: '1px solid #E2E8F0', fontSize: 12 }}
                formatter={(v: number) => `${v.toFixed(0)} ms`}
                labelFormatter={(l) => `window ${l}`}
              />
              <ReferenceLine y={3000} stroke="#F59E0B" strokeDasharray="4 4" label={{ value: '3 s target', fill: '#F59E0B', fontSize: 11, position: 'insideTopRight' }} />
              <Line type="monotone" dataKey="p95" stroke="#0D9488" strokeWidth={2.5} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        className="grid md:grid-cols-2 lg:grid-cols-4 gap-5"
      >
        <div className="bg-white rounded-xl border border-border p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <Database className="w-6 h-6 text-blue-600" aria-hidden="true" />
            </div>
            <h3 className="text-base font-semibold text-text-primary">SQLite Backend</h3>
          </div>
          <p className="text-text-secondary text-xs leading-relaxed">100k-row SQLite DB with WAL mode. Real contention under write load.</p>
        </div>
        <div className="bg-white rounded-xl border border-border p-5">
          <h3 className="text-base font-semibold text-text-primary mb-3">Endpoints</h3>
          <ul className="space-y-1.5">
            {endpoints.map((ep) => (
              <li key={ep} className="flex items-center gap-2">
                <code className="bg-surface-100 px-2 py-0.5 rounded text-[11px] font-mono">{ep}</code>
              </li>
            ))}
          </ul>
        </div>
        <div className="bg-white rounded-xl border border-border p-5">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
              <Zap className="w-6 h-6 text-amber-600" aria-hidden="true" />
            </div>
            <h3 className="text-base font-semibold text-text-primary">ARTIFICIAL_LATENCY_MS</h3>
          </div>
          <p className="text-text-secondary text-xs mb-2 leading-relaxed">Configurable 0–10 ms random delay per request.</p>
          <code className="bg-surface-100 px-2 py-1 rounded text-[11px] font-mono">ARTIFICIAL_LATENCY_MS=10</code>
        </div>
        <div className="bg-white rounded-xl border border-border p-5">
          <h3 className="text-base font-semibold text-text-primary mb-3">SQLite Contention</h3>
          <ul className="space-y-1 text-[11px] text-text-secondary leading-relaxed">
            <li>• ~40 concurrent writes/sec contending on lock</li>
            <li>• Each write waits for previous to commit</li>
            <li>• p95 latency spikes to 14 s under contention</li>
            <li>• CPU stays low (bottleneck is I/O lock)</li>
          </ul>
        </div>
      </motion.div>
    </section>
  )
}
