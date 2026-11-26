import { useEffect, useState, type ReactNode } from 'react'

// SHIELD-AI project page: plain, GitHub-README style. Every number comes from
// a file in the repository (results_live/, specs/, Paper/REVIEW_EVIDENCE/).

const REPO = 'https://github.com/sudo-Harshk/k8-auto-scaling-self-healing'
const BRANCH = `${REPO}/tree/paper-revision-eval`
const file = (p: string) => `${REPO}/blob/paper-revision-eval/${p}`
const fig = (name: string) => `${import.meta.env.BASE_URL}fig/${name}`

const toc = [
  ['how', 'How it works'],
  ['verification', 'Formal verification'],
  ['results', 'Live results'],
  ['healing', 'Self-healing'],
  ['limits', 'Limitations'],
  ['reproduce', 'Reproduce'],
]

const layers = [
  ['Telemetry', 'Prometheus scrapes CPU, memory, request rate, error rate, p95 latency and replica count every 5 s; a producer publishes them to Kafka.'],
  ['Stream processing', 'A Faust worker averages the samples over 15 s windows into one feature record per window.'],
  ['Decision engine', 'A Hoeffding Adaptive Tree forecasts the replicas needed next window; Half-Space Trees score anomalies; a per-pod check looks for a pod that stopped serving.'],
  ['Safety shield', 'Every proposed action is clamped or rejected if it would break the policy below.'],
  ['Actuator', 'A Python operator re-reads the live replica count, runs the shield again, then scales the Deployment or deletes the faulty pod. Every outcome is audited.'],
]

const policy = [
  ['Allowed actions', 'scale, heal, noop', 'anything else is rejected'],
  ['Cooldown after scale-up', '15 s', 'react quickly to rising load'],
  ['Cooldown after scale-down or heal', '60 s', 'avoid flapping'],
  ['Step up', '≤ max(4, 100 % of current)', 'same as the HPA default'],
  ['Step down', '≤ 2 replicas', 'release capacity gradually'],
  ['Bounds', '2 ≤ replicas ≤ 20', 'same range for every controller'],
  ['Heal', 'target = current', 'healing never changes capacity'],
]

const tla = `SafetyMinReplicas == current_replicas >= MIN_REPLICAS
SafetyMaxReplicas == current_replicas <= MAX_REPLICAS
SafetyScalingStep == /\\ current_replicas - prev_replicas <= UpLimit(prev_replicas)
                     /\\ prev_replicas - current_replicas <= STEP_DOWN
SafetyHealNoScale == /\\ (decision = "heal" => target_replicas = current_replicas)
                     /\\ (last_applied = "heal" => current_replicas = prev_replicas)
SafetyBoundedRate == /\\ (last_applied = "up" => gap_at_apply >= COOLDOWN_UP)
                     /\\ (last_applied \\in {"down","heal"} => gap_at_apply >= COOLDOWN_DOWN)
LivenessEventuallyScaleUp == \\A n \\in MIN_REPLICAS..MAX_REPLICAS-1 :
    []((consecutive_overload >= 2 /\\ current_replicas = n) => <>(current_replicas > n))`

