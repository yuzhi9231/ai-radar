"use client";

export function ThemeToggle() {
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
			<span id="theme-icon-light" className="dark:hidden">
				🌙
			</span>
			<span id="theme-icon-dark" className="hidden dark:inline">
				☀️
			</span>
		</button>
	);
}
