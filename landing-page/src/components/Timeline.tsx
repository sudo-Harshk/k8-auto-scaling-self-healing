import { motion } from 'framer-motion'
import { CheckCircle2 } from 'lucide-react'

interface Milestone {
  day: number
  title: string
  desc: string
  category: 'infrastructure' | 'ml' | 'safety' | 'evaluation' | 'paper'
}

const categoryColors: Record<Milestone['category'], { dot: string; pill: string; label: string }> = {
  infrastructure: { dot: 'bg-blue-500', pill: 'bg-blue-50 text-blue-700 border-blue-200', label: 'Infra' },
  ml: { dot: 'bg-violet-500', pill: 'bg-violet-50 text-violet-700 border-violet-200', label: 'Online ML' },
  safety: { dot: 'bg-teal-500', pill: 'bg-teal-50 text-teal-700 border-teal-200', label: 'Safety' },
  evaluation: { dot: 'bg-amber-500', pill: 'bg-amber-50 text-amber-700 border-amber-200', label: 'Eval' },
  paper: { dot: 'bg-rose-500', pill: 'bg-rose-50 text-rose-700 border-rose-200', label: 'Paper' },
}

const milestones: Milestone[] = [
  { day: 1, title: 'Cluster & Workload', desc: 'Kind cluster + workload-v2 deploy.', category: 'infrastructure' },
  { day: 2, title: 'Monitoring Stack', desc: 'Prometheus + Grafana + Alertmanager.', category: 'infrastructure' },
  { day: 3, title: 'Metrics API & Baseline', desc: 'Prometheus client + baseline Locust.', category: 'infrastructure' },
  { day: 4, title: 'Kafka Pipeline', desc: 'KRaft Kafka + 3 topics (k8s-metrics, features, decisions).', category: 'infrastructure' },
  { day: 5, title: 'Faust Stream Processor', desc: '30s windowed aggregation to feature vectors.', category: 'infrastructure' },
  { day: 6, title: 'Feature Engineering', desc: '285-row dataset from workload-v2 traffic (features_v2.csv).', category: 'ml' },
  { day: 7, title: 'Replica Predictor', desc: 'River HoeffdingAdaptiveTreeRegressor (MAE 0.007 on v2).', category: 'ml' },
  { day: 8, title: 'Anomaly Detection', desc: 'HalfSpaceTrees; threshold 0.484; 1.2% organic anomaly rate.', category: 'ml' },
  { day: 9, title: 'Decision Engine', desc: 'Predictor + anomaly + leave-one-out perturbation explainer.', category: 'ml' },
  { day: 10, title: 'TLA+ Spec', desc: '5 invariants + 1 liveness property across a state machine.', category: 'safety' },
  { day: 11, title: 'Shield in Python', desc: 'Re-implements the spec; anti-drift test suite.', category: 'safety' },
  { day: 12, title: 'Kubernetes Operator', desc: 'Kafka actuator + official k8s client; offline replay harness.', category: 'safety' },
  { day: 13, title: 'E2E + Chaos', desc: 'Scale 2->N, pod-kill heal, noop. Bugs caught and fixed in-loop.', category: 'evaluation' },
  { day: 14, title: 'Evaluation', desc: 'HPA vs KEDA vs AI, ablation, 3x3 comparison grid.', category: 'evaluation' },
  { day: 15, title: 'Liveness + N=3', desc: 'TLA+ liveness verified across 273,702 reachable states.', category: 'safety' },
  { day: 16, title: 'p95 Variability', desc: 'Flask + SQLite workload (48x p95 range: 290 ms to 14,000 ms).', category: 'evaluation' },
  { day: 17, title: 'Paper Strengthening', desc: 'Threat model, defense-in-depth, production roadmap added.', category: 'paper' },
  { day: 18, title: 'Research Gaps Closed', desc: 'N=10 deterministic replay, FIRM baseline, 3 TLA+ specs.', category: 'paper' },
  { day: 19, title: 'Student Delivery', desc: 'WSL2 bootstrap.sh so a fresh Windows laptop runs the viva demo.', category: 'paper' },
]

export function Timeline() {
  return (
    <section id="timeline" className="py-20 md:py-28 lg:py-32 px-6 md:px-12 max-w-6xl mx-auto" aria-labelledby="timeline-heading">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        transition={{ duration: 0.6 }}
        className="text-center max-w-3xl mx-auto mb-16"
      >
        <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary-50 text-primary-700 text-sm font-medium border border-primary-200 mb-4">
          Timeline
        </span>
        <h2 id="timeline-heading" className="text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary leading-tight mb-6">
          19 Days from Empty Cluster to Verified AI Operator
        </h2>
        <p className="text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
          Color-coded by phase. Each day is a single commit on <code>main</code>.
        </p>
      </motion.div>

      <ol className="relative">
        <div className="absolute left-6 top-0 bottom-0 w-px bg-border" aria-hidden="true" />
        <div className="space-y-6">
          {milestones.map((m, index) => {
            const colors = categoryColors[m.category]
            return (
              <motion.li
                key={m.day}
                initial={{ opacity: 0, x: -16 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ delay: Math.min(index, 6) * 0.04, duration: 0.4 }}
                className="relative pl-16"
              >
                <span
                  className={`absolute left-3 top-3 w-7 h-7 rounded-full ${colors.dot} ring-4 ring-white flex items-center justify-center text-white text-xs font-bold shadow-sm`}
                  aria-hidden="true"
                >
                  {m.day}
                </span>

                <div className="bg-white rounded-xl border border-border p-4 hover:border-primary-300 hover:shadow-sm transition-all">
                  <div className="flex items-center justify-between gap-3 mb-1">
                    <h3 className="text-base font-semibold text-text-primary">{m.title}</h3>
                    <div className="flex items-center gap-2">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 text-xs font-medium rounded-full border ${colors.pill}`}
                      >
                        {colors.label}
                      </span>
                      <span className="inline-flex items-center gap-1 text-xs text-green-700">
                        <CheckCircle2 className="w-3.5 h-3.5" aria-hidden="true" />
                        Done
                      </span>
                    </div>
                  </div>
                  <p className="text-sm text-text-secondary leading-relaxed">{m.desc}</p>
                </div>
              </motion.li>
            )
          })}
        </div>
      </ol>
    </section>
  )
}
