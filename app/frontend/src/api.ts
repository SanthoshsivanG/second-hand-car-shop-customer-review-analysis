export type JourneyOpt = { id: string; label: string };

export type FilterOptions = {
  store_name: string[];
  satisfaction: string[];
  journey: JourneyOpt[];
  topic: string[];
};

export type HeatCell = {
  journey: string;
  journey_label: string;
  satisfaction: string;
  count: number;
};

export type TopicBubble = {
  topic_id: number;
  name: string;
  journey: string;
  size: number;
  avg_rating: number;
  document_count: number;
  keywords: string[];
};

export type Filters = {
  store_name: string[];
  satisfaction: string[];
  journey: string[];
  topic: string[];
};

function qs(filters: Filters, extra: Record<string, string> = {}): string {
  const p = new URLSearchParams();
  for (const [k, vals] of Object.entries(filters)) {
    for (const v of vals) p.append(k, v);
  }
  for (const [k, v] of Object.entries(extra)) p.append(k, v);
  const s = p.toString();
  return s ? `?${s}` : "";
}

async function get<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`;
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === "string") msg = body.detail;
    } catch {
      /* keep status text */
    }
    throw new Error(msg);
  }
  return res.json() as Promise<T>;
}

export const fetchFilters = (f: Filters) => get<FilterOptions>(`/api/filters${qs(f)}`);
export const fetchHeatmap = (f: Filters) =>
  get<{ cells: HeatCell[] }>(`/api/heatmap${qs(f)}`);
export const fetchTopics = (f: Filters, journey: string, satisfaction: string) =>
  get<{ topics: TopicBubble[]; journey_label: string }>(
    `/api/topics${qs({ ...f, satisfaction: [satisfaction] }, { journey })}`
  );

export type IdeaComment = {
  store_name: string;
  stars: number | null;
  review: string;
  char_len: number;
};

export type IdeaResponse = {
  id: number | null;
  mode: "keep" | "improve";
  journey: string;
  journey_label: string;
  topic: string;
  satisfaction: string;
  comments: IdeaComment[];
  ideas: string[];
};

export type PolicyResponse = {
  content: string;
  updated_at: string | null;
};

export const fetchIdeas = (
  f: Filters,
  journey: string,
  topic: string,
  satisfaction: string
) =>
  get<IdeaResponse>(
    `/api/ideas${qs(
      { store_name: f.store_name, satisfaction: [], journey: [], topic: [] },
      { journey, topic, satisfaction }
    )}`
  );

export const fetchPolicy = () => get<PolicyResponse>("/api/policy");

export async function updatePolicy(content: string): Promise<PolicyResponse> {
  const res = await fetch("/api/policy", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`;
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (typeof body.detail === "string") msg = body.detail;
    } catch {
      /* keep status text */
    }
    throw new Error(msg);
  }
  return res.json() as Promise<PolicyResponse>;
}
