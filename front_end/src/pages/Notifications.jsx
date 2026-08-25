import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from '../api/resources';
import { errorMessage } from '../utils/formErrors';
import {
  EmptyState,
  ErrorAlert,
  PageHeader,
  Spinner,
  formatDateTime,
} from '../components/common';

const KIND_LABEL = {
  grade: 'Grade',
  assignment: 'Coursework',
  announcement: 'Announcement',
  reply: 'Discussion',
  drop_request: 'Drop request',
  drop_decision: 'Drop decision',
  attendance: 'Attendance',
};

export default function Notifications() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [unreadOnly, setUnreadOnly] = useState(false);

  async function load() {
    setLoading(true);
    setLoadError('');
    const result = await listNotifications(unreadOnly ? { unread: 'true' } : {});
    if (result.ok) setRows(result.data.results);
    else setLoadError(errorMessage(result.error));
    setLoading(false);
  }

  useEffect(() => {
    load();

  }, [unreadOnly]);

  async function handleRead(row) {
    await markNotificationRead(row.id);
    load();
  }

  async function handleReadAll() {
    await markAllNotificationsRead();
    load();
  }

  const unreadCount = rows.filter((row) => !row.is_read).length;

  return (
    <>
      <PageHeader
        title="Notifications"
        subtitle="Grades, coursework, announcements and replies."
        actions={
          unreadCount > 0 && (
            <button type="button" className="btn btn-outline-secondary" onClick={handleReadAll}>
              Mark all read
            </button>
          )
        }
      />

      <div className="erean-tabs">
        <button
          type="button"
          className={`erean-tab${unreadOnly ? '' : ' is-active'}`}
          onClick={() => setUnreadOnly(false)}
        >
          All
        </button>
        <button
          type="button"
          className={`erean-tab${unreadOnly ? ' is-active' : ''}`}
          onClick={() => setUnreadOnly(true)}
        >
          Unread
        </button>
      </div>

      <ErrorAlert message={loadError} onRetry={load} />

      {loading ? (
        <Spinner label="Loading notifications…" />
      ) : rows.length === 0 ? (
        <EmptyState
          icon="bi-bell"
          title={unreadOnly ? 'Nothing unread' : 'No notifications yet'}
          hint="They appear as your courses move along."
        />
      ) : (
        <div className="erean-card">
          {rows.map((row) => (
            <div
              className={`erean-list-row${row.is_read ? '' : ' is-unread'}`}
              key={row.id}
            >
              <div className="erean-list-row__main">
                <p className="erean-list-row__title">
                  {row.link_url ? (
                    <Link to={row.link_url} onClick={() => handleRead(row)}>
                      {row.message}
                    </Link>
                  ) : (
                    row.message
                  )}
                </p>
                <span className="erean-card__meta">
                  {KIND_LABEL[row.kind] || row.kind} · {formatDateTime(row.created_at)}
                </span>
              </div>
              {!row.is_read && (
                <button
                  type="button"
                  className="btn btn-sm btn-outline-secondary"
                  onClick={() => handleRead(row)}
                >
                  Mark read
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </>
  );
}
