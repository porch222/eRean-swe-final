import { useCallback, useEffect, useState } from 'react';

import { listActivityLogs } from '../api/resources';
import { errorMessage } from '../utils/formErrors';
import {
  EmptyState,
  ErrorAlert,
  PageHeader,
  Spinner,
  formatDateTime,
} from '../components/common';

const ACTION_LABELS = {
  course_created: 'created a course',
  course_updated: 'updated a course',
  course_deleted: 'deleted a course',
  course_approved: 'changed a course status',
  material_created: 'uploaded a material',
  material_updated: 'updated a material',
  material_deleted: 'deleted a material',
  material_downloaded: 'accessed a material',
  announcement_created: 'posted an announcement',
  announcement_updated: 'edited an announcement',
  announcement_deleted: 'deleted an announcement',
};

export default function AdminActivity() {
  const [logs, setLogs] = useState([]);
  const [count, setCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError('');
    const result = await listActivityLogs({ search, page });
    if (result.ok) {
      setLogs(result.data.results);
      setCount(result.data.count);
      setHasNext(Boolean(result.data.next));
    } else {
      setLoadError(errorMessage(result.error));
    }
    setLoading(false);
  }, [search, page]);

  useEffect(() => {
    const timer = setTimeout(load, 300);
    return () => clearTimeout(timer);
  }, [load]);

  return (
    <>
      <PageHeader
        title="Activity log"
        subtitle={`${count} recorded events. Read-only audit trail of what happens on the platform.`}
      />

      <div className="erean-card mb-3">
        <label className="form-label" htmlFor="log-search">Search</label>
        <input
          id="log-search"
          className="form-control"
          placeholder="Action, user or details"
          value={search}
          onChange={(e) => {
            setPage(1);
            setSearch(e.target.value);
          }}
        />
      </div>

      <ErrorAlert message={loadError} onRetry={load} />

      {loading ? (
        <Spinner label="Loading activity…" />
      ) : logs.length === 0 ? (
        <EmptyState
          icon="bi-journal-text"
          title="No activity recorded"
          hint={search ? 'Try a different search.' : 'Events will appear as people use the system.'}
        />
      ) : (
        <>
          <div className="erean-card">
            <div className="erean-table-wrap">
              <table className="table align-middle mb-0">
                <thead>
                  <tr>
                    <th scope="col">When</th>
                    <th scope="col">Who</th>
                    <th scope="col">What</th>
                    <th scope="col">Target</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr key={log.id}>
                      <td className="erean-card__meta">{formatDateTime(log.created_at)}</td>
                      <td>{log.actor_username || <em className="text-muted">deleted user</em>}</td>
                      <td>{ACTION_LABELS[log.action] || log.action}</td>
                      <td className="erean-card__meta">
                        {log.target_type}
                        {log.target_id ? ` #${log.target_id}` : ''}
                        {log.details ? ` · ${log.details}` : ''}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="d-flex justify-content-between align-items-center mt-3">
            <button
              type="button"
              className="btn btn-outline-secondary btn-sm"
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
            >
              Previous
            </button>
            <span className="erean-card__meta">Page {page}</span>
            <button
              type="button"
              className="btn btn-outline-secondary btn-sm"
              disabled={!hasNext}
              onClick={() => setPage((p) => p + 1)}
            >
              Next
            </button>
          </div>
        </>
      )}
    </>
  );
}
