import { Skeleton } from "@/components/ui/skeleton";

export function ArticleSkeleton({ count = 6 }: { count?: number }) {
	return (
		<div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
			{Array.from({ length: count }).map((_, i) => (
				<div key={i} className="rounded-lg border border-border p-4">
					<Skeleton className="mb-2 h-4 w-1/3" />
					<Skeleton className="mb-2 h-5 w-full" />
					<Skeleton className="mb-2 h-4 w-full" />
					<Skeleton className="h-4 w-2/3" />
				</div>
			))}
		</div>
	);
}
