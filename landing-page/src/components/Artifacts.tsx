import { motion } from 'framer-motion'
import { FileText, BarChart3, BarChart, Download, ExternalLink } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface Artifact {
  name: string
  desc: string
  path: string
  icon: LucideIcon
  color: 'blue' | 'purple' | 'teal' | 'green' | 'red'
}

const artifacts: Artifact[] = [
  {
    name: 'IEEE Paper (5pp)',
    desc: 'IEEE conference, 20 references, threat model + reproducibility, every claim cited.',
    path: 'docs/paper/main.pdf',
    icon: FileText,
    color: 'blue',
  },
  {
    name: 'Paper Source (.tex)',
    desc: 'main.tex + refs.bib; build with cd docs/paper && pdflatex && bibtex && pdflatex x2.',
    path: 'docs/paper/main.tex',
    icon: FileText,
    color: 'blue',
  },
  {
    name: 'Evidence Freeze',
    desc: 'Single source of truth for every paper number (sections A-L).',
    path: 'evidence-freeze.md',
    icon: FileText,
    color: 'teal',
  },
  {
    name: 'N=10 Stats Report',
    desc: 'results_N10/stats_report.md - 4 operators, 3 scenarios, 10 trials, sigma=0.',
    path: 'results_N10/stats_report.md',
    icon: BarChart,
    color: 'green',
  },
  {
    name: 'Day-15 N=3 (AI Failure)',
    desc: '100% error rate / replicas <= 2 across 9 of 9 runs (the motivating finding).',
    path: 'data/evaluation/comparison_results_N3.csv',
    icon: BarChart3,
    color: 'purple',
  },
  {
    name: 'TLC Trace - Composition',
    desc: 'ML+Shield joint spec: 53 reachable states, 0 errors, 1 s wall time.',
    path: 'specs/tlc_run_ml_composition.txt',
    icon: BarChart3,
    color: 'purple',
  },
  {
    name: 'TLC Trace - ML-only Counterexample',
    desc: 'Shield disabled; MlSafetyMinReplicas violated at depth 4 across 93 states.',
    path: 'specs/tlc_run_ml_only_counterexample.txt',
    icon: BarChart3,
    color: 'red',
  },
]

const colorClasses: Record<Artifact['color'], string> = {
  blue: 'bg-blue-100 text-blue-600',
  purple: 'bg-purple-100 text-purple-600',
  teal: 'bg-teal-100 text-teal-600',
  green: 'bg-green-100 text-green-600',
  red: 'bg-red-100 text-red-600',
}

export function Artifacts() {
  return (
    <section id="artifacts" className="py-20 md:py-28 lg:py-32 px-6 md:px-12 max-w-7xl mx-auto" aria-labelledby="artifacts-heading">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        transition={{ duration: 0.6 }}
        className="text-center max-w-3xl mx-auto mb-16"
      >
        <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-purple-50 text-purple-700 text-sm font-medium border border-purple-200 mb-4">
          Artifacts
        </span>
        <h2 id="artifacts-heading" className="text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary leading-tight mb-6">
          Reproducible Artifacts
        </h2>
        <p className="text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
          Every artifact is committed to the repo. Click to view or download.
        </p>
      </motion.div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {artifacts.map((artifact, index) => {
          const Icon = artifact.icon
          return (
            <motion.article
              key={artifact.name + artifact.path}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-50px' }}
              transition={{ delay: index * 0.08, duration: 0.5 }}
              className="group bg-white rounded-xl border border-border p-6 hover:shadow-lg hover:border-primary-300 transition-shadow duration-300"
            >
              <div className="flex items-start gap-4">
                <div className={`flex-shrink-0 w-12 h-12 rounded-xl flex items-center justify-center ${colorClasses[artifact.color]}`}>
                  <Icon className="w-6 h-6" aria-hidden="true" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-text-primary mb-1 group-hover:text-primary-600 transition-colors">
                    {artifact.name}
                  </h3>
                  <p className="text-text-secondary text-sm mb-3">{artifact.desc}</p>
                  <div className="flex items-center gap-3">
                    <a
                      href={artifact.path}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 text-sm font-medium text-primary-600 hover:text-primary-700 transition-colors"
                    >
                      View
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                    <a
                      href={artifact.path}
                      download
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-surface-100 text-text-secondary rounded hover:bg-surface-200 transition-colors"
                    >
                      <Download className="w-3.5 h-3.5" />
                      Download
                    </a>
                  </div>
                </div>
              </div>
            </motion.article>
          )
        })}
      </div>
    </section>
  )
}