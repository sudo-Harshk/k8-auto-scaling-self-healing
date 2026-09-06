import { motion } from 'framer-motion'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid } from 'recharts'
import { TrendingUp } from 'lucide-react'

interface EvalCell {
  operator: 'HPA' | 'KEDA' | 'AI-no-shield' | 'AI-shielded'
  scenario: 'idle' | 'steady' | 'spike'
  replicasEnd: number
  errorRate: number
}

const n10Rows: EvalCell[] = [
  { operator: 'HPA', scenario: 'idle', replicasEnd: 2, errorRate: 0 },
  { operator: 'HPA', scenario: 'steady', replicasEnd: 8, errorRate: 0 },
  { operator: 'HPA', scenario: 'spike', replicasEnd: 10, errorRate: 0 },
  { operator: 'KEDA', scenario: 'idle', replicasEnd: 2, errorRate: 0 },
  { operator: 'KEDA', scenario: 'steady', replicasEnd: 8, errorRate: 0 },
  { operator: 'KEDA', scenario: 'spike', replicasEnd: 10, errorRate: 0 },
  { operator: 'AI-no-shield', scenario: 'idle', replicasEnd: 2, errorRate: 100 },
  { operator: 'AI-no-shield', scenario: 'steady', replicasEnd: 2, errorRate: 100 },
  { operator: 'AI-no-shield', scenario: 'spike', replicasEnd: 2, errorRate: 100 },
  { operator: 'AI-shielded', scenario: 'idle', replicasEnd: 2, errorRate: 0 },
  { operator: 'AI-shielded', scenario: 'steady', replicasEnd: 8, errorRate: 0 },
  { operator: 'AI-shielded', scenario: 'spike', replicasEnd: 10, errorRate: 0 },
]

const aggregate = (op: EvalCell['operator']) => {
  const cells = n10Rows.filter((r) => r.operator === op)
  return {
    replicasMean: cells.reduce((s, c) => s + c.replicasEnd, 0) / cells.length,
    errorMean: cells.reduce((s, c) => s + c.errorRate, 0) / cells.length,
  }
}

const operators = ['HPA', 'KEDA', 'AI-no-shield', 'AI-shielded'] as const

const errorChartData = operators.map((op) => ({
  name: op,
  errorRate: aggregate(op).errorMean,
}))

const replicasChartData = operators.map((op) => ({
  name: op,
  replicas: aggregate(op).replicasMean,
}))

const errorColors: Record<string, string> = {
  HPA: '#14B8A6',
  KEDA: '#14B8A6',
  'AI-no-shield': '#EF4444',
  'AI-shielded': '#4F46E5',
}

