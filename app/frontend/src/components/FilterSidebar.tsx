import type { FilterOptions, Filters } from "../api";

type Props = {
  options: FilterOptions | null;
  filters: Filters;
  onChange: (next: Filters) => void;
};

function MultiSelect({
  label,
  values,
  selected,
  onToggle,
}: {
  label: string;
  values: { value: string; label: string }[];
  selected: string[];
  onToggle: (value: string) => void;
}) {
  return (
    <fieldset className="filter-group">
      <legend>{label}</legend>
      <div className="filter-list">
        {values.length === 0 && <span className="muted">No options</span>}
        {values.map((v) => (
          <label key={v.value} className="check">
            <input
              type="checkbox"
              checked={selected.includes(v.value)}
              onChange={() => onToggle(v.value)}
            />
            <span>{v.label}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

function toggle(list: string[], value: string): string[] {
  return list.includes(value) ? list.filter((x) => x !== value) : [...list, value];
}

export default function FilterSidebar({ options, filters, onChange }: Props) {
  const stores = (options?.store_name ?? []).map((s) => ({ value: s, label: s }));
  const sats = (options?.satisfaction ?? []).map((s) => ({
    value: s,
    label: s === "positive" ? "Positive" : "Negative",
  }));
  const journeys = (options?.journey ?? []).map((j) => ({ value: j.id, label: j.label }));
  const topics = (options?.topic ?? []).map((t) => ({ value: t, label: t }));

  return (
    <aside className="sidebar">
      <h2>Filters</h2>
      <button
        type="button"
        className="clear-btn"
        onClick={() =>
          onChange({
            store_name: [],
            satisfaction: [],
            journey: [],
            topic: [],
          })
        }
      >
        Clear all
      </button>
      <MultiSelect
        label="Shop name"
        values={stores}
        selected={filters.store_name}
        onToggle={(v) => onChange({ ...filters, store_name: toggle(filters.store_name, v) })}
      />
      <MultiSelect
        label="Sentiment"
        values={sats}
        selected={filters.satisfaction}
        onToggle={(v) =>
          onChange({ ...filters, satisfaction: toggle(filters.satisfaction, v) })
        }
      />
      <MultiSelect
        label="Customer journey"
        values={journeys}
        selected={filters.journey}
        onToggle={(v) => onChange({ ...filters, journey: toggle(filters.journey, v) })}
      />
      <MultiSelect
        label="BERTopic topics"
        values={topics}
        selected={filters.topic}
        onToggle={(v) => onChange({ ...filters, topic: toggle(filters.topic, v) })}
      />
    </aside>
  );
}
