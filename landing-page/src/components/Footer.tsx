export function Footer() {
  return (
    <footer className="bg-surface-100 border-t border-border py-12 px-6 md:px-12" role="contentinfo">
      <div className="max-w-7xl mx-auto">
        <div className="grid md:grid-cols-4 gap-8 mb-8">
          <div>
            <h3 className="font-semibold text-text-primary mb-4">K8s AI Operator</h3>
            <p className="text-text-secondary text-sm leading-relaxed max-w-xs">
              An AI-driven Kubernetes operator with TLA+-verified safety guarantees.
              Online learning + formal verification + active healing.
            </p>
          </div>
          <nav aria-label="Project links">
            <h4 className="font-semibold text-text-primary mb-4">Project</h4>
            <ul className="space-y-2 text-sm text-text-secondary">
              <li><a href="#problem" className="hover:text-primary-600 transition-colors">The Problem</a></li>
              <li><a href="#architecture" className="hover:text-primary-600 transition-colors">Architecture</a></li>
              <li><a href="#safety-shield" className="hover:text-primary-600 transition-colors">Safety Shield</a></li>
              <li><a href="#evaluation" className="hover:text-primary-600 transition-colors">Evaluation</a></li>
              <li><a href="#limitations" className="hover:text-primary-600 transition-colors">Limitations</a></li>
            </ul>
          </nav>
          <nav aria-label="Artifact links">
            <h4 className="font-semibold text-text-primary mb-4">Artifacts</h4>
            <ul className="space-y-2 text-sm text-text-secondary">
              <li><a href="docs/ieee_paper.md" className="hover:text-primary-600 transition-colors" target="_blank" rel="noopener noreferrer">IEEE Paper Draft</a></li>
              <li><a href="docs/dashboard.json" className="hover:text-primary-600 transition-colors" target="_blank" rel="noopener noreferrer">Grafana Dashboard</a></li>
              <li><a href="data/evaluation/comparison_results_N3.csv" className="hover:text-primary-600 transition-colors" target="_blank" rel="noopener noreferrer">Day-15 N=3 Results</a></li>
              <li><a href="data/evaluation/comparison_v2_N3.csv" className="hover:text-primary-600 transition-colors" target="_blank" rel="noopener noreferrer">Day-18 v2 N=3</a></li>
            </ul>
          </nav>
          <div>
            <h4 className="font-semibold text-text-primary mb-4">Connect</h4>
            <div className="space-y-3">
              <a
                href="https://github.com/sudo-Harshk/k8-auto-scaling-self-healing"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 text-sm text-text-secondary hover:text-primary-600 transition-colors"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.44 9.8 8.21 11.39.6.11.82-.26.82-.58v-2.04c-3.34.73-4.04-1.61-4.04-1.61-.55-1.39-1.34-1.76-1.34-1.76-1.1-.75.08-.74.08-.74 1.21.09 1.85 1.25 1.85 1.25 1.08 1.85 2.83 1.31 3.52 1 .11-.78.42-1.31.76-1.61-2.64-.3-5.41-1.32-5.41-5.87 0-1.3.47-2.36 1.23-3.19-.12-.3-.53-1.52.12-3.16 0 0 1-.32 3.3 1.23a11.5 11.5 0 0 1 6 0c2.29-1.55 3.3-1.23 3.3-1.23.65 1.64.24 2.86.12 3.16.77.83 1.23 1.89 1.23 3.19 0 4.56-2.78 5.56-5.43 5.86.43.37.81 1.1.81 2.22v3.29c0 .32.22.7.83.58A12 12 0 0 0 24 12c0-6.63-5.37-12-12-12Z" />
                </svg>
                GitHub
              </a>
              <p className="text-sm text-text-secondary">
                <a href="mailto:author@example.com" className="hover:text-primary-600 transition-colors">
                  author@example.com
                </a>
              </p>
            </div>
          </div>
        </div>
        <div className="border-t border-border pt-8 text-center">
          <p className="text-text-muted text-sm">
            MIT License &copy; 2026. Built with React, Tailwind CSS, Framer Motion.{' '}
            <a href="https://github.com/sudo-Harshk/k8-auto-scaling-self-healing" target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">
              View source on GitHub
            </a>
          </p>
          <p className="text-text-muted text-sm mt-2">
            Research prototype — not production software.{' '}
            <a href="https://github.com/sudo-Harshk/k8-auto-scaling-self-healing" target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">
              Reproducible artifacts
            </a>
          </p>
        </div>
      </div>
    </footer>
  )
}