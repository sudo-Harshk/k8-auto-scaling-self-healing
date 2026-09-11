import { motion } from 'framer-motion'
import { Copy, Github, ExternalLink, Terminal, Cloud, Server, Cpu } from 'lucide-react'
import { metrics } from '@/data/metrics'

interface Step {
  label: string
  cmd: string
  desc: string
  icon: 'terminal' | 'cloud' | 'server' | 'cpu'
}

const reproSteps: Step[] = [
  {
    label: 'One-line bootstrap (WSL2 / Ubuntu 24.04)',
    cmd: "curl -fsSL https://raw.githubusercontent.com/sudo-Harshk/k8-auto-scaling-self-healing/main/bootstrap.sh | bash",
    desc: 'Installs Docker CE, kubectl 1.30, kind 0.23, Helm 3, OpenJDK 17; clones the repo; pre-builds the k8-ai-ops image; adds demo aliases to ~/.bashrc. Idempotent (~15 min).',
    icon: 'terminal',
  },
  {
    label: 'Open a fresh shell and type any demo command',
    cmd: 'demo-quick     # 2-min evidence dump (no cluster required)\ndemo            # full 30-min 12-step live demo\ntlac            # only the TLA+ composition theorem (~4 min)',
    desc: 'All day-of-viva commands are aliases wired by bootstrap.sh.',
    icon: 'terminal',
  },
  {
    label: 'Verify every paper claim locally',
    cmd: 'python3 scripts/_phase5_audit.py    # 56 sourced / 0 unsourced\npython3 -m pytest tests/ -q             # 53 passed',
    desc: 'Two commands. The audit script proves every numeric claim in docs/paper/main.pdf traces to evidence-freeze.md. Pytest proves the implementation matches.',
    icon: 'cpu',
  },
]

const iconMap = { terminal: Terminal, cloud: Cloud, server: Server, cpu: Cpu }

export function Reproduce() {
  const copy = async (cmd: string) => {
    try {
      await navigator.clipboard.writeText(cmd)
    } catch {
      /* clipboard unavailable */
    }
  }

  return (
    <section id="reproduce" className="py-20 md:py-28 lg:py-32 px-6 md:px-12 max-w-5xl mx-auto" aria-labelledby="reproduce-heading">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        transition={{ duration: 0.6 }}
        className="text-center max-w-3xl mx-auto mb-16"
      >
        <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-accent-50 text-accent-700 text-sm font-medium border border-accent-200 mb-4">
          Reproduce in 2 or 30 Minutes
        </span>
        <h2 id="reproduce-heading" className="text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary leading-tight mb-6">
          One Curl, One Alias,{' '}
          <span className="text-accent-600">Total Reproducibility</span>
        </h2>
        <p className="text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
          On a clean Windows laptop with no dev tools installed, the entire stack is up in under 20 minutes.
          Or use the 2-minute highlight mode (typed alias) when an examiner is short on time.
        </p>
      </motion.div>

      <div className="space-y-5 max-w-3xl mx-auto">
        {reproSteps.map((step, i) => {
          const Icon = iconMap[step.icon]
          return (
            <motion.div
              key={step.label}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-50px' }}
              transition={{ delay: i * 0.08, duration: 0.5 }}
              className="relative p-5 bg-white rounded-2xl border border-border hover:border-primary-300 hover:shadow-lg transition-all"
            >
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-11 h-11 rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 text-white flex items-center justify-center">
                  <Icon className="w-5 h-5" aria-hidden="true" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-3 mb-2">
                    <h3 className="font-semibold text-text-primary">{step.label}</h3>
                    <button
                      type="button"
                      onClick={() => copy(step.cmd)}
                      className="shrink-0 inline-flex items-center gap-1 px-3 py-1 text-xs font-medium bg-surface-100 text-text-secondary rounded hover:bg-surface-200 transition-colors"
                      aria-label={`Copy command for ${step.label}`}
                    >
                      <Copy className="w-3.5 h-3.5" />
                      Copy
                    </button>
                  </div>
                  <p className="text-text-secondary text-sm mb-3 leading-relaxed">{step.desc}</p>
                  <pre className="block px-3 py-2.5 bg-slate-950 rounded-lg text-xs text-green-300 font-mono whitespace-pre-wrap break-all leading-relaxed">
                    {step.cmd}
                  </pre>
                </div>
              </div>
            </motion.div>
          )
        })}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        className="mt-12 grid md:grid-cols-3 gap-4"
      >
        {[
          { value: `${metrics.paperPages}pp`, label: 'IEEE conference paper' },
          { value: `${metrics.paperReferences}`, label: 'Cited references with DOI/URL' },
          { value: `${metrics.unitTestsTotal}/${metrics.unitTestsTotal}`, label: 'Unit tests passing' },
        ].map((s) => (
          <div key={s.label} className="p-4 bg-white border border-border rounded-xl text-center">
            <div className="text-2xl font-bold text-primary-600">{s.value}</div>
            <p className="text-xs text-text-secondary mt-1">{s.label}</p>
          </div>
        ))}
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        className="mt-12 text-center"
      >
        <a
          href={metrics.githubUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-7 py-3.5 rounded-lg bg-text-primary text-white font-medium hover:bg-black transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
        >
          <Github className="w-5 h-5" />
          Open the repository
          <ExternalLink className="w-4 h-4" />
        </a>
      </motion.div>
    </section>
  )
}