export function Evaluation() {
  return (
    <section id="evaluation" className="py-20 md:py-28 lg:py-32 px-6 md:px-12 max-w-6xl mx-auto" aria-labelledby="eval-heading">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        transition={{ duration: 0.6 }}
        className="text-center max-w-3xl mx-auto mb-12"
      >
        <span className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-primary-50 text-primary-700 text-sm font-medium border border-primary-200 mb-4">
          Evaluation
        </span>
        <h2 id="eval-heading" className="text-3xl md:text-4xl lg:text-5xl font-bold text-text-primary leading-tight mb-6">
          Replica outcomes &amp; error rate:{' '}
          <span className="text-primary-600">HPA, KEDA, AI no-shield, AI shielded</span>
        </h2>
        <p className="text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
          workload-v2, N=10 deterministic trials per cell. Without the shield the AI is stuck;
          with the shield it tracks HPA exactly.
        </p>
      </motion.div>

      <div className="grid lg:grid-cols-2 gap-6 mb-12">
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-50px' }}
          transition={{ duration: 0.5 }}
          className="bg-white rounded-2xl border border-border p-5 shadow-sm"
        >
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-base font-semibold text-text-primary">Replicas End (mean across 3 scenarios)</h3>
            <span className="text-xs text-text-muted">target up to 10</span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={replicasChartData} margin={{ top: 10, right: 10, bottom: 10, left: 0 }}>
                <CartesianGrid stroke="#E2E8F0" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#475569" fontSize={12} tickLine={false} axisLine={false} domain={[0, 11]} />
                <Tooltip
                  cursor={{ fill: 'rgba(99,102,241,0.06)' }}
                  contentStyle={{ borderRadius: 8, border: '1px solid #E2E8F0', fontSize: 12 }}
                  formatter={(v: number) => `${v.toFixed(1)} replicas`}
                />
                <Bar dataKey="replicas" radius={[6, 6, 0, 0]}>
                  {replicasChartData.map((entry) => (
                    <Cell key={entry.name} fill={errorColors[entry.name]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-50px' }}
          transition={{ duration: 0.5 }}
          className="bg-white rounded-2xl border border-border p-5 shadow-sm"
        >
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-base font-semibold text-text-primary">Error Rate (mean across 3 scenarios)</h3>
            <span className="text-xs text-text-muted">lower is better</span>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={errorChartData} margin={{ top: 10, right: 10, bottom: 10, left: 0 }}>
                <CartesianGrid stroke="#E2E8F0" strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" stroke="#475569" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#475569" fontSize={12} tickLine={false} axisLine={false} domain={[0, 105]} unit="%" />
                <Tooltip
                  cursor={{ fill: 'rgba(99,102,241,0.06)' }}
                  contentStyle={{ borderRadius: 8, border: '1px solid #E2E8F0', fontSize: 12 }}
                  formatter={(v: number) => `${v.toFixed(1)}%`}
                />
                <Bar dataKey="errorRate" radius={[6, 6, 0, 0]}>
                  {errorChartData.map((entry) => (
                    <Cell key={entry.name} fill={errorColors[entry.name]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </div>

      <div className="overflow-x-auto rounded-xl border border-border bg-white">
        <table className="w-full text-sm" role="table">
          <caption className="px-4 py-3 text-left text-xs text-text-muted">
            N=10 deterministic replay (workload-v2, σ=0 across trials; n=10 reported in <code>results_N10/stats_report.md</code>)
          </caption>
          <thead>
            <tr className="bg-surface-50 border-b border-border">
              <th className="px-4 py-3 text-left font-semibold text-text-primary">Operator</th>
              <th className="px-4 py-3 text-right font-semibold text-text-primary">Idle (replicas)</th>
              <th className="px-4 py-3 text-right font-semibold text-text-primary">Steady</th>
              <th className="px-4 py-3 text-right font-semibold text-text-primary">Spike</th>
              <th className="px-4 py-3 text-right font-semibold text-text-primary">Error rate</th>
            </tr>
          </thead>
          <tbody>
            {operators.map((op) => {
              const cells = n10Rows.filter((r) => r.operator === op)
              return (
                <tr key={op} className="border-t border-border hover:bg-surface-50">
                  <td className="px-4 py-3 font-medium text-text-primary">
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${op === 'AI-no-shield' ? 'bg-red-500' : op === 'AI-shielded' ? 'bg-primary-500' : 'bg-accent-500'}`} />
                      {op}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-text-secondary">{cells.find((c) => c.scenario === 'idle')!.replicasEnd}</td>
                  <td className="px-4 py-3 text-right font-mono text-text-secondary">{cells.find((c) => c.scenario === 'steady')!.replicasEnd}</td>
                  <td className="px-4 py-3 text-right font-mono text-text-secondary">{cells.find((c) => c.scenario === 'spike')!.replicasEnd}</td>
                  <td className={`px-4 py-3 text-right font-mono font-medium ${op === 'AI-no-shield' ? 'text-red-600' : 'text-accent-700'}`}>
                    {op === 'AI-no-shield' ? '100%' : '0%'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-100px' }}
        className="mt-12 p-6 bg-surface-50 rounded-2xl border border-border"
      >
        <div className="flex items-start gap-3">
          <TrendingUp className="w-6 h-6 text-primary-600 flex-shrink-0" />
          <div>
            <h3 className="text-lg font-semibold text-text-primary mb-2">What the Numbers Say</h3>
            <p className="text-text-secondary leading-relaxed">
              HPA, KEDA, and the shielded AI all converge to the same target replicas across the three scenarios (2 / 8 / 10).
              Remove the safety shield and the same ML controller is stuck at 2 with 100% errors &mdash; the <strong>v1 AI failure mode</strong> documented
              in the Day-15 N=3 replication (data/evaluation/comparison_results_N3.csv:20-28, 9 of 9 runs).
            </p>
          </div>
        </div>
      </motion.div>
    </section>
  )
}
