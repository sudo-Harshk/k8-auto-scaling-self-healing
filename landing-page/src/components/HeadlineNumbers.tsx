import { motion } from 'framer-motion'
import { TrendingUp, ShieldCheck, GitBranch, FileCheck2 } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { metrics } from '@/data/metrics'

interface HeadlineStat {
  value: string
  label: string
  detail: string
  Icon: LucideIcon
  tone: 'primary' | 'accent' | 'danger'
}

const stats: HeadlineStat[] = [
  {
    value: metrics.tlaDistinctStates.toLocaleString(),
    label: 'TLA+ reachable states',
    detail:
      '273,702 distinct states model-checked across the safety shield spec. Zero safety violations.',
    Icon: ShieldCheck,
    tone: 'primary',
  },
  {
    value: `${metrics.compositionDistinctStates} vs ${metrics.mlOnlyDistinctStates}`,
    label: 'With shield vs without',
    detail:
      'Composing ML with the shield produces 53 reachable states, all safe. Removing the shield lets the same ML reach 93 states - and one of them violates MlSafetyMinReplicas.',
    Icon: GitBranch,
    tone: 'primary',
  },
  {
    value: `${metrics.shieldClamp12of28}/${metrics.shieldStressTotal}`,
    label: 'Audit clamp rate',
    detail:
      'On the 28-row synthetic ML stress audit, the safety shield modified 12 of 28 (42.9%) of malicious ML proposals before they reached Kubernetes.',
    Icon: FileCheck2,
    tone: 'accent',
  },
  {
    value: '100% / 0%',
    label: 'N=3 AI failure mode',
    detail:
      'Day-15 N=3 replication: the unshielded ML controller produced 100% error rate and stuck at replicas ≤ 2 across all 9 runs. HPA and KEDA both scaled correctly.',
    Icon: TrendingUp,
    tone: 'danger',
  },
]

const toneClasses: Record<HeadlineStat['tone'], { ring: string; iconBg: string; iconColor: string; value: string }> = {
  primary: { ring: 'border-primary-200 hover:border-primary-400', iconBg: 'bg-primary-100', iconColor: 'text-primary-700', value: 'text-primary-700' },
  accent: { ring: 'border-accent-200 hover:border-accent-400', iconBg: 'bg-accent-100', iconColor: 'text-accent-700', value: 'text-accent-700' },
  danger: { ring: 'border-red-200 hover:border-red-400', iconBg: 'bg-red-100', iconColor: 'text-red-700', value: 'text-red-700' },
}

export function HeadlineNumbers() {
  return (
    <section
      id="headline-numbers"
      className="py-20 md:py-28 px-6 md:px-12 bg-gradient-to-b from-white via-surface-50 to-white"
      aria-labelledby="headline-heading"
    >
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6 }}
          className="text-center max-w-3xl mx-auto mb-16"
        >
          <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-amber-50 text-amber-800 text-sm font-medium border border-amber-200 mb-4">
            Headline Numbers
          </span>
          <h2 id="headline-heading" className="text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary leading-tight mb-6">
            Four claims, each{' '}
            <span className="text-primary-600">reproducible from saved data</span>
          </h2>
          <p className="text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
            Every number below is sourced from a file in this repository. The audit script
            <code className="mx-1.5 px-1.5 py-0.5 rounded bg-surface-100 text-text-primary text-sm font-mono">
              scripts/_phase5_audit.py
            </code>
            enforces this.
          </p>
        </motion.div>

        <div className="grid md:grid-cols-2 gap-6">
          {stats.map((s, index) => {
            const classes = toneClasses[s.tone]
            return (
              <motion.div
                key={s.label}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-50px' }}
                transition={{ delay: index * 0.08, duration: 0.5 }}
                className={`relative p-6 bg-white rounded-2xl border ${classes.ring} hover:shadow-xl transition-all`}
              >
                <div className="flex items-start gap-4">
                  <div className={`flex-shrink-0 w-12 h-12 rounded-xl ${classes.iconBg} ${classes.iconColor} flex items-center justify-center`}>
                    <s.Icon className="w-6 h-6" aria-hidden="true" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className={`text-3xl md:text-4xl font-bold tracking-tight ${classes.value}`}>
                      {s.value}
                    </div>
                    <p className="mt-1 font-medium text-text-primary text-sm">{s.label}</p>
                    <p className="mt-3 text-sm text-text-secondary leading-relaxed">{s.detail}</p>
                  </div>
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
