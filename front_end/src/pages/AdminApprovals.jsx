import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { approveCourse, listCourses } from '../api/resources';
import { errorMessage } from '../utils/formErrors';
import {
  EmptyState,
  ErrorAlert,
  PageHeader,
  Spinner,
  StatusBadge,
  formatDate,
  plural,
} from '../components/common';

const TABS = [
  { key: 'draft', label: 'Awaiting approval' },
  { key: 'published', label: 'Published' },
  { key: 'archived', label: 'Archived' },
];

export default function AdminApprovals() {
  const [tab, setTab] = useState('draft');
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [busyId, setBusyId] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError('');
    const result = await listCourses({ status: tab });
    if (result.ok) setCourses(result.data.results);
    else setLoadError(errorMessage(result.error));
    setLoading(false);
  }, [tab]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleApprove(course, status) {
    setBusyId(course.id);
    setLoadError('');
    const result = await approveCourse(course.id, status);
    if (result.ok) setCourses((rows) => rows.filter((row) => row.id !== course.id));
    else setLoadError(errorMessage(result.error));
    setBusyId(null);
  }

  return (
    <>
      <PageHeader
        title="Course approvals"
        subtitle="Instructors create drafts; a course is only visible to students once you publish it."
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

      <ErrorAlert message={loadError} onRetry={load} />

      {loading ? (
        <Spinner label="Loading courses…" />
      ) : courses.length === 0 ? (
        <EmptyState
          icon="bi-inbox"
          title={tab === 'draft' ? 'Nothing waiting for approval' : `No ${tab} courses`}
          hint={tab === 'draft' ? 'New course drafts will appear here.' : undefined}
        />
      ) : (
        <div className="erean-card">
          {courses.map((course) => (
            <div className="erean-list-row" key={course.id}>
              <div className="erean-list-row__main">
                <p className="erean-list-row__title">
                  <Link to={`/courses/${course.id}`}>{course.title}</Link>{' '}
                  <StatusBadge status={course.status} />
                </p>
                <span className="erean-card__meta">
                  {course.category} · {course.instructor_detail?.full_name} · created{' '}
                  {formatDate(course.created_at)} ·{' '}
                  {plural(course.material_count, 'material')},{' '}
                  {plural(course.assignment_count, 'assignment')}
                </span>
              </div>
              <div className="d-flex gap-2">
                {course.status !== 'published' && (
                  <button
                    type="button"
                    className="btn btn-sm btn-primary"
                    disabled={busyId === course.id}
                    onClick={() => handleApprove(course, 'published')}
                  >
                    Publish
                  </button>
                )}
                {course.status !== 'archived' && (
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-secondary"
                    disabled={busyId === course.id}
                    onClick={() => handleApprove(course, 'archived')}
                  >
                    Archive
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
