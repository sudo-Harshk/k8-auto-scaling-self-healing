import { motion } from 'framer-motion'
import { CheckCircle2, XCircle, Scale, Info } from 'lucide-react'

const worked = [
  'TLA+ Shield prevents runaway automation — ablation removes only the Shield, heal actions jump from 1 to 55 (N=3).',
  'KEDA logged 0 scale actions across all 18 v1+v2 N=3 runs — its CPU trigger produced no recorded scale events under either workload.',
  'v2 replica predictor agrees with HPA on target replicas (MAE 0.007).',
  'v2 anomaly detection catches ~1.2% of windows as anomalous (low signal, honest about it).',
  'Cooldown (60s) correctly rejects repeat heal requests — verified end-to-end in Day-18 E2E.',
]

const notWorked = [
  'v1 AI produced 100% error rate under load — HPA-derived decision logic misfired outside training distribution.',
  'v2 HPA never scaled up during the N=3 run (SQLite bottleneck, CPU stays under target).',
  'v2 anomaly detector only reports 1.2% organic anomalies — labeling heuristic is weak.',
  'Grafana dashboard JSON is hand-written, not exported — plugin install failed on-VM.',
  'No .tex build, no independent reproduction yet, single-node kind cluster only.',
]

const nuance = [
  'We do NOT claim the AI is faster than HPA. The value is safety + healing + explainability, not raw latency.',
  'HPA/KEDA are tightly integrated with Kubernetes; our AI is a separate control loop that must be wired carefully.',
  'The TLA+ proof covers the operator decision logic, NOT the workload metrics themselves.',
]

export function Honest() {
  return (
    <section
      id="honest"
      className="py-20 md:py-28 lg:py-32 px-6 md:px-12 max-w-7xl mx-auto"
      aria-labelledby="honest-heading"
    >
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        transition={{ duration: 0.6 }}
        className="text-center max-w-3xl mx-auto mb-16"
      >
        <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-surface-100 text-text-secondary text-sm font-medium border border-border mb-4">
          Honest Assessment
        </span>
        <h2
          id="honest-heading"
          className="text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary leading-tight mb-6"
        >
          What Worked, What Didn't
        </h2>
        <p className="text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
          A research prototype should report failures as loudly as successes. Here is the
          ground truth from the N=3 evaluation — including the parts that did not go our way.
        </p>
      </motion.div>

      <div className="grid lg:grid-cols-2 gap-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-50px' }}
          transition={{ duration: 0.5 }}
          className="bg-white rounded-xl border border-border p-6 lg:p-8"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-green-100 text-green-700 flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5 text-green-700" />
            </div>
            <h3 className="text-xl font-semibold text-text-primary">What Worked</h3>
          </div>
          <ul className="space-y-4">
            {worked.map((item, i) => (
              <li key={i} className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 flex-shrink-0 mt-0.5 text-green-600" />
                <span className="text-text-secondary text-sm leading-relaxed">{item}</span>
              </li>
            ))}
          </ul>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-50px' }}
          transition={{ duration: 0.5 }}
          className="bg-white rounded-xl border border-border p-6 lg:p-8"
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-xl bg-red-100 text-red-700 flex items-center justify-center">
              <XCircle className="w-5 h-5 text-red-700" />
            </div>
            <h3 className="text-xl font-semibold text-text-primary">What Didn't</h3>
          </div>
          <ul className="space-y-4">
            {notWorked.map((item, i) => (
              <li key={i} className="flex items-start gap-3">
                <XCircle className="w-5 h-5 flex-shrink-0 mt-0.5 text-red-600" />
                <span className="text-text-secondary text-sm leading-relaxed">{item}</span>
              </li>
            ))}
          </ul>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        className="mt-12 p-6 bg-surface-100 rounded-2xl border border-border"
      >
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary-100 text-primary-700 flex items-center justify-center flex-shrink-0">
            <Scale className="w-5 h-5 text-primary-700" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary mb-2">The Nuance</h3>
            <ul className="space-y-2">
              {nuance.map((n, i) => (
                <li key={i} className="flex items-start gap-2 text-text-secondary text-sm leading-relaxed">
                  <Info className="w-4 h-4 flex-shrink-0 mt-0.5 text-primary-600" />
                  {n}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </motion.div>
    </section>
  )
}