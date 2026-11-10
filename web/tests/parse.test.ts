/**
 * Tests for the JSON column parsers used by the API routes.
 * A corrupt or missing column must return an empty array, never throw.
 */

import { dataAgeHours, parseJsonArray, parseObjectArray } from "@/lib/parse";

describe("parseJsonArray", () => {
	it("returns the array for a valid JSON column", () => {
		expect(parseJsonArray('["ai", "policy"]')).toEqual(["ai", "policy"]);
	});

	it("returns [] for a missing value", () => {
		expect(parseJsonArray(null)).toEqual([]);
		expect(parseJsonArray(undefined)).toEqual([]);
		expect(parseJsonArray("")).toEqual([]);
	});

	it("returns [] for corrupt JSON instead of throwing", () => {
		expect(parseJsonArray('["ai",')).toEqual([]);
	});

	it("returns [] when the column is not an array", () => {
		expect(parseJsonArray('{"tags": ["ai"]}')).toEqual([]);
	});
});

describe("parseObjectArray", () => {
	it("returns the objects for a valid JSON column", () => {
		expect(parseObjectArray('[{"headline": "a", "summary": "b"}]')).toEqual([
			{ headline: "a", summary: "b" },
		]);
	});

	it("drops entries that are not objects", () => {
		expect(parseObjectArray('[{"headline": "a"}, "text", null, 3]')).toEqual([
			{ headline: "a" },
		]);
	});

	it("returns [] for corrupt JSON instead of throwing", () => {
		expect(parseObjectArray("[{headline:")).toEqual([]);
		expect(parseObjectArray(null)).toEqual([]);
	});
});

describe("dataAgeHours", () => {
	it("returns null when there is no timestamp", () => {
		expect(dataAgeHours(null)).toBeNull();
		expect(dataAgeHours("")).toBeNull();
	});

	it("returns null for an unreadable timestamp", () => {
		expect(dataAgeHours("not a date")).toBeNull();
	});

	it("measures the age of the newest stored article", () => {
		const fiveHoursAgo = new Date(Date.now() - 5 * 3600000).toISOString();
		expect(dataAgeHours(fiveHoursAgo)).toBe(5);
	});

	it("never reports a negative age for a future timestamp", () => {
		const inOneHour = new Date(Date.now() + 3600000).toISOString();
		expect(dataAgeHours(inOneHour)).toBe(0);
	});
});
