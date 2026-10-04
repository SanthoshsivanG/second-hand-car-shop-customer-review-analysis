import type { HeatCell } from "../api";

const JOURNEY_ORDER = ["pre_visit", "sales", "contract", "after_sales"];
const SENTIMENTS = ["positive", "negative"] as const;

type Selected = { journey: string; satisfaction: string } | null;

type Props = {
  cells: HeatCell[];
  selected: Selected;
  onSelect: (cell: { journey: string; satisfaction: string }) => void;
};

function intensity(count: number, max: number): number {
  if (max <= 0 || count <= 0) return 0.08;
  return 0.2 + 0.75 * (count / max);
}

function cellColor(sat: string, count: number, max: number): string {
  const a = intensity(count, max);
  if (sat === "positive") return `rgba(34, 140, 72, ${a})`;
  return `rgba(196, 48, 48, ${a})`;
}

export default function Heatmap({ cells, selected, onSelect }: Props) {
  const map = new Map(cells.map((c) => [`${c.journey}|${c.satisfaction}`, c]));
  const maxPos = Math.max(
    0,
    ...cells.filter((c) => c.satisfaction === "positive").map((c) => c.count)
  );
  const maxNeg = Math.max(
    0,
    ...cells.filter((c) => c.satisfaction === "negative").map((c) => c.count)
  );

  return (
    <div className="heatmap-wrap">
      <table className="heatmap">
        <thead>
          <tr>
            <th>Journey</th>
            <th>Positive</th>
            <th>Negative</th>
          </tr>
        </thead>
        <tbody>
          {JOURNEY_ORDER.map((journey) => {
            const label =
              map.get(`${journey}|positive`)?.journey_label ??
              journey.replace("_", "-");
            return (
              <tr key={journey}>
                <th scope="row">{label}</th>
                {SENTIMENTS.map((sat) => {
                  const cell = map.get(`${journey}|${sat}`);
                  const count = cell?.count ?? 0;
                  const max = sat === "positive" ? maxPos : maxNeg;
                  const isSel =
                    selected?.journey === journey && selected?.satisfaction === sat;
                  return (
                    <td key={sat}>
                      <button
                        type="button"
                        className={`heat-cell${isSel ? " selected" : ""}`}
                        style={{ background: cellColor(sat, count, max) }}
                        onClick={() => onSelect({ journey, satisfaction: sat })}
                      >
                        {count.toLocaleString()}
                      </button>
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="hint">Click a cell to explore BERTopic themes for that journey and sentiment.</p>
    </div>
  );
}
