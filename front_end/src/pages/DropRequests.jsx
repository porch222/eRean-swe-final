import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { decideDropRequest, listDropRequests } from '../api/resources';
import { useConfirm } from '../components/ConfirmDialog';
import { errorMessage } from '../utils/formErrors';
import {
  EmptyState,
  ErrorAlert,
  PageHeader,
  Spinner,
  formatDateTime,
} from '../components/common';

const FILTERS = [
  { key: 'pending', label: 'Waiting' },
  { key: 'approved', label: 'Approved' },
  { key: 'rejected', label: 'Rejected' },
  { key: '', label: 'All' },
];

export default function DropRequests() {
  const confirm = useConfirm();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [filter, setFilter] = useState('pending');
  const [busy, setBusy] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError('');
    const result = await listDropRequests(filter ? { status: filter } : {});
    if (result.ok) setRows(result.data.results);
    else setLoadError(errorMessage(result.error));
    setLoading(false);
  }, [filter]);

  useEffect(() => {
    load();
  }, [load]);

  async function decide(row, status) {
    const approving = status === 'approved';
    const ok = await confirm({
      title: approving
        ? `Approve the drop for ${row.student_detail?.full_name}?`
        : `Reject the drop for ${row.student_detail?.full_name}?`,
      body: approving
        ? `They will be removed from ${row.course_title}. Their work is kept.`
        : 'They stay enrolled and will be told the request was turned down.',
      confirmLabel: approving ? 'Approve drop' : 'Reject',
      tone: approving ? 'danger' : undefined,
    });
    if (!ok) return;

    setBusy(row.id);
    const result = await decideDropRequest(row.id, { status });
    if (result.ok) await load();
    else setLoadError(errorMessage(result.error));
    setBusy(null);
  }

  return (
    <>
      <PageHeader
        title="Drop requests"
        subtitle="Students cannot leave a course on their own — each request needs a decision."
      />

      <div className="erean-tabs">
        {FILTERS.map((item) => (
          <button
            key={item.key || 'all'}
            type="button"
            className={`erean-tab${filter === item.key ? ' is-active' : ''}`}
            onClick={() => setFilter(item.key)}
          >
            {item.label}
          </button>
        ))}
      </div>

      <ErrorAlert message={loadError} onRetry={load} />

      {loading ? (
        <Spinner label="Loading requests…" />
      ) : rows.length === 0 ? (
        <EmptyState
          icon="bi-inbox"
          title={filter === 'pending' ? 'Nothing waiting' : 'No requests'}
          hint="Requests appear here when a student asks to leave one of your courses."
        />
      ) : (
        <div className="erean-card">
          {rows.map((row) => (
            <div className="erean-list-row" key={row.id}>
              <div className="erean-list-row__main">
                <p className="erean-list-row__title">
                  {row.student_detail?.full_name || row.student_detail?.username}
                  <span className="erean-card__meta"> wants to drop </span>
                  <Link to={`/courses/${row.course}`}>{row.course_title}</Link>
                </p>
                <span className="erean-card__meta">
                  Asked {formatDateTime(row.created_at)}
                  {row.decided_at && ` · decided ${formatDateTime(row.decided_at)}`}
                  {row.decided_by_name && ` by ${row.decided_by_name}`}
                </span>
                {row.reason && (
                  <p className="erean-card__meta mt-1 mb-0 erean-prewrap">
                    <strong>Reason:</strong> {row.reason}
                  </p>
                )}
              </div>

              {row.status === 'pending' ? (
                <div className="d-flex gap-2 flex-wrap">
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-secondary"
                    onClick={() => decide(row, 'rejected')}
                    disabled={busy === row.id}
                  >
                    Reject
                  </button>
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-danger"
                    onClick={() => decide(row, 'approved')}
                    disabled={busy === row.id}
                  >
                    {busy === row.id ? 'Saving…' : 'Approve drop'}
                  </button>
                </div>
              ) : (
                <span
                  className={`erean-badge erean-badge--${
                    row.status === 'approved' ? 'danger' : 'muted'
                  }`}
                >
                  {row.status}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </>
  );
}