// mean ± SD over 5 seeds (results_live/analysis/RESULTS.md)
const main = [
  ['Spike', 'HPA', '45.5 ± 12.5', '34.0 ± 24.2', '23.6 ± 4.1', '0.6 ± 0.9'],
  ['', 'KEDA', '36.9 ± 14.4', '10.7 ± 11.2', '53.3 ± 7.5', '3.6 ± 0.5'],
  ['', 'MT (FIRM-inspired)', '26.1 ± 11.8', '7.4 ± 5.7', '80.8 ± 4.5', '0.6 ± 0.5'],
  ['', 'ML-only', '36.3 ± 9.5', '15.8 ± 14.0', '47.8 ± 8.1', '8.6 ± 3.4'],
  ['', 'SHIELD-AI', '24.3 ± 18.5', '8.3 ± 18.5', '79.6 ± 24.4', '0.0 ± 0.0'],
  ['Diurnal', 'HPA', '49.6 ± 6.4', '0.5 ± 0.4', '40.5 ± 11.7', '1.2 ± 0.8'],
  ['', 'KEDA', '33.1 ± 20.0', '0.1 ± 0.1', '64.1 ± 1.1', '5.0 ± 0.7'],
  ['', 'MT (FIRM-inspired)', '41.0 ± 18.6', '0.1 ± 0.1', '74.4 ± 3.2', '0.0 ± 0.0'],
  ['', 'ML-only', '31.5 ± 17.8', '0.2 ± 0.3', '65.1 ± 9.1', '11.8 ± 1.6'],
  ['', 'SHIELD-AI', '19.5 ± 23.6', '0.8 ± 1.7', '76.5 ± 10.3', '0.0 ± 0.0'],
  ['Bursty', 'HPA', '62.6 ± 13.1', '19.0 ± 15.8', '33.1 ± 6.2', '0.2 ± 0.4'],
  ['', 'KEDA', '35.7 ± 19.0', '8.8 ± 5.7', '70.5 ± 8.0', '1.6 ± 0.9'],
  ['', 'MT (FIRM-inspired)', '29.9 ± 10.7', '8.0 ± 2.6', '81.2 ± 5.4', '0.4 ± 0.5'],
  ['', 'ML-only', '45.9 ± 12.0', '5.9 ± 3.1', '63.1 ± 7.8', '15.4 ± 2.1'],
  ['', 'SHIELD-AI', '32.3 ± 14.5', '5.5 ± 5.1', '74.7 ± 15.6', '0.2 ± 0.4'],
]

// results_live/heal_analysis/HEAL_RESULTS.md
const heal = [
  ['SHIELD-AI, per-pod healing', '15', '10 (10)', '19.2', '18', '0 / 15'],
  ['SHIELD-AI, no healing', '15', '—', '7.5', '17', '6 / 15'],
  ['SHIELD-AI, anomaly-gated', '5', '0', '89.4', '234', '5 / 5'],
  ['HPA', '5', '—', '100', '235', '5 / 5'],
]

const limits = [
  ['One machine', 'All nodes are containers on one VM; node failures and network partitions are not tested.'],
  ['Two VM types', 'Seeds 1–3 and 4–5 of the scaling study ran on different VMs; comparisons are also made per seed.'],
  ['One workload', 'A single stateless service (podinfo); models trained on one 20-minute trace.'],
  ['FIRM-inspired baseline', 'The multi-threshold controller borrows FIRM’s signals, not its reinforcement-learning agent.'],
  ['Finite model', 'TLC checks bounded constants; the link to Python rests on conformance tests, not a refinement proof.'],
  ['One fault type', 'Self-healing was tested with a frozen pod at one load level.'],
]

type Theme = 'light' | 'dark'

