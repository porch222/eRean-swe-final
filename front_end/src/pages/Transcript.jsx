import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import { getTranscript } from '../api/resources';
import { errorMessage } from '../utils/formErrors';
import {
  EmptyState,
  ErrorAlert,
  PageHeader,
  Spinner,
  Stat,
  plural,
} from '../components/common';

export default function Transcript() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  async function load() {
    setLoading(true);
    setLoadError('');
    const result = await getTranscript();
    if (result.ok) setData(result.data);
    else setLoadError(errorMessage(result.error));
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  if (loading) return <Spinner label="Loading your record…" />;

  return (
    <>
      <PageHeader
        title="Transcript"
        subtitle="Your complete academic record, term by term."
      />

      <ErrorAlert message={loadError} onRetry={load} />

      {!data || data.entries.length === 0 ? (
        <EmptyState
          icon="bi-journal-text"
          title="Nothing on your record yet"
          hint="Courses appear here as soon as you enroll, and earn credits once graded."
          action={
            <Link to="/courses" className="btn btn-primary btn-sm mt-2">
              Browse courses
            </Link>
          }
        />
      ) : (
        <>
          <div className="erean-stats">
            <Stat value={data.credits_earned} label="Credits earned" icon="bi-award" />
            <Stat value={data.credits_attempted} label="Credits attempted" icon="bi-journals" />
            <Stat value={data.gpa ?? '—'} label="GPA" icon="bi-clipboard-data" />
          </div>

          {data.terms.map((term) => (
            <div className="erean-card mb-3" key={term.term_name}>
              <div className="erean-transcript__head">
                <div>
                  <span className="erean-eyebrow">Term</span>
                  <h2 className="erean-card__title">{term.term_name}</h2>
                </div>
                <span className="erean-transcript__credits">
                  {plural(term.credits_earned, 'credit')} earned
                </span>
              </div>

              <div className="erean-table-wrap">
                <table className="table align-middle mb-0">
                  <thead>
                    <tr>
                      <th>Course</th>
                      <th>Major</th>
                      <th className="text-end">Credits</th>
                      <th className="text-end">Score</th>
                      <th className="text-end">Grade</th>
                    </tr>
                  </thead>
                  <tbody>
                    {term.entries.map((entry) => (
                      <tr key={entry.course}>
                        <td>
                          <Link to={`/courses/${entry.course}`}>{entry.course_title}</Link>
                          {entry.status !== 'completed' && (
                            <span className="erean-card__meta"> · {entry.status}</span>
                          )}
                        </td>
                        <td className="erean-card__meta">{entry.major || '—'}</td>
                        <td className="text-end erean-num">
                          {entry.credits_earned}/{entry.credits}
                        </td>
                        <td className="text-end erean-num">
                          {entry.final_score === null ? '—' : `${entry.final_score}%`}
                        </td>
                        <td className="text-end">
                          {entry.letter_grade ? (
                            <span
                              className={`erean-letter${
                                entry.is_passed === false ? ' erean-letter--fail' : ''
                              }`}
                            >
                              {entry.letter_grade}
                            </span>
                          ) : (
                            <span className="erean-card__meta">in progress</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </>
      )}
    </>
  );
}
