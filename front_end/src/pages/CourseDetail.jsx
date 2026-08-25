import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import {
  deleteCourse,
  requestDrop,
  enroll,
  getCourse,
  listMajors,
  listTerms,
  updateCourse,
} from '../api/resources';
import { useAuth } from '../context/AuthContext';
import { useConfirm } from '../components/ConfirmDialog';
import AnnouncementsTab from '../components/AnnouncementsTab';
import AttendanceTab from '../components/AttendanceTab';
import AssignmentsTab from '../components/AssignmentsTab';
import DiscussionsTab from '../components/DiscussionsTab';
import MaterialsTab from '../components/MaterialsTab';
import RosterTab from '../components/RosterTab';
import { errorMessage } from '../utils/formErrors';
import {
  EmptyState,
  ErrorAlert,
  PageHeader,
  ProgressBar,
  Spinner,
  Stat,
  plural,
  StatusBadge,
} from '../components/common';

export default function CourseDetail() {
  const confirm = useConfirm();
  const { courseId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [course, setCourse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [loadError, setLoadError] = useState('');
  const [actionError, setActionError] = useState('');
  const [busy, setBusy] = useState(false);
  const [tab, setTab] = useState('overview');
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState({ title: '', description: '', major: '', credits: 3, term: '' });
  const [majors, setMajors] = useState([]);
  const [terms, setTerms] = useState([]);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError('');
    setNotFound(false);

    const result = await getCourse(courseId);
    if (result.ok) {
      setCourse(result.data);
      setDraft({
        title: result.data.title,
        description: result.data.description,
        major: result.data.major || '',
        credits: result.data.credits ?? 3,
        term: result.data.term || '',
      });
    } else if (result.status === 404) {
      setNotFound(true);
    } else {
      setLoadError(errorMessage(result.error));
    }
    setLoading(false);
  }, [courseId]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    if (user.role === 'student') return;
    listMajors().then((r) => r.ok && setMajors(r.data));
    listTerms().then((r) => r.ok && setTerms(r.data));
  }, [user.role]);

  if (loading) return <Spinner label="Loading course…" />;

  if (notFound) {
    return (
      <EmptyState
        icon="bi-slash-circle"
        title="Course not found"
        hint="It may have been removed, or it isn't published yet."
      />
    );
  }

  if (!course) return <ErrorAlert message={loadError} onRetry={load} />;

  const isOwner = user.role === 'admin' || course.instructor === user.id;
  const canManage = isOwner;
  const enrollment = course.my_enrollment;
  const isEnrolled = enrollment && enrollment.status === 'active';
  const isStudent = user.role === 'student';

  const canSeeContent = !isStudent || isEnrolled;

  async function handleEnroll() {
    setBusy(true);
    setActionError('');
    const result = await enroll(course.id);
    if (result.ok) await load();
    else setActionError(errorMessage(result.error));
    setBusy(false);
  }

  async function handleDrop() {
    const ok = await confirm({
      title: `Ask to drop "${course.title}"?`,
      body:
        'Your instructor or an administrator has to approve this. You stay '
        + 'enrolled until they do.',
      confirmLabel: 'Send request',
    });
    if (!ok) return;
    setBusy(true);
    setActionError('');
    const result = await requestDrop(enrollment.id, '');
    if (result.ok) await load();
    else setActionError(errorMessage(result.error));
    setBusy(false);
  }

  async function handleSaveEdit(event) {
    event.preventDefault();
    setBusy(true);
    setActionError('');
    const result = await updateCourse(course.id, {
      ...draft,
      credits: Number(draft.credits) || 3,
      term: draft.term || null,
      major: draft.major || null,
    });
    if (result.ok) {
      setEditing(false);
      await load();
    } else {
      setActionError(errorMessage(result.error));
    }
    setBusy(false);
  }

  async function handleDeleteCourse() {
    const ok = await confirm({
      title: `Delete "${course.title}"?`,
      body: 'Its materials, coursework and announcements go with it.',
      confirmLabel: 'Delete',
      tone: 'danger',
    });
    if (!ok) return;
    setBusy(true);
    const result = await deleteCourse(course.id);
    if (result.ok) navigate('/courses');
    else {
      setActionError(errorMessage(result.error));
      setBusy(false);
    }
  }

  const tabs = [
    { key: 'overview', label: 'Overview' },
    { key: 'materials', label: 'Materials' },
    { key: 'announcements', label: 'Announcements' },
    { key: 'assignments', label: 'Coursework' },
    { key: 'discussions', label: 'Discussions' },
    { key: 'attendance', label: 'Attendance' },
    ...(canManage ? [{ key: 'roster', label: 'Students' }] : []),
  ];

  return (
    <>
      <PageHeader
        backTo="/courses"
        backLabel="All courses"
        title={course.title}
        subtitle={[
          course.major_detail?.name,
          course.term_detail?.name,
          plural(course.credits, 'credit'),
          course.instructor_detail?.full_name || 'Unknown instructor',
        ]
          .filter(Boolean)
          .join(' · ')}
        actions={
          <>
            {canManage && (
              <>
                <Link
                  to={`/courses/${course.id}/gradebook`}
                  className="btn btn-outline-primary"
                >
                  <i className="bi bi-table me-1" aria-hidden="true" />
                  Gradebook
                </Link>
                <button
                  type="button"
                  className="btn btn-outline-secondary"
                  onClick={() => setEditing((open) => !open)}
                >
                  {editing ? 'Cancel' : 'Edit'}
                </button>
                <button
                  type="button"
                  className="btn btn-outline-danger"
                  onClick={handleDeleteCourse}
                  disabled={busy}
                >
                  Delete
                </button>
              </>
            )}
            {isStudent && !isEnrolled && (
              <button
                type="button"
                className="btn btn-primary"
                onClick={handleEnroll}
                disabled={busy}
              >
                {busy ? 'Enrolling…' : 'Enroll'}
              </button>
            )}
            {isStudent && isEnrolled && (
              <button
                type="button"
                className="btn btn-outline-danger"
                onClick={handleDrop}
                disabled={busy}
              >
                Request drop
              </button>
            )}
          </>
        }
      />

      <ErrorAlert message={actionError || loadError} />

      <div className="erean-card mb-3">
        <div className="d-flex justify-content-between align-items-start gap-3 flex-wrap">
          <div className="flex-grow-1">
            {editing ? (
              <form onSubmit={handleSaveEdit}>
                <div className="mb-2">
                  <label className="form-label" htmlFor="c-title">Title</label>
                  <input
                    id="c-title"
                    className="form-control"
                    value={draft.title}
                    onChange={(e) => setDraft({ ...draft, title: e.target.value })}
                  />
                </div>
                <div className="row g-2 mb-2">
                  <div className="col-12 col-md-5">
                    <label className="form-label" htmlFor="c-major">Major</label>
                    <select
                      id="c-major"
                      className="form-select"
                      value={draft.major}
                      onChange={(e) => setDraft({ ...draft, major: e.target.value })}
                    >
                      <option value="">Choose a major…</option>
                      {majors.map((major) => (
                        <option key={major.id} value={major.id}>
                          {major.code} — {major.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="col-12 col-md-4">
                    <label className="form-label" htmlFor="c-term">Term</label>
                    <select
                      id="c-term"
                      className="form-select"
                      value={draft.term}
                      onChange={(e) => setDraft({ ...draft, term: e.target.value })}
                    >
                      <option value="">No term</option>
                      {terms.map((term) => (
                        <option key={term.id} value={term.id}>{term.name}</option>
                      ))}
                    </select>
                  </div>
                  <div className="col-12 col-md-3">
                    <label className="form-label" htmlFor="c-credits">Credits</label>
                    <input
                      id="c-credits"
                      type="number"
                      min={1}
                      max={12}
                      className="form-control"
                      value={draft.credits}
                      onChange={(e) => setDraft({ ...draft, credits: e.target.value })}
                    />
                  </div>
                </div>
                <div className="mb-2">
                  <label className="form-label" htmlFor="c-desc">Description</label>
                  <textarea
                    id="c-desc"
                    rows={4}
                    className="form-control"
                    value={draft.description}
                    onChange={(e) => setDraft({ ...draft, description: e.target.value })}
                  />
                </div>
                <button type="submit" className="btn btn-primary" disabled={busy}>
                  {busy ? 'Saving…' : 'Save'}
                </button>
              </form>
            ) : (
              <p className="mb-0 erean-prewrap">{course.description}</p>
            )}
          </div>
          <div className="text-end">
            {(canManage || user.role === 'admin') && <StatusBadge status={course.status} />}
            {enrollment && (
              <div className="mt-2" style={{ minWidth: 140 }}>
                <ProgressBar value={enrollment.progress} />
                <div className="erean-card__meta mt-1">
                  <StatusBadge status={enrollment.status} />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {course.status === 'draft' && canManage && (
        <div className="alert alert-warning">
          This course is a <strong>draft</strong>. Students cannot see it until an
          administrator publishes it.
        </div>
      )}

      <div className="erean-tabs" role="tablist">
        {tabs.map((item) => (
          <button
            key={item.key}
            type="button"
            role="tab"
            aria-selected={tab === item.key}
            className={`erean-tab${tab === item.key ? ' is-active' : ''}`}
            onClick={() => setTab(item.key)}
          >
            {item.label}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <div className="erean-stats">
          <Stat value={course.material_count} label="Materials" icon="bi-folder2-open" />
          <Stat value={course.assignment_count} label="Coursework" icon="bi-pencil-square" />
          <Stat value={course.enrolled_count} label="Enrolled" icon="bi-people" />
        </div>
      )}

      {tab !== 'overview' && tab !== 'roster' && !canSeeContent && (
        <EmptyState
          icon="bi-lock"
          title="Enroll to see this"
          hint="Course materials, announcements and coursework are available to enrolled students."
        />
      )}

      {canSeeContent && tab === 'materials' && (
        <MaterialsTab courseId={course.id} canManage={canManage} />
      )}
      {canSeeContent && tab === 'announcements' && (
        <AnnouncementsTab courseId={course.id} canManage={canManage} />
      )}
      {canSeeContent && tab === 'assignments' && (
        <AssignmentsTab courseId={course.id} canManage={canManage} />
      )}
      {canSeeContent && tab === 'discussions' && (
        <DiscussionsTab courseId={course.id} canManage={canManage} />
      )}
      {canSeeContent && tab === 'attendance' && (
        <AttendanceTab courseId={course.id} canManage={canManage} />
      )}
      {tab === 'roster' && canManage && <RosterTab courseId={course.id} />}
    </>
  );
}
