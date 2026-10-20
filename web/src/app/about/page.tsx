import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AboutPage() {
  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight">关于 AI Radar</h1>
        <p className="text-muted-foreground">自动化 AI 行业情报收集与智能摘要</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>项目简介</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm leading-relaxed text-foreground/80">
          <p>
            AI Radar 是一个自动化 AI 行业新闻采集与智能摘要工具。它每日从 TechCrunch、The Verge、Hacker News 等来源收集 AI 相关报道，
            通过本地 AI 模型（Ollama）进行中文摘要、分类和重要性评分，最终生成结构化的每日简报。
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>架构</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 text-sm">
            <div className="flex items-start gap-3 rounded-lg bg-muted p-3">
              <span className="text-lg">📡</span>
              <div>
                <p className="font-medium">Collector (Python)</p>
                <p className="text-muted-foreground">RSS/API 采集 → 去重 → AI 加工 → SQLite 存储</p>
              </div>
            </div>
            <div className="flex items-start gap-3 rounded-lg bg-muted p-3">
              <span className="text-lg">💾</span>
              <div>
                <p className="font-medium">SQLite Database</p>
                <p className="text-muted-foreground">单文件数据库，Docker volume 持久化到 G 盘</p>
              </div>
            </div>
            <div className="flex items-start gap-3 rounded-lg bg-muted p-3">
              <span className="text-lg">🌐</span>
              <div>
                <p className="font-medium">Web (Next.js)</p>
                <p className="text-muted-foreground">App Router + Tailwind CSS，提供文章浏览、每日简报、深色模式</p>
              </div>
            </div>
            <div className="flex items-start gap-3 rounded-lg bg-muted p-3">
              <span className="text-lg">🤖</span>
              <div>
                <p className="font-medium">Ollama</p>
                <p className="text-muted-foreground">本地运行 Qwen3.6-35B-A3B，支持 Mock AI 模式</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>数据源</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex justify-between border-b border-border py-2">
            <span>TechCrunch AI</span>
            <span className="text-muted-foreground">RSS</span>
          </div>
          <div className="flex justify-between border-b border-border py-2">
            <span>The Verge AI</span>
            <span className="text-muted-foreground">RSS</span>
          </div>
          <div className="flex justify-between py-2">
            <span>Hacker News</span>
            <span className="text-muted-foreground">Algolia API</span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
