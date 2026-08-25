import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import {
  createAssignment,
  deleteAssignment,
  listAssignments,
  updateAssignment,
} from '../api/resources';
import { useConfirm } from './ConfirmDialog';
import { errorMessage, parseApiError } from '../utils/formErrors';
import { EmptyState, ErrorAlert, FieldError, Spinner, formatDateTime } from './common';

const BLANK = {
  title: '',
  description: '',
  type: 'assignment',
  due_date: '',
  max_score: 100,
};

export default function AssignmentsTab({ courseId, canManage }) {
  const confirm = useConfirm();
  const [assignments, setAssignments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  const [showForm, setShowForm] = useState(false);

  const [editing, setEditing] = useState(null);
  const [draft, setDraft] = useState(BLANK);
  const [formErrors, setFormErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    setLoadError('');
    const result = await listAssignments(courseId);
    if (result.ok) setAssignments(result.data.results);
    else setLoadError(errorMessage(result.error));
    setLoading(false);
  }

  useEffect(() => {
    load();

  }, [courseId]);

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setFormErrors({});
    setFormError('');

    const payload = {
      ...draft,
      max_score: Number(draft.max_score),

      due_date: draft.due_date ? new Date(draft.due_date).toISOString() : null,
    };

    const result = editing
      ? await updateAssignment(courseId, editing.id, payload)
      : await createAssignment(courseId, payload);

    if (result.ok) {
      closeForm();
      load();
    } else {
      const { fieldErrors, generalError } = parseApiError(result.error);
      setFormErrors(fieldErrors);
      setFormError(generalError);
    }
    setSaving(false);
  }

  function closeForm() {
    setShowForm(false);
    setEditing(null);
    setDraft(BLANK);
    setFormErrors({});
    setFormError('');
  }

  function toLocalInput(iso) {
    if (!iso) return '';
    const d = new Date(iso);
    const pad = (n) => String(n).padStart(2, '0');
    return (
      `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
      `T${pad(d.getHours())}:${pad(d.getMinutes())}`
    );
  }

  function startEdit(assignment) {
    setEditing(assignment);
    setDraft({
      title: assignment.title,
      description: assignment.description || '',
      type: assignment.type,
      due_date: toLocalInput(assignment.due_date),
      max_score: assignment.max_score,
    });
    setShowForm(true);
    setFormErrors({});
    setFormError('');
  }

  async function handleDelete(assignment) {
    const count = assignment.submission_count || 0;
    const noun = assignment.type === 'quiz' ? 'attempt' : 'submission';

    const body =
      count > 0
        ? `This will also delete ${count} student ${noun}${count === 1 ? '' : 's'}, ` +
          'and that cannot be undone. To fix a mistake in the title, ' +
          'instructions, due date or points, use Edit instead.'
        : 'Nothing has been handed in yet, so no student work will be lost.';

    const ok = await confirm({
      title: `Delete "${assignment.title}"?`,
      body,
      confirmLabel: count > 0 ? `Delete and lose ${count} ${noun}${count === 1 ? '' : 's'}` : 'Delete',
      tone: 'danger',
    });
    if (!ok) return;

    const result = await deleteAssignment(courseId, assignment.id);
    if (result.ok) setAssignments((rows) => rows.filter((a) => a.id !== assignment.id));
    else setLoadError(errorMessage(result.error));
  }

  const typeLocked =
    !!editing &&
    ((editing.submission_count || 0) > 0 || (editing.question_count || 0) > 0);

  return (
    <>
      {canManage && (
        <div className="mb-3">
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={() => (showForm ? closeForm() : setShowForm(true))}
          >
            {showForm ? 'Cancel' : 'New assignment or quiz'}
          </button>
        </div>
      )}

      {showForm && (
        <div className="erean-card mb-3">
          {editing && (
            <span className="erean-eyebrow d-block mb-2">
              Editing “{editing.title}”
            </span>
          )}
          {formError && <div className="alert alert-danger">{formError}</div>}
          <form onSubmit={handleSubmit} noValidate>
            <div className="row g-3">
              <div className="col-12 col-md-6">
                <label className="form-label" htmlFor="as-title">Title</label>
                <input
                  id="as-title"
                  className={`form-control${formErrors.title ? ' is-invalid' : ''}`}
                  value={draft.title}
                  onChange={(e) => setDraft({ ...draft, title: e.target.value })}
                />
                <FieldError message={formErrors.title} />
              </div>
              <div className="col-6 col-md-2">
                <label className="form-label" htmlFor="as-type">Type</label>
                <select
                  id="as-type"
                  className={`form-select${formErrors.type ? ' is-invalid' : ''}`}
                  value={draft.type}

                  disabled={typeLocked}
                  onChange={(e) => setDraft({ ...draft, type: e.target.value })}
                >
                  <option value="assignment">Assignment</option>
                  <option value="quiz">Quiz</option>
                </select>
                <FieldError message={formErrors.type} />
              </div>
              <div className="col-6 col-md-2">
                <label className="form-label" htmlFor="as-score">Max score</label>
                <input
                  id="as-score"
                  type="number"
                  min="1"
                  className={`form-control${formErrors.max_score ? ' is-invalid' : ''}`}
                  value={draft.max_score}
                  onChange={(e) => setDraft({ ...draft, max_score: e.target.value })}
                />
                <FieldError message={formErrors.max_score} />
              </div>
              <div className="col-12 col-md-2">
                <label className="form-label" htmlFor="as-due">Due date</label>
                <input
                  id="as-due"
                  type="datetime-local"
                  className={`form-control${formErrors.due_date ? ' is-invalid' : ''}`}
                  value={draft.due_date}
                  onChange={(e) => setDraft({ ...draft, due_date: e.target.value })}
                />
                <FieldError message={formErrors.due_date} />
              </div>
              <div className="col-12">
                <label className="form-label" htmlFor="as-desc">Instructions</label>
                <textarea
                  id="as-desc"
                  rows={3}
                  className={`form-control${formErrors.description ? ' is-invalid' : ''}`}
                  value={draft.description}
                  onChange={(e) => setDraft({ ...draft, description: e.target.value })}
                />
                <FieldError message={formErrors.description} />
              </div>
            </div>
            <button type="submit" className="btn btn-primary mt-3" disabled={saving}>
              {saving
                ? editing
                  ? 'Saving…'
                  : 'Creating…'
                : editing
                  ? 'Save changes'
                  : 'Create'}
            </button>
            {typeLocked && (
              <p className="erean-card__meta mt-2 mb-0">
                The type is fixed now that work exists here. Everything else can
                still be changed, and nothing already handed in will be lost.
              </p>
            )}
            {!editing && draft.type === 'quiz' && (
              <p className="erean-card__meta mt-2 mb-0">
                You'll add questions and answer choices after creating the quiz.
              </p>
            )}
          </form>
        </div>
      )}

      <ErrorAlert message={loadError} onRetry={load} />

      {loading ? (
        <Spinner label="Loading coursework…" />
      ) : assignments.length === 0 ? (
        <EmptyState
          icon="bi-pencil-square"
          title="No coursework yet"
          hint={canManage ? 'Create an assignment or a quiz.' : 'Nothing has been set yet.'}
        />
      ) : (
        <div className="erean-card">
          {assignments.map((assignment) => (
            <div className="erean-list-row" key={assignment.id}>
              <div className="erean-list-row__main">
                <p className="erean-list-row__title">
                  <Link to={`/courses/${courseId}/assignments/${assignment.id}`}>
                    {assignment.title}
                  </Link>{' '}
                  <span
                    className={`erean-badge erean-badge--${
                      assignment.type === 'quiz' ? 'info' : 'muted'
                    }`}
                  >
                    {assignment.type}
                  </span>
                  {assignment.is_past_due && (
                    <span className="erean-badge erean-badge--danger ms-1">past due</span>
                  )}
                </p>
                <span className="erean-card__meta">
                  Due {formatDateTime(assignment.due_date)} · {assignment.max_score} points
                  {assignment.type === 'quiz' && ` · ${assignment.question_count} questions`}
                  {canManage && ` · ${assignment.submission_count} submissions`}
                </span>
              </div>
              <div className="d-flex gap-2">
                <Link
                  className="btn btn-sm btn-outline-primary"
                  to={`/courses/${courseId}/assignments/${assignment.id}`}
                >
                  Open
                </Link>
                {canManage && (
                  <>
                    <button
                      type="button"
                      className="btn btn-sm btn-outline-secondary"
                      onClick={() => startEdit(assignment)}
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      className="btn btn-sm btn-outline-danger"
                      onClick={() => handleDelete(assignment)}
                    >
                      Delete
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
