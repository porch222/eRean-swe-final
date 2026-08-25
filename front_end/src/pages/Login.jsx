import { useState } from 'react';
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import { parseApiError } from '../utils/formErrors';
import { FieldError, Spinner } from '../components/common';

export default function Login() {
  const { user, loading, loginUser } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [form, setForm] = useState({ username: '', password: '' });
  const [errors, setErrors] = useState({});
  const [generalError, setGeneralError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (loading) return <Spinner label="Checking your session…" />;
  if (user) return <Navigate to="/dashboard" replace />;

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setErrors({});
    setGeneralError('');

    const result = await loginUser(form.username, form.password);
    if (!result.ok) {
      if (result.status === 429) {
        setGeneralError('Too many attempts. Please wait a minute and try again.');
      } else if (result.status === 401) {
        setGeneralError('Incorrect username or password.');
      } else {
        const { fieldErrors, generalError: message } = parseApiError(result.error);
        setErrors(fieldErrors);
        setGeneralError(message);
      }
      setSubmitting(false);
      return;
    }
    navigate('/dashboard');
  }

  return (
    <div className="erean-auth">
      <div className="erean-auth__card">
        <div className="erean-auth__brand">
          <span className="erean-sidebar__mark" aria-hidden="true">
            <i className="bi bi-mortarboard-fill" />
          </span>
          <span className="erean-auth__word">eRean</span>
        </div>
        <p className="erean-auth__tagline">Online Course Management System</p>

        {searchParams.get('registered') === '1' && (
          <div className="alert alert-success">
            Account created. Sign in to get started.
          </div>
        )}
        {generalError && <div className="alert alert-danger">{generalError}</div>}

        <form onSubmit={handleSubmit} noValidate>
          <div className="mb-3">
            <label className="form-label" htmlFor="username">
              Username
            </label>
            <input
              id="username"
              className={`form-control${errors.username ? ' is-invalid' : ''}`}
              value={form.username}
              onChange={(e) => update('username', e.target.value)}
              autoComplete="username"
              required
            />
            <FieldError message={errors.username} />
          </div>

          <div className="mb-4">
            <label className="form-label" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              className={`form-control${errors.password ? ' is-invalid' : ''}`}
              value={form.password}
              onChange={(e) => update('password', e.target.value)}
              autoComplete="current-password"
              required
            />
            <FieldError message={errors.password} />
          </div>

          <button
            type="submit"
            className="btn btn-primary w-100"
            disabled={submitting}
          >
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p className="text-center mt-3 mb-0 small text-muted">
          No account? <Link to="/register">Register as a student</Link>
        </p>
      </div>
    </div>
  );
}
