import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';

import {
  getUnreadCount,
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
} from '../api/resources';
import { formatDateTime } from './common';

const KIND_ICON = {
  grade: 'bi-clipboard-data',
  assignment: 'bi-pencil-square',
  announcement: 'bi-megaphone',
  reply: 'bi-chat-left-text',
  drop_request: 'bi-box-arrow-right',
  drop_decision: 'bi-check2-square',
  attendance: 'bi-calendar-check',
};

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [rows, setRows] = useState([]);
  const [unread, setUnread] = useState(0);
  const panelRef = useRef(null);

  async function refreshCount() {
    const result = await getUnreadCount();
    if (result.ok) setUnread(result.data.unread);
  }

  useEffect(() => {
    refreshCount();
  }, []);

  useEffect(() => {
    if (!open) return undefined;
    function onClick(event) {
      if (panelRef.current && !panelRef.current.contains(event.target)) setOpen(false);
    }
    function onKey(event) {
      if (event.key === 'Escape') setOpen(false);
    }
    document.addEventListener('mousedown', onClick);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onClick);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  async function toggle() {
    const next = !open;
    setOpen(next);
    if (next) {
      const result = await listNotifications();
      if (result.ok) setRows(result.data.results.slice(0, 8));
    }
  }

  async function handleRead(row) {
    if (row.is_read) return;
    await markNotificationRead(row.id);
    setRows((current) =>
      current.map((item) => (item.id === row.id ? { ...item, is_read: true } : item)),
    );
    refreshCount();
  }

  async function handleReadAll() {
    await markAllNotificationsRead();
    setRows((current) => current.map((item) => ({ ...item, is_read: true })));
    setUnread(0);
  }

  return (
    <div className="erean-bell" ref={panelRef}>
      <button
        type="button"
        className="erean-bell__button"
        onClick={toggle}
        aria-label={unread ? `Notifications, ${unread} unread` : 'Notifications'}
        aria-expanded={open}
      >
        <i className="bi bi-bell" aria-hidden="true" />
        {unread > 0 && <span className="erean-bell__count">{unread > 9 ? '9+' : unread}</span>}
      </button>

      {open && (
        <div className="erean-bell__panel">
          <div className="erean-bell__head">
            <span className="erean-eyebrow">Notifications</span>
            {unread > 0 && (
              <button type="button" className="erean-linkbutton" onClick={handleReadAll}>
                Mark all read
              </button>
            )}
          </div>

          {rows.length === 0 ? (
            <p className="erean-bell__empty">Nothing yet.</p>
          ) : (
            <ul className="erean-bell__list">
              {rows.map((row) => {
                const body = (
                  <>
                    <i
                      className={`bi ${KIND_ICON[row.kind] || 'bi-dot'}`}
                      aria-hidden="true"
                    />
                    <span className="erean-bell__text">
                      {row.message}
                      <span className="erean-bell__when">{formatDateTime(row.created_at)}</span>
                    </span>
                  </>
                );
                return (
                  <li
                    key={row.id}
                    className={`erean-bell__item${row.is_read ? '' : ' is-unread'}`}
                  >
                    {row.link_url ? (
                      <Link to={row.link_url} onClick={() => { handleRead(row); setOpen(false); }}>
                        {body}
                      </Link>
                    ) : (
                      <button type="button" onClick={() => handleRead(row)}>{body}</button>
                    )}
                  </li>
                );
              })}
            </ul>
          )}

          <Link
            to="/notifications"
            className="erean-bell__all"
            onClick={() => setOpen(false)}
          >
            See all
          </Link>
        </div>
      )}
    </div>
  );
}
