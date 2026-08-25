import { Link } from 'react-router-dom';

export function Spinner({ label = 'Loading…' }) {
  return (
    <div className="erean-state" role="status">
      <div className="spinner-border text-primary" aria-hidden="true" />
      <p className="erean-state__text mt-3">{label}</p>
    </div>
  );
}

export function ErrorAlert({ message, onRetry }) {
  if (!message) return null;
  return (
    <div className="alert alert-danger d-flex justify-content-between align-items-center gap-3">
      <span>
        <i className="bi bi-exclamation-triangle-fill me-2" aria-hidden="true" />
        {message}
      </span>
      {onRetry && (
        <button type="button" className="btn btn-sm btn-outline-danger" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState({ icon = 'bi-inbox', title, hint, action }) {
  return (
    <div className="erean-state">
      <div className="erean-state__icon" aria-hidden="true">
        <i className={`bi ${icon}`} />
      </div>
      <p className="erean-state__title">{title}</p>
      {hint && <p className="erean-state__text">{hint}</p>}
      {action && <div className="mt-3">{action}</div>}
    </div>
  );
}

const STATUS = {
  published: ['success', 'bi-broadcast'],
  draft: ['warning', 'bi-pencil'],
  archived: ['muted', 'bi-archive'],
  active: ['success', 'bi-check-circle'],
  dropped: ['danger', 'bi-x-circle'],
  completed: ['info', 'bi-patch-check'],
};

export function StatusBadge({ status }) {
  if (!status) return null;
  const [tone, icon] = STATUS[status] || ['muted', ''];
  return (
    <span className={`erean-badge erean-badge--${tone}`}>
      {icon && <i className={`bi ${icon}`} aria-hidden="true" />}
      {status}
    </span>
  );
}

const ROLES = {
  admin: ['danger', 'bi-shield-lock'],
  instructor: ['info', 'bi-person-video3'],
  student: ['muted', 'bi-mortarboard'],
};

export function RoleBadge({ role }) {
  const [tone, icon] = ROLES[role] || ['muted', ''];
  return (
    <span className={`erean-badge erean-badge--${tone}`}>
      <i className={`bi ${icon}`} aria-hidden="true" />
      {role}
    </span>
  );
}

export function ProgressBar({ value }) {
  const percent = Math.min(100, Math.max(0, parseFloat(value) || 0));
  return (
    <div className="erean-progress" title={`${percent}% complete`}>
      <div className="erean-progress__track">
        <div
          className={`erean-progress__bar${percent >= 100 ? ' is-complete' : ''}`}
          style={{ width: `${percent}%` }}
        />
      </div>
      <span className="erean-progress__label">{percent.toFixed(0)}%</span>
    </div>
  );
}

export function Grade({ value, outOf, large }) {
  if (value === null || value === undefined || value === '') {
    return <span className="erean-grade erean-grade--ungraded">Not graded</span>;
  }
  return (
    <span className={`erean-grade${large ? ' erean-grade--lg' : ''}`}>
      {parseFloat(value).toFixed(0)}
      <span className="erean-grade__of">/{outOf}</span>
    </span>
  );
}

export function Stat({ value, label, icon }) {
  return (
    <div className="erean-stat">
      <div className="erean-stat__head">
        {icon && <i className={`bi ${icon}`} aria-hidden="true" />}
        {label}
      </div>
      <div className="erean-stat__value">{value}</div>
    </div>
  );
}

export function PageHeader({ title, subtitle, actions, backTo, backLabel }) {
  return (
    <header className="erean-page-header">
      <div>
        {backTo && (
          <Link to={backTo} className="erean-backlink">
            <i className="bi bi-arrow-left" aria-hidden="true" />
            {backLabel || 'Back'}
          </Link>
        )}
        <h1 className="erean-page-header__title">{title}</h1>
        {subtitle && <p className="erean-page-header__subtitle">{subtitle}</p>}
      </div>
      {actions && <div className="erean-page-header__actions">{actions}</div>}
    </header>
  );
}

export function FieldError({ message }) {
  if (!message) return null;
  return <div className="invalid-feedback d-block">{message}</div>;
}

export function plural(count, singular, pluralForm) {
  return `${count} ${count === 1 ? singular : pluralForm || `${singular}s`}`;
}

export function formatDate(value) {
  if (!value) return '—';
  return new Date(value).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatDateTime(value) {
  if (!value) return '—';
  return new Date(value).toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
