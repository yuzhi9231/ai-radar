import * as React from "react";
import { cn } from "@/lib/cn";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
	variant?: "default" | "secondary" | "destructive" | "outline";
}

const variantClasses = {
	default: "border-transparent bg-primary text-primary-foreground",
	secondary: "border-transparent bg-secondary text-secondary-foreground",
	destructive: "border-transparent bg-destructive text-destructive-foreground",
	outline: "text-foreground",
};

export function Badge({
	className,
	variant = "default",
	...props
}: BadgeProps) {
	return (
		<div
			className={cn(
				"inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors",
				variantClasses[variant],
				className,
			)}
			{...props}
		/>
	);
}
