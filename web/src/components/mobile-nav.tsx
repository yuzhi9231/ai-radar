"use client";

import { useState } from "react";

const navItems = [
	{ href: "/", label: "首页" },
	{ href: "/articles", label: "文章" },
	{ href: "/briefs", label: "每日简报" },
	{ href: "/about", label: "关于" },
];

export function MobileNav() {
	const [open, setOpen] = useState(false);

	return (
		<>
			{/* Hamburger button */}
			<button
				type="button"
				aria-label={open ? "关闭菜单" : "打开菜单"}
				aria-expanded={open}
				onClick={() => setOpen(!open)}
				className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-border bg-background text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground md:hidden"
			>
				{open ? "✕" : "☰"}
			</button>

			{/* Full-screen overlay */}
			{open && (
				<div
					className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm md:hidden"
					onClick={() => setOpen(false)}
					onKeyDown={(e) => {
						if (e.key === "Escape" || e.key === "Enter") setOpen(false);
					}}
					role="button"
					tabIndex={0}
					aria-hidden="true"
				>
					<nav
						className="mt-24 flex flex-col items-center gap-6 text-lg"
						aria-label="移动导航"
					>
						{navItems.map((item) => (
							<a
								key={item.href}
								href={item.href}
								onClick={() => setOpen(false)}
								className="text-muted-foreground transition-colors hover:text-foreground"
							>
								{item.label}
							</a>
						))}
					</nav>
				</div>
			)}
		</>
	);
}
