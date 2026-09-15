import { Header } from '@/components/Header'
import { Sidebar } from '@/components/Sidebar'
import { Content } from '@/components/Content'
import { Footer } from '@/components/Footer'

const sections = [
  { id: 'about', label: 'About' },
  { id: 'stats', label: 'Stats' },
  { id: 'features', label: 'Features' },
  { id: 'architecture', label: 'Architecture' },
  { id: 'safety', label: 'Safety' },
  { id: 'why', label: 'Why SHIELD-AI' },
  { id: 'stack', label: 'Tech Stack' },
  { id: 'start', label: 'Get Started' },
]

export default function App() {
  return (
    <div className="min-h-screen bg-[#0D0D0D] text-white flex flex-col">
      <Header />
      <div className="flex-1 flex max-w-6xl mx-auto w-full px-6 py-8 gap-12">
        <Sidebar sections={sections} />
        <Content />
      </div>
      <Footer />
    </div>
  )
}
