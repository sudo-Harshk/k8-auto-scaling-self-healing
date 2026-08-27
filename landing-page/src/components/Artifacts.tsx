import { motion } from 'framer-motion'
import { FileText, BarChart3, TrendingUp, BarChart, Download, ExternalLink } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface Artifact {
  name: string
  desc: string
  path: string
  icon: LucideIcon
  color: 'blue' | 'purple' | 'teal' | 'green'
}

const artifacts: Artifact[] = [
  {
    name: 'IEEE Paper Draft',
    desc: '6-page conference-format draft (Markdown) with threat model and defense-in-depth.',
    path: 'docs/ieee_paper.md',
    icon: FileText,
    color: 'blue',
  },
  {
    name: 'Grafana Dashboard',
    desc: '10-panel JSON export (decisions, replicas, anomaly, CPU, memory, audit).',
    path: 'docs/dashboard.json',
    icon: BarChart3,
    color: 'purple',
  },
  {
    name: 'Day-15 N=3 Results',
    desc: 'HPA vs KEDA vs AI comparison, 27 cells (mean ± std).',
    path: 'data/evaluation/comparison_results_N3.csv',
    icon: BarChart,
    color: 'green',
  },
  {
    name: 'v2 N=3 Comparison',
    desc: 'HPA/KEDA/AI on workload-v2 with metrics filled from Locust CSVs.',
    path: 'data/evaluation/comparison_v2_N3.csv',
    icon: TrendingUp,
    color: 'purple',
  },
  {
    name: 'Ablation Results (N=3)',
    desc: 'Full AI / –SHAP / –Shield action counts across three repetitions.',
    path: 'data/evaluation/ablation_results_N3.csv',
    icon: BarChart,
    color: 'purple',
  },
  {
    name: 'v2 Dataset (Day 16)',
    desc: '285 rows, 48× p95 range (290ms to 14,000ms).',
    path: 'data/features_v2.csv',
    icon: FileText,
    color: 'teal',
  },
  {
    name: 'v2 Models',
    desc: 'Replica predictor v2 (MAE 0.007) + Anomaly detector v3.',
    path: 'data/replica_model_v2.pkl',
    icon: TrendingUp,
    color: 'purple',
  },
]

const colorClasses: Record<Artifact['color'], string> = {
  blue: 'bg-blue-100 text-blue-600',
  purple: 'bg-purple-100 text-purple-600',
  teal: 'bg-teal-100 text-teal-600',
  green: 'bg-green-100 text-green-600',
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