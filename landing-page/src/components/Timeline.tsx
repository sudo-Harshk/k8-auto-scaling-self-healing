import { motion } from 'framer-motion'
import { CheckCircle } from 'lucide-react'

const milestones = [
  { day: 1, title: 'Cluster & Workload', desc: 'Kind cluster + podinfo deployment.', status: 'completed' },
  { day: 2, title: 'Monitoring Stack', desc: 'Prometheus + Grafana + Alertmanager.', status: 'completed' },
  { day: 3, title: 'Metrics API & Baseline', desc: 'Prometheus metrics client + baseline Locust test.', status: 'completed' },
  { day: 4, title: 'Kafka Pipeline', desc: 'Strimzi Kafka + topics.', status: 'completed' },
  { day: 5, title: 'Faust Stream Processor', desc: '30s window Faust processor (k8s-metrics → k8s-features).', status: 'completed' },
  { day: 6, title: 'Feature Engineering', desc: '55 rows × 4 scenarios → features.csv.', status: 'completed' },
  { day: 7, title: 'Replica Predictor', desc: 'River HoeffdingAdaptiveTreeRegressor (MAE 0.24).', status: 'completed' },
  { day: 8, title: 'Anomaly Detection', desc: 'HalfSpaceTrees (threshold 0.2417, 55% detection, 6.7× separation).', status: 'completed' },
  { day: 9, title: 'Decision Engine', desc: 'Predictor + anomaly detector + perturbation FI.', status: 'completed' },
  { day: 10, title: 'TLA+ Safety Shield Spec', desc: '5 safety invariants, 217-line spec.', status: 'completed' },
  { day: 11, title: 'Safety Shield Implementation', desc: 'Python implementation + 16 tests (8 anti-drift).', status: 'completed' },
  { day: 12, title: 'Kubernetes Operator', desc: 'Kafka actuator (python), 8/8 tests pass.', status: 'completed' },
  { day: 13, title: 'E2E Integration + Chaos', desc: 'Scale 2→4, heal pod delete, noop. 3 critical bugs found & fixed.', status: 'completed' },
  { day: 14, title: 'Evaluation & Comparison', desc: 'HPA vs KEDA vs AI, ablation study, N=3 stats.', status: 'completed' },
  { day: 15, title: 'Liveness Property + N=3', desc: 'TLA+ liveness verified (273k states), 40 tests.', status: 'completed' },
  { day: 16, title: 'p95 Variability + v2 Workload', desc: 'Flask + SQLite workload, 48× p95 range (290ms–14,000ms).', status: 'completed' },
  { day: 17, title: 'Paper Strengthening', desc: 'Threat model, defense-in-depth, production roadmap.', status: 'completed' },
  { day: 18, title: 'Research Gaps Closed', desc: 'v2 AI pipeline, Day-13 E2E re-run, N=3 v2, 5 new tests → 45/45.', status: 'completed' },
]

export function Timeline() {
  return (
    <section id="timeline" className="py-20 md:py-28 lg:py-32 px-6 md:px-12 max-w-7xl mx-auto" aria-labelledby="timeline-heading">
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
          18 Days of Implementation
        </h2>
        <p className="text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
          From empty cluster to TLA+-verified AI operator with formal safety guarantees.
        </p>
      </motion.div>

      <div className="relative">
        <div className="hidden lg:block absolute left-1/2 top-0 bottom-0 w-px bg-border -translate-x-1/2" aria-hidden="true" />

        <div className="relative space-y-6">
          {milestones.map((milestone, index) => (
            <motion.div
              key={milestone.day}
              initial={{ opacity: 0, x: index % 2 === 0 ? -30 : 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: '-50px' }}
              transition={{ delay: index * 0.05, duration: 0.5 }}
              className="relative flex items-start gap-6"
            >
              <div
                className={`w-1/2 ${index % 2 === 0 ? 'pr-12 text-right' : 'pl-12 text-left'} relative z-10 flex ${
                  index % 2 === 0 ? 'justify-end' : ''
                }`}
              >
                <div className={`inline-flex items-center justify-center w-10 h-10 rounded-full bg-primary-600 text-white font-bold text-sm flex-shrink-0 ${
                  index % 2 === 0 ? 'order-1 ml-0' : ''
                }`}>
                  {milestone.day}
                </div>
                <div className={index % 2 === 0 ? 'pr-4' : 'pl-4'}>
                  <span className="inline-flex items-center gap-1 px-3 py-1 text-xs font-medium rounded-full bg-green-50 text-green-700 border border-green-200 mb-2">
                    <CheckCircle className="w-3 h-3" aria-hidden="true" /> Completed
                  </span>
                  <h3 className="text-lg font-semibold text-text-primary mb-1">{milestone.title}</h3>
                  <p className="text-text-secondary text-sm">{milestone.desc}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}