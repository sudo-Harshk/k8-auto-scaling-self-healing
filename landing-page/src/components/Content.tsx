import { Github, Shield, Cpu, Database, AlertTriangle, CheckCircle, XCircle } from 'lucide-react'

const githubUrl = 'https://github.com/sudo-Harshk/k8-auto-scaling-self-healing'

const features = [
  {
    icon: Cpu,
    title: 'Online Machine Learning',
    desc: 'River HTR + Half-Space-Trees for real-time workload prediction and anomaly detection.',
  },
  {
    icon: Shield,
    title: 'TLA+ Safety Shield',
    desc: 'Formally verified safety invariants. 273,702 reachable states checked, 0 violations.',
  },
  {
    icon: Database,
    title: 'Streaming Pipeline',
    desc: 'Prometheus → Kafka → Faust for real-time feature aggregation.',
  },
  {
    icon: AlertTriangle,
    title: 'Self-Healing',
    desc: 'Automatic failure detection and recovery with safety constraints.',
  },
]

const stats = [
  { value: '273,702', label: 'TLC Verified States' },
  { value: '53/53', label: 'Tests Passing' },
  { value: '0', label: 'Safety Violations' },
  { value: '10', label: 'Evaluation Trials' },
]

const architecture = [
  { name: 'Prometheus', desc: 'Metrics collection (10s scrape interval)' },
  { name: 'Kafka', desc: 'Streaming message bus (KRaft mode)' },
  { name: 'Faust', desc: '30-second windowed feature aggregation' },
  { name: 'River ML', desc: 'Hoeffding Adaptive Tree + Half-Space-Trees' },
  { name: 'Safety Shield', desc: 'TLA+ verified decision constraints' },
  { name: 'Kubernetes Operator', desc: 'Actuator for scale and heal actions' },
]

const invariants = [
  { name: 'Min Replicas', formula: 'replicas >= 1' },
  { name: 'Max Replicas', formula: 'replicas <= 10' },
  { name: 'Bounded Step', formula: '|new - old| <= 2' },
  { name: 'Heal Preserves', formula: 'heal => target = current' },
  { name: 'Cooldown', formula: '(clock - last) % 11 >= 6' },
]

