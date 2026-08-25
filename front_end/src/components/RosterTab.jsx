import { useEffect, useState } from 'react';

import { getCoursePerformance, listEnrollments, updateEnrollment } from '../api/resources';
import { errorMessage } from '../utils/formErrors';
import { EmptyState, ErrorAlert, ProgressBar, Spinner, Stat, StatusBadge, formatDate } from './common';

export default function RosterTab({ courseId }) {
  const [rows, setRows] = useState([]);
  const [performance, setPerformance] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  async function load() {
    setLoading(true);
    setLoadError('');
    const [enrollRes, perfRes] = await Promise.all([
      listEnrollments({ course: courseId }),
      getCoursePerformance(courseId),
    ]);
    if (enrollRes.ok) setRows(enrollRes.data.results);
    else setLoadError(errorMessage(enrollRes.error));
    if (perfRes.ok) setPerformance(perfRes.data);
    setLoading(false);
  }

  useEffect(() => {
    load();

  }, [courseId]);

  async function handleStatusChange(enrollment, status) {
    const result = await updateEnrollment(enrollment.id, { status });
    if (result.ok) {
      setRows((current) =>
        current.map((row) => (row.id === enrollment.id ? { ...row, status } : row)),
      );
    } else {
      setLoadError(errorMessage(result.error));
    }
  }

  if (loading) return <Spinner label="Loading roster…" />;

  return (
    <>
      <ErrorAlert message={loadError} onRetry={load} />

      {performance && (
        <div className="erean-stats">
          <Stat value={performance.students_enrolled} label="Enrolled" icon="bi-people" />
          <Stat value={performance.assignments} label="Assignments" icon="bi-pencil-square" />
          <Stat
            value={`${performance.graded_submissions}/${performance.submissions}`}
            label="Graded"
            icon="bi-check2-circle"
          />
          <Stat
            value={`${parseFloat(performance.average_progress).toFixed(0)}%`}
            label="Avg progress"
            icon="bi-graph-up"
          />
          <Stat
            value={
              performance.average_grade === null
                ? '—'
                : parseFloat(performance.average_grade).toFixed(1)
            }
            label="Avg grade"
            icon="bi-clipboard-data"
          />
        </div>
      )}

      {rows.length === 0 ? (
        <EmptyState icon="bi-people" title="Nobody enrolled yet" hint="Students will appear here once they enroll." />
      ) : (
        <div className="erean-card">
          <div className="erean-table-wrap">
            <table className="table align-middle mb-0">
              <thead>
                <tr>
                  <th scope="col">Student</th>
                  <th scope="col">Enrolled</th>
                  <th scope="col">Progress</th>
                  <th scope="col">Status</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr key={row.id}>
                    <td>
                      <strong>{row.student_detail?.full_name}</strong>
                      <div className="erean-card__meta">{row.student_detail?.email}</div>
                    </td>
                    <td>{formatDate(row.enrolled_at)}</td>
                    <td style={{ minWidth: 140 }}>
                      <ProgressBar value={row.progress} />
                    </td>
                    <td>
                      <select
                        className="form-select form-select-sm"
                        value={row.status}
                        onChange={(e) => handleStatusChange(row, e.target.value)}
                        aria-label={`Status for ${row.student_detail?.username}`}
                      >
                        <option value="active">Active</option>
                        <option value="completed">Completed</option>
                        <option value="dropped">Dropped</option>
                      </select>
                      <div className="mt-1">
                        <StatusBadge status={row.status} />
                      </div>
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
