import { motion } from 'framer-motion'
import { ShieldCheck, Terminal } from 'lucide-react'

export function TrustCallout() {
  return (
    <section
      id="trust"
      className="py-20 md:py-28 px-6 md:px-12"
      aria-labelledby="trust-heading"
    >
      <div className="max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-100px' }}
          transition={{ duration: 0.6 }}
          className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-text-primary via-slate-900 to-text-primary text-white p-10 md:p-14"
        >
          <div
            className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_rgba(20,184,166,0.4)_0%,_transparent_60%)]"
            aria-hidden="true"
          />
          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 rounded-xl bg-accent-500/20 text-accent-300 flex items-center justify-center">
                <ShieldCheck className="w-6 h-6" aria-hidden="true" />
              </div>
              <div>
                <p className="text-xs font-medium uppercase tracking-widest text-accent-300">
                  The Strongest Single Claim
                </p>
                <h2 id="trust-heading" className="text-2xl md:text-3xl font-bold">
                  Every paper number traces to a saved file.
                </h2>
              </div>
            </div>

            <p className="text-slate-300 leading-relaxed mb-6 max-w-2xl">
              The repo ships with an audit script that parses <code>docs/paper/main.tex</code>,
              extracts every numeric literal, and checks each one against <code>evidence-freeze.md</code>.
              If a number is added to the paper without a matching entry in the freeze file,
              CI fails.
            </p>

            <div className="bg-slate-950/80 backdrop-blur rounded-xl p-4 font-mono text-sm">
              <div className="flex items-center gap-2 mb-3 text-slate-400 text-xs">
                <Terminal className="w-3.5 h-3.5" /> Bash
              </div>
              <div className="text-emerald-300">
                $ python3 scripts/_phase5_audit.py
              </div>
              <div className="mt-3 space-y-1 text-slate-300">
                <div>
                  <span className="text-slate-500">Reading docs/paper/main.tex</span>
                  <span className="ml-2 text-slate-400">............</span>
                  <span className="ml-2 text-cyan-300">84</span> numeric literals
                </div>
                <div>
                  <span className="text-slate-500">Reading evidence-freeze.md</span>
                  <span className="ml-2 text-slate-400">.....</span>
                  <span className="ml-2 text-emerald-300">(canonical)</span>
                </div>
                <div className="pt-2 border-t border-slate-800 mt-2 space-y-0.5">
                  <div>
                    <span className="text-slate-500">SOURCED&nbsp;&nbsp;&nbsp;</span>
                    <span className="text-emerald-300 font-bold">57</span>
                    <span className="text-slate-500"> (every cited number traces to EF)</span>
                  </div>
                  <div>
                    <span className="text-slate-500">UNSOURCED</span>
                    <span className="text-amber-300 font-bold">0</span>
                    <span className="text-slate-500"> (zero fabricated paper claims)</span>
                  </div>
                </div>
                <div className="pt-2 border-t border-slate-800 mt-2 text-slate-400 text-xs">
                  Audit PASSED (exit code 0).
                </div>
              </div>
            </div>

            <div className="mt-6 text-xs text-slate-400">
              Run from repo root: <code className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-200">python3 scripts/_phase5_audit.py</code>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
