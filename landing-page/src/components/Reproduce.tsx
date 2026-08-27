import { motion } from 'framer-motion'
import { Copy, Github, ExternalLink } from 'lucide-react'

interface Step {
  label: string
  cmd: string
  desc: string
}

const reproSteps: Step[] = [
  { label: 'Provision Azure VM', cmd: 'az vm create --resource-group myrg --name k8-vm --image Ubuntu2204 --size Standard_D4as_v5 --generate-ssh-keys', desc: 'Provision Standard_D4as_v5 (4 vCPU, 16GB).' },
  { label: 'SSH into VM', cmd: 'ssh azureuser@<vm-ip>', desc: 'SSH into the VM.' },
  { label: 'Run Bootstrap Script', cmd: 'curl -fsSL https://raw.githubusercontent.com/sudo-Harshk/k8-auto-scaling-self-healing/main/scripts/bootstrap_vm.sh | bash', desc: 'Installs Docker, kind, Helm, Java, TLA+ tools.' },
  { label: 'Deploy Infrastructure', cmd: 'cd k8-auto-scaling-self-healing && ./scripts/deploy_infra.sh', desc: 'Applies podinfo, monitoring, kafka, HPA, KEDA.' },
  { label: 'Run AI Pipeline', cmd: './scripts/run_pipeline.sh', desc: 'Starts producer + Faust + engine + operator.' },
  { label: 'Run Comparison', cmd: './scripts/run_comparison.sh', desc: 'Runs N=3 comparison (HPA / KEDA / AI × 3 scenarios).' },
]

export function Reproduce() {
  const copy = async (cmd: string) => {
    try {
      await navigator.clipboard.writeText(cmd)
    } catch {
      /* clipboard unavailable */
    }
  }

  return (
    <section id="reproduce" className="py-20 md:py-28 lg:py-32 px-6 md:px-12 max-w-7xl mx-auto" aria-labelledby="reproduce-heading">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        transition={{ duration: 0.6 }}
        className="text-center max-w-3xl mx-auto mb-16"
      >
        <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-green-50 text-green-700 text-sm font-medium border border-green-200 mb-4">
          Reproduce in 30 Minutes
        </span>
        <h2 id="reproduce-heading" className="text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary leading-tight mb-6">
          Reproduce on a Fresh VM in <span className="text-primary-600">30 Minutes</span>
        </h2>
        <p className="text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
          One script bootstraps a fresh Azure VM with Docker, kind, Helm, Java, TLA+ tools,
          and the full pipeline. Reproduce our N=3 results yourself.
        </p>
      </motion.div>

      <div className="space-y-4 max-w-3xl mx-auto">
        {reproSteps.map((step, i) => (
          <motion.div
            key={step.label}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-50px' }}
            transition={{ delay: i * 0.08, duration: 0.5 }}
            className="flex items-start gap-4 p-4 bg-white rounded-xl border border-border hover:border-primary-300 hover:shadow-lg transition-all"
          >
            <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-primary-100 text-primary-600 flex items-center justify-center">
              <span className="text-primary-600 font-bold text-base">{i + 1}</span>
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-2">
                <h3 className="font-semibold text-text-primary">{step.label}</h3>
                <button
                  type="button"
                  onClick={() => copy(step.cmd)}
                  className="ml-auto shrink-0 inline-flex items-center gap-1 px-3 py-1 text-xs font-medium bg-surface-100 text-text-secondary rounded hover:bg-surface-200 transition-colors"
                  aria-label={`Copy command for ${step.label}`}
                >
                  <Copy className="w-3.5 h-3.5" />
                  Copy
                </button>
              </div>
              <p className="text-text-secondary text-sm mb-2">{step.desc}</p>
              <code className="block px-3 py-2 bg-slate-950 rounded-lg text-xs text-green-300 font-mono whitespace-pre-wrap break-all">
                {step.cmd}
              </code>
            </div>
          </motion.div>
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        className="mt-16 text-center"
      >
        <a
          href="https://github.com/sudo-Harshk/k8-auto-scaling-self-healing"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-8 py-4 rounded-lg bg-primary-600 text-white font-medium hover:bg-primary-700 transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
        >
          <Github className="w-5 h-5" />
          View Full Repository on GitHub
          <ExternalLink className="w-4 h-4" />
        </a>
      </motion.div>
    </section>
  )
}