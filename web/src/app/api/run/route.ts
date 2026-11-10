import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { NextResponse } from "next/server";

// The web layer only reads SQLite; the collector is a separate process. This route
// shells out to it, which works only when the collector lives on this machine.
// A full run is fetch + one model call per new article, so give it room: a slow
// network plus a couple of minutes of model time is normal.
const RUN_TIMEOUT_MS = 600_000;

// One run at a time: two concurrent pipelines would fight over the same SQLite file.
let running = false;

interface RunSummary {
	fetched: number | null;
	new_articles: number | null;
	processed_ok: number | null;
	processed_failed: number | null;
	status: string | null;
}

function collectorRoot(): string | null {
	const root = path.resolve(process.cwd(), "..");
	return fs.existsSync(path.join(root, "collector", "cli.py")) ? root : null;
}

// The CLI prints the summary as plain lines; read the numbers back out of them.
function parseSummary(stdout: string): RunSummary {
	const numberAfter = (label: string): number | null => {
		const match = stdout.match(new RegExp(`${label}:\\s*(\\d+)`));
		return match ? Number.parseInt(match[1], 10) : null;
	};

	const processed = stdout.match(
		/Processed:\s*(\d+)\s*ok\s*\/\s*(\d+)\s*failed/,
	);
	const status = stdout.match(/Status:\s*(\S+)/);

	return {
		fetched: numberAfter("Fetched"),
		new_articles: numberAfter("New"),
		processed_ok: processed ? Number.parseInt(processed[1], 10) : null,
		processed_failed: processed ? Number.parseInt(processed[2], 10) : null,
		status: status ? status[1] : null,
	};
}

function runCollector(root: string): Promise<RunSummary> {
	const python = process.env.COLLECTOR_PYTHON || "python";

	return new Promise((resolve, reject) => {
		const child = spawn(python, ["-m", "collector.cli", "run"], { cwd: root });
		let stdout = "";
		let stderr = "";

		child.stdout.on("data", (chunk) => {
			stdout += chunk;
		});
		child.stderr.on("data", (chunk) => {
			stderr += chunk;
		});

		const timer = setTimeout(() => {
			child.kill();
			reject(new Error(`运行超时（${Math.round(RUN_TIMEOUT_MS / 1000)} 秒）`));
		}, RUN_TIMEOUT_MS);

		child.on("error", (err) => {
			clearTimeout(timer);
			reject(err);
		});

		child.on("close", (code) => {
			clearTimeout(timer);
			if (code === 0) {
				resolve(parseSummary(stdout));
			} else {
				reject(
					new Error(
						stderr.trim() || `collector 退出码 ${code}（模型服务在跑吗？）`,
					),
				);
			}
		});
	});
}

export async function POST() {
	if (running) {
		return NextResponse.json(
			{ ok: false, error: "已经有一个运行在进行中" },
			{ status: 409 },
		);
	}

	const root = collectorRoot();
	if (!root) {
		return NextResponse.json(
			{
				ok: false,
				error:
					"这台机器上找不到 collector，请手动运行 python -m collector.cli run",
			},
			{ status: 503 },
		);
	}

	running = true;
	try {
		const summary = await runCollector(root);
		return NextResponse.json({ ok: true, ...summary });
	} catch (err) {
		const message = err instanceof Error ? err.message : String(err);
		console.error("POST /api/run error:", message);
		return NextResponse.json({ ok: false, error: message }, { status: 500 });
	} finally {
		running = false;
	}
}
