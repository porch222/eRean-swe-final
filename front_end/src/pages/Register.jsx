import { useState } from 'react';
import { Link, Navigate, useNavigate } from 'react-router-dom';

import { register } from '../api/resources';
import { useAuth } from '../context/AuthContext';
import { parseApiError } from '../utils/formErrors';
import { FieldError } from '../components/common';

const EMPTY = {
  username: '',
  email: '',
  first_name: '',
  last_name: '',
  password: '',
  password_confirm: '',
};

export default function Register() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState(EMPTY);
  const [errors, setErrors] = useState({});
  const [generalError, setGeneralError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  if (user) return <Navigate to="/dashboard" replace />;

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setErrors({});
    setGeneralError('');

    const result = await register(form);
    if (!result.ok) {
      const { fieldErrors, generalError: message } = parseApiError(result.error);
      setErrors(fieldErrors);
      setGeneralError(result.status === 429 ? 'Too many sign-up attempts. Try again later.' : message);
      setSubmitting(false);
      return;
    }
    navigate('/login?registered=1');
  }

  const field = (name, label, type = 'text', autoComplete) => (
    <div className="mb-3">
      <label className="form-label" htmlFor={name}>
        {label}
      </label>
      <input
        id={name}
        type={type}
        autoComplete={autoComplete}
        className={`form-control${errors[name] ? ' is-invalid' : ''}`}
        value={form[name]}
        onChange={(e) => update(name, e.target.value)}
      />
      <FieldError message={errors[name]} />
    </div>
  );

  return (
    <div className="erean-auth">
      <div className="erean-auth__card">
        <div className="erean-auth__brand">
          <span className="erean-sidebar__mark" aria-hidden="true">
            <i className="bi bi-mortarboard-fill" />
          </span>
          <span className="erean-auth__word">eRean</span>
        </div>
        <p className="erean-auth__tagline">Create your student account</p>

        {generalError && <div className="alert alert-danger">{generalError}</div>}

        <form onSubmit={handleSubmit} noValidate>
          {field('username', 'Username', 'text', 'username')}
          {field('email', 'Email', 'email', 'email')}
          <div className="row">
            <div className="col-6">{field('first_name', 'First name', 'text', 'given-name')}</div>
            <div className="col-6">{field('last_name', 'Last name', 'text', 'family-name')}</div>
          </div>
          {field('password', 'Password', 'password', 'new-password')}
          {field('password_confirm', 'Confirm password', 'password', 'new-password')}

          <button type="submit" className="btn btn-primary w-100" disabled={submitting}>
            {submitting ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <p className="text-center mt-3 mb-0 small text-muted">

          Already registered? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
