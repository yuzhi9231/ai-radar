/** @type {import('next').NextConfig} */
const nextConfig = {
	output: "standalone",
	// better-sqlite3 loads a native binding at runtime, which the bundler cannot
	// resolve, so it must stay external to the server bundle.
	serverExternalPackages: ["better-sqlite3"],
	env: {
		DATABASE_URL: process.env.DATABASE_URL || "file:/data/ai-radar.db",
		DATABASE_PATH: process.env.DATABASE_PATH || "/data/ai-radar.db",
	},
};

module.exports = nextConfig;
