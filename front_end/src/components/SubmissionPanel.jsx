import { useEffect, useState } from 'react';

import {
  createSubmission,
  downloadSubmission,
  gradeSubmission,
  listSubmissions,
} from '../api/resources';
import { useAuth } from '../context/AuthContext';
import { errorMessage, parseApiError } from '../utils/formErrors';
import {
  EmptyState,
  ErrorAlert,
  FieldError,
  Grade,
  Spinner,
  StatusBadge,
  formatDateTime,
} from './common';

const MAX_MB = 50;
const ALLOWED = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png', '.zip'];

export default function SubmissionPanel({ courseId, assignment }) {
  const { user } = useAuth();
  const isStudent = user.role === 'student';

  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  const [file, setFile] = useState(null);
  const [uploadErrors, setUploadErrors] = useState({});
  const [uploadError, setUploadError] = useState('');
  const [uploading, setUploading] = useState(false);

  const [grading, setGrading] = useState({});
  const [savingId, setSavingId] = useState(null);

  async function load() {
    setLoading(true);
    setLoadError('');
    const result = await listSubmissions(courseId, assignment.id);
    if (result.ok) {
      setSubmissions(result.data.results);
      const initial = {};
      result.data.results.forEach((row) => {
        initial[row.id] = {
          grade: row.grade ?? '',
          feedback: row.feedback ?? '',
        };
      });
      setGrading(initial);
    } else {
      setLoadError(errorMessage(result.error));
    }
    setLoading(false);
  }

  useEffect(() => {
    load();

  }, [courseId, assignment.id]);

  async function handleUpload(event) {
    event.preventDefault();
    setUploadErrors({});
    setUploadError('');

    if (!file) {
      setUploadErrors({ file_url: 'Please choose a file.' });
      return;
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      setUploadErrors({ file_url: `File must not exceed ${MAX_MB}MB.` });
      return;
    }
    const name = file.name.toLowerCase();
    if (!ALLOWED.some((ext) => name.endsWith(ext))) {
      setUploadErrors({ file_url: `Allowed file types: ${ALLOWED.join(', ')}.` });
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file_url', file);
    const result = await createSubmission(courseId, assignment.id, formData);
    if (result.ok) {
      setFile(null);
      load();
    } else {
      const { fieldErrors, generalError } = parseApiError(result.error);
      setUploadErrors(fieldErrors);
      setUploadError(generalError);
    }
    setUploading(false);
  }

  async function handleGrade(submission) {
    setSavingId(submission.id);
    setLoadError('');
    const entry = grading[submission.id];
    const result = await gradeSubmission(courseId, assignment.id, submission.id, {
      grade: entry.grade === '' ? null : Number(entry.grade),
      feedback: entry.feedback,
    });
    if (result.ok) {
      setSubmissions((rows) =>
        rows.map((row) => (row.id === submission.id ? result.data : row)),
      );
    } else {
      setLoadError(errorMessage(result.error));
    }
    setSavingId(null);
  }

  async function handleDownload(submission) {
    const result = await downloadSubmission(
      courseId,
      assignment.id,
      submission.id,
      submission.filename,
    );
    if (!result.ok) setLoadError(errorMessage(result.error));
  }

  if (loading) return <Spinner label="Loading submissions…" />;

  if (isStudent) {
    const mine = submissions[0];

    if (mine) {
      return (
        <div className="erean-card">
          <h3 className="erean-card__title">Your submission</h3>
          <p className="erean-card__meta">
            Submitted {formatDateTime(mine.submitted_at)} · {mine.filename}
          </p>
          <ErrorAlert message={loadError} />
          <div className="mt-3">
            {mine.is_graded ? (
              <>
                <p className="mb-1">
                  <Grade value={mine.grade} outOf={assignment.max_score} />{' '}
                  <StatusBadge status="completed" />
                </p>
                {mine.feedback && (
                  <div className="alert alert-light border mt-2 mb-0">
                    <strong>Feedback:</strong>
                    <p className="mb-0 erean-prewrap">{mine.feedback}</p>
                  </div>
                )}
              </>
            ) : (
              <p className="text-muted mb-0">Not graded yet.</p>
            )}
          </div>
          <button
            type="button"
            className="btn btn-sm btn-outline-primary mt-3"
            onClick={() => handleDownload(mine)}
          >
            Download my file
          </button>
        </div>
      );
    }

    if (assignment.is_past_due) {
      return (
        <EmptyState
          icon="bi-clock-history"
          title="This assignment is past its due date"
          hint="Submissions are closed. Contact your instructor if you need an extension."
        />
      );
    }

    return (
      <div className="erean-card">
        <h3 className="erean-card__title mb-3">Submit your work</h3>
        {uploadError && <div className="alert alert-danger">{uploadError}</div>}
        <form onSubmit={handleUpload} noValidate>
          <div className="mb-3">
            <label className="form-label" htmlFor="sub-file">
              File (max {MAX_MB}MB)
            </label>
            <input
              id="sub-file"
              type="file"
              accept={ALLOWED.join(',')}
              className={`form-control${uploadErrors.file_url ? ' is-invalid' : ''}`}
              onChange={(e) => setFile(e.target.files[0] || null)}
            />
            <FieldError message={uploadErrors.file_url} />
            <div className="form-text">Allowed: {ALLOWED.join(', ')}</div>
          </div>
          <button type="submit" className="btn btn-primary" disabled={uploading}>
            {uploading ? 'Uploading…' : 'Submit'}
          </button>
          <p className="erean-card__meta mt-2 mb-0">
            You can only submit once, so check your file before uploading.
          </p>
        </form>
      </div>
    );
  }

  return (
    <>
      <ErrorAlert message={loadError} onRetry={load} />
      {submissions.length === 0 ? (
        <EmptyState icon="bi-inbox" title="No submissions yet" hint="Students' work will appear here." />
      ) : (
        <div className="erean-card">
          <div className="erean-table-wrap erean-table-wrap--wide">
            <table className="table align-middle mb-0">
              <thead>
                <tr>
                  <th scope="col">Student</th>
                  <th scope="col">Submitted</th>
                  <th scope="col">File</th>
                  <th scope="col" style={{ width: 110 }}>Grade</th>
                  <th scope="col">Feedback</th>
                  <th scope="col" />
                </tr>
              </thead>
              <tbody>
                {submissions.map((submission) => (
                  <tr key={submission.id}>
                    <td>
                      <strong>{submission.student_detail?.full_name}</strong>
                      <div className="erean-card__meta">
                        {submission.is_graded ? (
                          <span className="erean-badge erean-badge--success">graded</span>
                        ) : (
                          <span className="erean-badge erean-badge--warning">not graded</span>
                        )}
                      </div>
                    </td>
                    <td className="erean-card__meta">
                      {formatDateTime(submission.submitted_at)}
                    </td>
                    <td>
                      {submission.filename ? (
                        <button
                          type="button"
                          className="btn btn-sm btn-outline-primary"
                          onClick={() => handleDownload(submission)}
                        >
                          Download
                        </button>
                      ) : (
                        <span className="erean-card__meta">—</span>
                      )}
                    </td>
                    <td>
                      <input
                        type="number"
                        min="0"
                        max={assignment.max_score}
                        className="form-control form-control-sm"
                        aria-label={`Grade for ${submission.student_detail?.username}`}
                        value={grading[submission.id]?.grade ?? ''}
                        onChange={(e) =>
                          setGrading((current) => ({
                            ...current,
                            [submission.id]: {
                              ...current[submission.id],
                              grade: e.target.value,
                            },
                          }))
                        }
                      />
                      <div className="erean-card__meta">/ {assignment.max_score}</div>
                    </td>
                    <td style={{ minWidth: 200 }}>
                      <textarea
                        rows={2}
                        className="form-control form-control-sm"
                        aria-label={`Feedback for ${submission.student_detail?.username}`}
                        value={grading[submission.id]?.feedback ?? ''}
                        onChange={(e) =>
                          setGrading((current) => ({
                            ...current,
                            [submission.id]: {
                              ...current[submission.id],
                              feedback: e.target.value,
                            },
                          }))
                        }
                      />
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-sm btn-primary"
                        onClick={() => handleGrade(submission)}
                        disabled={savingId === submission.id}
                      >
                        {savingId === submission.id ? 'Saving…' : 'Save'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  );
}
