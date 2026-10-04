import { useMemo, useState, type CSSProperties } from "react";
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  Tooltip,
  ReferenceArea,
  ReferenceLine,
} from "recharts";
import type { TopicBubble } from "../api";

type QuadrantKey = "critical" | "highVolume" | "watch" | "lowPriority";

type Props = {
  topics: TopicBubble[];
  title: string;
  /** Heatmap cell sentiment: drives quadrant labels */
  satisfaction: "positive" | "negative";
  onTopicClick?: (topic: TopicBubble) => void;
};

const QUAD_NEG: Record<
  QuadrantKey,
  { fill: string; stroke: string; label: string; action: string }
> = {
  critical: {
    fill: "#ffebee",
    stroke: "#f44336",
    label: "Priority fix",
    action: "High volume · lower rating",
  },
  highVolume: {
    fill: "#fff3e0",
    stroke: "#ff9800",
    label: "High volume",
    action: "High volume · higher rating",
  },
  watch: {
    fill: "#fffde7",
    stroke: "#c9a227",
    label: "Watch",
    action: "Low volume · lower rating",
  },
  lowPriority: {
    fill: "#e8f5e9",
    stroke: "#4caf50",
    label: "Low priority",
    action: "Low volume · higher rating",
  },
};

const QUAD_POS: Record<
  QuadrantKey,
  { fill: string; stroke: string; label: string; action: string }
> = {
  critical: {
    fill: "#fff3e0",
    stroke: "#ff9800",
    label: "Improve",
    action: "High volume · lower rating",
  },
  highVolume: {
    fill: "#e8f5e9",
    stroke: "#4caf50",
    label: "Strength",
    action: "High volume · higher rating",
  },
  watch: {
    fill: "#e3f2fd",
    stroke: "#2196f3",
    label: "Watch",
    action: "Low volume · lower rating",
  },
  lowPriority: {
    fill: "#fffde7",
    stroke: "#c9a227",
    label: "Hidden strength",
    action: "Low volume · higher rating",
  },
};

function median(arr: number[]): number {
  if (arr.length === 0) return 1;
  const sorted = [...arr].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid]! : (sorted[mid - 1]! + sorted[mid]!) / 2;
}

function quadrant(
  x: number,
  y: number,
  ratingMedian: number,
  countMedian: number
): QuadrantKey {
  if (x < ratingMedian) return y >= countMedian ? "critical" : "watch";
  return y >= countMedian ? "highVolume" : "lowPriority";
}

type Row = TopicBubble & {
  x: number;
  y: number;
  z: number;
  quadrant: QuadrantKey;
};

