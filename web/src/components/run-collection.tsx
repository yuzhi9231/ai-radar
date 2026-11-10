"use client";

import { Button } from "@/components/ui/button";
import { useState } from "react";

interface RunResponse {
	ok: boolean;
	error?: string;
	fetched?: number | null;
	new_articles?: number | null;
	processed_ok?: number | null;
	processed_failed?: number | null;
	status?: string | null;
}

interface RunCollectionProps {
	/** Called after a successful run so the caller can reload what it shows. */
	onFinished?: () => void;
}

export function RunCollection({ onFinished }: RunCollectionProps) {
	const [running, setRunning] = useState(false);
	const [message, setMessage] = useState<string | null>(null);

	const handleRun = async () => {
		if (running) return;
		setRunning(true);
		setMessage(null);

		try {
			const res = await fetch("/api/run", { method: "POST", cache: "no-store" });
			const data = (await res.json()) as RunResponse;

			if (!res.ok || !data.ok) {
				setMessage(data.error || `API ${res.status}`);
				return;
			}

			setMessage(
				`抓取 ${data.fetched ?? "?"} · 新增 ${data.new_articles ?? "?"} · 分析 ${data.processed_ok ?? "?"} 成功 / ${data.processed_failed ?? 0} 失败`,
			);
			onFinished?.();
		} catch (err) {
			setMessage(err instanceof Error ? err.message : "运行失败");
		} finally {
			setRunning(false);
		}
	};

	return (
		<div className="flex flex-wrap items-center gap-3">
			<Button
				variant="outline"
				size="sm"
				onClick={handleRun}
				disabled={running}
				title="运行一次采集 + 分析（调用本地模型）"
			>
				{running ? "正在运行..." : "跑一次"}
			</Button>
			{message && (
				<span className="text-sm text-muted-foreground">{message}</span>
			)}
		</div>
	);
}
