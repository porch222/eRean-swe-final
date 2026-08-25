import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { createCourse, listCourses, listMajors, listTerms } from '../api/resources';
import { useAuth } from '../context/AuthContext';
import { errorMessage, parseApiError } from '../utils/formErrors';
import {
  EmptyState,
  ErrorAlert,
  FieldError,
  PageHeader,
  Spinner,
  StatusBadge,
  plural,
} from '../components/common';

function CourseCard({ course, canSeeStatus }) {
  return (
    <Link to={`/courses/${course.id}`} className="erean-card erean-course-card">
      <div className="d-flex justify-content-between align-items-start gap-2">
        <span className="erean-course-card__category">
          {course.major_detail?.name || 'Unassigned'}
        </span>
        {canSeeStatus && <StatusBadge status={course.status} />}
      </div>
      <h2 className="erean-card__title mt-1">{course.title}</h2>
      {course.term_detail && (
        <span className="erean-course-card__term">{course.term_detail.name}</span>
      )}
      <p className="erean-course-card__desc">{course.description}</p>
      <div className="erean-course-card__foot">
        <span>{course.instructor_detail?.full_name || 'Unknown instructor'}</span>
        <span>
          {plural(course.credits, 'credit')} ·{' '}
          {plural(course.assignment_count, 'assignment')}
        </span>
      </div>
      {course.my_enrollment && (
        <div className="mt-2">
          <StatusBadge status={course.my_enrollment.status} />
        </div>
      )}
    </Link>
  );
}

const BLANK_COURSE = { title: '', description: '', major: '', credits: 3, term: '' };

