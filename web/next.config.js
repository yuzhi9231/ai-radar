/** @type {import('next').NextConfig} */
const nextConfig = {
	output: "standalone",
	env: {
		DATABASE_URL: process.env.DATABASE_URL || "file:/data/ai-radar.db",
		DATABASE_PATH: process.env.DATABASE_PATH || "/data/ai-radar.db",
	},
};

module.exports = nextConfig;
