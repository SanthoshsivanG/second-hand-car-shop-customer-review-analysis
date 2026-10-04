import { useEffect, useState } from "react";
import { fetchPolicy, updatePolicy } from "../api";

type Props = {
  open: boolean;
  onClose: () => void;
};

export default function PolicyEditor({ open, onClose }: Props) {
  const [content, setContent] = useState("");
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    setError(null);
    setSaved(false);
    fetchPolicy()
      .then((res) => {
        setContent(res.content);
        setUpdatedAt(res.updated_at);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [open]);

  if (!open) return null;

  const handleSave = () => {
    setSaving(true);
    setError(null);
    setSaved(false);
    updatePolicy(content)
      .then((res) => {
        setContent(res.content);
        setUpdatedAt(res.updated_at);
        setSaved(true);
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setSaving(false));
  };

  return (
    <div className="modal-backdrop" onClick={onClose} role="presentation">
      <div
        className="modal policy-modal"
        role="dialog"
        aria-modal="true"
        aria-label="Idea policy editor"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="modal-head">
          <div>
            <h3>Idea policy</h3>
            <p className="muted">
              Stored in Postgres. Used for every keep/improve generation.
            </p>
          </div>
          <button type="button" className="modal-close" onClick={onClose}>
            Close
          </button>
        </header>

        {loading && <p className="muted">Loading policy…</p>}
        {error && <p className="error">{error}</p>}
        {saved && <p className="ok">Saved.</p>}

        {!loading && (
          <>
            <textarea
              className="policy-textarea"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={18}
              spellCheck={false}
            />
            <footer className="policy-footer">
              {updatedAt && (
                <span className="muted">
                  Updated: {new Date(updatedAt).toLocaleString()}
                </span>
              )}
              <button
                type="button"
                className="primary-btn"
                onClick={handleSave}
                disabled={saving || !content.trim()}
              >
                {saving ? "Saving…" : "Save policy"}
              </button>
            </footer>
          </>
        )}
      </div>
    </div>
  );
}
