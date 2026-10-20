import type { Metadata } from "next";
import "./globals.css";
import { MobileNav } from "@/components/mobile-nav";
import { ThemeToggle } from "@/components/theme-toggle";

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
						<a href="/" aria-label="AI Radar 首页" className="flex items-center gap-2">
							<span className="text-2xl font-bold tracking-tight">
								AI <span className="text-primary">Radar</span>
							</span>
						</a>
						<nav className="flex items-center gap-4" aria-label="主导航">
							<a
								href="/articles"
								aria-label="查看全部文章"
								className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
							>
								文章
							</a>
							<a
								href="/briefs"
								aria-label="查看每日简报"
								className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
							>
								每日简报
							</a>
							<a
								href="/about"
								aria-label="关于 AI Radar"
								className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
							>
								关于
							</a>
							<MobileNav />
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
