import { Badge } from "@/components/ui/badge";

const VERSION = "0.1.0";

export function AppVersion() {
	return (
		<Badge variant="secondary" className="font-mono">
			v{VERSION}
		</Badge>
	);
}
