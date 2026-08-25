import { Link } from 'react-router-dom';

export default function NotFound() {
  return (
    <div className="erean-auth">
      <div className="erean-auth__card text-center">
        <div className="erean-state__icon" aria-hidden="true">
          <i className="bi bi-signpost-split" />
        </div>
        <h1 className="h4">Page not found</h1>
        <p className="text-muted">
          That address doesn't match anything in eRean.
        </p>
        <Link to="/dashboard" className="btn btn-primary">
          Back to dashboard
        </Link>
      </div>
    </div>
  );
}
