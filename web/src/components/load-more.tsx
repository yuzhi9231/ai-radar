"use client";

import { Button } from "@/components/ui/button";
import { useState } from "react";

interface LoadMoreProps {
	total: number;
	loaded: number;
	limit: number;
	onLoadMore: () => Promise<void>;
}

export function LoadMore({ total, loaded, limit, onLoadMore }: LoadMoreProps) {
	const [loading, setLoading] = useState(false);

	const hasMore = loaded < total;

	const handleClick = async () => {
		if (loading || !hasMore) return;
		setLoading(true);
		try {
			await onLoadMore();
		} finally {
			setLoading(false);
		}
	};

	if (!hasMore) return null;

	return (
		<div className="flex justify-center pt-6">
			<Button
				variant="outline"
				size="lg"
				onClick={handleClick}
				disabled={loading}
			>
				{loading ? "加载中..." : `加载更多 (${loaded}/${total})`}
			</Button>
		</div>
	);
}
