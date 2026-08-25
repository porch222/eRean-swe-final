import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { getCurriculumProgress, listCurricula } from '../api/resources';
import { useAuth } from '../context/AuthContext';
import { errorMessage } from '../utils/formErrors';
import {
  EmptyState,
  ErrorAlert,
  PageHeader,
  ProgressBar,
  Spinner,
  Stat,
  plural,
} from '../components/common';

const STATUS_LABEL = {
  not_taken: 'Not taken',
  active: 'In progress',
  completed: 'Completed',
  dropped: 'Dropped',
};

function groupByYearAndTerm(entries) {
  const years = new Map();
  for (const entry of entries) {
    if (!years.has(entry.year_level)) years.set(entry.year_level, new Map());
    const terms = years.get(entry.year_level);
    if (!terms.has(entry.term)) terms.set(entry.term, []);
    terms.get(entry.term).push(entry);
  }
  return [...years.entries()]
    .sort((a, b) => a[0] - b[0])
    .map(([year, terms]) => ({
      year,
      terms: [...terms.entries()]
        .sort((a, b) => a[0] - b[0])
        .map(([term, rows]) => ({ term, rows })),
    }));
}

export default function Curriculum() {
  const { user } = useAuth();

  const [curricula, setCurricula] = useState([]);
  const [selected, setSelected] = useState(null);
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    let cancelled = false;

    async function loadCurricula() {
      if (!user?.major) {
        setLoading(false);
        return;
      }
      const result = await listCurricula({ major: user.major, active: 'true' });
      if (cancelled) return;
      if (result.ok) {
        const list = result.data.results ?? result.data;
        setCurricula(list);

        setSelected(list[0]?.id ?? null);
        if (list.length === 0) setLoading(false);
      } else {
        setLoadError(errorMessage(result.error));
        setLoading(false);
      }
    }

    loadCurricula();
    return () => {
      cancelled = true;
    };
  }, [user?.major]);

  useEffect(() => {
    let cancelled = false;

    async function loadProgress() {
      if (!selected) return;
      setLoading(true);
      setLoadError('');
      const result = await getCurriculumProgress(selected);
      if (cancelled) return;
      if (result.ok) setProgress(result.data);
      else setLoadError(errorMessage(result.error));
      setLoading(false);
    }

    loadProgress();
    return () => {
      cancelled = true;
    };
  }, [selected]);

  if (!user?.major) {
    return (
      <>
        <PageHeader title="My curriculum" />
        <EmptyState
          icon="bi-diagram-3"
          title="No programme assigned"
          hint="Your account isn't attached to a major yet. The registrar assigns
                this — ask an administrator to set it on your record."
        />
      </>
    );
  }

  if (loading) return <Spinner label="Loading your curriculum…" />;

  if (curricula.length === 0) {
    return (
      <>
        <PageHeader title="My curriculum" subtitle={user.major_detail?.name} />
        <ErrorAlert message={loadError} />
        <EmptyState
          icon="bi-diagram-3"
          title="No active curriculum"
          hint="Your major has no published course plan yet."
        />
      </>
    );
  }

  const percent = progress?.percent_complete ?? 0;

  const remaining = progress
    ? Math.max(0, progress.credits_to_graduate - progress.credits_earned_total)
    : 0;

  const requiredLeft = progress
    ? Math.max(0, progress.credits_required - progress.credits_earned_required)
    : 0;

  return (
    <>
      <PageHeader
        title="My curriculum"
        subtitle={
          progress
            ? `${progress.major} · ${progress.curriculum_name}`
            : user.major_detail?.name
        }
        actions={
          curricula.length > 1 && (
            <select
              className="form-select form-select-sm"
              value={selected ?? ''}
              onChange={(e) => setSelected(Number(e.target.value))}
              aria-label="Curriculum version"
            >
              {curricula.map((curriculum) => (
                <option value={curriculum.id} key={curriculum.id}>
                  {curriculum.name} ({curriculum.year})
                </option>
              ))}
            </select>
          )
        }
      />

      <ErrorAlert message={loadError} />

      {progress && (
        <>
          <div className="erean-card erean-plan__hero">
            <div>
              <span className="erean-eyebrow">Progress towards the degree</span>
              <p className="erean-plan__headline">
                {progress.is_complete
                  ? 'Every requirement met.'
                  : remaining > 0
                    ? `${plural(remaining, 'credit')} to go.`
                    : `${plural(requiredLeft, 'required credit')} still outstanding.`}
              </p>
              {progress.is_complete || remaining === 0 || requiredLeft === 0 ? null : (
                <p className="erean-card__meta mb-0">
                  {plural(requiredLeft, 'credit')} of that must come from
                  required courses.
                </p>
              )}
            </div>
            <ProgressBar value={percent} />
          </div>

          <div className="erean-stats">
            <Stat
              value={`${progress.credits_earned_total}/${progress.credits_to_graduate}`}
              label="Credits to graduate"
              icon="bi-mortarboard"
            />
            <Stat
              value={`${progress.credits_earned_required}/${progress.credits_required}`}
              label="Required credits"
              icon="bi-award"
            />
            <Stat
              value={`${progress.credits_earned_elective}/${progress.credits_elective_available}`}
              label="Elective credits"
              icon="bi-stars"
            />
            <Stat
              value={progress.credits_in_progress}
              label="Credits in progress"
              icon="bi-hourglass-split"
            />
          </div>

          {progress.entries.length === 0 ? (
            <EmptyState
              icon="bi-journals"
              title="No courses in this plan"
              hint="The curriculum exists but has no courses on it yet."
            />
          ) : (
            groupByYearAndTerm(progress.entries).map((year) => (
              <div className="erean-card mb-3" key={year.year}>
                <h2 className="erean-card__title mb-3">Year {year.year}</h2>

                {year.terms.map((term) => (
                  <div className="erean-plan__term" key={term.term}>
                    <span className="erean-eyebrow">Term {term.term}</span>
                    <div className="erean-table-wrap">
                      <table className="table align-middle mb-0">
                        <thead>
                          <tr>
                            <th>Course</th>
                            <th>Type</th>
                            <th className="text-end">Credits</th>
                            <th className="text-end">Status</th>
                            <th className="text-end">Grade</th>
                          </tr>
                        </thead>
                        <tbody>
                          {term.rows.map((entry) => (
                            <tr
                              className={entry.passed ? 'erean-plan__row--done' : undefined}
                              key={entry.course}
                            >
                              <td>
                                <Link to={`/courses/${entry.course}`}>
                                  {entry.course_title}
                                </Link>
                              </td>
                              <td className="erean-card__meta">
                                {entry.is_required ? 'Required' : 'Elective'}
                              </td>
                              <td className="text-end erean-num">{entry.credits}</td>
                              <td className="text-end">
                                <span
                                  className={`erean-badge erean-badge--${
                                    entry.passed
                                      ? 'success'
                                      : entry.status === 'active'
                                        ? 'info'
                                        : entry.status === 'dropped'
                                          ? 'danger'
                                          : 'muted'
                                  }`}
                                >
                                  {STATUS_LABEL[entry.status] || entry.status}
                                </span>
                              </td>
                              <td className="text-end">
                                {entry.letter_grade ? (
                                  <span
                                    className={`erean-letter${
                                      entry.passed ? '' : ' erean-letter--fail'
                                    }`}
                                  >
                                    {entry.letter_grade}
                                  </span>
                                ) : (
                                  <span className="erean-card__meta">—</span>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ))}
              </div>
            ))
          )}
        </>
      )}
    </>
  );
}