export function Content() {
  return (
    <div className="flex-1 min-w-0">
      {/* Hero */}
      <section id="about" className="py-16 border-b border-white/10">
        <div className="max-w-2xl">
          <h1 className="text-4xl font-bold text-white mb-4">SHIELD-AI</h1>
          <p className="text-xl text-gray-400 mb-6">
            A Kubernetes operator that combines online ML with a formally verified safety shield.
          </p>
          <p className="text-gray-400 mb-8">
            ML proposes. The Safety Shield decides. Kubernetes executes.
          </p>
          <div className="flex flex-wrap gap-3">
            <a
              href={githubUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-[#F12525] text-white font-medium rounded-lg hover:bg-[#FF3A3A] transition-colors"
            >
              <Github className="w-4 h-4" />
              View on GitHub
            </a>
            <a
              href="#architecture"
              className="inline-flex items-center gap-2 px-5 py-2.5 bg-white/10 text-white font-medium rounded-lg hover:bg-white/20 transition-colors"
            >
              Learn More
            </a>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section id="stats" className="py-12 border-b border-white/10">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {stats.map((stat) => (
            <div key={stat.label}>
              <div className="text-3xl font-bold text-white">{stat.value}</div>
              <div className="text-sm text-gray-500 mt-1">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-12 border-b border-white/10">
        <h2 className="text-2xl font-bold text-white mb-6">Features</h2>
        <div className="grid md:grid-cols-2 gap-4">
          {features.map((feature) => (
            <div key={feature.title} className="p-4 rounded-lg bg-white/5">
              <div className="flex items-center gap-3 mb-2">
                <feature.icon className="w-5 h-5 text-[#F12525]" />
                <h3 className="font-semibold text-white">{feature.title}</h3>
              </div>
              <p className="text-sm text-gray-400">{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Architecture */}
      <section id="architecture" className="py-12 border-b border-white/10">
        <h2 className="text-2xl font-bold text-white mb-6">Architecture</h2>
        <div className="space-y-3">
          {architecture.map((item, i) => (
            <div key={item.name} className="flex items-start gap-3">
              <div className="flex items-center justify-center w-6 h-6 rounded-full bg-white/10 text-xs font-medium text-gray-400 flex-shrink-0 mt-0.5">
                {i + 1}
              </div>
              <div>
                <div className="font-medium text-white">{item.name}</div>
                <div className="text-sm text-gray-500">{item.desc}</div>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-6 flex items-center gap-2 text-sm text-gray-500">
          <span className="text-[#F12525]">→</span>
          <span>Kubernetes executes only verified actions</span>
        </div>
      </section>

      {/* Safety */}
      <section id="safety" className="py-12 border-b border-white/10">
        <h2 className="text-2xl font-bold text-white mb-6">Safety Shield</h2>
        <p className="text-gray-400 mb-6">
          Every ML recommendation passes through a TLA+-verified safety layer before reaching Kubernetes.
        </p>
        <div className="space-y-3">
          {invariants.map((inv) => (
            <div key={inv.name} className="flex items-center gap-4 p-3 rounded-lg bg-white/5">
              <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
              <span className="font-medium text-white w-32">{inv.name}</span>
              <code className="text-sm text-gray-400">{inv.formula}</code>
            </div>
          ))}
        </div>
        <div className="mt-6 p-4 rounded-lg bg-green-500/10 border border-green-500/30">
          <div className="flex items-center gap-2 text-green-400 font-medium">
            <CheckCircle className="w-5 h-5" />
            53 States · 0 Violations
          </div>
          <p className="text-sm text-gray-400 mt-1">
            With SHIELD-AI: 53 reachable states, zero safety violations.
            ML-only path: 93 states with multiple violations.
          </p>
        </div>
      </section>

      {/* Why */}
      <section id="why" className="py-12 border-b border-white/10">
        <h2 className="text-2xl font-bold text-white mb-6">Why SHIELD-AI?</h2>
        <div className="space-y-4">
          <div className="p-4 rounded-lg bg-white/5">
            <div className="flex items-start gap-3">
              <XCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-medium text-white">Pure ML Controllers Are Unsafe</div>
                <p className="text-sm text-gray-400 mt-1">
                  ML-only controllers can violate infrastructure constraints. In testing: 93 states with
                  multiple safety violations including out-of-bounds replica counts.
                </p>
              </div>
            </div>
          </div>
          <div className="p-4 rounded-lg bg-white/5">
            <div className="flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
              <div>
                <div className="font-medium text-white">SHIELD-AI Adds Formal Guarantees</div>
                <p className="text-sm text-gray-400 mt-1">
                  Every ML proposal is validated against TLA+ specifications. Out-of-bounds values are
                  clamped. Unsafe actions are rejected. 53 states, zero violations.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Tech Stack */}
      <section id="stack" className="py-12 border-b border-white/10">
        <h2 className="text-2xl font-bold text-white mb-6">Tech Stack</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-sm">
          {[
            ['Kubernetes', 'v1.30.0'],
            ['Python', '3.11'],
            ['River ML', '0.26.0'],
            ['Kafka', '3.9.1 KRaft'],
            ['Faust', '0.11.3'],
            ['TLA+ / TLC', '2026.08'],
            ['Prometheus', 'Latest'],
            ['Locust', '2.31.1'],
            ['53 Unit Tests', 'pytest'],
          ].map(([tech, version]) => (
            <div key={tech} className="flex justify-between p-3 rounded-lg bg-white/5">
              <span className="text-white">{tech}</span>
              <span className="text-gray-500">{version}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Get Started */}
      <section id="start" className="py-12">
        <h2 className="text-2xl font-bold text-white mb-6">Get Started</h2>
        <div className="space-y-4 text-gray-400">
          <p>Clone the repository and run the bootstrap script:</p>
          <pre className="p-4 rounded-lg bg-black/50 text-sm overflow-x-auto">
            <code>{`git clone https://github.com/sudo-Harshk/k8-auto-scaling-self-healing
cd k8-auto-scaling-self-healing
./bootstrap.sh`}</code>
          </pre>
          <p>Run the demo:</p>
          <pre className="p-4 rounded-lg bg-black/50 text-sm overflow-x-auto">
            <code>{`make demo          # Full 30-min demo
make demo-quick   # 2-min highlight run
make tla          # Verify safety shield`}</code>
          </pre>
        </div>
        <div className="mt-8">
          <a
            href={githubUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-6 py-3 bg-[#F12525] text-white font-medium rounded-lg hover:bg-[#FF3A3A] transition-colors"
          >
            <Github className="w-5 h-5" />
            View on GitHub
          </a>
        </div>
      </section>
    </div>
  )
}
