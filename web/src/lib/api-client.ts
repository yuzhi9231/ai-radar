/** Server-side API client that talks to the Next.js API routes. */

const BASE = "/api";

async function json<T>(url: string): Promise<T> {
  const res = await fetch(`${BASE}${url}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

export async function getAllArticles(): Promise<any[]> {
  return json<any[]>("/articles");
}

export async function getArticleById(id: string): Promise<any> {
  return json<any>(`/articles/${id}`);
}

export async function getSources(): Promise<any[]> {
  return json<any[]>("/sources");
}

export async function getStats(): Promise<any> {
  return json<any>("/stats");
}

export async function getTodayBrief(): Promise<any | null> {
  const today = new Date().toISOString().split("T")[0];
  const data = await json<any>(`/briefs?date=${today}`);
  return data.brief || null;
}
