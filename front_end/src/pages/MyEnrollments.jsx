import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { listDropRequests, listEnrollments, requestDrop } from '../api/resources';
import { useConfirm } from '../components/ConfirmDialog';
import { errorMessage } from '../utils/formErrors';
import {
  EmptyState,
  ErrorAlert,
  Grade,
  PageHeader,
  ProgressBar,
  Spinner,
  StatusBadge,
  formatDate,
} from '../components/common';

const FILTERS = [
  { key: '', label: 'All' },
  { key: 'active', label: 'Active' },
  { key: 'completed', label: 'Completed' },
  { key: 'dropped', label: 'Dropped' },
];

export default function MyEnrollments() {
  const confirm = useConfirm();
  const [rows, setRows] = useState([]);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [pending, setPending] = useState(new Set());

  async function load(status) {
    setLoading(true);
    setLoadError('');
    const result = await listEnrollments({ status });
    if (result.ok) setRows(result.data.results);
    else setLoadError(errorMessage(result.error));
    setLoading(false);
  }

  useEffect(() => {
    load(filter);
  }, [filter]);

  useEffect(() => {
    listDropRequests({ status: 'pending' }).then((result) => {
      if (result.ok) {
        setPending(new Set(result.data.results.map((row) => row.enrollment)));
      }
    });
  }, [rows]);

  async function handleRequestDrop(enrollment) {
    const ok = await confirm({
      title: `Ask to drop "${enrollment.course_title}"?`,
      body:
        'Your instructor or an administrator has to approve this. You stay '
        + 'enrolled until they do.',
      confirmLabel: 'Send request',
    });
    if (!ok) return;
    const result = await requestDrop(enrollment.id, '');
    if (result.ok) load(filter);
    else setLoadError(errorMessage(result.error));
  }

  return (
    <>
      <PageHeader
        title="My courses"
        subtitle="Everything you're enrolled in, and how far along you are."
        actions={
          <Link to="/courses" className="btn btn-primary">
            Browse courses
          </Link>
        }
      />

      <div className="erean-tabs">
        {FILTERS.map((item) => (
          <button
            key={item.key}
            type="button"
            className={`erean-tab${filter === item.key ? ' is-active' : ''}`}
            onClick={() => setFilter(item.key)}
          >
            {item.label}
          </button>
        ))}
      </div>

      <ErrorAlert message={loadError} onRetry={() => load(filter)} />

      {loading ? (
        <Spinner label="Loading your courses…" />
      ) : rows.length === 0 ? (
        <EmptyState
          icon="bi-mortarboard"
          title="Nothing here yet"
          hint="Enroll in a published course to see it listed."
          action={
            <Link to="/courses" className="btn btn-primary btn-sm mt-2">
              Browse courses
            </Link>
          }
        />
      ) : (
        <div className="erean-card">
          {rows.map((enrollment) => (
            <div className="erean-list-row" key={enrollment.id}>
              <div className="erean-list-row__main">
                <p className="erean-list-row__title">
                  <Link to={`/courses/${enrollment.course}`}>{enrollment.course_title}</Link>
                </p>
                <span className="erean-card__meta">
                  Enrolled {formatDate(enrollment.enrolled_at)}
                </span>{' '}
                <StatusBadge status={enrollment.status} />
              </div>
              <div className="d-flex align-items-center gap-3 flex-wrap">
                {enrollment.finalized_at ? (
                  <Grade value={enrollment.final_score} outOf={100} />
                ) : (
                  <ProgressBar value={enrollment.progress} />
                )}
                {enrollment.letter_grade && (
                  <span className="erean-badge erean-badge--info">
                    {enrollment.letter_grade}
                  </span>
                )}
                {pending.has(enrollment.id) ? (
                  <span className="erean-badge erean-badge--warning">
                    <i className="bi bi-hourglass-split" aria-hidden="true" />
                    Drop requested
                  </span>
                ) : (
                  enrollment.status === 'active' && (
                    <button
                      type="button"
                      className="btn btn-sm btn-outline-danger"
                      onClick={() => handleRequestDrop(enrollment)}
                    >
                      Request drop
                    </button>
                  )
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