export default function TopicBubbles({
  topics,
  title,
  satisfaction,
  onTopicClick,
}: Props) {
  const [selectedQuadrant, setSelectedQuadrant] = useState<QuadrantKey | null>(
    null
  );
  const quads = satisfaction === "positive" ? QUAD_POS : QUAD_NEG;

  const { data, ratingMedian, countMedian, xDomain, yDomain, zRange } =
    useMemo(() => {
      const usable = topics.filter((t) => t.size > 0 && t.avg_rating > 0);
      if (usable.length === 0) {
        return {
          data: [] as Row[],
          ratingMedian: 3,
          countMedian: 1,
          xDomain: [1, 5] as [number, number],
          yDomain: [1, 10] as [number, number],
          zRange: [60, 280] as [number, number],
        };
      }
      const counts = usable.map((t) => t.size);
      const ratings = usable.map((t) => t.avg_rating);
      const countMed = median(counts);
      const ratingMed = median(ratings);
      const minR = Math.min(...ratings);
      const maxR = Math.max(...ratings);
      // Extra room so large bubbles at extremes are not clipped.
      const xPad = Math.max((maxR - minR) * 0.28, 0.35);
      const xDomain: [number, number] = [
        Math.max(0.5, minR - xPad),
        Math.min(5.5, maxR + xPad),
      ];
      const minC = Math.max(1, Math.min(...counts));
      const maxC = Math.max(...counts);
      const yDomain: [number, number] = [
        Math.max(1, minC / 1.45),
        maxC * 1.45,
      ];
      const data: Row[] = usable.map((t) => ({
        ...t,
        x: t.avg_rating,
        y: t.size,
        z: t.size,
        quadrant: quadrant(t.avg_rating, t.size, ratingMed, countMed),
      }));
      return {
        data,
        ratingMedian: ratingMed,
        countMedian: countMed,
        xDomain,
        yDomain,
        zRange: [50, Math.min(300, 70 + (maxC - minC) * 2)] as [number, number],
      };
    }, [topics]);

  const visible = selectedQuadrant
    ? data.filter((d) => d.quadrant === selectedQuadrant)
    : data;

  if (topics.length === 0 || data.length === 0) {
    return (
      <section className="bubble-panel">
        <h3>{title}</h3>
        <p className="muted">No topics match the current filters.</p>
      </section>
    );
  }

  return (
    <section className="bubble-panel">
      <h3>{title}</h3>
      <p className="muted">
        4-quadrant topic map · X = average stars · Y = review count (log).
        Click a bubble or topic name for AI ideas.
      </p>
      <div className="bubble-chart tall">
        <ResponsiveContainer width="100%" height="100%">
          <ScatterChart margin={{ top: 36, right: 36, bottom: 40, left: 52 }}>
            <XAxis
              type="number"
              dataKey="x"
              domain={xDomain}
              name="Avg stars"
              tickCount={6}
              tickFormatter={(v: number) => Number(v).toFixed(1)}
              padding={{ left: 28, right: 28 }}
              label={{ value: "Average stars", position: "bottom", offset: 12 }}
            />
            <YAxis
              type="number"
              dataKey="y"
              scale="log"
              domain={yDomain}
              allowDataOverflow={false}
              name="Count"
              padding={{ top: 28, bottom: 28 }}
              tickFormatter={(v: number) => {
                const n = Number(v);
                return Number.isInteger(n) ? String(n) : n.toFixed(0);
              }}
              label={{ value: "Count", angle: -90, position: "insideLeft" }}
            />
            <ZAxis type="number" dataKey="z" range={zRange} />

            <ReferenceArea
              x1={xDomain[0]}
              x2={ratingMedian}
              y1={countMedian}
              y2={yDomain[1]}
              fill={quads.critical.fill}
              fillOpacity={0.65}
              label={{ value: quads.critical.label, position: "insideTopLeft" }}
              style={{ cursor: "pointer" }}
              onClick={() =>
                setSelectedQuadrant((p) => (p === "critical" ? null : "critical"))
              }
            />
            <ReferenceArea
              x1={ratingMedian}
              x2={xDomain[1]}
              y1={countMedian}
              y2={yDomain[1]}
              fill={quads.highVolume.fill}
              fillOpacity={0.65}
              label={{
                value: quads.highVolume.label,
                position: "insideTopRight",
              }}
              style={{ cursor: "pointer" }}
              onClick={() =>
                setSelectedQuadrant((p) =>
                  p === "highVolume" ? null : "highVolume"
                )
              }
            />
            <ReferenceArea
              x1={xDomain[0]}
              x2={ratingMedian}
              y1={yDomain[0]}
              y2={countMedian}
              fill={quads.watch.fill}
              fillOpacity={0.65}
              label={{ value: quads.watch.label, position: "insideBottomLeft" }}
              style={{ cursor: "pointer" }}
              onClick={() =>
                setSelectedQuadrant((p) => (p === "watch" ? null : "watch"))
              }
            />
            <ReferenceArea
              x1={ratingMedian}
              x2={xDomain[1]}
              y1={yDomain[0]}
              y2={countMedian}
              fill={quads.lowPriority.fill}
              fillOpacity={0.65}
              label={{
                value: quads.lowPriority.label,
                position: "insideBottomRight",
              }}
              style={{ cursor: "pointer" }}
              onClick={() =>
                setSelectedQuadrant((p) =>
                  p === "lowPriority" ? null : "lowPriority"
                )
              }
            />
            <ReferenceLine x={ratingMedian} stroke="#666" strokeDasharray="4 4" />
            <ReferenceLine y={countMedian} stroke="#666" strokeDasharray="4 4" />

            <Tooltip
              cursor={{ strokeDasharray: "3 3" }}
              content={({ payload }) => {
                const row = payload?.[0]?.payload as Row | undefined;
                if (!row) return null;
                return (
                  <div className="tooltip">
                    <strong>{row.name}</strong>
                    <div>Count: {row.size}</div>
                    <div>Avg stars: {row.avg_rating.toFixed(1)}</div>
                    <div>Zone: {quads[row.quadrant].label}</div>
                  </div>
                );
              }}
            />
            <Scatter
              data={visible}
              fill="#222"
              fillOpacity={0.85}
              cursor={onTopicClick ? "pointer" : "default"}
              onClick={(entry: { payload?: Row }) => {
                const row = entry?.payload;
                if (row && onTopicClick) onTopicClick(row);
              }}
            />
          </ScatterChart>
        </ResponsiveContainer>
      </div>

      <div className="quad-chips">
        {(Object.keys(quads) as QuadrantKey[]).map((k) => (
          <button
            key={k}
            type="button"
            className={`quad-chip${selectedQuadrant === k ? " active" : ""}`}
            style={
              {
                "--chip-bg": quads[k].fill,
                "--chip-stroke": quads[k].stroke,
              } as CSSProperties
            }
            onClick={() =>
              setSelectedQuadrant((prev) => (prev === k ? null : k))
            }
          >
            {quads[k].label}: {quads[k].action}
          </button>
        ))}
      </div>

      <ul className="topic-legend">
        {visible.map((t) => (
          <li key={`${t.journey}-${t.topic_id}`}>
            <button
              type="button"
              className="topic-link"
              onClick={() => onTopicClick?.(t)}
            >
              <span
                className="dot"
                style={{ background: quads[t.quadrant].stroke }}
              />
              {t.name}{" "}
              <em>
                ({t.size} · ★{t.avg_rating.toFixed(1)} ·{" "}
                {quads[t.quadrant].label})
              </em>
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
