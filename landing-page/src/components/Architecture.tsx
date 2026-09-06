import { motion } from 'framer-motion'
import { ArrowRight } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { Database, Server, Cpu, Brain, GitBranch, ShieldCheck, ServerCog } from 'lucide-react'

interface Stage {
  name: string
  description: string
  Icon: LucideIcon
}

const stages: Stage[] = [
  { name: 'Prometheus', description: 'Scrapes metrics every 10 s', Icon: Database },
  { name: 'Kafka', description: 'KRaft bus, 3 topics', Icon: Server },
  { name: 'Faust', description: '30 s windowed aggregations', Icon: Cpu },
  { name: 'River ML', description: 'Online HTR + HalfSpaceTrees', Icon: Brain },
  { name: 'Decision', description: 'Predict · detect · explain', Icon: GitBranch },
  { name: 'TLA+ Shield', description: '5 invariants + 1 liveness', Icon: ShieldCheck },
  { name: 'K8s Operator', description: 'Patches Deployment spec', Icon: ServerCog },
]

export function Architecture() {
  return (
    <section id="architecture" className="py-20 md:py-28 lg:py-32 px-6 md:px-12 max-w-6xl mx-auto" aria-labelledby="arch-heading">
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
          End-to-end pipeline,{' '}
          <span className="text-primary-600">scraped to applied</span>
        </h2>
        <p className="text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
          Each box is a single, replaceable component. The shield sits between the
          ML decision and the Kubernetes API &mdash; not on top of it, and not under it.
        </p>
      </motion.div>

      {/* Horizontal pipeline */}
      <div className="relative overflow-x-auto pb-4">
        <div className="flex items-stretch gap-3 min-w-max lg:min-w-0 lg:justify-center">
          {stages.map((s, i) => {
            const Icon = s.Icon
            const isShield = s.name === 'TLA+ Shield'
            return (
              <div key={s.name} className="flex items-stretch">
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, margin: '-50px' }}
                  transition={{ delay: i * 0.05, duration: 0.4 }}
                  className={`relative w-32 lg:w-36 p-3 rounded-xl text-center ${
                    isShield
                      ? 'bg-gradient-to-br from-accent-50 to-primary-50 border-2 border-accent-300 shadow-lg'
                      : 'bg-white border border-border hover:border-primary-300 hover:shadow-md transition-all'
                  }`}
                >
                  <div className={`w-9 h-9 mx-auto rounded-lg flex items-center justify-center mb-2 ${
                    isShield ? 'bg-accent-500/20 text-accent-700' : 'bg-primary-100 text-primary-700'
                  }`}>
                    <Icon className="w-5 h-5" aria-hidden="true" />
                  </div>
                  <h3 className={`text-xs font-semibold ${isShield ? 'text-accent-800' : 'text-text-primary'}`}>
                    {s.name}
                  </h3>
                  <p className="text-[10px] text-text-secondary mt-1 leading-tight">{s.description}</p>
                  {isShield && (
                    <span className="absolute -top-2 left-1/2 -translate-x-1/2 px-1.5 py-0.5 bg-accent-600 text-white text-[9px] font-bold rounded-full uppercase tracking-wider">
                      Proven
                    </span>
                  )}
                </motion.div>
                {i < stages.length - 1 && (
                  <div className="flex items-center justify-center text-text-muted px-2">
                    <ArrowRight className="w-4 h-4" aria-hidden="true" />
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Visual: where the shield sits */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        transition={{ duration: 0.5 }}
        className="mt-12 grid md:grid-cols-3 gap-4 max-w-4xl mx-auto"
      >
        <div className="p-4 bg-white border border-border rounded-xl">
          <h4 className="text-xs font-semibold text-text-primary uppercase tracking-wider mb-1">Above shield</h4>
          <p className="text-xs text-text-secondary leading-relaxed">
            Onward ML controller decides <em>what</em> the right action would be in an ideal world.
          </p>
        </div>
        <div className="p-4 bg-accent-50 border-2 border-accent-300 rounded-xl">
          <h4 className="text-xs font-semibold text-accent-700 uppercase tracking-wider mb-1">TLA+ Shield (here)</h4>
          <p className="text-xs text-accent-800 leading-relaxed">
            Verifies the proposal against the formal spec. Clamps out-of-bounds values; rejects violations.
          </p>
        </div>
        <div className="p-4 bg-white border border-border rounded-xl">
          <h4 className="text-xs font-semibold text-text-primary uppercase tracking-wider mb-1">Below shield</h4>
          <p className="text-xs text-text-secondary leading-relaxed">
            Operator only ever sees verified, within-bounds actions. It does not need its own safety logic.
          </p>
        </div>
      </motion.div>
    </section>
  )
}
