import { motion } from 'framer-motion'
import { Cpu, Server, AlertTriangle, Zap } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface Problem {
  icon: LucideIcon
  title: string
  detail: string
}

const problems: Problem[] = [
  { icon: Cpu, title: 'HPA = CPU Only', detail: 'Horizontal Pod Autoscaler only watches CPU utilization. Cannot respond to memory pressure, latency, or error rate.' },
  { icon: Server, title: 'KEDA Inherits HPA Limits', detail: 'KEDA adds event triggers but inherits HPA\'s single-signal reactive model. No formal safety guarantees.' },
  { icon: AlertTriangle, title: 'No Formal Safety', detail: 'Neither HPA nor KEDA provides formal guarantees. A buggy model can scale to 0 or crash the cluster.' },
  { icon: Zap, title: 'No Active Healing', detail: 'Neither HPA nor KEDA detects anomalous pods. Operators must build separate healing pipelines.' },
]

export function Problem() {
  return (
    <section id="problem" className="py-20 md:py-28 lg:py-32 px-6 md:px-12 max-w-7xl mx-auto" aria-labelledby="problem-heading">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        transition={{ duration: 0.6 }}
        className="text-center max-w-3xl mx-auto mb-16"
      >
        <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary-50 text-primary-700 text-sm font-medium border border-primary-200 mb-4">
          The Problem
        </span>
        <h2 id="problem-heading" className="text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary leading-tight mb-6">
          Kubernetes Auto-Scaling Today Is <span className="text-primary-600">Reactive & Single-Signal</span>
        </h2>
        <p className="text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
          HPA scales only on CPU. KEDA adds triggers but inherits HPA's limitations.
          No formal safety. No anomaly-driven healing.
        </p>
      </motion.div>

      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
        {problems.map((problem, index) => {
          const Icon = problem.icon
          return (
            <motion.div
              key={problem.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-100px' }}
              transition={{ delay: index * 0.1, duration: 0.5 }}
              className="group bg-white rounded-xl border border-border p-6 hover:border-primary-300 hover:shadow-lg transition-all duration-300"
            >
              <div className="w-12 h-12 rounded-xl bg-primary-50 text-primary-600 flex items-center justify-center mb-4">
                <Icon className="w-6 h-6 text-primary-600" aria-hidden="true" />
              </div>
              <h3 className="text-lg font-semibold text-text-primary mb-2">{problem.title}</h3>
              <p className="text-text-secondary leading-relaxed">{problem.detail}</p>
            </motion.div>
          )
        })}
      </div>
    </section>
  )
}