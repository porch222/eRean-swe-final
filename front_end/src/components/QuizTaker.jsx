import { useEffect, useState } from 'react';

import { listAttempts, listQuestions, submitAttempt } from '../api/resources';
import { errorMessage } from '../utils/formErrors';
import { EmptyState, ErrorAlert, Grade, Spinner, formatDateTime } from './common';

export default function QuizTaker({ courseId, assignment }) {
  const [questions, setQuestions] = useState([]);
  const [attempt, setAttempt] = useState(null);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    setLoading(true);
    setLoadError('');
    const [questionRes, attemptRes] = await Promise.all([
      listQuestions(courseId, assignment.id),
      listAttempts(courseId, assignment.id),
    ]);
    if (questionRes.ok) setQuestions(questionRes.data.results);
    else setLoadError(errorMessage(questionRes.error));
    if (attemptRes.ok && attemptRes.data.results.length > 0) {
      setAttempt(attemptRes.data.results[0]);
    }
    setLoading(false);
  }

  useEffect(() => {
    load();

  }, [courseId, assignment.id]);

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitting(true);
    setLoadError('');

    const payload = questions.map((question) => {
      const value = answers[question.id];
      if (question.type === 'written') {
        return { question: question.id, text_answer: value || '' };
      }
      if (question.type === 'multiple') {
        return { question: question.id, selected_choices: value || [] };
      }
      return { question: question.id, selected_choice: Number(value) };
    });

    const result = await submitAttempt(courseId, assignment.id, payload);
    if (result.ok) setAttempt(result.data);
    else setLoadError(errorMessage(result.error));
    setSubmitting(false);
  }

  if (loading) return <Spinner label="Loading quiz…" />;

  if (attempt) {

    const answerByQuestion = {};
    (attempt.answers || []).forEach((answer) => {
      answerByQuestion[answer.question] = answer;
    });

    return (
      <>
        <div className="erean-card mb-3 text-center">
          <p className="erean-card__meta mb-1">Your score</p>
          <p className="mb-1">
            <Grade value={attempt.score} outOf={assignment.max_score} large />
          </p>
          <p className="erean-card__meta mb-0">
            Submitted {formatDateTime(attempt.submitted_at)} · one attempt only
          </p>
        </div>

        {questions.map((question, index) => {
          const answer = answerByQuestion[question.id];
          return (
            <div className="erean-question" key={question.id}>
              <p className="fw-semibold mb-2">
                {index + 1}. {question.text}{' '}
                <span
                  className={`erean-badge erean-badge--${answer?.is_correct ? 'success' : 'danger'}`}
                >
                  {answer?.is_correct ? 'correct' : 'incorrect'}
                </span>
              </p>
              {question.choices.map((choice) => {
                const picked = answer?.selected_choice === choice.id;
                let className = 'erean-choice';
                if (picked) {
                  className += answer.is_correct
                    ? ' erean-choice--correct'
                    : ' erean-choice--wrong';
                }
                return (
                  <div key={choice.id} className={className}>
                    <span aria-hidden="true">{picked ? '●' : '○'}</span>
                    <span>{choice.text}</span>
                    {picked && <span className="erean-card__meta ms-auto">your answer</span>}
                  </div>
                );
              })}
            </div>
          );
        })}
      </>
    );
  }

  if (questions.length === 0) {
    return (
      <EmptyState
        icon="bi-patch-question"
        title="This quiz has no questions yet"
        hint="Check back once your instructor has finished setting it up."
      />
    );
  }

  if (assignment.is_past_due) {
    return (
      <EmptyState
        icon="bi-clock-history"
        title="This quiz has closed"
        hint="The due date has passed and it can no longer be attempted."
      />
    );
  }

  const allAnswered = questions.every((question) => {
    const value = answers[question.id];
    if (question.type === 'written') return Boolean(value && value.trim());
    if (question.type === 'multiple') return Array.isArray(value) && value.length > 0;
    return Boolean(value);
  });

  const hasWritten = questions.some((question) => question.type === 'written');

  return (
    <form onSubmit={handleSubmit}>
      <ErrorAlert message={loadError} />

      <div className="alert alert-info">
        You have <strong>one attempt</strong>. Answer every question, then submit.
        {hasWritten && (
          <>
            {' '}This quiz has written answers, so your score is not final until your
            instructor marks them.
          </>
        )}
      </div>

      {questions.map((question, index) => (
        <div className="erean-question" key={question.id}>
          <p className="fw-semibold mb-2">
            {index + 1}. {question.text}{' '}
            <span className="erean-badge">{question.points} pts</span>
          </p>
          {question.type === 'written' ? (
            <textarea
              rows={4}
              className="form-control"
              placeholder="Write your answer…"
              value={answers[question.id] || ''}
              onChange={(e) =>
                setAnswers((current) => ({ ...current, [question.id]: e.target.value }))
              }
            />
          ) : (
            question.choices.map((choice) => {
              const multiple = question.type === 'multiple';
              const picked = multiple
                ? (answers[question.id] || []).includes(choice.id)
                : answers[question.id] === choice.id;
              return (
                <label className="erean-choice" key={choice.id}>
                  <input
                    type={multiple ? 'checkbox' : 'radio'}
                    className="form-check-input mt-0"
                    name={`question-${question.id}`}
                    checked={picked}
                    onChange={() =>
                      setAnswers((current) => {
                        if (!multiple) return { ...current, [question.id]: choice.id };
                        const chosen = current[question.id] || [];
                        return {
                          ...current,
                          [question.id]: chosen.includes(choice.id)
                            ? chosen.filter((id) => id !== choice.id)
                            : [...chosen, choice.id],
                        };
                      })
                    }
                  />
                  <span>{choice.text}</span>
                </label>
              );
            })
          )}
          {question.type === 'multiple' && (
            <p className="erean-card__meta mt-1 mb-0">Pick every correct answer.</p>
          )}
        </div>
      ))}

      <button
        type="submit"
        className="btn btn-primary"
        disabled={!allAnswered || submitting}
      >
        {submitting ? 'Submitting…' : 'Submit quiz'}
      </button>
      {!allAnswered && (
        <p className="erean-card__meta mt-2 mb-0">
          Answer all {questions.length} questions to submit.
        </p>
      )}
    </form>
  );
}
