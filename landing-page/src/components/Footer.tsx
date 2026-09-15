const githubUrl = 'https://github.com/sudo-Harshk/k8-auto-scaling-self-healing'

export function Footer() {
  return (
    <footer className="border-t border-white/10 py-8 mt-auto">
      <div className="max-w-6xl mx-auto px-6">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <span>© 2026 SHIELD-AI</span>
            <span>·</span>
            <span>MIT License</span>
          </div>
          <a
            href={githubUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-gray-500 hover:text-white transition-colors"
          >
            View on GitHub
          </a>
        </div>
      </div>
    </footer>
  )
}
