"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getAllArticles, getBriefByDate } from "@/lib/api-client";
import { formatDate } from "@/lib/utils";
import { useCallback, useEffect, useState } from "react";

type Brief = {
	trend_summary?: string;
	highlights: { headline: string; summary: string; tags?: string[] }[];
	dev_focus: { headline: string; summary: string; tags?: string[] }[];
} | null;

function SourceDistribution({ articles }: { articles: any[] }) {
	const counts: Record<string, number> = {};
	for (const a of articles) {
		counts[a.source_name] = (counts[a.source_name] || 0) + 1;
	}
	const total = articles.length;
	if (total === 0) return null;

	const maxCount = Math.max(...Object.values(counts));

	return (
		<Card>
			<CardHeader>
				<CardTitle>来源分布</CardTitle>
			</CardHeader>
			<CardContent className="space-y-3">
				{Object.entries(counts)
					.sort(([, a], [, b]) => b - a)
					.map(([name, count]) => (
						<div key={name} className="space-y-1">
							<div className="flex items-center justify-between text-sm">
								<span className="font-medium">{name}</span>
								<span className="text-muted-foreground">
									{count} 篇 ({Math.round((count / total) * 100)}%)
								</span>
							</div>
							<div className="h-2 w-full overflow-hidden rounded-full bg-muted">
								<div
									className="h-full rounded-full bg-primary transition-all"
									style={{
										width: `${(count / maxCount) * 100}%`,
									}}
								/>
							</div>
						</div>
					))}
			</CardContent>
		</Card>
	);
}

function BriefContent({ brief, date }: { brief: Brief; date: string }) {
	if (!brief) {
		return (
			<Card>
				<CardContent className="pt-6 text-center text-sm text-muted-foreground">
					当日暂无 AI 简报
				</CardContent>
			</Card>
		);
	}

	return (
		<div className="space-y-6">
			{/* Trend Summary */}
			{brief.trend_summary && (
				<Card>
					<CardHeader>
						<CardTitle>趋势摘要</CardTitle>
					</CardHeader>
					<CardContent>
						<p className="whitespace-pre-wrap leading-relaxed text-foreground/90">
							{brief.trend_summary}
						</p>
					</CardContent>
				</Card>
			)}

			{/* Highlights */}
			{brief.highlights.length > 0 && (
				<div className="space-y-3">
					<div className="flex items-center gap-2">
						<h2 className="text-xl font-semibold">精选文章</h2>
						<Badge variant="secondary" className="text-xs">
							Top {brief.highlights.length}
						</Badge>
					</div>
					{brief.highlights.map((h, i) => (
						<Card key={i}>
							<CardHeader className="pb-3">
								<CardTitle className="text-base flex items-start gap-2">
									<span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
										{i + 1}
									</span>
									<span className="flex-1">{h.headline}</span>
								</CardTitle>
							</CardHeader>
							<CardContent>
								<p className="text-sm text-muted-foreground">{h.summary}</p>
								{h.tags && h.tags.length > 0 && (
									<div className="mt-2 flex flex-wrap gap-1">
										{h.tags.map((tag) => (
											<Badge key={tag} variant="secondary" className="text-xs">
												{tag}
											</Badge>
										))}
									</div>
								)}
							</CardContent>
						</Card>
					))}
				</div>
			)}

			{/* Developer Focus */}
			{brief.dev_focus.length > 0 && (
				<div className="space-y-3">
					<h2 className="text-xl font-semibold">开发者关注</h2>
					{brief.dev_focus.map((d, i) => (
						<Card key={i}>
							<CardHeader className="pb-3">
								<CardTitle className="text-base">{d.headline}</CardTitle>
							</CardHeader>
							<CardContent>
								<p className="text-sm text-muted-foreground">{d.summary}</p>
								{d.tags && d.tags.length > 0 && (
									<div className="mt-2 flex flex-wrap gap-1">
										{d.tags.map((tag) => (
											<Badge key={tag} variant="secondary" className="text-xs">
												{tag}
											</Badge>
										))}
									</div>
								)}
							</CardContent>
						</Card>
					))}
				</div>
			)}
		</div>
	);
}

