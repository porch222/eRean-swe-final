import { useState } from 'react';

import { changePassword, updateMe } from '../api/resources';
import { useAuth } from '../context/AuthContext';
import { parseApiError } from '../utils/formErrors';
import { FieldError, PageHeader, RoleBadge } from '../components/common';

export default function Profile() {
  const { user, setUser } = useAuth();

  const [profile, setProfile] = useState({
    first_name: user.first_name || '',
    last_name: user.last_name || '',
    email: user.email || '',
  });
  const [profileErrors, setProfileErrors] = useState({});
  const [profileMessage, setProfileMessage] = useState('');
  const [savingProfile, setSavingProfile] = useState(false);

  const [passwords, setPasswords] = useState({
    current_password: '',
    new_password: '',
    new_password_confirm: '',
  });
  const [passwordErrors, setPasswordErrors] = useState({});
  const [passwordMessage, setPasswordMessage] = useState('');
  const [savingPassword, setSavingPassword] = useState(false);

  async function saveProfile(event) {
    event.preventDefault();
    setSavingProfile(true);
    setProfileErrors({});
    setProfileMessage('');

    const result = await updateMe(profile);
    if (result.ok) {
      setUser(result.data);
      setProfileMessage('Profile updated.');
    } else {
      const { fieldErrors, generalError } = parseApiError(result.error);
      setProfileErrors(fieldErrors);
      setProfileMessage(generalError);
    }
    setSavingProfile(false);
  }

  async function savePassword(event) {
    event.preventDefault();
    setSavingPassword(true);
    setPasswordErrors({});
    setPasswordMessage('');

    const result = await changePassword(passwords);
    if (result.ok) {
      setPasswords({ current_password: '', new_password: '', new_password_confirm: '' });
      setPasswordMessage('Password updated.');
    } else {
      const { fieldErrors, generalError } = parseApiError(result.error);
      setPasswordErrors(fieldErrors);
      setPasswordMessage(generalError);
    }
    setSavingPassword(false);
  }

  return (
    <>
      <PageHeader title="My profile" subtitle="Your account details and password." />

      <div className="row g-3">
        <div className="col-12 col-lg-6">
          <div className="erean-card">
            <h2 className="erean-card__title">Account</h2>
            <p className="erean-card__meta mb-3">
              Signed in as <strong>{user.username}</strong> <RoleBadge role={user.role} />

            </p>

            {profileMessage && (
              <div className="alert alert-info py-2">{profileMessage}</div>
            )}

            <form onSubmit={saveProfile} noValidate>
              <div className="mb-3">
                <label className="form-label" htmlFor="first_name">First name</label>
                <input
                  id="first_name"
                  className={`form-control${profileErrors.first_name ? ' is-invalid' : ''}`}
                  value={profile.first_name}
                  onChange={(e) => setProfile({ ...profile, first_name: e.target.value })}
                />
                <FieldError message={profileErrors.first_name} />
              </div>
              <div className="mb-3">
                <label className="form-label" htmlFor="last_name">Last name</label>
                <input
                  id="last_name"
                  className={`form-control${profileErrors.last_name ? ' is-invalid' : ''}`}
                  value={profile.last_name}
                  onChange={(e) => setProfile({ ...profile, last_name: e.target.value })}
                />
                <FieldError message={profileErrors.last_name} />
              </div>
              <div className="mb-3">
                <label className="form-label" htmlFor="email">Email</label>
                <input
                  id="email"
                  type="email"
                  className={`form-control${profileErrors.email ? ' is-invalid' : ''}`}
                  value={profile.email}
                  onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                />
                <FieldError message={profileErrors.email} />
              </div>
              <button type="submit" className="btn btn-primary" disabled={savingProfile}>
                {savingProfile ? 'Saving…' : 'Save changes'}
              </button>
            </form>
          </div>
        </div>

        <div className="col-12 col-lg-6">
          <div className="erean-card">
            <h2 className="erean-card__title mb-3">Change password</h2>

            {passwordMessage && (
              <div className="alert alert-info py-2">{passwordMessage}</div>
            )}

            <form onSubmit={savePassword} noValidate>
              <div className="mb-3">
                <label className="form-label" htmlFor="current_password">Current password</label>
                <input
                  id="current_password"
                  type="password"
                  autoComplete="current-password"
                  className={`form-control${passwordErrors.current_password ? ' is-invalid' : ''}`}
                  value={passwords.current_password}
                  onChange={(e) =>
                    setPasswords({ ...passwords, current_password: e.target.value })
                  }
                />
                <FieldError message={passwordErrors.current_password} />
              </div>
              <div className="mb-3">
                <label className="form-label" htmlFor="new_password">New password</label>
                <input
                  id="new_password"
                  type="password"
                  autoComplete="new-password"
                  className={`form-control${passwordErrors.new_password ? ' is-invalid' : ''}`}
                  value={passwords.new_password}
                  onChange={(e) =>
                    setPasswords({ ...passwords, new_password: e.target.value })
                  }
                />
                <FieldError message={passwordErrors.new_password} />
              </div>
              <div className="mb-3">
                <label className="form-label" htmlFor="new_password_confirm">
                  Confirm new password
                </label>
                <input
                  id="new_password_confirm"
                  type="password"
                  autoComplete="new-password"
                  className={`form-control${passwordErrors.new_password_confirm ? ' is-invalid' : ''}`}
                  value={passwords.new_password_confirm}
                  onChange={(e) =>
                    setPasswords({ ...passwords, new_password_confirm: e.target.value })
                  }
                />
                <FieldError message={passwordErrors.new_password_confirm} />
              </div>
              <button type="submit" className="btn btn-primary" disabled={savingPassword}>
                {savingPassword ? 'Updating…' : 'Update password'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </>
  );
}
