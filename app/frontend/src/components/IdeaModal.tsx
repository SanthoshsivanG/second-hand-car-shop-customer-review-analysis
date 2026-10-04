import type { IdeaResponse } from "../api";

type Props = {
  open: boolean;
  loading: boolean;
  error: string | null;
  data: IdeaResponse | null;
  topicName: string;
  onClose: () => void;
};

export default function IdeaModal({
  open,
  loading,
  error,
  data,
  topicName,
  onClose,
}: Props) {
  if (!open) return null;

  const title =
    data?.mode === "keep"
      ? "Points to keep"
      : data?.mode === "improve"
        ? "Improvement ideas"
        : "Generating…";

  return (
    <div className="modal-backdrop" onClick={onClose} role="presentation">
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(e) => e.stopPropagation()}
      >
        <header className="modal-head">
          <div>
            <h3>{title}</h3>
            <p className="muted">
              Topic: {topicName}
              {data ? ` · ${data.journey_label} · ${data.satisfaction}` : ""}
            </p>
          </div>
          <button type="button" className="modal-close" onClick={onClose}>
            Close
          </button>
        </header>

        {loading && <p className="muted">Generating with AI from longest comments…</p>}
        {error && <p className="error">{error}</p>}

        {data && !loading && (
          <>
            <section className="modal-section">
              <h4>{data.mode === "keep" ? "Keep doing" : "Improve"}</h4>
              <ul className="idea-list">
                {data.ideas.map((idea) => (
                  <li key={idea}>{idea}</li>
                ))}
              </ul>
            </section>

            <section className="modal-section">
              <h4>Source comments (longest {data.comments.length})</h4>
              <ol className="comment-list">
                {data.comments.map((c, i) => (
                  <li key={`${c.char_len}-${i}`}>
                    <div className="comment-meta">
                      {c.store_name} · ★{c.stars ?? "-"} · {c.char_len} chars
                    </div>
                    <p>{c.review}</p>
                  </li>
                ))}
              </ol>
            </section>
          </>
        )}
      </div>
    </div>
  );
}
