import { useEffect, useState } from "react";
import {
  fetchFilters,
  fetchHeatmap,
  fetchIdeas,
  fetchTopics,
  type FilterOptions,
  type Filters,
  type HeatCell,
  type IdeaResponse,
  type TopicBubble,
} from "./api";
import FilterSidebar from "./components/FilterSidebar";
import Heatmap from "./components/Heatmap";
import IdeaModal from "./components/IdeaModal";
import PolicyEditor from "./components/PolicyEditor";
import TopicBubbles from "./components/TopicBubbles";

const emptyFilters = (): Filters => ({
  store_name: [],
  satisfaction: [],
  journey: [],
  topic: [],
});

function sameList(a: string[], b: string[]): boolean {
  if (a.length !== b.length) return false;
  return a.every((v, i) => v === b[i]);
}

function pruneFilters(filters: Filters, options: FilterOptions): Filters | null {
  const storeSet = new Set(options.store_name);
  const satSet = new Set(options.satisfaction);
  const journeySet = new Set(options.journey.map((j) => j.id));
  const topicSet = new Set(options.topic);

  const next: Filters = {
    store_name: filters.store_name.filter((s) => storeSet.has(s)),
    satisfaction: filters.satisfaction.filter((s) => satSet.has(s)),
    journey: filters.journey.filter((j) => journeySet.has(j)),
    topic: filters.topic.filter((t) => topicSet.has(t)),
  };

  const changed =
    !sameList(next.store_name, filters.store_name) ||
    !sameList(next.satisfaction, filters.satisfaction) ||
    !sameList(next.journey, filters.journey) ||
    !sameList(next.topic, filters.topic);

  return changed ? next : null;
}

export default function App() {
  const [filters, setFilters] = useState<Filters>(emptyFilters);
  const [options, setOptions] = useState<FilterOptions | null>(null);
  const [cells, setCells] = useState<HeatCell[]>([]);
  const [topics, setTopics] = useState<TopicBubble[]>([]);
  const [topicTitle, setTopicTitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [ideaOpen, setIdeaOpen] = useState(false);
  const [ideaLoading, setIdeaLoading] = useState(false);
  const [ideaError, setIdeaError] = useState<string | null>(null);
  const [ideaData, setIdeaData] = useState<IdeaResponse | null>(null);
  const [ideaTopicName, setIdeaTopicName] = useState("");
  const [policyOpen, setPolicyOpen] = useState(false);

  const selected =
    filters.journey.length === 1 && filters.satisfaction.length === 1
      ? { journey: filters.journey[0], satisfaction: filters.satisfaction[0] }
      : null;

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all([fetchFilters(filters), fetchHeatmap(filters)])
      .then(([opts, heat]) => {
        if (cancelled) return;
        setOptions(opts);
        setCells(heat.cells);
        const pruned = pruneFilters(filters, opts);
        if (pruned) setFilters(pruned);
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [filters]);

  useEffect(() => {
    if (!selected) {
      setTopics([]);
      setTopicTitle("");
      return;
    }
    let cancelled = false;
    fetchTopics(filters, selected.journey, selected.satisfaction)
      .then((res) => {
        if (cancelled) return;
        setTopics(res.topics);
        const sat = selected.satisfaction === "positive" ? "Positive" : "Negative";
        setTopicTitle(`${res.journey_label} · ${sat}`);
      })
      .catch((e: Error) => {
        if (!cancelled) setError(e.message);
      });
    return () => {
      cancelled = true;
    };
  }, [selected?.journey, selected?.satisfaction, filters]);

  const handleCellSelect = (cell: { journey: string; satisfaction: string }) => {
    const same =
      filters.journey.length === 1 &&
      filters.journey[0] === cell.journey &&
      filters.satisfaction.length === 1 &&
      filters.satisfaction[0] === cell.satisfaction;

    if (same) {
      setFilters({
        ...filters,
        journey: [],
        satisfaction: [],
        topic: [],
      });
      return;
    }

    setFilters({
      ...filters,
      journey: [cell.journey],
      satisfaction: [cell.satisfaction],
      topic: [],
    });
  };

  const handleFilterChange = (next: Filters) => {
    const journeyChanged = !sameList(next.journey, filters.journey);
    const satChanged = !sameList(next.satisfaction, filters.satisfaction);
    setFilters({
      ...next,
      topic: journeyChanged || satChanged ? [] : next.topic,
    });
  };

  const handleTopicClick = (topic: TopicBubble) => {
    if (!selected) return;
    setIdeaOpen(true);
    setIdeaLoading(true);
    setIdeaError(null);
    setIdeaData(null);
    setIdeaTopicName(topic.name);
    fetchIdeas(filters, selected.journey, topic.name, selected.satisfaction)
      .then((res) => setIdeaData(res))
      .catch((e: Error) => setIdeaError(e.message))
      .finally(() => setIdeaLoading(false));
  };

  return (
    <div className="app">
      <header className="top">
        <h1>Customer Review Dashboard</h1>
        <button type="button" className="policy-btn" onClick={() => setPolicyOpen(true)}>
          Edit policy
        </button>
      </header>
      <div className="body">
        <FilterSidebar
          options={options}
          filters={filters}
          onChange={handleFilterChange}
        />
        <main className="main">
          {error && <p className="error">Failed to load: {error}</p>}
          {loading && <p className="muted">Loading…</p>}
          <Heatmap cells={cells} selected={selected} onSelect={handleCellSelect} />
          {selected && (
            <TopicBubbles
              topics={topics}
              title={topicTitle}
              satisfaction={
                selected.satisfaction === "positive" ? "positive" : "negative"
              }
              onTopicClick={handleTopicClick}
            />
          )}
        </main>
      </div>

      <IdeaModal
        open={ideaOpen}
        loading={ideaLoading}
        error={ideaError}
        data={ideaData}
        topicName={ideaTopicName}
        onClose={() => setIdeaOpen(false)}
      />
      <PolicyEditor open={policyOpen} onClose={() => setPolicyOpen(false)} />
    </div>
  );
}
