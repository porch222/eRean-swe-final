import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';

import { finalizeGrade, getGradebook } from '../api/resources';
import { useConfirm } from '../components/ConfirmDialog';
import { errorMessage } from '../utils/formErrors';
import {
  EmptyState,
  ErrorAlert,
  Grade,
  PageHeader,
  Spinner,
  Stat,
  plural,
} from '../components/common';

export default function Gradebook() {
  const { courseId } = useParams();
  const confirm = useConfirm();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [busy, setBusy] = useState(null);

  async function load() {
    setLoading(true);
    setLoadError('');
    const result = await getGradebook(courseId);
    if (result.ok) setData(result.data);
    else setLoadError(errorMessage(result.error));
    setLoading(false);
  }

  useEffect(() => {
    load();

  }, [courseId]);

  async function handleFinalize(row) {
    const ok = await confirm({
      title: `Finalise ${row.name}'s grade?`,
      body:
        'The grade is frozen at its current value. Editing a mark afterwards '
        + 'will not change it.',
      confirmLabel: 'Finalise',
    });
    if (!ok) return;
    setBusy(row.enrollment);
    const result = await finalizeGrade(row.enrollment);
    if (result.ok) await load();
    else setLoadError(errorMessage(result.error));
    setBusy(null);
  }

  if (loading) return <Spinner label="Loading the gradebook…" />;
  if (!data) return <ErrorAlert message={loadError} onRetry={load} />;

  const finalised = data.students.filter((row) => row.finalized).length;

  return (
    <>
      <PageHeader
        backTo={`/courses/${courseId}`}
        backLabel="Back to course"
        title="Gradebook"
        subtitle={data.course_title}
      />

      <ErrorAlert message={loadError} onRetry={load} />

      {data.students.length === 0 ? (
        <EmptyState
          icon="bi-people"
          title="Nobody enrolled yet"
          hint="Students appear here once they enroll."
        />
      ) : (
        <>
          <div className="erean-stats">
            <Stat value={data.students.length} label="Students" icon="bi-people" />
            <Stat value={data.assignments.length} label="Coursework" icon="bi-pencil-square" />
            <Stat value={data.points_possible} label="Points possible" icon="bi-bullseye" />
            <Stat
              value={`${finalised}/${data.students.length}`}
              label="Finalised"
              icon="bi-lock"
            />
          </div>

          <div className="erean-card">
            <div className="erean-table-wrap erean-table-wrap--wide">
              <table className="table align-middle mb-0">
                <thead>
                  <tr>
                    <th>Student</th>
                    {data.assignments.map((assignment) => (
                      <th key={assignment.id} className="text-end">
                        {assignment.title}
                        <span className="erean-gradebook__max">/{assignment.max_score}</span>
                      </th>
                    ))}
                    <th className="text-end">Total</th>
                    <th className="text-end">Final</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {data.students.map((row) => (
                    <tr key={row.student}>
                      <td className="erean-gradebook__name">{row.name}</td>
                      {row.cells.map((cell) => (
                        <td key={cell.assignment} className="text-end">
                          {!cell.submitted ? (
                            <span className="erean-gradebook__missing" title="Not submitted">
                              —
                            </span>
                          ) : cell.grade === null ? (
                            <span className="erean-badge erean-badge--warning">to mark</span>
                          ) : (
                            <span className="erean-num">
                              {Math.round(parseFloat(cell.grade))}
                              {cell.is_late && (
                                <i
                                  className="bi bi-clock-history erean-gradebook__late"
                                  title="Submitted late"
                                  aria-label="late"
                                />
                              )}
                              {cell.attempt > 1 && (
                                <span
                                  className="erean-gradebook__attempt"
                                  title={`Attempt ${cell.attempt}`}
                                >
                                  ×{cell.attempt}
                                </span>
                              )}
                            </span>
                          )}
                        </td>
                      ))}
                      <td className="text-end">
                        <Grade value={row.total} outOf={data.points_possible} />
                      </td>
                      <td className="text-end">
                        {row.finalized ? (
                          <span className="erean-letter">{row.letter_grade}</span>
                        ) : (
                          <span className="erean-card__meta">{row.percent ?? 0}%</span>
                        )}
                      </td>
                      <td className="text-end">
                        {!row.finalized && (
                          <button
                            type="button"
                            className="btn btn-sm btn-outline-primary"
                            onClick={() => handleFinalize(row)}
                            disabled={busy === row.enrollment}
                          >
                            {busy === row.enrollment ? 'Saving…' : 'Finalise'}
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <p className="erean-card__meta mt-2">
            <i className="bi bi-clock-history" aria-hidden="true" /> late ·{' '}
            <span className="erean-gradebook__attempt">×n</span> resubmitted ·{' '}
            <Link to={`/courses/${courseId}`}>back to the course</Link>
          </p>
        </>
      )}
    </>
  );
}
