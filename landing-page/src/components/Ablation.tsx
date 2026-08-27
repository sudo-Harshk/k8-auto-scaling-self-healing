import { motion } from 'framer-motion'
import { X } from 'lucide-react'

interface Variant {
  name: string
  scale: number
  heal: number
  noop: number
  rejected: number
  applied: number
  color: 'purple' | 'blue' | 'red'
}

const variants: Variant[] = [
  { name: 'Full AI', scale: 0, heal: 1, noop: 0, rejected: 54, applied: 1, color: 'purple' },
  { name: '-SHAP', scale: 0, heal: 1, noop: 0, rejected: 54, applied: 1, color: 'blue' },
  { name: '-Safety Shield', scale: 0, heal: 55, noop: 0, rejected: 0, applied: 55, color: 'red' },
]

const badgeClasses: Record<Variant['color'], string> = {
  purple: 'bg-purple-100 text-purple-700 border-purple-200',
  blue: 'bg-blue-100 text-blue-700 border-blue-200',
  red: 'bg-red-100 text-red-700 border-red-200',
}

function Stat({ label, value, highlight }: { label: string; value: number; highlight?: boolean }) {
  return (
    <div className="p-3 rounded-lg bg-surface-50 border border-border">
      <p className="text-xs text-text-muted">{label}</p>
      <p className={`text-lg font-semibold ${highlight ? 'text-red-600' : 'text-text-primary'}`}>{value}</p>
    </div>
  )
}

export function Ablation() {
  return (
    <section id="ablation" className="py-20 md:py-28 lg:py-32 px-6 md:px-12 max-w-7xl mx-auto" aria-labelledby="ablation-heading">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        transition={{ duration: 0.6 }}
        className="text-center max-w-3xl mx-auto mb-16"
      >
        <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-purple-50 text-purple-700 text-sm font-medium border border-purple-200 mb-4">
          Ablation Study
        </span>
        <h2 id="ablation-heading" className="text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary leading-tight mb-6">
          Ablation: <span className="text-red-600">Safety Shield</span> Is the Critical Component
        </h2>
        <p className="text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
          Removing the Safety Shield allows the AI to apply 55 unconstrained heal actions.
          With the shield, only 1 is applied (cooldown enforced).
        </p>
      </motion.div>

      <div className="grid md:grid-cols-3 gap-6">
        {variants.map((variant, index) => (
          <motion.div
            key={variant.name}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ delay: index * 0.15, duration: 0.5 }}
            className={`bg-white rounded-xl border p-6 hover:shadow-lg transition-all duration-300 ${
              variant.color === 'purple' ? 'border-purple-200' :
              variant.color === 'blue' ? 'border-blue-200' :
              'border-red-300'
            }`}
          >
            <div className="flex items-center gap-3 mb-4">
              <span className={`px-3 py-1 rounded-full text-sm font-medium border ${badgeClasses[variant.color]}`}>
                {variant.name}
              </span>
              {variant.name === '-Safety Shield' && (
                <span className="px-2 py-0.5 text-xs font-semibold bg-red-100 text-red-700 rounded-full">
                  Critical
                </span>
              )}
            </div>
            <div className="grid grid-cols-2 gap-3 mb-4">
              <Stat label="Scale" value={variant.scale} />
              <Stat label="Heal" value={variant.heal} />
              <Stat label="Noop" value={variant.noop} />
              <Stat label="Rejected" value={variant.rejected} />
              <Stat label="Applied" value={variant.applied} highlight={variant.name === '-Safety Shield'} />
            </div>
            <div className="pt-4 border-t border-border">
              <p className="text-sm text-text-secondary">
                {variant.name === '-Safety Shield'
                  ? 'Without shield: 55 unconstrained heal actions applied!'
                  : 'Safety Shield correctly enforces cooldown'}
              </p>
            </div>
          </motion.div>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        className="mt-16 p-6 bg-red-50 rounded-2xl border border-red-200"
      >
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-xl bg-red-100 text-red-600 flex items-center justify-center flex-shrink-0">
            <X className="w-6 h-6 text-red-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary mb-1">Without Safety Shield: Runaway Automation</h3>
            <p className="text-text-secondary mt-1">
              The AI engine would apply <strong>55 unconstrained heal actions</strong> in 55 consecutive windows.
              The Safety Shield's cooldown gate reduces this to <strong>1 applied action</strong>.
            </p>
            <p className="text-text-secondary mt-2 text-sm">
              This is the paper's strongest safety claim: the Shield prevents runaway automation
              by enforcing cooldown, bounded step size, and heal-preserves-replicas invariants.
            </p>
          </div>
        </div>
      </motion.div>
    </section>
  )
}