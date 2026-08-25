import { NavLink, useNavigate } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';

const NAV = {
  student: [
    {
      section: 'Learn',
      links: [
        { to: '/dashboard', label: 'Dashboard', icon: 'bi-grid-1x2' },
        { to: '/courses', label: 'Browse courses', icon: 'bi-compass' },
        { to: '/enrollments', label: 'My courses', icon: 'bi-journal-bookmark' },
        { to: '/grades', label: 'My grades', icon: 'bi-bar-chart' },
        { to: '/transcript', label: 'Transcript', icon: 'bi-journal-text' },
        { to: '/curriculum', label: 'My curriculum', icon: 'bi-diagram-3' },
      ],
    },
  ],
  instructor: [
    {
      section: 'Teach',
      links: [
        { to: '/dashboard', label: 'Dashboard', icon: 'bi-grid-1x2' },
        { to: '/courses', label: 'My courses', icon: 'bi-journals' },
        { to: '/drop-requests', label: 'Drop requests', icon: 'bi-box-arrow-right' },
      ],
    },
  ],
  admin: [
    {
      section: 'Overview',
      links: [
        { to: '/dashboard', label: 'Dashboard', icon: 'bi-grid-1x2' },
        { to: '/courses', label: 'Courses', icon: 'bi-journals' },
      ],
    },
    {
      section: 'Administration',
      links: [
        { to: '/admin/users', label: 'Users', icon: 'bi-people' },
        { to: '/admin/academics', label: 'Academic setup', icon: 'bi-diagram-3' },
        { to: '/drop-requests', label: 'Drop requests', icon: 'bi-box-arrow-right' },
        { to: '/admin/approvals', label: 'Approvals', icon: 'bi-check2-square' },
        { to: '/admin/activity', label: 'Activity log', icon: 'bi-clock-history' },
      ],
    },
  ],
};

function initials(user) {
  const first = user.first_name?.[0] || user.username[0];
  const last = user.last_name?.[0] || '';
  return (first + last).toUpperCase();
}

export default function Sidebar({ open, onNavigate }) {
  const { user, logoutUser } = useAuth();
  const navigate = useNavigate();

  if (!user) return null;

  async function handleLogout() {
    await logoutUser();
    navigate('/login');
  }

  return (
    <aside className={`erean-sidebar${open ? ' is-open' : ''}`}>
      <div className="erean-sidebar__brand">
        <span className="erean-sidebar__mark" aria-hidden="true">
          <i className="bi bi-mortarboard-fill" />
        </span>
        <span className="erean-sidebar__word">eRean</span>
      </div>

      <nav className="erean-sidebar__nav">
        {(NAV[user.role] || []).map((group) => (
          <div key={group.section}>
            <p className="erean-sidebar__section">{group.section}</p>
            {group.links.map((link) => (
              <NavLink
                key={link.to}
                to={link.to}
                onClick={onNavigate}
                className={({ isActive }) => `erean-navlink${isActive ? ' is-active' : ''}`}
              >
                <i className={`bi ${link.icon}`} aria-hidden="true" />
                {link.label}
              </NavLink>
            ))}
          </div>
        ))}
      </nav>

      <div className="erean-sidebar__foot">
        <NavLink to="/profile" className="erean-user" onClick={onNavigate}>
          <span className="erean-avatar" aria-hidden="true">{initials(user)}</span>
          <span className="flex-grow-1 min-w-0">
            <span className="erean-user__name d-block">{user.full_name || user.username}</span>
            <span className="erean-user__role">{user.role}</span>
          </span>
        </NavLink>
        <button
          type="button"
          className="btn btn-outline-secondary btn-sm w-100 mt-2"
          onClick={handleLogout}
        >
          <i className="bi bi-box-arrow-right me-1" aria-hidden="true" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
