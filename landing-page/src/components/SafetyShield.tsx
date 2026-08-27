import { motion } from 'framer-motion'
import { Clock, GitBranch, ShieldCheck } from 'lucide-react'

const invariants = [
  { name: 'Min Replicas', formula: 'current_replicas ≥ 1', desc: 'Replica count never drops below 1' },
  { name: 'Max Replicas', formula: 'current_replicas ≤ 10', desc: 'Replica count never exceeds 10' },
  { name: 'Bounded Scale Step', formula: '|new - old| ≤ 2', desc: 'Single decision changes replicas by ≤ 2' },
  { name: 'Heal Preserves Replicas', formula: 'heal ⇒ target = current', desc: 'Heal actions never change replica count' },
  { name: 'Cooldown Enforced', formula: 'clock - last_action ≥ COOLDOWN', desc: '60s minimum between actions' },
]

export function SafetyShield() {
  return (
    <section id="safety-shield" className="py-20 md:py-28 lg:py-32 px-6 md:px-12 max-w-7xl mx-auto" aria-labelledby="shield-heading">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        transition={{ duration: 0.6 }}
        className="text-center max-w-3xl mx-auto mb-16"
      >
        <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-accent-50 text-accent-700 text-sm font-medium border border-accent-200 mb-4">
          Safety Shield (TLA+)
        </span>
        <h2 id="shield-heading" className="text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary leading-tight mb-6">
          TLA+ Verified Safety Shield
        </h2>
        <p className="text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
          Five safety invariants + one liveness property. Exhaustively model-checked by TLC across 273,702 reachable states. Zero errors found.
        </p>
      </motion.div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {invariants.map((invariant, index) => (
          <motion.div
            key={invariant.name}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ delay: index * 0.1, duration: 0.5 }}
            className="bg-white rounded-xl border border-border p-6 hover:border-primary-300 hover:shadow-lg transition-all duration-300"
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-xl bg-accent-50 text-accent-600 flex items-center justify-center">
                <ShieldCheck className="w-5 h-5 text-accent-600" />
              </div>
              <span className="text-xs font-semibold text-primary-600 uppercase tracking-wider">Invariant</span>
            </div>
            <h3 className="text-lg font-semibold text-text-primary mb-1">{invariant.name}</h3>
            <code className="block text-sm font-mono text-primary-600 bg-primary-50 px-2 py-0.5 rounded mb-2">{invariant.formula}</code>
            <p className="text-text-secondary text-sm">{invariant.desc}</p>
          </motion.div>
        ))}

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-50px' }}
          transition={{ delay: 0.5, duration: 0.5 }}
          className="bg-accent-50 rounded-xl border border-accent-200 p-6"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-accent-100 text-accent-600 flex items-center justify-center">
              <GitBranch className="w-5 h-5 text-accent-600" />
            </div>
            <span className="text-xs font-semibold text-accent-700 uppercase tracking-wider">Liveness</span>
          </div>
          <h3 className="text-lg font-semibold text-text-primary mb-1">Eventually Scale Up</h3>
          <code className="block text-sm font-mono text-accent-700 bg-accent-100 px-2 py-0.5 rounded mb-2">sustained demand → scale up</code>
          <p className="text-text-secondary text-sm">
            When sustained demand is detected (10+ consecutive windows), the operator eventually scales up. Verified with strong fairness on Tick, ApplyScaleUp, and ApplyScaleDown.
          </p>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        className="mt-16 p-6 bg-primary-50 rounded-2xl border border-primary-200"
      >
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-xl bg-primary-100 text-primary-600 flex items-center justify-center flex-shrink-0">
            <Clock className="w-5 h-5 text-primary-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary mb-1">Cyclic Clock Subtlety</h3>
            <p className="text-text-secondary text-sm">
              The logical clock cycles modulo 11. Naive integer subtraction (clock - last_action_clock) becomes negative after wrap-around, silently disabling cooldown. Fixed with modular arithmetic in CooldownElapsed.
            </p>
          </div>
        </div>
      </motion.div>
    </section>
  )
}