export default function CourseList() {
  const { user } = useAuth();
  const isStaff = user.role === 'admin' || user.role === 'instructor';

  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [termFilter, setTermFilter] = useState('');
  const [terms, setTerms] = useState([]);
  const [majors, setMajors] = useState([]);

  const [showForm, setShowForm] = useState(false);
  const [draft, setDraft] = useState(BLANK_COURSE);
  const [formErrors, setFormErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError('');
    const result = await listCourses({
      search,
      status: isStaff ? statusFilter : undefined,
      term: termFilter || undefined,
    });
    if (result.ok) setCourses(result.data.results);
    else setLoadError(errorMessage(result.error));
    setLoading(false);
  }, [search, statusFilter, termFilter, isStaff]);

  useEffect(() => {
    listTerms().then((r) => r.ok && setTerms(r.data));
    if (isStaff) listMajors().then((r) => r.ok && setMajors(r.data));
  }, [isStaff]);

  useEffect(() => {
    const timer = setTimeout(load, 300);
    return () => clearTimeout(timer);
  }, [load]);

  async function handleCreate(event) {
    event.preventDefault();
    setSaving(true);
    setFormErrors({});
    setFormError('');

    const result = await createCourse({
      ...draft,
      credits: Number(draft.credits) || 3,

      term: draft.term || null,
    });
    if (result.ok) {
      setDraft(BLANK_COURSE);
      setShowForm(false);
      load();
    } else {
      const { fieldErrors, generalError } = parseApiError(result.error);
      setFormErrors(fieldErrors);
      setFormError(generalError);
    }
    setSaving(false);
  }

  return (
    <>
      <PageHeader
        title={user.role === 'student' ? 'Browse courses' : 'Courses'}
        subtitle={
          user.role === 'student'
            ? 'Published courses you can enroll in.'
            : 'Courses you manage. New courses start as drafts until an admin approves them.'
        }
        actions={
          isStaff && (
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => setShowForm((open) => !open)}
            >
              {showForm ? 'Cancel' : 'New course'}
            </button>
          )
        }
      />

      {showForm && (
        <div className="erean-card mb-3">
          <h2 className="erean-card__title mb-3">Create a course</h2>
          {formError && <div className="alert alert-danger">{formError}</div>}
          <form onSubmit={handleCreate} noValidate>
            <div className="row g-3">
              <div className="col-12">
                <label className="form-label" htmlFor="title">Title</label>
                <input
                  id="title"
                  className={`form-control${formErrors.title ? ' is-invalid' : ''}`}
                  value={draft.title}
                  onChange={(e) => setDraft({ ...draft, title: e.target.value })}
                />
                <FieldError message={formErrors.title} />
              </div>
              <div className="col-12 col-md-5">
                <label className="form-label" htmlFor="major">Major</label>
                <select
                  id="major"
                  className={`form-select${formErrors.major ? ' is-invalid' : ''}`}
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
                <FieldError message={formErrors.major} />
              </div>
              <div className="col-12 col-md-4">
                <label className="form-label" htmlFor="term">Term</label>
                <select
                  id="term"
                  className={`form-select${formErrors.term ? ' is-invalid' : ''}`}
                  value={draft.term}
                  onChange={(e) => setDraft({ ...draft, term: e.target.value })}
                >
                  <option value="">No term</option>
                  {terms.map((term) => (
                    <option key={term.id} value={term.id}>
                      {term.name}
                      {term.is_current ? ' (current)' : ''}
                    </option>
                  ))}
                </select>
                <FieldError message={formErrors.term} />
              </div>
              <div className="col-12 col-md-3">
                <label className="form-label" htmlFor="credits">Credits</label>
                <input
                  id="credits"
                  type="number"
                  min={1}
                  max={12}
                  className={`form-control${formErrors.credits ? ' is-invalid' : ''}`}
                  value={draft.credits}
                  onChange={(e) => setDraft({ ...draft, credits: e.target.value })}
                />
                <FieldError message={formErrors.credits} />
              </div>
              <div className="col-12">
                <label className="form-label" htmlFor="description">Description</label>
                <textarea
                  id="description"
                  rows={3}
                  className={`form-control${formErrors.description ? ' is-invalid' : ''}`}
                  value={draft.description}
                  onChange={(e) => setDraft({ ...draft, description: e.target.value })}
                />
                <FieldError message={formErrors.description} />
              </div>
            </div>
            <button type="submit" className="btn btn-primary mt-3" disabled={saving}>
              {saving ? 'Creating…' : 'Create course'}
            </button>
          </form>
        </div>
      )}

      <div className="erean-card mb-3">
        <div className="row g-2 align-items-end">
          <div className="col-12 col-md">
            <label className="form-label" htmlFor="search">Search</label>
            <input
              id="search"
              className="form-control"
              placeholder="Title, major or term"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="col-12 col-md-3">
            <label className="form-label" htmlFor="term-filter">Term</label>
            <select
              id="term-filter"
              className="form-select"
              value={termFilter}
              onChange={(e) => setTermFilter(e.target.value)}
            >
              <option value="">All terms</option>
              <option value="current">Current term</option>
              {terms.map((term) => (
                <option key={term.id} value={term.id}>{term.name}</option>
              ))}
            </select>
          </div>
          {isStaff && (
            <div className="col-12 col-md-3">
              <label className="form-label" htmlFor="status">Status</label>
              <select
                id="status"
                className="form-select"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <option value="">All</option>
                <option value="draft">Draft</option>
                <option value="published">Published</option>
                <option value="archived">Archived</option>
              </select>
            </div>
          )}
        </div>
      </div>

      <ErrorAlert message={loadError} onRetry={load} />

      {loading ? (
        <Spinner label="Loading courses…" />
      ) : courses.length === 0 ? (
        <EmptyState
          icon="bi-search"
          title="No courses found"
          hint={search ? 'Try a different search term.' : 'Nothing has been published yet.'}
        />
      ) : (
        <div className="erean-grid">
          {courses.map((course) => (
            <CourseCard key={course.id} course={course} canSeeStatus={isStaff} />
          ))}
        </div>
      )}
    </>
  );
}
