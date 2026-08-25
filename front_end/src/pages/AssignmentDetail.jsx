import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';

import { getAssignment, getCourse } from '../api/resources';
import { useAuth } from '../context/AuthContext';
import QuizBuilder from '../components/QuizBuilder';
import QuizTaker from '../components/QuizTaker';
import SubmissionPanel from '../components/SubmissionPanel';
import { errorMessage } from '../utils/formErrors';
import { EmptyState, ErrorAlert, PageHeader, Spinner, formatDateTime } from '../components/common';

export default function AssignmentDetail() {
  const { courseId, assignmentId } = useParams();
  const { user } = useAuth();

  const [assignment, setAssignment] = useState(null);
  const [course, setCourse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setNotFound(false);
      setLoadError('');

      const [assignmentRes, courseRes] = await Promise.all([
        getAssignment(courseId, assignmentId),
        getCourse(courseId),
      ]);
      if (!active) return;

      if (assignmentRes.status === 404) setNotFound(true);
      else if (!assignmentRes.ok) setLoadError(errorMessage(assignmentRes.error));
      else setAssignment(assignmentRes.data);

      if (courseRes.ok) setCourse(courseRes.data);
      setLoading(false);
    }

    load();
    return () => {
      active = false;
    };
  }, [courseId, assignmentId]);

  if (loading) return <Spinner label="Loading…" />;

  if (notFound) {
    return (
      <EmptyState
        icon="bi-slash-circle"
        title="Assignment not found"
        hint="It may have been deleted, or you may not have access to this course."
      />
    );
  }

  if (!assignment) return <ErrorAlert message={loadError} />;

  const canManage = user.role === 'admin' || course?.instructor === user.id;
  const isQuiz = assignment.type === 'quiz';

  return (
    <>
      <PageHeader
        backTo={`/courses/${courseId}`}
        backLabel={course?.title || 'Back to course'}
        title={assignment.title}
        subtitle={
          `${isQuiz ? 'Quiz' : 'Assignment'} · ${assignment.max_score} points · ` +
          `due ${formatDateTime(assignment.due_date)}`
        }
      />

      <ErrorAlert message={loadError} />

      {assignment.description && (
        <div className="erean-card mb-3">
          <h2 className="erean-card__title">Instructions</h2>
          <p className="mb-0 erean-prewrap">{assignment.description}</p>
        </div>
      )}

      {isQuiz ? (
        canManage ? (
          <QuizBuilder courseId={courseId} assignment={assignment} />
        ) : (
          <QuizTaker courseId={courseId} assignment={assignment} />
        )
      ) : (
        <SubmissionPanel courseId={courseId} assignment={assignment} />
      )}
    </>
  );
}
