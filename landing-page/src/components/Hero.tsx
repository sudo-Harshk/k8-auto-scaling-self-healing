import { motion } from 'framer-motion'
import { ArrowRight, Github } from 'lucide-react'

export function Hero() {
  return (
    <section
      className="relative min-h-[90vh] flex items-center justify-center pt-20 pb-20 px-6 md:px-12 overflow-hidden"
      aria-labelledby="hero-heading"
    >
      <div
        className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_#E0E7FF_0%,_transparent_70%)] opacity-60"
        aria-hidden="true"
      />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
        className="relative z-10 max-w-5xl mx-auto text-center px-6"
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
          Research Prototype — 18 Days · 45 Tests · TLA+ Verified
        </motion.span>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1, duration: 0.6, ease: 'easeOut' }}
          id="hero-heading"
          className="mt-6 text-4xl md:text-5xl lg:text-6xl font-bold text-text-primary leading-tight"
        >
          An AI-Driven Kubernetes Operator with{' '}
          <span className="text-primary-600">TLA+-Verified Safety</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.6 }}
          className="mt-6 text-lg md:text-xl text-text-secondary max-w-3xl mx-auto leading-relaxed"
        >
          Online learning + formal verification + active healing for Kubernetes.{' '}
          <span className="font-medium">18-day research prototype.</span> Honest about scope.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.6 }}
          className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4"
        >
          <a
            href="https://github.com/sudo-Harshk/k8-auto-scaling-self-healing"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-primary-600 text-white font-medium hover:bg-primary-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          >
            <Github className="w-5 h-5" aria-hidden="true" />
            View on GitHub
          </a>

          <a
            href="#reproduce"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-white text-text-primary font-medium border border-border hover:bg-surface-100 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          >
            Reproduce in 30 min
            <ArrowRight className="w-4 h-4" aria-hidden="true" />
          </a>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.6 }}
          className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-3xl mx-auto"
        >
          {[
            { value: '18', label: 'Implementation days' },
            { value: '45', label: 'Automated tests passing' },
            { value: '273,702', label: 'TLC model-checked states' },
            { value: '0', label: 'Safety violations found' },
          ].map((stat) => (
            <div key={stat.label} className="px-4 py-4 rounded-xl bg-white border border-border text-center">
              <div className="text-2xl md:text-3xl font-bold text-primary-600">{stat.value}</div>
              <p className="text-xs text-text-secondary mt-1">{stat.label}</p>
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