function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(() =>
    (document.documentElement.dataset.theme as Theme) ||
    (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'))
  useEffect(() => {
    document.documentElement.dataset.theme = theme
    try { localStorage.setItem('theme', theme) } catch { /* private mode */ }
  }, [theme])
  const next = theme === 'dark' ? 'light' : 'dark'
  return (
    <button className="toggle" type="button" onClick={() => setTheme(next)} aria-label={`Switch to ${next} mode`}>
      {theme === 'dark' ? '☀ Light' : '☾ Dark'}
    </button>
  )
}

function Figure({ src, alt, caption }: { src: string; alt: string; caption: ReactNode }) {
  return (
    <figure>
      <a href={fig(src)}><img src={fig(src)} alt={alt} loading="lazy" /></a>
      <figcaption>{caption}</figcaption>
    </figure>
  )
}

function Table({ head, rows, numFrom = 99, hl }: { head: string[]; rows: string[][]; numFrom?: number; hl?: (r: string[]) => boolean }) {
  return (
    <div className="table-wrap">
      <table>
        <thead><tr>{head.map((h, i) => <th key={h} className={i >= numFrom ? 'num' : undefined}>{h}</th>)}</tr></thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className={hl?.(r) ? 'hl' : undefined}>
              {r.map((c, j) => <td key={j} className={j >= numFrom ? 'num' : undefined}>{c}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const H2 = ({ id, children }: { id: string; children: ReactNode }) => (
  <h2 id={id}><a className="anchor" href={`#${id}`} aria-hidden="true">#</a>{children}</h2>
)

export default function App() {
  return (
    <>
      <header className="topbar">
        <div className="container topbar-row">
          <a className="repo" href={REPO}>sudo-Harshk / <strong>k8-auto-scaling-self-healing</strong></a>
          <div className="topbar-end">
            <ThemeToggle />
            <a className="btn" href={BRANCH}>View on GitHub</a>
          </div>
        </div>
      </header>

      <main className="container markdown">
        <h1 id="top">SHIELD-AI</h1>
        <p className="subtitle">Safe online-learning autoscaling and self-healing for Kubernetes</p>
        <p>
          A learned model proposes scaling and healing actions. A runtime shield, model-checked in TLA+
          against an untrusted model, decides which of them reach the cluster.
        </p>
        <p className="badges">
          <span>Kubernetes</span><span>Online learning</span><span>TLA+</span><span>MIT License</span>
        </p>

        <h3>Key numbers</h3>
        <ul>
          <li><strong>2,535,840</strong> states model-checked by TLC, no violation of 5 invariants and 2 action properties.</li>
          <li><strong>7 / 7</strong> mutants caught: removing any one shield rule breaks its property.</li>
          <li><strong>178 / 179</strong> unsafe changes removed (same model with vs. without the shield, 15 live runs).</li>
          <li><strong>75</strong> live runs: 5 controllers × 3 load scenarios × 5 seeds.</li>
        </ul>

        <nav className="toc" aria-label="Contents">
          <strong>Contents</strong>
          <ol>{toc.map(([id, l]) => <li key={id}><a href={`#${id}`}>{l}</a></li>)}</ol>
        </nav>

        <H2 id="how">How it works</H2>
        <p>
          Rule-based autoscalers follow one signal through a fixed rule and treat a broken pod like a busy one. A learned
          controller can do better, but nothing stops it from scaling to zero, jumping by many pods or flipping back and
          forth. SHIELD-AI keeps the model and puts a verified boundary around it.
        </p>
        <Figure src="fig1_architecture.png"
          alt="Five layers connected by Kafka topics: telemetry, stream processing, decision engine, safety shield, actuator."
          caption="Figure 1. Five layers connected by Kafka topics. The actuator repeats the shield check with the live replica count before it calls the Kubernetes API." />
        <ol>{layers.map(([t, d]) => <li key={t}><strong>{t}.</strong> {d}</li>)}</ol>
        <h3>Safety policy enforced by the shield</h3>
        <Table head={['Rule', 'Value', 'Purpose']} rows={policy} />

        <H2 id="verification">Formal verification</H2>
        <p>
          The TLA+ model leaves the ML output unconstrained: any value from 0 to 25 replicas. TLC explores every state,
          and mutation testing shows each property actually guards its rule.
        </p>
        <ul>
          <li><strong>2,535,840 states, no violation</strong> — 5 invariants and 2 action properties; replicas 2–20; depth 28; 68 s.</li>
          <li><strong>Always scales up under overload</strong> — liveness verified on 234,639 states, under fairness for time and scale-up.</li>
          <li><strong>7 / 7 mutants caught</strong> — remove any one rule and TLC finds a violation. Without the shield, the model proposes 0 replicas.</li>
        </ul>
        <p className="code-label"><code>specs/SafetyShieldV2.tla</code></p>
        <pre><code>{tla}</code></pre>
        <p>
          The Python shield applies the same rules in the same order; twelve conformance tests map one-to-one to the
          TLA+ properties. A check takes a median of 55 µs. Decision-to-actuation median: 529 ms with the shield, 537 ms without.
        </p>

        <H2 id="results">Live results</H2>
        <p>
          Five controllers, three 360 s load scenarios, five seeds each, on a four-node kind cluster. The peak needs about
          16 of 20 replicas, so every controller misses the latency objective for part of each run.
        </p>
        <p className="caption">Table 1. Mean ± SD over 5 seeds.</p>
        <Table head={['Scenario', 'Controller', 'SLO violation %', 'Error %', 'Replica-minutes', 'Policy violations']}
          rows={main} numFrom={2} hl={(r) => r[1] === 'SHIELD-AI'} />
        <Figure src="timeline_spike.png"
          alt="Spike scenario: replica count of each controller against demand, and p95 latency against the 250 ms objective."
          caption="Figure 2. Spike scenario: replicas per controller (mean and min–max over 5 seeds) against demand, and p95 latency against the 250 ms objective." />
        <blockquote>
          <p><strong>What the statistics support.</strong> With Holm-corrected Mann–Whitney tests at n = 5, SHIELD-AI
            under-provisions significantly less than HPA, and the shield significantly cuts policy violations and scale
            events versus the same model without it. SHIELD-AI had lower SLO-violation time than HPA in all 15
            seed–scenario pairs, but that difference does not survive correction. Latency and SLO are on par with KEDA and
            the multi-threshold controller, at a higher replica cost than HPA.</p>
        </blockquote>
        <Figure src="bar_policy_viol.png" alt="Bar chart of policy-violating replica changes per run."
          caption="Figure 3. Policy-violating changes per run. Without the shield: 179 in 15 runs. With it: 1." />
        <Figure src="fig_anomaly_roc_pr.png" alt="ROC and precision-recall curves of the anomaly detector."
          caption="Figure 4. Anomaly detector: ROC-AUC 0.806. At its threshold, no false alarms but 22 % recall." />

        <H2 id="healing">Self-healing</H2>
        <p>
          One pod is frozen 60 s into constant load. Healing and no-healing arms ran 15 times each, with a test plan fixed
          in writing before the extension runs.
        </p>
        <ul>
          <li><strong>10 / 10 heals on the right pod</strong>, 22–66 s after the fault. The aggregate anomaly score never noticed a single frozen pod.</li>
          <li><strong>0 false heals</strong> in the 15 fault-free runs.</li>
          <li><strong>No faster recovery</strong>: 18 s vs 17 s, p = 0.95. Kubernetes’ own scale-down removes unready pods first, which removed the frozen pod in 9 of 15 runs without healing.</li>
        </ul>
        <p className="caption">Table 2. Fault runs (medians).</p>
        <Table head={['Variant', 'Runs', 'Heals (on frozen pod)', 'SLO violation %', 'Time to recover (s)', 'Frozen pod left at end']}
          rows={heal} numFrom={1} />
        <Figure src="fig_heal.png" alt="Dot plot of SLO-violation time and recovery time per fault run."
          caption="Figure 5. Fault runs, one dot per run; the bar marks the median." />
        <p>
          Two heals were blocked by the shield's shared cooldown right after a scale action. Five runs whose injection
          failed were excluded, fixed and repeated; the failed runs and the deviation log are in the repository.
        </p>

        <H2 id="limits">Limitations</H2>
        <ul>{limits.map(([t, d]) => <li key={t}><strong>{t}.</strong> {d}</li>)}</ul>

        <H2 id="reproduce">Reproduce</H2>
        <p>
          Code, TLA+ specifications, TLC outputs, raw data of every run and the analysis scripts are public. The{' '}
          <a href={file('Paper/REVIEW_EVIDENCE/README.md')}>evidence index</a> maps each number to the file and command that produced it.
        </p>
        <pre><code>{`bash scripts/eval/live/setup_cluster.sh     # kind cluster, Prometheus, KEDA, Kafka, podinfo
bash scripts/eval/live/calibrate.sh         # per-replica capacity
bash scripts/eval/live/train_ml.sh          # train on a separate trace
SEEDS="1 2 3 4 5" bash scripts/eval/live/run_matrix.sh
python scripts/eval/live/analyze.py results_live/runs results_live/analysis

cd specs && java -cp ../tools/tla2tools.jar tlc2.TLC \\
  -config SafetyShieldV2_safety.cfg SafetyShieldV2.tla`}</code></pre>
      </main>

      <footer className="container footer">
        SHIELD-AI · MIT License · <a href={REPO}>github.com/sudo-Harshk/k8-auto-scaling-self-healing</a>
      </footer>
    </>
  )
}
