import { useCallback, useEffect, useState } from 'react';

import { createUser, deleteUser, listUsers, updateUser } from '../api/resources';
import { useConfirm } from '../components/ConfirmDialog';
import { useAuth } from '../context/AuthContext';
import { errorMessage, parseApiError } from '../utils/formErrors';
import {
  EmptyState,
  ErrorAlert,
  FieldError,
  PageHeader,
  RoleBadge,
  Spinner,
  formatDate,
} from '../components/common';

const BLANK = {
  username: '',
  email: '',
  first_name: '',
  last_name: '',
  password: '',
  role: 'instructor',
};

export default function AdminUsers() {
  const confirm = useConfirm();
  const { user: currentUser } = useAuth();

  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');

  const [showForm, setShowForm] = useState(false);
  const [draft, setDraft] = useState(BLANK);
  const [formErrors, setFormErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError('');
    const result = await listUsers({ search, role: roleFilter });
    if (result.ok) setUsers(result.data.results);
    else setLoadError(errorMessage(result.error));
    setLoading(false);
  }, [search, roleFilter]);

  useEffect(() => {
    const timer = setTimeout(load, 300);
    return () => clearTimeout(timer);
  }, [load]);

  async function handleRoleChange(target, role) {
    const result = await updateUser(target.id, { role });
    if (result.ok) {
      setUsers((rows) => rows.map((row) => (row.id === target.id ? result.data : row)));
    } else {
      setLoadError(errorMessage(result.error));
    }
  }

  async function handleDelete(target) {
    const ok = await confirm({
      title: `Delete ${target.username}?`,
      body:
        'If they are an instructor, their courses and all related coursework ' +
        'will be deleted too.',
      confirmLabel: 'Delete',
      tone: 'danger',
    });
    if (!ok) return;
    const result = await deleteUser(target.id);
    if (result.ok) setUsers((rows) => rows.filter((row) => row.id !== target.id));
    else setLoadError(errorMessage(result.error));
  }

  async function handleCreate(event) {
    event.preventDefault();
    setSaving(true);
    setFormErrors({});
    setFormError('');

    const result = await createUser(draft);
    if (result.ok) {
      setDraft(BLANK);
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
        title="Users"
        subtitle="Manage students, instructors and administrators."
        actions={
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setShowForm((open) => !open)}
          >
            {showForm ? 'Cancel' : 'Add user'}
          </button>
        }
      />

      {showForm && (
        <div className="erean-card mb-3">
          <h2 className="erean-card__title mb-3">Create an account</h2>
          <p className="erean-card__meta mb-3">
            Public registration only creates students, so instructor and admin
            accounts are made here.
          </p>
          {formError && <div className="alert alert-danger">{formError}</div>}
          <form onSubmit={handleCreate} noValidate>
            <div className="row g-3">
              <div className="col-12 col-md-4">
                <label className="form-label" htmlFor="u-username">Username</label>
                <input
                  id="u-username"
                  className={`form-control${formErrors.username ? ' is-invalid' : ''}`}
                  value={draft.username}
                  onChange={(e) => setDraft({ ...draft, username: e.target.value })}
                />
                <FieldError message={formErrors.username} />
              </div>
              <div className="col-12 col-md-4">
                <label className="form-label" htmlFor="u-email">Email</label>
                <input
                  id="u-email"
                  type="email"
                  className={`form-control${formErrors.email ? ' is-invalid' : ''}`}
                  value={draft.email}
                  onChange={(e) => setDraft({ ...draft, email: e.target.value })}
                />
                <FieldError message={formErrors.email} />
              </div>
              <div className="col-12 col-md-4">
                <label className="form-label" htmlFor="u-role">Role</label>
                <select
                  id="u-role"
                  className="form-select"
                  value={draft.role}
                  onChange={(e) => setDraft({ ...draft, role: e.target.value })}
                >
                  <option value="student">Student</option>
                  <option value="instructor">Instructor</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="col-6 col-md-4">
                <label className="form-label" htmlFor="u-first">First name</label>
                <input
                  id="u-first"
                  className="form-control"
                  value={draft.first_name}
                  onChange={(e) => setDraft({ ...draft, first_name: e.target.value })}
                />
              </div>
              <div className="col-6 col-md-4">
                <label className="form-label" htmlFor="u-last">Last name</label>
                <input
                  id="u-last"
                  className="form-control"
                  value={draft.last_name}
                  onChange={(e) => setDraft({ ...draft, last_name: e.target.value })}
                />
              </div>
              <div className="col-12 col-md-4">
                <label className="form-label" htmlFor="u-password">Password</label>
                <input
                  id="u-password"
                  type="password"
                  autoComplete="new-password"
                  className={`form-control${formErrors.password ? ' is-invalid' : ''}`}
                  value={draft.password}
                  onChange={(e) => setDraft({ ...draft, password: e.target.value })}
                />
                <FieldError message={formErrors.password} />
              </div>
            </div>
            <button type="submit" className="btn btn-primary mt-3" disabled={saving}>
              {saving ? 'Creating…' : 'Create user'}
            </button>
          </form>
        </div>
      )}

      <div className="erean-card mb-3">
        <div className="row g-2 align-items-end">
          <div className="col-12 col-md">
            <label className="form-label" htmlFor="u-search">Search</label>
            <input
              id="u-search"
              className="form-control"
              placeholder="Username, email or name"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <div className="col-12 col-md-3">
            <label className="form-label" htmlFor="u-filter">Role</label>
            <select
              id="u-filter"
              className="form-select"
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
            >
              <option value="">All roles</option>
              <option value="student">Students</option>
              <option value="instructor">Instructors</option>
              <option value="admin">Admins</option>
            </select>
          </div>
        </div>
      </div>

      <ErrorAlert message={loadError} onRetry={load} />

      {loading ? (
        <Spinner label="Loading users…" />
      ) : users.length === 0 ? (
        <EmptyState icon="bi-search" title="No users found" hint="Try a different search." />
      ) : (
        <div className="erean-card">
          <div className="erean-table-wrap">
            <table className="table align-middle mb-0">
              <thead>
                <tr>
                  <th scope="col">User</th>
                  <th scope="col">Email</th>
                  <th scope="col">Joined</th>
                  <th scope="col">Role</th>
                  <th scope="col" />
                </tr>
              </thead>
              <tbody>
                {users.map((row) => {
                  const isSelf = row.id === currentUser.id;
                  return (
                    <tr key={row.id}>
                      <td>
                        <strong>{row.full_name}</strong>
                        <div className="erean-card__meta">@{row.username}</div>
                      </td>
                      <td className="erean-card__meta">{row.email || '—'}</td>
                      <td className="erean-card__meta">
                        {formatDate(row.date_joined)}
                      </td>
                      <td>
                        {isSelf ? (
                          <RoleBadge role={row.role} />
                        ) : (
                          <select
                            className="form-select form-select-sm"
                            value={row.role}
                            onChange={(e) => handleRoleChange(row, e.target.value)}
                            aria-label={`Role for ${row.username}`}
                          >
                            <option value="student">Student</option>
                            <option value="instructor">Instructor</option>
                            <option value="admin">Admin</option>
                          </select>
                        )}
                      </td>
                      <td>

                        {!isSelf && (
                          <button
                            type="button"
                            className="btn btn-sm btn-outline-danger"
                            onClick={() => handleDelete(row)}
                          >
                            Delete
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
