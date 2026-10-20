"use client";

import { cn } from "@/lib/cn";
import { useEffect, useState } from "react";

interface Source {
	name: string;
	enabled: number;
}

interface ArticleFilterBarProps {
	initialSource?: string;
	initialCategory?: string;
	initialSort?: "newest" | "oldest" | "importance";
	onFilterChange: (filters: {
		source: string | undefined;
		category: string | undefined;
		sort: "newest" | "oldest" | "importance";
	}) => void;
}

const categories = ["", "AI", "Industry", "Research", "Product", "Business"];

const sortOptions = [
	{ value: "newest", label: "最新" },
	{ value: "oldest", label: "最早" },
	{ value: "importance", label: "重要性" },
] as const;

const selectBase =
	"inline-flex h-9 appearance-none items-center rounded-md border border-transparent bg-transparent text-sm ring-offset-background transition-colors focus:border-ring focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 px-3 py-1.5";

export function ArticleFilterBar({
	initialSource = "",
	initialCategory = "",
	initialSort = "newest",
	onFilterChange,
}: ArticleFilterBarProps) {
	const [sources, setSources] = useState<Source[]>([]);
	const [selectedSource, setSelectedSource] = useState(initialSource || "");
	const [selectedCategory, setSelectedCategory] = useState(
		initialCategory || "",
	);
	const [selectedSort, setSelectedSort] = useState(initialSort);

	useEffect(() => {
		fetch("/api/sources")
			.then((res) => res.json())
			.then((data: Source[]) => setSources(data))
			.catch(() => setSources([]));
	}, []);

	const handleSourceChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
		const value = e.target.value;
		setSelectedSource(value);
		onFilterChange({
			source: value || undefined,
			category: selectedCategory || undefined,
			sort: selectedSort,
		});
	};

	const handleCategoryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
		const value = e.target.value;
		setSelectedCategory(value);
		onFilterChange({
			source: selectedSource || undefined,
			category: value || undefined,
			sort: selectedSort,
		});
	};

	const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
		const value = e.target.value as "newest" | "oldest" | "importance";
		setSelectedSort(value);
		onFilterChange({
			source: selectedSource || undefined,
			category: selectedCategory || undefined,
			sort: value,
		});
	};

	return (
		<div className="flex flex-wrap items-center gap-3">
			<div className="relative inline-flex items-center">
				<select
					className={cn(selectBase, "pr-7")}
					value={selectedSource}
					onChange={handleSourceChange}
				>
					<option value="">所有来源</option>
					{sources.map((s) => (
						<option key={s.name} value={s.name}>
							{s.name}
						</option>
					))}
				</select>
				<svg
					aria-hidden="true"
					className="absolute right-2 top-1/2 h-3 w-3 -translate-y-1/2 text-muted-foreground pointer-events-none"
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					strokeWidth="2"
					strokeLinecap="round"
					strokeLinejoin="round"
				>
					<path d="m6 9 6 6 6-6" />
				</svg>
			</div>

			<div className="relative inline-flex items-center">
				<select
					className={cn(selectBase, "pr-7")}
					value={selectedCategory}
					onChange={handleCategoryChange}
				>
					<option value="">所有分类</option>
					{categories.map((c) => (
						<option key={c} value={c}>
							{c || "不限"}
						</option>
					))}
				</select>
				<svg
					aria-hidden="true"
					className="absolute right-2 top-1/2 h-3 w-3 -translate-y-1/2 text-muted-foreground pointer-events-none"
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					strokeWidth="2"
					strokeLinecap="round"
					strokeLinejoin="round"
				>
					<path d="m6 9 6 6 6-6" />
				</svg>
			</div>

			<div className="relative inline-flex items-center">
				<select
					className={cn(selectBase, "pr-7")}
					value={selectedSort}
					onChange={handleSortChange}
				>
					{sortOptions.map((opt) => (
						<option key={opt.value} value={opt.value}>
							{opt.label}
						</option>
					))}
				</select>
				<svg
					aria-hidden="true"
					className="absolute right-2 top-1/2 h-3 w-3 -translate-y-1/2 text-muted-foreground pointer-events-none"
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					strokeWidth="2"
					strokeLinecap="round"
					strokeLinejoin="round"
				>
					<path d="m6 9 6 6 6-6" />
				</svg>
			</div>
		</div>
	);
}
