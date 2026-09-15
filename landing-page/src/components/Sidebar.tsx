import { Github } from 'lucide-react'

interface SidebarProps {
  sections: { id: string; label: string }[]
}

export function Sidebar({ sections }: SidebarProps) {
  const scrollTo = (id: string) => {
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  return (
    <aside className="hidden lg:block w-48 flex-shrink-0">
      <nav className="sticky top-24 space-y-1">
        <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 px-3">Navigation</div>
        {sections.map((section) => (
          <button
            key={section.id}
            onClick={() => scrollTo(section.id)}
            className="block w-full text-left px-3 py-2 text-sm text-gray-400 hover:text-white hover:bg-white/5 rounded-lg transition-colors"
          >
            {section.label}
          </button>
        ))}
        <div className="pt-4 mt-4 border-t border-white/10 px-3">
          <a
            href="https://github.com/sudo-Harshk/k8-auto-scaling-self-healing"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-sm text-gray-400 hover:text-white"
          >
            <Github className="w-4 h-4" />
            View on GitHub
          </a>
        </div>
      </nav>
    </aside>
  )
}
