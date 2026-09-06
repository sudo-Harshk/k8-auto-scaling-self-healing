import { motion } from 'framer-motion'
import { Clock, GitBranch, ShieldCheck, AlertOctagon } from 'lucide-react'
import { tlaSnippet, mlOnlyCounterexampleSnippet } from '@/data/metrics'

const invariants = [
  { name: 'Min Replicas', formula: 'replicas >= 1', desc: 'Replica count never drops below 1' },
  { name: 'Max Replicas', formula: 'replicas <= 10', desc: 'Replica count never exceeds 10' },
  { name: 'Bounded Scale Step', formula: '|new - old| <= 2', desc: 'Single decision changes replicas by ≤ 2' },
  { name: 'Heal Preserves Replicas', formula: 'heal => target = current', desc: 'Heal actions never change replica count' },
  { name: 'Cooldown Enforced', formula: '(clock - lastAction) mod 11 >= 6', desc: '60s minimum between actions (with cyclic-clock fix)' },
]

export function SafetyShield() {
  return (
    <section id="safety-shield" className="py-20 md:py-28 lg:py-32 px-6 md:px-12 max-w-6xl mx-auto" aria-labelledby="shield-heading">
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
          TLA+-verified safety that{' '}
          <span className="text-accent-600">ML alone cannot provide</span>
        </h2>
        <p className="text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
          Five safety invariants + one liveness property. Exhaustively model-checked by TLC
          across <strong>273,702 distinct reachable states</strong> in 1m47s. Zero errors.
        </p>
      </motion.div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
        {invariants.map((inv, index) => (
          <motion.div
            key={inv.name}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ delay: index * 0.08, duration: 0.5 }}
            className="group bg-white rounded-xl border border-border p-5 hover:border-accent-300 hover:shadow-lg transition-all"
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-xl bg-accent-50 text-accent-700 flex items-center justify-center">
                <ShieldCheck className="w-5 h-5" aria-hidden="true" />
              </div>
              <span className="text-xs font-semibold text-accent-700 uppercase tracking-wider">Invariant</span>
            </div>
            <h3 className="text-base font-semibold text-text-primary mb-1">{inv.name}</h3>
            <code className="block text-xs font-mono text-primary-700 bg-primary-50 px-2 py-0.5 rounded mb-2">{inv.formula}</code>
            <p className="text-text-secondary text-sm leading-relaxed">{inv.desc}</p>
          </motion.div>
        ))}

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-50px' }}
          transition={{ delay: 0.5, duration: 0.5 }}
          className="bg-gradient-to-br from-accent-50 to-primary-50 rounded-xl border border-accent-200 p-5"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-xl bg-white text-accent-700 flex items-center justify-center">
              <GitBranch className="w-5 h-5" aria-hidden="true" />
            </div>
            <span className="text-xs font-semibold text-accent-700 uppercase tracking-wider">Liveness</span>
          </div>
          <h3 className="text-base font-semibold text-text-primary mb-1">Eventually Scale Up</h3>
          <code className="block text-xs font-mono text-accent-700 bg-white px-2 py-0.5 rounded mb-2">
            sustained demand =&gt; scale up
          </code>
          <p className="text-text-secondary text-sm leading-relaxed">
            When sustained demand is detected (10+ consecutive windows), the operator eventually
            scales up. Verified with strong fairness on Tick, ApplyScaleUp, ApplyScaleDown.
          </p>
        </motion.div>
      </div>

      <div className="mt-12 grid lg:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-50px' }}
          transition={{ duration: 0.5 }}
          className="bg-slate-950 rounded-2xl overflow-hidden shadow-xl"
        >
          <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
              <span className="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300">TLA+</span>
              specs/SafetyShield.tla
            </div>
            <span className="text-xs text-emerald-400 font-mono">273,702 states · 0 errors</span>
          </div>
          <pre className="p-5 text-[12px] text-slate-200 font-mono overflow-x-auto leading-relaxed">
            {tlaSnippet}
          </pre>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-50px' }}
          transition={{ duration: 0.5 }}
          className="bg-red-950/90 rounded-2xl overflow-hidden shadow-xl text-red-50"
        >
          <div className="px-4 py-3 border-b border-red-800/60 flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs text-red-200 font-mono">
              <span className="px-2 py-0.5 rounded bg-red-500/30 text-red-100">COUNTEREXAMPLE</span>
              ML_Only path (shield disabled)
            </div>
            <span className="text-xs text-red-300 font-mono">93 states · violation</span>
          </div>
          <div className="p-5">
            <div className="flex items-center gap-2 mb-3 text-red-200 text-xs font-mono">
              <AlertOctagon className="w-4 h-4 text-red-300" /> <span>MlSafetyMinReplicas violated</span>
            </div>
            <pre className="text-[12px] text-red-100 font-mono overflow-x-auto leading-relaxed whitespace-pre-wrap">
              {mlOnlyCounterexampleSnippet}
            </pre>
          </div>
        </motion.div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        className="mt-12 p-6 bg-amber-50 rounded-2xl border border-amber-200"
      >
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center flex-shrink-0">
            <Clock className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-amber-900 mb-1">Cyclic Clock Subtlety</h3>
            <p className="text-amber-900/80 text-sm leading-relaxed">
              The logical clock cycles modulo 11. Naive integer subtraction
              (clock &minus; last_action_clock) becomes negative after wrap-around,
              silently disabling cooldown. Fixed with modular arithmetic in CooldownElapsed:
              <code className="mx-1 px-1.5 py-0.5 rounded bg-amber-100/60 font-mono text-amber-900">
                (clock - lastActionClock) % 11 &gt;= CooldownTicks
              </code>.
            </p>
          </div>
        </div>
      </motion.div>
    </section>
  )
}
