import { useEffect, useState } from 'react'
import { Menu, X } from 'lucide-react'

interface Section {
  id: string
  label: string
}

interface NavProps {
  sections: Section[]
}

export function Nav({ sections }: NavProps) {
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState<string>('')
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => {
      setScrolled(window.scrollY > 8)
    }
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    const onScroll = () => {
      const pos = window.scrollY + 120
      let current = sections[0]?.id ?? ''
      for (const section of sections) {
        const el = document.getElementById(section.id)
        if (el && el.offsetTop <= pos) {
          current = section.id
        }
      }
      setActive(current)
    }
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [sections])

  const goTo = (id: string) => {
    setOpen(false)
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }

  const closeOnEscape = (event: React.KeyboardEvent) => {
    if (event.key === 'Escape') {
      setOpen(false)
    }
  }

  return (
    <header
      className={`sticky top-0 z-50 transition-all duration-300 ${
        scrolled ? 'bg-white/95 backdrop-blur-sm shadow-sm' : 'bg-white/80 backdrop-blur-sm'
      }`}
      onKeyDown={closeOnEscape}
    >
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[60] focus:px-4 focus:py-2 focus:rounded-lg focus:bg-primary-600 focus:text-white focus:text-sm"
      >
        Skip to content
      </a>
      <div className="max-w-7xl mx-auto px-6 md:px-12 flex items-center justify-between h-16">
        <a
          href="#top"
          onClick={(e) => {
            e.preventDefault()
            window.scrollTo({ top: 0, behavior: 'smooth' })
          }}
          className="flex items-center gap-2 font-semibold text-text-primary"
        >
          <span className="w-8 h-8 rounded-lg bg-primary-600 text-white flex items-center justify-center text-sm font-bold">
            K
          </span>
          <span className="hidden sm:inline">K8s AI Operator</span>
        </a>

        <nav className="hidden lg:flex items-center gap-1" aria-label="Main navigation">
          {sections.map((section) => (
            <a
              key={section.id}
              href={`#${section.id}`}
              onClick={(e) => {
                e.preventDefault()
                goTo(section.id)
              }}
              className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                active === section.id
                  ? 'text-primary-700 bg-primary-50'
                  : 'text-text-secondary hover:text-text-primary hover:bg-surface-100'
              }`}
            >
              {section.label}
            </a>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <a
            href="https://github.com/sudo-Harshk/k8-auto-scaling-self-healing"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden md:inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 transition-colors"
          >
            View on GitHub
          </a>
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            className="lg:hidden inline-flex items-center justify-center w-10 h-10 rounded-lg text-text-secondary hover:bg-surface-100 transition-colors"
            aria-expanded={open}
            aria-label={open ? 'Close menu' : 'Open menu'}
          >
            {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {open && (
        <nav className="lg:hidden border-t border-border bg-white" aria-label="Mobile navigation">
          <ul className="py-2">
            {sections.map((section) => (
              <li key={section.id}>
                <a
                  href={`#${section.id}`}
                  onClick={(e) => {
                    e.preventDefault()
                    goTo(section.id)
                  }}
                  className={`block px-6 py-2.5 text-sm font-medium transition-colors ${
                    active === section.id
                      ? 'text-primary-700 bg-primary-50'
                      : 'text-text-secondary hover:bg-surface-100 hover:text-text-primary'
                  }`}
                >
                  {section.label}
                </a>
              </li>
            ))}
          </ul>
        </nav>
      )}
    </header>
  )
}