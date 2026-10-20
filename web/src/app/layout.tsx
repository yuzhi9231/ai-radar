import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Radar",
  description: "每日 AI 行业精选资讯，智能摘要，一键订阅",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className="min-h-screen bg-background text-foreground antialiased">
        <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 lg:px-8">
          <header className="mb-8 flex items-center justify-between border-b border-border pb-4">
            <a href="/" className="flex items-center gap-2">
              <span className="text-2xl font-bold tracking-tight">
                AI <span className="text-primary">Radar</span>
              </span>
            </a>
            <nav className="flex items-center gap-4">
              <a href="/articles" className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
                文章
              </a>
              <a href="/about" className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
                关于
              </a>
              <ThemeToggle />
            </nav>
          </header>
          <main>{children}</main>
          <footer className="mt-12 border-t border-border pt-6 text-center text-xs text-muted-foreground">
            Powered by AI Radar &middot; Phase 1
          </footer>
        </div>
      </body>
    </html>
  );
}

function ThemeToggle() {
  return (
    <button
      id="theme-toggle"
      aria-label="切换主题"
      onClick={() => {
        const root = document.documentElement;
        const isDark = root.classList.contains("dark");
        if (isDark) {
          root.classList.remove("dark");
          localStorage.setItem("theme", "light");
        } else {
          root.classList.add("dark");
          localStorage.setItem("theme", "dark");
        }
      }}
      className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-border bg-background text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
    >
      <span id="theme-icon-light" className="dark:hidden">🌙</span>
      <span id="theme-icon-dark" className="hidden dark:inline">☀️</span>
    </button>
  );
}
