import { motion } from 'framer-motion'

export function Evaluation() {
  return (
    <section id="evaluation" className="py-20 md:py-28 lg:py-32 px-6 md:px-12 max-w-7xl mx-auto" aria-labelledby="eval-heading">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        transition={{ duration: 0.6 }}
        className="text-center max-w-3xl mx-auto mb-16"
      >
        <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary-50 text-primary-700 text-sm font-medium border border-primary-200 mb-4">
          Evaluation
        </span>
        <h2 id="eval-heading" className="text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary leading-tight mb-6">
          N=3 Statistical Comparison
        </h2>
        <p className="text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
          Three operators × three scenarios × three repetitions = 27 cells. Mean ± std reported.
        </p>
      </motion.div>

      <div className="overflow-x-auto rounded-xl border border-border bg-white">
        <table className="w-full text-sm" role="table">
          <thead>
            <tr className="bg-surface-50 border-b border-border">
              <th className="px-4 py-3 text-left font-semibold text-text-primary">Operator</th>
              <th className="px-4 py-3 text-right font-semibold text-text-primary">Scaling Lag (s)</th>
              <th className="px-4 py-3 text-right font-semibold text-text-primary">p95 Latency (ms)</th>
              <th className="px-4 py-3 text-right font-semibold text-text-primary">Error Rate (%)</th>
              <th className="px-4 py-3 text-right font-semibold text-text-primary">Scale Actions</th>
              <th className="px-4 py-3 text-right font-semibold text-text-primary">Heal Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-t border-border hover:bg-surface-50">
              <td className="px-4 py-3 font-medium text-text-primary">HPA</td>
              <td className="px-4 py-3 text-right text-text-secondary">5.0 ± 0.0</td>
              <td className="px-4 py-3 text-right font-mono">3.3 ± 0.5</td>
              <td className="px-4 py-3 text-right text-red-600 font-medium">0.0 ± 0.0</td>
              <td className="px-4 py-3 text-right font-mono">7.3 ± 1.2</td>
              <td className="px-4 py-3 text-right font-mono text-green-600">0</td>
            </tr>
            <tr className="border-t border-border hover:bg-surface-50">
              <td className="px-4 py-3 font-medium text-text-primary">KEDA</td>
              <td className="px-4 py-3 text-right text-text-secondary">5.0 ± 0.0</td>
              <td className="px-4 py-3 text-right font-mono">3.2 ± 0.4</td>
              <td className="px-4 py-3 text-right text-red-600 font-medium">0.0 ± 0.0</td>
              <td className="px-4 py-3 text-right font-mono">0.0 ± 0.0</td>
              <td className="px-4 py-3 text-right font-mono text-green-600">0</td>
            </tr>
            <tr className="border-t border-border hover:bg-surface-50">
              <td className="px-4 py-3 font-medium text-text-primary">AI (v1)</td>
              <td className="px-4 py-3 text-right text-text-secondary">5.0 ± 0.0</td>
              <td className="px-4 py-3 text-right font-mono">30000 ± 0</td>
              <td className="px-4 py-3 text-right text-red-600 font-medium">100.0 ± 0.0</td>
              <td className="px-4 py-3 text-right font-mono">15.1 ± 8.5</td>
              <td className="px-4 py-3 text-right font-mono text-green-600">1.0 ± 0.0</td>
            </tr>
          </tbody>
        </table>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        className="mt-12 p-6 bg-surface-50 rounded-2xl border border-border"
      >
        <h3 className="text-lg font-semibold text-text-primary mb-4">What the Numbers Say (v1, podinfo)</h3>
        <p className="text-text-secondary mb-4">
          Three operators ran against the same podinfo workload (spike 100 / steady 50 / idle 10 users, 60s each, N=3):
        </p>
        <ul className="space-y-2 text-sm text-text-secondary mb-6">
          <li><strong>HPA scaled reliably</strong> (2→8–10 replicas) with 0% errors and ~3ms p95 — it works well when the bottleneck is CPU, which is exactly what it watches.</li>
          <li><strong>KEDA recorded 0 scale actions</strong> in all 9 runs: its CPU trigger never fired, because podinfo's faster replicas kept utilization under the threshold before the trigger evaluated.</li>
          <li><strong>AI (v1) hit 100% error rate and p95 of 30,000ms</strong> — the worst result. The safety shield rejected 14–37 decisions per run, so replicas never moved off 2. This is the honest core finding: the v1 AI decision logic misfired out of distribution, and the shield contained it (no runaway, but also no help).</li>
        </ul>
        <div className="grid md:grid-cols-3 gap-4 mt-4">
          {[
            { op: 'HPA', note: 'Scales 2→8–10, 0% errors, ~3ms p95' },
            { op: 'KEDA', note: '0 scale actions — CPU trigger never fired' },
            { op: 'AI (v1)', note: '100% errors, shield rejected 14–37×/run' },
          ].map(({ op, note }) => (
            <div key={op} className="p-4 bg-white rounded-xl border border-border">
              <div className="flex items-center gap-2 mb-2">
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${['bg-blue-100 text-blue-700', 'bg-green-100 text-green-700', 'bg-purple-100 text-purple-700'][['HPA', 'KEDA', 'AI (v1)'].indexOf(op)]}`}>
                  {op}
                </span>
              </div>
              <p className="text-sm text-text-secondary">{note}</p>
            </div>
          ))}
        </div>
      </motion.div>
    </section>
  )
}