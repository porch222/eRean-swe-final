import { Navigate, Outlet } from 'react-router-dom';

import { useAuth } from '../context/AuthContext';
import { Spinner } from './common';

export default function ProtectedRoute({ allowedRoles }) {
  const { user, loading } = useAuth();

  if (loading) return <Spinner label="Checking your session…" />;
  if (!user) return <Navigate to="/login" replace />;

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return (
      <div className="erean-main">
        <div className="alert alert-warning">
          <strong>Not available for your role.</strong> This page is limited to:{' '}
          {allowedRoles.join(', ')}.
        </div>
      </div>
    );
  }

  return <Outlet />;
}
