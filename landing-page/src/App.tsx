import { Nav } from '@/components/Nav'
import { Footer } from '@/components/Footer'
import { Hero } from '@/components/Hero'
import { Problem } from '@/components/Problem'
import { Architecture } from '@/components/Architecture'
import { Timeline } from '@/components/Timeline'
import { SafetyShield } from '@/components/SafetyShield'
import { Evaluation } from '@/components/Evaluation'
import { Ablation } from '@/components/Ablation'
import { V2Workload } from '@/components/V2Workload'
import { Honest } from '@/components/Honest'
import { Reproduce } from '@/components/Reproduce'
import { Artifacts } from '@/components/Artifacts'
import { Limitations } from '@/components/Limitations'

import { MotionConfig } from 'framer-motion'

const sections = [
  { id: 'problem', label: 'Problem' },
  { id: 'architecture', label: 'Architecture' },
  { id: 'timeline', label: 'Timeline' },
  { id: 'safety-shield', label: 'Safety Shield' },
  { id: 'evaluation', label: 'Evaluation' },
  { id: 'ablation', label: 'Ablation' },
  { id: 'v2-workload', label: 'v2 Workload' },
  { id: 'honest', label: 'Honest' },
  { id: 'reproduce', label: 'Reproduce' },
  { id: 'artifacts', label: 'Artifacts' },
  { id: 'limitations', label: 'Limitations' },
]

export default function App() {
  return (
    <MotionConfig reducedMotion="user">
      <div id="top" className="min-h-screen bg-surface-50">
      <Nav sections={sections} />
      <main id="main-content">
        <Hero />
        <Problem />
        <Architecture />
        <Timeline />
        <SafetyShield />
        <Evaluation />
        <Ablation />
        <V2Workload />
        <Honest />
        <Reproduce />
        <Artifacts />
        <Limitations />
      </main>
      <Footer />
      </div>
    </MotionConfig>
  )
}