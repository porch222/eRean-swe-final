import { useCallback, useEffect, useState } from 'react';

import { gradeWrittenAnswer, listPendingWrittenAnswers } from '../api/resources';
import { errorMessage } from '../utils/formErrors';
import { EmptyState, ErrorAlert, Spinner } from './common';

export default function WrittenAnswerMarking({ courseId, assignment, onMarked }) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [points, setPoints] = useState({});
  const [busy, setBusy] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    const result = await listPendingWrittenAnswers(courseId, assignment.id);
    if (result.ok) {
      const list = result.data.results ?? result.data;
      setRows(list);

      const seeded = {};
      for (const row of list) seeded[row.id] = '';
      setPoints(seeded);
    } else {
      setLoadError(errorMessage(result.error));
    }
    setLoading(false);
  }, [courseId, assignment.id]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleMark(row) {
    const value = points[row.id];
    if (value === '' || value === undefined) {
      setLoadError('Enter a mark before saving.');
      return;
    }
    setBusy(row.id);
    setLoadError('');
    const result = await gradeWrittenAnswer(courseId, assignment.id, row.id, Number(value));
    if (result.ok) {
      await load();
      onMarked?.();
    } else {
      setLoadError(errorMessage(result.error));
    }
    setBusy(null);
  }

  if (loading) return <Spinner label="Loading written answers…" />;

  return (
    <>
      <h3 className="erean-card__title mt-4 mb-2">
        Written answers
        {rows.length > 0 && (
          <span className="erean-badge erean-badge--warning ms-2">
            {rows.length} to mark
          </span>
        )}
      </h3>

      <ErrorAlert message={loadError} onRetry={load} />

      {rows.length === 0 ? (
        <EmptyState
          icon="bi-check2-circle"
          title="Nothing waiting"
          hint="Written answers appear here as students submit them, and disappear once marked."
        />
      ) : (
        rows.map((row) => {
          const max = row.question_points ?? 0;
          return (
            <div className="erean-card mb-3 erean-marking" key={row.id}>
              <span className="erean-eyebrow">
                {row.student_name || 'Student'}
              </span>
              <p className="erean-marking__question">{row.question_text}</p>

              <blockquote className="erean-marking__answer erean-prewrap">
                {row.text_answer || <em className="text-muted">Left blank.</em>}
              </blockquote>

              <div className="erean-marking__foot">
                <label className="form-label mb-0" htmlFor={`mark-${row.id}`}>
                  Mark
                </label>
                <div className="erean-marking__input">
                  <input
                    id={`mark-${row.id}`}
                    type="number"
                    min={0}
                    max={max || undefined}
                    step="0.5"
                    className="form-control"
                    value={points[row.id] ?? ''}
                    onChange={(e) =>
                      setPoints((current) => ({ ...current, [row.id]: e.target.value }))
                    }
                  />
                  <span className="erean-marking__outof">/ {max}</span>
                </div>
                {max > 0 && (
                  <button
                    type="button"
                    className="erean-linkbutton"
                    onClick={() =>
                      setPoints((current) => ({ ...current, [row.id]: String(max) }))
                    }
                  >
                    Full marks
                  </button>
                )}
                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  onClick={() => handleMark(row)}
                  disabled={busy === row.id}
                >
                  {busy === row.id ? 'Saving…' : 'Save mark'}
                </button>
              </div>
            </div>
          );
        })
      )}
    </>
  );
}
