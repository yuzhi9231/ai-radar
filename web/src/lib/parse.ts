/** Parse a JSON column that may be missing or corrupt. */
export function parseJsonArray(value: unknown): string[] {
	if (typeof value !== "string" || !value) {
		return [];
	}
	try {
		const parsed = JSON.parse(value);
		return Array.isArray(parsed) ? (parsed as string[]) : [];
	} catch {
		return [];
	}
}

/** Parse a JSON column that holds an array of objects (brief highlights, dev focus). */
export function parseObjectArray(value: unknown): Record<string, unknown>[] {
	if (typeof value !== "string" || !value) {
		return [];
	}
	try {
		const parsed = JSON.parse(value);
		return Array.isArray(parsed)
			? parsed.filter(
					(v): v is Record<string, unknown> =>
						typeof v === "object" && v !== null,
				)
			: [];
	} catch {
		return [];
	}
}

/** Age of the newest stored article in hours, or null when the DB has no articles. */
export function dataAgeHours(lastFetchedAt: unknown): number | null {
	if (typeof lastFetchedAt !== "string" || !lastFetchedAt) {
		return null;
	}
	const fetched = new Date(lastFetchedAt).getTime();
	if (Number.isNaN(fetched)) {
		return null;
	}
	return Math.max(0, Math.round((Date.now() - fetched) / 3600000));
}