function LoadingState() {
	return (
		<div className="space-y-6">
			<div className="space-y-2">
				<Skeleton className="h-8 w-48" />
				<Skeleton className="h-4 w-32" />
			</div>
			<Skeleton className="h-32 w-full" />
			<Skeleton className="h-48 w-full" />
			<Skeleton className="h-32 w-full" />
		</div>
	);
}

export default function BriefsPage() {
	const [date, setDate] = useState<string>(
		new Date().toISOString().split("T")[0],
	);
	const [brief, setBrief] = useState<Brief | null>(null);
	const [articles, setArticles] = useState<any[]>([]);
	const [loading, setLoading] = useState(true);
	const [copied, setCopied] = useState(false);

	const loadBrief = useCallback(async (d: string) => {
		setLoading(true);
		try {
			const [briefData, articlesRes] = await Promise.all([
				getBriefByDate(d),
				getAllArticles({ sort: "importance", limit: 20, offset: 0 }),
			]);
			setBrief(briefData);
			setArticles(articlesRes.articles);
		} finally {
			setLoading(false);
		}
	}, []);

	useEffect(() => {
		loadBrief(date);
	}, [date, loadBrief]);

	const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		setDate(e.target.value);
	};

	const handleShare = async () => {
		const url = `${window.location.origin}/briefs?date=${date}`;
		try {
			await navigator.clipboard.writeText(url);
			setCopied(true);
			setTimeout(() => setCopied(false), 2000);
		} catch {
			// Fallback for older browsers
			const ta = document.createElement("textarea");
			ta.value = url;
			document.body.appendChild(ta);
			ta.select();
			document.execCommand("copy");
			document.body.removeChild(ta);
			setCopied(true);
			setTimeout(() => setCopied(false), 2000);
		}
	};

	const handleExport = () => {
		const lines: string[] = [];
		lines.push("# AI Radar 每日简报");
		lines.push(`日期：${formatDate(date)}`);
		lines.push("");

		if (brief?.trend_summary) {
			lines.push("## 趋势摘要");
			lines.push(brief.trend_summary);
			lines.push("");
		}

		if (brief?.highlights.length) {
			lines.push("## 精选文章");
			brief.highlights.forEach((h, i) => {
				lines.push(`### ${i + 1}. ${h.headline}`);
				lines.push(h.summary);
				if (h.tags?.length) {
					lines.push(`标签：${h.tags.join(", ")}`);
				}
				lines.push("");
			});
		}

		if (brief?.dev_focus.length) {
			lines.push("## 开发者关注");
			brief.dev_focus.forEach((d, i) => {
				lines.push(`### ${i + 1}. ${d.headline}`);
				lines.push(d.summary);
				if (d.tags?.length) {
					lines.push(`标签：${d.tags.join(", ")}`);
				}
				lines.push("");
			});
		}

		if (
			!brief?.trend_summary &&
			!brief?.highlights.length &&
			!brief?.dev_focus.length
		) {
			lines.push("当日暂无 AI 简报");
		}

		const blob = new Blob([lines.join("\n")], {
			type: "text/markdown;charset=utf-8",
		});
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = `ai-radar-brief-${date}.md`;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
	};

	return (
		<div className="space-y-6">
			{/* Header */}
			<div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
				<div className="space-y-1">
					<h1 className="text-3xl font-bold tracking-tight">每日简报</h1>
					<p className="text-sm text-muted-foreground">{formatDate(date)}</p>
				</div>
				<div className="flex items-center gap-2">
					<input
						type="date"
						value={date}
						onChange={handleDateChange}
						className="h-9 rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
					/>
					<Button variant="outline" size="sm" onClick={handleShare}>
						{copied ? "已复制" : "分享"}
					</Button>
					<Button variant="outline" size="sm" onClick={handleExport}>
						导出
					</Button>
				</div>
			</div>

			{loading ? (
				<LoadingState />
			) : (
				<>
					<BriefContent brief={brief} date={date} />
					<SourceDistribution articles={articles} />
				</>
			)}
		</div>
	);
}
