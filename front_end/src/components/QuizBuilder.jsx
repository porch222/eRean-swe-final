import { useEffect, useState } from 'react';

import {
  createChoice,
  createQuestion,
  deleteChoice,
  deleteQuestion,
  listAttempts,
  listQuestions,
} from '../api/resources';
import { errorMessage } from '../utils/formErrors';
import { useConfirm } from './ConfirmDialog';
import WrittenAnswerMarking from './WrittenAnswerMarking';
import { EmptyState, ErrorAlert, Grade, Spinner, formatDateTime } from './common';

const BLANK_QUESTION = {
  text: '',
  type: 'single',
  points: 10,
  choices: ['', '', '', ''],

  correctIndex: 0,
  correctSet: [],
};

const TYPES = [
  ['single', 'Multiple choice — one answer'],
  ['multiple', 'Multiple choice — several answers'],
  ['true_false', 'True or false'],
  ['written', 'Written answer'],
];

const TYPE_LABEL = Object.fromEntries(TYPES);

const TRUE_FALSE_CHOICES = ['True', 'False'];

export default function QuizBuilder({ courseId, assignment }) {
  const confirm = useConfirm();
  const [questions, setQuestions] = useState([]);
  const [attempts, setAttempts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  const [showForm, setShowForm] = useState(false);
  const [draft, setDraft] = useState(BLANK_QUESTION);
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    setLoadError('');
    const [questionRes, attemptRes] = await Promise.all([
      listQuestions(courseId, assignment.id),
      listAttempts(courseId, assignment.id),
    ]);
    if (questionRes.ok) setQuestions(questionRes.data.results);
    else setLoadError(errorMessage(questionRes.error));
    if (attemptRes.ok) setAttempts(attemptRes.data.results);
    setLoading(false);
  }

  useEffect(() => {
    load();

  }, [courseId, assignment.id]);

  async function refreshAttempts() {
    const result = await listAttempts(courseId, assignment.id);
    if (result.ok) setAttempts(result.data.results);
  }

  async function handleAddQuestion(event) {
    event.preventDefault();
    if (!draft.text.trim()) {
      setLoadError('The question needs some text.');
      return;
    }

    const isWritten = draft.type === 'written';
    const isTrueFalse = draft.type === 'true_false';
    const choiceTexts = isTrueFalse ? TRUE_FALSE_CHOICES : draft.choices;
    const filled = choiceTexts.map((c) => c.trim()).filter(Boolean);

    if (!isWritten) {
      if (filled.length < 2) {
        setLoadError('Give the question at least two answer choices.');
        return;
      }
      if (draft.type === 'multiple') {
        if (draft.correctSet.length === 0) {
          setLoadError('Mark at least one choice correct.');
          return;
        }
      } else if (!choiceTexts[draft.correctIndex]?.trim()) {
        setLoadError('The choice marked correct cannot be empty.');
        return;
      }
    }

    setSaving(true);
    setLoadError('');

    const questionRes = await createQuestion(courseId, assignment.id, {
      text: draft.text,
      type: draft.type,
      points: Number(draft.points),
      order: questions.length,
    });
    if (!questionRes.ok) {
      setLoadError(errorMessage(questionRes.error));
      setSaving(false);
      return;
    }

    if (!isWritten) {
      for (let index = 0; index < choiceTexts.length; index += 1) {
        const text = choiceTexts[index].trim();
        if (!text) continue;
        const correct =
          draft.type === 'multiple'
            ? draft.correctSet.includes(index)
            : index === draft.correctIndex;

        await createChoice(courseId, assignment.id, questionRes.data.id, {
          text,
          is_correct: correct,
          order: index,
        });
      }
    }

    setDraft(BLANK_QUESTION);
    setShowForm(false);
    setSaving(false);
    load();
  }

  async function handleDeleteQuestion(question) {
    const ok = await confirm({
      title: 'Delete this question?',
      body: 'Its choices go with it.',
      confirmLabel: 'Delete',
      tone: 'danger',
    });
    if (!ok) return;
    const result = await deleteQuestion(courseId, assignment.id, question.id);
    if (result.ok) setQuestions((rows) => rows.filter((q) => q.id !== question.id));
    else setLoadError(errorMessage(result.error));
  }

  async function handleDeleteChoice(question, choice) {
    const ok = await confirm({
      title: `Remove "${choice.text}"?`,
      body: 'The rest of the question is unaffected.',
      confirmLabel: 'Remove',
      tone: 'danger',
    });
    if (!ok) return;

    const result = await deleteChoice(courseId, assignment.id, question.id, choice.id);
    if (result.ok) {
      setQuestions((rows) =>
        rows.map((q) =>
          q.id === question.id
            ? { ...q, choices: q.choices.filter((c) => c.id !== choice.id) }
            : q,
        ),
      );
    } else {

      setLoadError(errorMessage(result.error));
    }
  }

  if (loading) return <Spinner label="Loading quiz…" />;

  const totalPoints = questions.reduce((sum, q) => sum + q.points, 0);

  return (
    <>
      <ErrorAlert message={loadError} onRetry={load} />

      <div className="d-flex justify-content-between align-items-center mb-3 flex-wrap gap-2">
        <p className="erean-card__meta mb-0">
          {questions.length} questions · {totalPoints} points total
          {totalPoints > assignment.max_score && (
            <span className="erean-badge erean-badge--warning ms-2">
              exceeds max score, scores are capped at {assignment.max_score}
            </span>
          )}
        </p>
        <button
          type="button"
          className="btn btn-primary btn-sm"
          onClick={() => setShowForm((open) => !open)}
        >
          {showForm ? 'Cancel' : 'Add question'}
        </button>
      </div>

      {showForm && (
        <div className="erean-card mb-3">
          <form onSubmit={handleAddQuestion}>
            <div className="row g-3">
              <div className="col-12 col-md-6">
                <label className="form-label" htmlFor="q-text">Question</label>
                <input
                  id="q-text"
                  className="form-control"
                  value={draft.text}
                  onChange={(e) => setDraft({ ...draft, text: e.target.value })}
                />
              </div>
              <div className="col-8 col-md-3">
                <label className="form-label" htmlFor="q-type">Type</label>
                <select
                  id="q-type"
                  className="form-select"
                  value={draft.type}
                  onChange={(e) =>
                    setDraft({ ...draft, type: e.target.value, correctIndex: 0, correctSet: [] })
                  }
                >
                  {TYPES.map(([value, label]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>
              <div className="col-4 col-md-3">
                <label className="form-label" htmlFor="q-points">Points</label>
                <input
                  id="q-points"
                  type="number"
                  min="1"
                  className="form-control"
                  value={draft.points}
                  onChange={(e) => setDraft({ ...draft, points: e.target.value })}
                />
              </div>
            </div>

            {draft.type === 'written' ? (
              <p className="erean-card__meta mt-3 mb-0">
                <i className="bi bi-info-circle" aria-hidden="true" /> Written answers are
                marked by hand. The quiz stays unscored until you mark them.
              </p>
            ) : draft.type === 'true_false' ? (
              <>
                <p className="form-label mt-3 mb-1">Correct answer</p>
                <div className="d-flex gap-3">
                  {TRUE_FALSE_CHOICES.map((label, index) => (
                    <label key={label} className="erean-roster__choice">
                      <input
                        type="radio"
                        name="tf-correct"
                        checked={draft.correctIndex === index}
                        onChange={() => setDraft({ ...draft, correctIndex: index })}
                      />
                      {label}
                    </label>
                  ))}
                </div>
              </>
            ) : (
              <>
                <p className="form-label mt-3 mb-1">Answer choices</p>
                <p className="erean-card__meta mb-2">
                  {draft.type === 'multiple'
                    ? 'Tick every choice that is correct. A student has to pick them all.'
                    : 'Select the radio button next to the correct answer.'}
                </p>
                {draft.choices.map((choice, index) => (

                  <div className="input-group mb-2" key={index}>
                    <div className="input-group-text">
                      <input
                        type={draft.type === 'multiple' ? 'checkbox' : 'radio'}
                        className="form-check-input mt-0"
                        name="correct-choice"
                        checked={
                          draft.type === 'multiple'
                            ? draft.correctSet.includes(index)
                            : draft.correctIndex === index
                        }
                        onChange={() =>
                          setDraft((current) =>
                            current.type === 'multiple'
                              ? {
                                  ...current,
                                  correctSet: current.correctSet.includes(index)
                                    ? current.correctSet.filter((i) => i !== index)
                                    : [...current.correctSet, index],
                                }
                              : { ...current, correctIndex: index },
                          )
                        }
                        aria-label={`Mark choice ${index + 1} as correct`}
                      />
                    </div>
                    <input
                      className="form-control"
                      placeholder={`Choice ${index + 1}`}
                      value={choice}
                      onChange={(e) => {
                        const next = [...draft.choices];
                        next[index] = e.target.value;
                        setDraft({ ...draft, choices: next });
                      }}
                    />
                  </div>
                ))}
              </>
            )}

            <button type="submit" className="btn btn-primary mt-2" disabled={saving}>
              {saving ? 'Adding…' : 'Add question'}
            </button>
          </form>
        </div>
      )}

      {questions.length === 0 ? (
        <EmptyState
          icon="bi-patch-question"
          title="This quiz has no questions yet"
          hint="Students cannot take it until you add at least one question."
        />
      ) : (
        questions.map((question, index) => (
          <div className="erean-question" key={question.id}>
            <div className="d-flex justify-content-between align-items-start gap-2">
              <p className="fw-semibold mb-2">
                {index + 1}. {question.text}{' '}
                <span className="erean-badge">{question.points} pts</span>
              </p>
              <button
                type="button"
                className="btn btn-sm btn-outline-danger"
                onClick={() => handleDeleteQuestion(question)}
              >
                Delete
              </button>
            </div>
            {question.choices.map((choice) => (
              <div
                key={choice.id}
                className={`erean-choice${choice.is_correct ? ' erean-choice--correct' : ''}`}
              >
                <i className={`bi ${choice.is_correct ? 'bi-check-circle-fill' : 'bi-circle'}`} aria-hidden="true" />
                <span>{choice.text}</span>

                {question.choices.length > 2 && (
                  <button
                    type="button"
                    className="erean-choice__remove"
                    aria-label={`Remove choice "${choice.text}"`}
                    onClick={() => handleDeleteChoice(question, choice)}
                  >
                    <i className="bi bi-x-lg" aria-hidden="true" />
                  </button>
                )}
              </div>
            ))}
          </div>
        ))
      )}

      {questions.some((question) => question.type === 'written') && (
        <WrittenAnswerMarking
          courseId={courseId}
          assignment={assignment}
          onMarked={refreshAttempts}
        />
      )}

      <h3 className="erean-card__title mt-4 mb-2">Student results</h3>
      {attempts.length === 0 ? (
        <EmptyState icon="bi-clipboard-data" title="No attempts yet" hint="Scores appear here as students finish." />
      ) : (
        <div className="erean-card">
          {attempts.map((attempt) => (
            <div className="erean-list-row" key={attempt.id}>
              <div className="erean-list-row__main">
                <p className="erean-list-row__title">
                  {attempt.student_detail?.full_name}
                </p>
                <span className="erean-card__meta">
                  {formatDateTime(attempt.submitted_at)}
                </span>
              </div>
              <Grade value={attempt.score} outOf={assignment.max_score} />
            </div>
          ))}
        </div>
      )}
    </>
  );
}
