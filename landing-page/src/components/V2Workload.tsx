import { motion } from 'framer-motion'
import { Database, Zap } from 'lucide-react'

const p95Cards = [
  { load: 'Idle', p95: '~2ms', note: 'no users, nothing in flight', color: 'blue' },
  { load: 'Steady', p95: '~2–5ms', note: 'normal traffic, healthy DB', color: 'green' },
  { load: 'Spike (contention)', p95: 'up to 23,200ms', note: 'SQLite write lock serialization', color: 'red' },
]

const endpoints = ['GET /', 'GET /api/query?type=count', 'GET /api/query?type=stats', 'POST /api/write']

const colorBadge: Record<string, string> = {
  blue: 'bg-blue-100 text-blue-700',
  green: 'bg-green-100 text-green-700',
  red: 'bg-red-100 text-red-700',
}

export function V2Workload() {
  return (
    <section id="v2-workload" className="py-20 md:py-28 lg:py-32 px-6 md:px-12 max-w-7xl mx-auto" aria-labelledby="v2-heading">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        transition={{ duration: 0.6 }}
        className="text-center max-w-3xl mx-auto mb-16"
      >
        <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-teal-50 text-teal-700 text-sm font-medium border border-teal-200 mb-4">
          Day 16: v2 Workload
        </span>
        <h2 id="v2-heading" className="text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary leading-tight mb-6">
          p95 Variability Rework: <span className="text-teal-600">CPU-Blind Bottleneck</span>
        </h2>
        <p className="text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
          The original podinfo workload had near-constant p95 (~3ms). Day 16 replaced it with a
          DB-backed Flask + SQLite service (285-row dataset in <code>features_v2.csv</code>) where the
          bottleneck is SQLite write serialization — not CPU — so p95 spans <strong>~2ms idle to
          23,200ms under contention</strong>.
        </p>
      </motion.div>

      <div className="grid md:grid-cols-3 gap-6 mb-12" role="list">
        {p95Cards.map((item, i) => (
          <motion.div
            key={item.load}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ delay: i * 0.1, duration: 0.5 }}
            className="bg-white rounded-xl border border-border p-6 text-center hover:shadow-lg transition-shadow"
            role="listitem"
          >
            <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm font-medium ${colorBadge[item.color]}`}>
              {item.load}
            </span>
            <div className="mt-4">
              <div className="text-3xl md:text-4xl font-bold text-text-primary">{item.p95}</div>
              <p className="text-text-secondary text-sm mt-1">{item.note}</p>
            </div>
          </motion.div>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12"
      >
        <div className="bg-white rounded-xl border border-border p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <Database className="w-6 h-6 text-blue-600" />
            </div>
            <h3 className="text-lg font-semibold text-text-primary">SQLite Backend</h3>
          </div>
          <p className="text-text-secondary">100k-row SQLite DB with WAL mode. Real contention under write load.</p>
        </div>
        <div className="bg-white rounded-xl border border-border p-6">
          <h3 className="text-lg font-semibold text-text-primary mb-2">Endpoints</h3>
          <ul className="space-y-2">
            {endpoints.map((ep, i) => (
              <li key={i} className="flex items-center gap-2">
                <code className="bg-surface-100 px-2 py-0.5 rounded text-sm">{ep}</code>
              </li>
            ))}
          </ul>
        </div>
        <div className="bg-white rounded-xl border border-border p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
              <Zap className="w-6 h-6 text-amber-600" />
            </div>
            <h3 className="text-lg font-semibold text-text-primary">ARTIFICIAL_LATENCY_MS</h3>
          </div>
          <p className="text-text-secondary text-sm mb-2">
            Configurable 0–10ms random delay per request. Ensures p95 variance even at low load.
          </p>
          <code className="bg-surface-100 px-2 py-1 rounded text-sm">ARTIFICIAL_LATENCY_MS=10</code>
        </div>
        <div className="bg-white rounded-xl border border-border p-6">
          <h3 className="text-lg font-semibold text-text-primary mb-2">SQLite Contention</h3>
          <p className="text-text-secondary text-sm mb-3">
            SQLite serializes writes. At 80 concurrent users with 50% writes:
          </p>
          <ul className="space-y-1 text-sm text-text-secondary">
            <li>• ~40 concurrent writes/sec contending on single SQLite lock</li>
            <li>• Each write waits for previous to commit</li>
            <li>• p95 latency spikes to 14s under contention</li>
            <li>• CPU stays low (bottleneck is I/O lock, not compute)</li>
          </ul>
        </div>
      </motion.div>
    </section>
  )
}