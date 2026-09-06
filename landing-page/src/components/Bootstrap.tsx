import { motion } from 'framer-motion'
import { Copy, Terminal, CheckCircle2, Github } from 'lucide-react'

const checklist = [
  'Docker CE (apt, no Docker Desktop license required)',
  'kubectl 1.30 + kind 0.23 + Helm 3 (pinned to the project Makefile)',
  'OpenJDK 17 (for the TLC model checker)',
  'Clones the public repo to ~/k8-auto-scaling-self-healing',
  'Pre-builds the k8-ai-ops:dev Docker image (saves 5 min per demo)',
  'Adds demo / demo-quick / demo-reset / tlac / paper aliases to ~/.bashrc',
]

const dailyCommands = [
  { cmd: 'demo-quick', note: '2-min highlight - dumps TLC traces + paper + audit logs + stats' },
  { cmd: 'demo', note: '30-min 12-step live demo on the kind cluster' },
  { cmd: 'demo-reset', note: 'wipe cluster + image cache, rebuild from scratch' },
  { cmd: 'tlac', note: 'only the TLA+ composition theorem (~4 min)' },
]

export function Bootstrap() {
  const copy = async (cmd: string) => {
    try { await navigator.clipboard.writeText(cmd) } catch { /* unavailable */ }
  }

  return (
    <section
      id="bootstrap"
      className="py-20 md:py-28 lg:py-32 px-6 md:px-12 bg-gradient-to-b from-surface-100 via-surface-50 to-white"
      aria-labelledby="bootstrap-heading"
    >
      <div className="max-w-6xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6 }}
          className="text-center max-w-3xl mx-auto mb-12"
        >
          <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-accent-50 text-accent-700 text-sm font-medium border border-accent-200 mb-4">
            Day 19: Student Laptop Delivery
          </span>
          <h2 id="bootstrap-heading" className="text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary leading-tight mb-6">
            From a Windows laptop with{' '}
            <span className="text-accent-600">zero tools</span> to a working demo in 20 minutes
          </h2>
          <p className="text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
            One PowerShell command + one bash command. No Docker Desktop, no WSL2 image download,
            no manual config. The student never runs <code>apt</code>, <code>kubectl</code>,
            or <code>kind</code> directly - all of it is hidden behind five demo aliases.
          </p>
        </motion.div>

        <div className="grid lg:grid-cols-5 gap-6">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ duration: 0.5 }}
            className="lg:col-span-3"
          >
            <div className="bg-slate-950 rounded-2xl overflow-hidden shadow-xl">
              <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-800">
                <div className="flex gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
                  <span className="w-2.5 h-2.5 rounded-full bg-yellow-500/80" />
                  <span className="w-2.5 h-2.5 rounded-full bg-green-500/80" />
                </div>
                <div className="ml-3 flex items-center gap-1.5 text-slate-400 text-xs font-mono">
                  <Terminal className="w-3.5 h-3.5" /> PowerShell (Administrator)
                </div>
              </div>
              <div className="p-6 space-y-4 font-mono text-sm">
                <div>
                  <span className="text-slate-500 select-none">$ </span>
                  <span className="text-cyan-300">wsl</span>{' '}
                  <span className="text-emerald-300">--install</span>{' '}
                  <span className="text-amber-200">-d</span> Ubuntu-24.04
                  <div className="mt-1 text-slate-500 text-xs">→ Reboot. Open "Ubuntu 24.04" from Start menu.</div>
                </div>
                <div className="pt-4 border-t border-slate-800">
                  <span className="text-slate-500 select-none">$ </span>
                  <span className="text-cyan-300">curl</span>{' '}
                  <span className="text-emerald-300">-fsSL</span>{' '}
                  <a
                    className="text-yellow-200 break-all hover:underline"
                    href="https://raw.githubusercontent.com/sudo-Harshk/k8-auto-scaling-self-healing/main/bootstrap.sh"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    https://raw.githubusercontent.com/sudo-Harshk/k8-auto-scaling-self-healing/main/bootstrap.sh
                  </a>{' '}
                  <span className="text-emerald-300">|</span> bash
                  <div className="mt-1 text-slate-500 text-xs">→ ~15 min unattended. Idempotent.</div>
                </div>
                <div className="pt-4 border-t border-slate-800">
                  <span className="text-slate-500 select-none">$ </span>
                  <span className="text-cyan-300">demo-quick</span>
                  <div className="mt-1 text-slate-500 text-xs">→ 2-min highlight run for the viva.</div>
                </div>
              </div>
            </div>

            <div className="mt-4 grid sm:grid-cols-2 gap-3">
              {dailyCommands.map(({ cmd, note }) => (
                <div
                  key={cmd}
                  className="group flex items-start gap-3 p-3 bg-white border border-border rounded-xl hover:border-accent-300 hover:shadow-sm transition-all"
                >
                  <code className="shrink-0 inline-flex items-center px-2.5 py-1 bg-slate-950 text-emerald-300 text-xs font-mono rounded">
                    {cmd}
                  </code>
                  <p className="text-xs text-text-secondary leading-relaxed flex-1">{note}</p>
                  <button
                    type="button"
                    onClick={() => copy(cmd)}
                    className="opacity-0 group-hover:opacity-100 inline-flex items-center justify-center w-7 h-7 rounded text-text-secondary hover:bg-surface-100 transition"
                    aria-label={`Copy ${cmd}`}
                  >
                    <Copy className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ duration: 0.5 }}
            className="lg:col-span-2 bg-white rounded-2xl border border-border p-6 shadow-sm"
          >
            <h3 className="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-green-600" />
              What bootstrap.sh installs
            </h3>
            <ul className="space-y-3 mb-6">
              {checklist.map((item) => (
                <li key={item} className="flex items-start gap-2 text-sm text-text-secondary">
                  <CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0 text-accent-600" />
                  <span className="leading-relaxed">{item}</span>
                </li>
              ))}
            </ul>

            <div className="pt-5 border-t border-border space-y-3">
              <a
                href="https://raw.githubusercontent.com/sudo-Harshk/k8-auto-scaling-self-healing/main/bootstrap.sh"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between gap-2 px-3 py-2.5 text-sm bg-surface-100 hover:bg-surface-200 text-text-primary rounded-lg transition-colors"
              >
                <span className="font-mono text-xs">bootstrap.sh</span>
                <Copy className="w-3.5 h-3.5 text-text-secondary" />
              </a>
              <a
                href="https://raw.githubusercontent.com/sudo-Harshk/k8-auto-scaling-self-healing/main/RUN_DEMO.md"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between gap-2 px-3 py-2.5 text-sm bg-surface-100 hover:bg-surface-200 text-text-primary rounded-lg transition-colors"
              >
                <span className="font-mono text-xs">RUN_DEMO.md (cheat-sheet)</span>
                <Copy className="w-3.5 h-3.5 text-text-secondary" />
              </a>
              <a
                href="https://github.com/sudo-Harshk/k8-auto-scaling-self-healing"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2 px-3 py-2.5 text-sm bg-text-primary hover:bg-black text-white rounded-lg transition-colors font-medium"
              >
                <Github className="w-4 h-4" />
                Repository on GitHub
              </a>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  )
}
