import { motion } from 'framer-motion'
import { Database, Server, Cpu, Brain, GitBranch, Shield, ServerCog } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface Stage {
  name: string
  description: string
  Icon: LucideIcon
}

const stages: Stage[] = [
  { name: 'Prometheus', description: 'Scrapes metrics every 10s.', Icon: Database },
  { name: 'Kafka', description: 'Buffers metric snapshots.', Icon: Server },
  { name: 'Faust (30s)', description: 'Windowed aggregation to features.', Icon: Cpu },
  { name: 'River-ML', description: 'Online predictor + anomaly detector.', Icon: Brain },
  { name: 'Decision Engine', description: 'Predict + anomaly + explainability.', Icon: GitBranch },
  { name: 'TLA+ Shield', description: '5 invariants + 1 liveness.', Icon: Shield },
  { name: 'K8s Operator', description: 'Kafka actuator → K8s API.', Icon: ServerCog },
]

export function Architecture() {
  return (
    <section id="architecture" className="py-20 md:py-28 lg:py-32 px-6 md:px-12 max-w-7xl mx-auto" aria-labelledby="arch-heading">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        transition={{ duration: 0.6 }}
        className="text-center max-w-3xl mx-auto mb-16"
      >
        <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary-50 text-primary-700 text-sm font-medium border border-primary-200 mb-4">
          Architecture
        </span>
        <h2 id="arch-heading" className="text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary leading-tight mb-6">
          End-to-End Pipeline
        </h2>
        <p className="text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
          Prometheus scrapes → Kafka buffers → Faust windows (30s) → River-ML predicts & detects →
          Decision Engine explains → Safety Shield verifies → Operator applies.
        </p>
      </motion.div>

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stages.map((stage, index) => {
          const Icon = stage.Icon
          return (
            <motion.div
              key={stage.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-50px' }}
              transition={{ delay: index * 0.1, duration: 0.5 }}
              className="bg-white rounded-xl border border-border p-6 hover:border-primary-300 hover:shadow-lg transition-all duration-300"
            >
              <div className="w-12 h-12 rounded-xl bg-primary-50 text-primary-600 flex items-center justify-center mb-4">
                <Icon className="w-6 h-6 text-primary-600" aria-hidden="true" />
              </div>
              <h3 className="text-lg font-semibold text-text-primary mb-1">{stage.name}</h3>
              <p className="text-text-secondary text-sm">{stage.description}</p>
            </motion.div>
          )
        })}
      </div>
    </section>
  )
}