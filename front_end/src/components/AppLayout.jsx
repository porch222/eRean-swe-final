import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';

import NotificationBell from './NotificationBell';
import Sidebar from './Sidebar';

const TITLES = [
  [/^\/dashboard/, 'Dashboard'],
  [/^\/courses\/\d+\/gradebook/, 'Gradebook'],
  [/^\/courses\/\d+\/assignments/, 'Coursework'],
  [/^\/courses\/\d+/, 'Course'],
  [/^\/courses/, 'Courses'],
  [/^\/enrollments/, 'My courses'],
  [/^\/grades/, 'My grades'],
  [/^\/profile/, 'Profile'],
  [/^\/notifications/, 'Notifications'],
  [/^\/transcript/, 'Transcript'],
  [/^\/admin\/academics/, 'Academic setup'],
  [/^\/admin\/drop-requests/, 'Drop requests'],
  [/^\/admin\/users/, 'Users'],
  [/^\/admin\/approvals/, 'Course approvals'],
  [/^\/admin\/activity/, 'Activity log'],
];

export default function AppLayout({ children }) {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();

  useEffect(() => setOpen(false), [pathname]);

  const title = TITLES.find(([pattern]) => pattern.test(pathname))?.[1] || 'eRean';

  return (
    <div className="erean-shell">
      <Sidebar open={open} onNavigate={() => setOpen(false)} />
      {open && <div className="erean-scrim" onClick={() => setOpen(false)} aria-hidden="true" />}

      <div className="erean-body">
        <header className="erean-topbar">
          <button
            type="button"
            className="erean-burger"
            onClick={() => setOpen((value) => !value)}
            aria-label="Toggle navigation"
          >
            <i className="bi bi-list" />
          </button>
          <p className="erean-topbar__title">{title}</p>
          <NotificationBell />
        </header>

        <main className="erean-main">{children}</main>
      </div>
    </div>
  );
}
