import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { listMySubmissions } from '../api/resources';
import { errorMessage } from '../utils/formErrors';
import {
  EmptyState,
  ErrorAlert,
  Grade,
  PageHeader,
  Spinner,
  Stat,
  formatDateTime,
  plural,
} from '../components/common';

function averagePercent(rows) {
  const graded = rows.filter((row) => row.grade !== null);
  if (graded.length === 0) return null;
  const total = graded.reduce((sum, row) => sum + (parseFloat(row.grade) / row.max_score) * 100, 0);
  return Math.round(total / graded.length);
}

function courseSummaries(rows) {
  const byCourse = new Map();
  for (const row of rows) {
    if (!byCourse.has(row.course)) {
      byCourse.set(row.course, {
        id: row.course,
        title: row.course_title,
        category: row.course_category,
        rows: [],
      });
    }
    byCourse.get(row.course).rows.push(row);
  }
  return [...byCourse.values()].sort((a, b) => a.title.localeCompare(b.title));
}

function FilterCard({ eyebrow, title, count, average, selected, onSelect }) {
  return (
    <button
      type="button"
      className={`erean-filter-card${selected ? ' is-selected' : ''}`}
      aria-pressed={selected}
      onClick={onSelect}
    >
      <span className="erean-eyebrow">{eyebrow}</span>
      <span className="erean-filter-card__title">{title}</span>
      <span className="erean-filter-card__foot">
        <span className="erean-filter-card__count">{plural(count, 'result')}</span>
        <span className="erean-filter-card__avg">{average === null ? '—' : `${average}%`}</span>
      </span>
    </button>
  );
}

export default function MyGrades() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  const [courseId, setCourseId] = useState(null);

  async function load() {
    setLoading(true);
    setLoadError('');
    const result = await listMySubmissions();
    if (result.ok) setRows(result.data.results);
    else setLoadError(errorMessage(result.error));
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  const courses = courseSummaries(rows);

  const activeId = courses.some((c) => c.id === courseId) ? courseId : null;
  const shown = activeId === null ? rows : rows.filter((row) => row.course === activeId);
  const graded = shown.filter((row) => row.grade !== null);
  const average = averagePercent(shown);
  const activeCourse = courses.find((c) => c.id === activeId);

  return (
    <>
      <PageHeader
        title="My grades"
        subtitle="Results and instructor feedback across all your courses."
      />

      <ErrorAlert message={loadError} onRetry={load} />

      {loading ? (
        <Spinner label="Loading your results…" />
      ) : rows.length === 0 ? (
        <EmptyState
          icon="bi-clipboard-data"
          title="No results yet"
          hint="Submit an assignment or take a quiz and your grades will show up here."
        />
      ) : (
        <>
          <div className="erean-filters" role="group" aria-label="Filter results by course">
            <FilterCard
              eyebrow="Everything"
              title="All courses"
              count={rows.length}
              average={averagePercent(rows)}
              selected={activeId === null}
              onSelect={() => setCourseId(null)}
            />
            {courses.map((course) => (
              <FilterCard
                key={course.id}
                eyebrow={course.category}
                title={course.title}
                count={course.rows.length}
                average={averagePercent(course.rows)}
                selected={activeId === course.id}
                onSelect={() => setCourseId(course.id)}
              />
            ))}
          </div>

          <div className="erean-stats">
            <Stat value={shown.length} label="Submitted" icon="bi-upload" />
            <Stat value={graded.length} label="Graded" icon="bi-check2-circle" />
            <Stat
              value={average === null ? '—' : `${average}%`}
              label="Average"
              icon="bi-clipboard-data"
            />
          </div>

          <div className="erean-card">
            {activeCourse && (
              <p className="erean-card__meta mb-3">
                Showing {plural(shown.length, 'result')} from {activeCourse.title}.{' '}
                <button type="button" className="erean-linkbutton" onClick={() => setCourseId(null)}>
                  Show all courses
                </button>
              </p>
            )}
            {shown.map((row) => (
              <div className="erean-list-row" key={row.id}>
                <div className="erean-list-row__main">
                  <p className="erean-list-row__title">
                    <Link to={`/courses/${row.course}/assignments/${row.assignment}`}>
                      {row.assignment_title}
                    </Link>{' '}
                    <span className="erean-badge">{row.assignment_type}</span>
                  </p>
                  <span className="erean-card__meta">
                    {row.course_title} · submitted {formatDateTime(row.submitted_at)}
                  </span>
                  {row.feedback && (
                    <p className="erean-card__meta mt-1 mb-0 erean-prewrap">
                      <strong>Feedback:</strong> {row.feedback}
                    </p>
                  )}
                </div>
                <div className="text-end">
                  <Grade value={row.grade} outOf={row.max_score} />
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </>
  );
}
