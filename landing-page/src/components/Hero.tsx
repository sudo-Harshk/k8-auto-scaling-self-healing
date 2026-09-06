import { motion } from 'framer-motion'
import { ArrowRight, Github, Sparkles } from 'lucide-react'
import { metrics } from '@/data/metrics'

export function Hero() {
  return (
    <section
      className="relative min-h-[90vh] flex items-center justify-center pt-24 pb-20 px-6 md:px-12 overflow-hidden"
      aria-labelledby="hero-heading"
    >
      <div
        className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_#E0E7FF_0%,_transparent_55%)] opacity-60"
        aria-hidden="true"
      />
      <div
        className="absolute -top-32 left-1/2 -translate-x-1/2 w-[60rem] h-[60rem] bg-[radial-gradient(circle,_rgba(20,184,166,0.18)_0%,_transparent_60%)] pointer-events-none"
        aria-hidden="true"
      />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
        className="relative z-10 max-w-6xl mx-auto text-center px-6"
      >
        <motion.span
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary-50 text-primary-700 text-sm font-medium border border-primary-200"
        >
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-primary-500" />
          </span>
          Research Prototype &mdash; {metrics.implementationDays} Days &middot; {metrics.unitTestsTotal} Tests &middot; TLA+ Verified
        </motion.span>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.6, ease: 'easeOut' }}
          id="hero-heading"
          className="mt-6 text-4xl md:text-6xl lg:text-7xl font-bold text-text-primary leading-[1.05] tracking-tight"
        >
          A Kubernetes operator that scales with ML &mdash;
          <br />
          <span className="bg-gradient-to-r from-primary-600 via-accent-600 to-primary-600 bg-clip-text text-transparent">
            but only does what the math says is safe.
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6 }}
          className="mt-8 text-lg md:text-xl text-text-secondary max-w-3xl mx-auto leading-relaxed"
        >
          SHIELD-AI pairs an online machine-learning controller (River HTR +
          Half-Space-Trees) with a <strong>TLA+-verified safety shield</strong>
          that exhaustively proves 273,702 reachable states cannot violate
          replicas-in-range, bounded step, cooldown, or heal-preserves-replicas.
          A bare ML controller is unsafe under burst load &mdash; this work fixes that.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <a
            href={metrics.githubUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-text-primary text-white font-medium hover:bg-black transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          >
            <Github className="w-5 h-5" aria-hidden="true" />
            View source on GitHub
          </a>

          <a
            href="#bootstrap"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-primary-600 text-white font-medium hover:bg-primary-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          >
            <Sparkles className="w-5 h-5" aria-hidden="true" />
            Run in 2 minutes
            <ArrowRight className="w-4 h-4" aria-hidden="true" />
          </a>

          <a
            href="#reproduce"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-white text-text-primary font-medium border border-border hover:bg-surface-100 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          >
            Full 30-min demo
            <ArrowRight className="w-4 h-4" aria-hidden="true" />
          </a>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.6 }}
          className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto"
        >
          {[
            { value: metrics.implementationDays.toString(), label: 'Implementation days', tone: 'neutral' },
            { value: `${metrics.tlaDistinctStates.toLocaleString()}`, label: 'TLC reachable states', tone: 'primary' },
            { value: `${metrics.shieldClamp12of28}/${metrics.shieldStressTotal}`, label: 'Clamp rate per audit', tone: 'accent' },
            { value: `${metrics.unitTestsTotal}/${metrics.unitTestsTotal}`, label: 'Tests passing', tone: 'accent' },
          ].map((stat) => (
            <div
              key={stat.label}
              className={`px-4 py-5 rounded-xl border transition-shadow hover:shadow-md ${
                stat.tone === 'primary'
                  ? 'bg-primary-50 border-primary-200 text-primary-700'
                  : stat.tone === 'accent'
                  ? 'bg-accent-50 border-accent-200 text-accent-700'
                  : 'bg-white border-border text-text-primary'
              }`}
            >
              <div className={`text-2xl md:text-3xl font-bold ${stat.tone === 'neutral' ? 'text-text-primary' : ''}`}>
                {stat.value}
              </div>
              <p className="text-xs mt-1 opacity-80">{stat.label}</p>
            </div>
          ))}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.65, duration: 0.6 }}
          className="mt-10 flex items-center justify-center"
        >
          <a
            href="#problem"
            className="flex items-center gap-2 text-text-secondary hover:text-primary-600 transition-colors"
            aria-label="Scroll to problem section"
          >
            <span className="text-text-muted text-sm">Scroll to explore</span>
            <motion.span
              animate={{ y: [0, 8, 0] }}
              transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
              className="text-text-muted"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V4" />
              </svg>
            </motion.span>
          </a>
        </motion.div>
      </motion.div>
    </section>
  )
}
