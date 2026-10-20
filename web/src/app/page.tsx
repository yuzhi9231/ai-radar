import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getTodayBrief } from "@/lib/api-client";
import { formatDate } from "@/lib/utils";

export default async function HomePage() {
  const brief = await getTodayBrief();
  const today = new Date().toISOString().split("T")[0];

  if (!brief) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <h1 className="text-2xl font-semibold text-foreground">暂无今日简报</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          数据采集完成后将自动生成本日 AI 行业简报
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight">今日简报</h1>
        <p className="text-sm text-muted-foreground">{formatDate(today)}</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>趋势摘要</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="whitespace-pre-wrap leading-relaxed text-foreground/90">
            {brief.trend_summary || "暂无摘要"}
          </p>
        </CardContent>
      </Card>

      {brief.highlights.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-xl font-semibold">精选文章</h2>
          {brief.highlights.map((h: any, i: number) => (
            <Card key={i}>
              <CardHeader>
                <CardTitle className="text-base">{h.headline}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{h.summary}</p>
                <div className="mt-2 flex flex-wrap gap-1">
                  {(h.tags || []).map((tag: string) => (
                    <span
                      key={tag}
                      className="inline-block rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium text-secondary-foreground"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {brief.dev_focus.length > 0 && (
        <div className="space-y-3">
          <h2 className="text-xl font-semibold">开发者关注</h2>
          {brief.dev_focus.map((d: any, i: number) => (
            <Card key={i}>
              <CardHeader>
                <CardTitle className="text-base">{d.headline}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{d.summary}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
