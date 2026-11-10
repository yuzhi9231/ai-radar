import { runStatusLabel } from "@/lib/utils";

describe("runStatusLabel", () => {
	it("labels the statuses the collector can write", () => {
		expect(runStatusLabel("success")).toBe("成功");
		expect(runStatusLabel("partial_failure")).toBe("部分失败");
		expect(runStatusLabel("failed")).toBe("失败");
		expect(runStatusLabel("interrupted")).toBe("中断");
		expect(runStatusLabel("running")).toBe("运行中");
	});

	it("shows an unknown status as-is", () => {
		expect(runStatusLabel("some_new_status")).toBe("some_new_status");
	});
});
