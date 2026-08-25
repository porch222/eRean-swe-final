import { useCallback, useEffect, useState } from 'react';

import {
  addCourseToCurriculum,
  createCurriculum,
  createMajor,
  createTerm,
  deleteCurriculum,
  deleteMajor,
  deleteTerm,
  listCourses,
  listCurricula,
  listMajors,
  listTerms,
  removeCourseFromCurriculum,
  updateCurriculum,
  updateMajor,
  updateTerm,
} from '../api/resources';
import { useConfirm } from '../components/ConfirmDialog';
import { errorMessage } from '../utils/formErrors';
import {
  EmptyState,
  ErrorAlert,
  PageHeader,
  Spinner,
  formatDate,
  plural,
} from '../components/common';

const TABS = [
  { key: 'terms', label: 'Terms' },
  { key: 'majors', label: 'Majors' },
  { key: 'curricula', label: 'Curricula' },
];

function TermsPanel({ terms, reload, setError }) {
  const confirm = useConfirm();
  const [draft, setDraft] = useState({
    code: '', name: '', year: new Date().getFullYear(), starts_on: '', ends_on: '',
  });

  async function handleCreate(event) {
    event.preventDefault();
    const result = await createTerm(draft);
    if (result.ok) {
      setDraft({ code: '', name: '', year: new Date().getFullYear(), starts_on: '', ends_on: '' });
      reload();
    } else setError(errorMessage(result.error));
  }

  async function makeCurrent(term) {
    const result = await updateTerm(term.id, { is_current: true });
    if (result.ok) reload();
    else setError(errorMessage(result.error));
  }

  async function handleDelete(term) {
    const ok = await confirm({
      title: `Delete ${term.name}?`,
      body: 'Only possible while no course belongs to it.',
      confirmLabel: 'Delete',
      tone: 'danger',
    });
    if (!ok) return;
    const result = await deleteTerm(term.id);
    if (result.ok) reload();
    else setError(errorMessage(result.error));
  }

  return (
    <>
      <form className="erean-card mb-3" onSubmit={handleCreate}>
        <span className="erean-eyebrow">Add a term</span>
        <div className="row g-2 align-items-end">
          <div className="col-6 col-md-2">
            <label className="form-label" htmlFor="t-code">Code</label>
            <input
              id="t-code" required className="form-control" placeholder="2027-SP"
              value={draft.code} onChange={(e) => setDraft({ ...draft, code: e.target.value })}
            />
          </div>
          <div className="col-6 col-md-3">
            <label className="form-label" htmlFor="t-name">Name</label>
            <input
              id="t-name" required className="form-control" placeholder="Spring 2027"
              value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })}
            />
          </div>
          <div className="col-4 col-md-2">
            <label className="form-label" htmlFor="t-year">Year</label>
            <input
              id="t-year" type="number" required className="form-control"
              value={draft.year} onChange={(e) => setDraft({ ...draft, year: e.target.value })}
            />
          </div>
          <div className="col-6 col-md-2">
            <label className="form-label" htmlFor="t-start">Starts</label>
            <input
              id="t-start" type="date" required className="form-control"
              value={draft.starts_on}
              onChange={(e) => setDraft({ ...draft, starts_on: e.target.value })}
            />
          </div>
          <div className="col-6 col-md-2">
            <label className="form-label" htmlFor="t-end">Ends</label>
            <input
              id="t-end" type="date" required className="form-control"
              value={draft.ends_on}
              onChange={(e) => setDraft({ ...draft, ends_on: e.target.value })}
            />
          </div>
          <div className="col-12 col-md-1">
            <button type="submit" className="btn btn-primary w-100">Add</button>
          </div>
        </div>
      </form>

      {terms.length === 0 ? (
        <EmptyState icon="bi-calendar3" title="No terms yet" hint="Add one above." />
      ) : (
        <div className="erean-card">
          {terms.map((term) => (
            <div className="erean-list-row" key={term.id}>
              <div className="erean-list-row__main">
                <p className="erean-list-row__title">
                  {term.name}
                  {term.is_current && (
                    <span className="erean-badge erean-badge--success">Current</span>
                  )}
                </p>
                <span className="erean-card__meta">
                  <span className="erean-num">{term.code}</span> ·{' '}
                  {formatDate(term.starts_on)} – {formatDate(term.ends_on)} ·{' '}
                  {plural(term.course_count, 'course')}
                </span>
              </div>
              <div className="d-flex gap-2">
                {!term.is_current && (
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-primary"
                    onClick={() => makeCurrent(term)}
                  >
                    Make current
                  </button>
                )}
                <button
                  type="button"
                  className="btn btn-sm btn-outline-danger"
                  onClick={() => handleDelete(term)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

const BLANK_MAJOR = { code: '', name: '', description: '' };

function MajorsPanel({ majors, reload, setError }) {
  const confirm = useConfirm();
  const [draft, setDraft] = useState(BLANK_MAJOR);

  const [editingId, setEditingId] = useState(null);

  async function handleCreate(event) {
    event.preventDefault();
    const result = editingId
      ? await updateMajor(editingId, draft)
      : await createMajor(draft);
    if (result.ok) {
      setDraft(BLANK_MAJOR);
      setEditingId(null);
      setError('');
      reload();
    } else setError(errorMessage(result.error));
  }

  function startEdit(major) {
    setEditingId(major.id);
    setDraft({
      code: major.code,
      name: major.name,
      description: major.description || '',
    });
    setError('');
  }

  function cancelEdit() {
    setEditingId(null);
    setDraft(BLANK_MAJOR);
  }

  async function handleDelete(major) {
    const ok = await confirm({
      title: `Delete ${major.name}?`,
      body: 'Only possible while no course belongs to it.',
      confirmLabel: 'Delete',
      tone: 'danger',
    });
    if (!ok) return;
    const result = await deleteMajor(major.id);
    if (result.ok) reload();
    else setError(errorMessage(result.error));
  }

  return (
    <>
      <form className="erean-card mb-3" onSubmit={handleCreate}>
        <span className="erean-eyebrow">
          {editingId ? `Editing ${draft.code || 'major'}` : 'Add a major'}
        </span>
        <div className="row g-2 align-items-end">
          <div className="col-6 col-md-2">
            <label className="form-label" htmlFor="m-code">Code</label>
            <input
              id="m-code" required className="form-control" placeholder="BIO"
              value={draft.code} onChange={(e) => setDraft({ ...draft, code: e.target.value })}
            />
          </div>
          <div className="col-6 col-md-4">
            <label className="form-label" htmlFor="m-name">Name</label>
            <input
              id="m-name" required className="form-control" placeholder="Biology"
              value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })}
            />
          </div>
          <div className="col-12 col-md-5">
            <label className="form-label" htmlFor="m-desc">Description</label>
            <input
              id="m-desc" className="form-control"
              value={draft.description}
              onChange={(e) => setDraft({ ...draft, description: e.target.value })}
            />
          </div>
          <div className="col-12 col-md-1">
            <button type="submit" className="btn btn-primary w-100">
              {editingId ? 'Save' : 'Add'}
            </button>
          </div>
        </div>
        {editingId && (
          <button
            type="button"
            className="erean-linkbutton mt-2"
            onClick={cancelEdit}
          >
            Cancel edit
          </button>
        )}
      </form>

      {majors.length === 0 ? (
        <EmptyState icon="bi-mortarboard" title="No majors yet" hint="Add one above." />
      ) : (
        <div className="erean-card">
          {majors.map((major) => (
            <div className="erean-list-row" key={major.id}>
              <div className="erean-list-row__main">
                <p className="erean-list-row__title">
                  <span className="erean-num">{major.code}</span> — {major.name}
                </p>
                <span className="erean-card__meta">
                  {plural(major.course_count, 'course')}
                  {major.description ? ` · ${major.description}` : ''}
                </span>
              </div>
              <div className="d-flex gap-2">
              <button
                type="button"
                className="btn btn-sm btn-outline-secondary"
                onClick={() => startEdit(major)}
              >
                Edit
              </button>
              <button
                type="button"
                className="btn btn-sm btn-outline-danger"
                onClick={() => handleDelete(major)}
              >
                Delete
              </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

function CurriculaPanel({ curricula, majors, reload, setError }) {
  const confirm = useConfirm();
  const blankDraft = () => ({
    major: '',
    name: '',
    year: new Date().getFullYear(),
    credits_to_graduate: '',
  });
  const [draft, setDraft] = useState(blankDraft);
  const [openId, setOpenId] = useState(null);
  const [courses, setCourses] = useState([]);
  const [pick, setPick] = useState({ course: '', year_level: 1, term: 1, is_required: true });

  const [creditDraft, setCreditDraft] = useState({});

  useEffect(() => {
    listCourses({}).then((r) => r.ok && setCourses(r.data.results));
  }, []);

  async function handleCreate(event) {
    event.preventDefault();
    const result = await createCurriculum({
      ...draft,

      credits_to_graduate: draft.credits_to_graduate === ''
        ? null
        : Number(draft.credits_to_graduate),
    });
    if (result.ok) {
      setDraft(blankDraft());
      reload();
    } else setError(errorMessage(result.error));
  }

  async function handleSaveCredits(curriculum, event) {
    event.preventDefault();
    const raw = creditDraft[curriculum.id];
    const result = await updateCurriculum(curriculum.id, {
      credits_to_graduate: raw === '' || raw === undefined ? null : Number(raw),
    });
    if (result.ok) {
      setCreditDraft((current) => {
        const next = { ...current };
        delete next[curriculum.id];
        return next;
      });
      setError('');
      reload();
    } else setError(errorMessage(result.error));
  }

  async function handleAdd(curriculum, event) {
    event.preventDefault();
    const result = await addCourseToCurriculum(curriculum.id, {
      ...pick,
      course: Number(pick.course),
      year_level: Number(pick.year_level),
      term: Number(pick.term),
    });
    if (result.ok) {
      setPick({ course: '', year_level: 1, term: 1, is_required: true });
      reload();
    } else setError(errorMessage(result.error));
  }

  async function handleRemove(curriculum, entry) {
    const result = await removeCourseFromCurriculum(curriculum.id, entry.id);
    if (result.ok) reload();
    else setError(errorMessage(result.error));
  }

  async function handleDelete(curriculum) {
    const ok = await confirm({
      title: `Delete ${curriculum.name}?`,
      body: 'The courses themselves are not affected.',
      confirmLabel: 'Delete',
      tone: 'danger',
    });
    if (!ok) return;
    const result = await deleteCurriculum(curriculum.id);
    if (result.ok) reload();
    else setError(errorMessage(result.error));
  }

  return (
    <>
      <form className="erean-card mb-3" onSubmit={handleCreate}>
        <span className="erean-eyebrow">Add a curriculum</span>
        <div className="row g-2 align-items-end">
          <div className="col-12 col-md-3">
            <label className="form-label" htmlFor="cu-major">Major</label>
            <select
              id="cu-major" required className="form-select"
              value={draft.major} onChange={(e) => setDraft({ ...draft, major: e.target.value })}
            >
              <option value="">Choose…</option>
              {majors.map((m) => (
                <option key={m.id} value={m.id}>{m.code} — {m.name}</option>
              ))}
            </select>
          </div>
          <div className="col-8 col-md-3">
            <label className="form-label" htmlFor="cu-name">Name</label>
            <input
              id="cu-name" required className="form-control" placeholder="BSCS 2027"
              value={draft.name} onChange={(e) => setDraft({ ...draft, name: e.target.value })}
            />
          </div>
          <div className="col-4 col-md-2">
            <label className="form-label" htmlFor="cu-year">Intake</label>
            <input
              id="cu-year" type="number" required className="form-control"
              value={draft.year} onChange={(e) => setDraft({ ...draft, year: e.target.value })}
            />
          </div>
          <div className="col-8 col-md-3">
            <label className="form-label" htmlFor="cu-credits">
              Credits to graduate
            </label>
            <input
              id="cu-credits" type="number" min={0} className="form-control"
              placeholder="Required courses only"
              value={draft.credits_to_graduate}
              onChange={(e) => setDraft({ ...draft, credits_to_graduate: e.target.value })}
            />
          </div>
          <div className="col-4 col-md-1">
            <button type="submit" className="btn btn-primary w-100">Add</button>
          </div>
        </div>
      </form>

      {curricula.length === 0 ? (
        <EmptyState icon="bi-diagram-3" title="No curricula yet" hint="Add one above." />
      ) : (
        curricula.map((curriculum) => (
          <div className="erean-card mb-3" key={curriculum.id}>
            <div className="erean-list-row">
              <div className="erean-list-row__main">
                <p className="erean-list-row__title">{curriculum.name}</p>
                <span className="erean-card__meta">
                  {curriculum.major_detail?.name} · intake {curriculum.year} ·{' '}
                  {plural(curriculum.course_count, 'course')} ·{' '}
                  {curriculum.total_credits} required credits ·{' '}
                  {curriculum.graduation_credits} to graduate
                  {curriculum.credits_to_graduate === null && ' (from required courses)'}
                </span>
              </div>
              <div className="d-flex gap-2">
                <button
                  type="button"
                  className="btn btn-sm btn-outline-secondary"
                  onClick={() => setOpenId(openId === curriculum.id ? null : curriculum.id)}
                >
                  {openId === curriculum.id ? 'Close' : 'Courses'}
                </button>
                <button
                  type="button"
                  className="btn btn-sm btn-outline-danger"
                  onClick={() => handleDelete(curriculum)}
                >
                  Delete
                </button>
              </div>
            </div>

            {openId === curriculum.id && (
              <div className="erean-curriculum">
                <form
                  className="erean-gradbar"
                  onSubmit={(e) => handleSaveCredits(curriculum, e)}
                >
                  <label className="form-label mb-0" htmlFor={`grad-${curriculum.id}`}>
                    Credits to graduate
                  </label>
                  <input
                    id={`grad-${curriculum.id}`}
                    type="number"
                    min={0}
                    className="form-control form-control-sm"
                    placeholder={`${curriculum.total_credits} (required courses)`}
                    value={
                      creditDraft[curriculum.id] ??
                      (curriculum.credits_to_graduate ?? '')
                    }
                    onChange={(e) =>
                      setCreditDraft((current) => ({
                        ...current,
                        [curriculum.id]: e.target.value,
                      }))
                    }
                  />
                  <button type="submit" className="btn btn-sm btn-primary">
                    Save
                  </button>
                  <span className="erean-card__meta">
                    Blank means the required courses and nothing more. Anything
                    above {curriculum.total_credits} must be made up in electives.
                  </span>
                </form>

                {curriculum.entries.length === 0 ? (
                  <p className="erean-card__meta">No courses in this plan yet.</p>
                ) : (
                  <div className="erean-table-wrap">
                    <table className="table align-middle mb-0">
                      <thead>
                        <tr>
                          <th>Course</th>
                          <th className="text-end">Year</th>
                          <th className="text-end">Term</th>
                          <th className="text-end">Credits</th>
                          <th>Type</th>
                          <th />
                        </tr>
                      </thead>
                      <tbody>
                        {curriculum.entries.map((entry) => (
                          <tr key={entry.id}>
                            <td>{entry.course_title}</td>
                            <td className="text-end erean-num">{entry.year_level}</td>
                            <td className="text-end erean-num">{entry.term}</td>
                            <td className="text-end erean-num">{entry.course_credits}</td>
                            <td>
                              <span
                                className={`erean-badge ${
                                  entry.is_required ? 'erean-badge--info' : 'erean-badge--muted'
                                }`}
                              >
                                {entry.is_required ? 'Required' : 'Elective'}
                              </span>
                            </td>
                            <td className="text-end">
                              <button
                                type="button"
                                className="btn btn-sm btn-outline-danger"
                                onClick={() => handleRemove(curriculum, entry)}
                              >
                                Remove
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                <form className="row g-2 align-items-end mt-3" onSubmit={(e) => handleAdd(curriculum, e)}>
                  <div className="col-12 col-md-5">
                    <label className="form-label" htmlFor={`add-${curriculum.id}`}>Add a course</label>
                    <select
                      id={`add-${curriculum.id}`}
                      required
                      className="form-select"
                      value={pick.course}
                      onChange={(e) => setPick({ ...pick, course: e.target.value })}
                    >
                      <option value="">Choose…</option>
                      {courses.map((c) => (
                        <option key={c.id} value={c.id}>{c.title}</option>
                      ))}
                    </select>
                  </div>
                  <div className="col-4 col-md-2">
                    <label className="form-label" htmlFor={`yl-${curriculum.id}`}>Year</label>
                    <input
                      id={`yl-${curriculum.id}`} type="number" min={1} max={6}
                      className="form-control" value={pick.year_level}
                      onChange={(e) => setPick({ ...pick, year_level: e.target.value })}
                    />
                  </div>
                  <div className="col-4 col-md-2">
                    <label className="form-label" htmlFor={`tm-${curriculum.id}`}>Term</label>
                    <input
                      id={`tm-${curriculum.id}`} type="number" min={1} max={4}
                      className="form-control" value={pick.term}
                      onChange={(e) => setPick({ ...pick, term: e.target.value })}
                    />
                  </div>
                  <div className="col-4 col-md-2">
                    <label className="form-label d-block" htmlFor={`rq-${curriculum.id}`}>
                      Required
                    </label>
                    <input
                      id={`rq-${curriculum.id}`} type="checkbox" className="form-check-input"
                      checked={pick.is_required}
                      onChange={(e) => setPick({ ...pick, is_required: e.target.checked })}
                    />
                  </div>
                  <div className="col-12 col-md-1">
                    <button type="submit" className="btn btn-primary w-100">Add</button>
                  </div>
                </form>
              </div>
            )}
          </div>
        ))
      )}
    </>
  );
}

export default function AdminAcademics() {
  const [tab, setTab] = useState('terms');
  const [terms, setTerms] = useState([]);
  const [majors, setMajors] = useState([]);
  const [curricula, setCurricula] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const reload = useCallback(async () => {
    setLoading(true);
    const [t, m, c] = await Promise.all([listTerms(), listMajors(), listCurricula()]);
    if (t.ok) setTerms(t.data);
    if (m.ok) setMajors(m.data);
    if (c.ok) setCurricula(c.data.results);
    setLoading(false);
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  return (
    <>
      <PageHeader
        title="Academic setup"
        subtitle="Terms, majors and the curricula that tie courses to a programme."
      />

      <div className="erean-tabs">
        {TABS.map((item) => (
          <button
            key={item.key}
            type="button"
            className={`erean-tab${tab === item.key ? ' is-active' : ''}`}
            onClick={() => setTab(item.key)}
          >
            {item.label}
          </button>
        ))}
      </div>

      <ErrorAlert message={error} onRetry={reload} />

      {loading ? (
        <Spinner label="Loading academic setup…" />
      ) : (
        <>
          {tab === 'terms' && (
            <TermsPanel terms={terms} reload={reload} setError={setError} />
          )}
          {tab === 'majors' && (
            <MajorsPanel majors={majors} reload={reload} setError={setError} />
          )}
          {tab === 'curricula' && (
            <CurriculaPanel
              curricula={curricula}
              majors={majors}
              reload={reload}
              setError={setError}
            />
          )}
        </>
      )}
    </>
  );
}
