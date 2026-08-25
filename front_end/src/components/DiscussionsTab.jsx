import { useCallback, useEffect, useState } from 'react';

import {
  acceptAnswer,
  createReply,
  createThread,
  deleteReply,
  deleteThread,
  getThread,
  listThreads,
  moderateThread,
} from '../api/resources';
import { useAuth } from '../context/AuthContext';
import { useConfirm } from './ConfirmDialog';
import { errorMessage } from '../utils/formErrors';
import {
  EmptyState,
  ErrorAlert,
  Spinner,
  formatDateTime,
  plural,
} from './common';

const FILTERS = [
  { key: '', label: 'Everything' },
  { key: 'discussion', label: 'Discussions' },
  { key: 'question', label: 'Questions' },
  { key: 'unanswered', label: 'Unanswered' },
];

function ThreadView({ courseId, threadId, canManage, onBack, onChanged }) {
  const { user } = useAuth();
  const confirm = useConfirm();
  const [thread, setThread] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [body, setBody] = useState('');
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    const result = await getThread(courseId, threadId);
    if (result.ok) setThread(result.data);
    else setError(errorMessage(result.error));
    setLoading(false);
  }, [courseId, threadId]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleReply(event) {
    event.preventDefault();
    setSaving(true);
    const result = await createReply(courseId, threadId, body);
    if (result.ok) {
      setBody('');
      await load();
    } else {
      setError(errorMessage(result.error));
    }
    setSaving(false);
  }

  async function handleAccept(reply) {
    const result = await acceptAnswer(courseId, threadId, reply.id);
    if (result.ok) await load();
    else setError(errorMessage(result.error));
  }

  async function handleDeleteReply(reply) {
    const ok = await confirm({
      title: 'Delete this reply?',
      body: reply.is_answer
        ? 'It is the accepted answer, so the question will go back to unanswered.'
        : 'This cannot be undone.',
      confirmLabel: 'Delete',
      tone: 'danger',
    });
    if (!ok) return;
    const result = await deleteReply(courseId, threadId, reply.id);
    if (result.ok) await load();
    else setError(errorMessage(result.error));
  }

  async function handleDelete() {
    const ok = await confirm({
      title: `Delete "${thread.title}"?`,
      body: 'Its replies go with it.',
      confirmLabel: 'Delete',
      tone: 'danger',
    });
    if (!ok) return;
    const result = await deleteThread(courseId, threadId);
    if (result.ok) {
      onChanged();
      onBack();
    } else setError(errorMessage(result.error));
  }

  async function toggle(field) {
    const result = await moderateThread(courseId, threadId, { [field]: !thread[field] });
    if (result.ok) await load();
    else setError(errorMessage(result.error));
  }

  if (loading) return <Spinner label="Loading thread…" />;
  if (!thread) return <ErrorAlert message={error} />;

  const isAsker = thread.author === user.id;
  const canModerate = canManage;
  const isQuestion = thread.kind === 'question';

  return (
    <>
      <button type="button" className="erean-backlink" onClick={onBack}>
        <i className="bi bi-arrow-left" aria-hidden="true" />
        All threads
      </button>

      <ErrorAlert message={error} />

      <article className="erean-card mb-3">
        <div className="erean-thread__head">
          <div>
            <span className="erean-eyebrow">
              {isQuestion ? 'Question' : 'Discussion'}
              {thread.is_pinned ? ' · Pinned' : ''}
              {thread.is_locked ? ' · Locked' : ''}
            </span>
            <h2 className="erean-thread__title">{thread.title}</h2>
            <span className="erean-card__meta">
              {thread.author_detail?.full_name || 'Unknown'} ·{' '}
              {formatDateTime(thread.created_at)}
            </span>
          </div>
          {(canModerate || thread.author === user.id) && (
            <div className="d-flex gap-2 flex-wrap">
              {canModerate && (
                <>
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-secondary"
                    onClick={() => toggle('is_pinned')}
                  >
                    {thread.is_pinned ? 'Unpin' : 'Pin'}
                  </button>
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-secondary"
                    onClick={() => toggle('is_locked')}
                  >
                    {thread.is_locked ? 'Unlock' : 'Lock'}
                  </button>
                </>
              )}
              <button
                type="button"
                className="btn btn-sm btn-outline-danger"
                onClick={handleDelete}
              >
                Delete
              </button>
            </div>
          )}
        </div>
        <p className="erean-prewrap mb-0 mt-3">{thread.body}</p>
      </article>

      <div className="erean-card">
        <span className="erean-eyebrow">{plural(thread.replies.length, 'reply', 'replies')}</span>
        {thread.replies.length === 0 ? (
          <p className="erean-card__meta mb-0">Nobody has replied yet.</p>
        ) : (
          thread.replies.map((reply) => (
            <div
              className={`erean-reply${reply.is_answer ? ' is-answer' : ''}`}
              key={reply.id}
            >
              <div className="erean-reply__head">
                <span className="erean-reply__author">
                  {reply.author_detail?.full_name || 'Unknown'}
                </span>
                <span className="erean-card__meta">{formatDateTime(reply.created_at)}</span>
                {reply.is_answer && (
                  <span className="erean-badge erean-badge--success">
                    <i className="bi bi-check-circle-fill" aria-hidden="true" />
                    Answer
                  </span>
                )}
              </div>
              <p className="erean-prewrap mb-0">{reply.body}</p>
              <div className="erean-reply__actions">
                {isQuestion && !reply.is_answer && (isAsker || canModerate) && (
                  <button
                    type="button"
                    className="erean-linkbutton"
                    onClick={() => handleAccept(reply)}
                  >
                    Mark as the answer
                  </button>
                )}

                {(reply.author === user.id || canModerate) && (
                  <button
                    type="button"
                    className="erean-linkbutton erean-linkbutton--danger"
                    onClick={() => handleDeleteReply(reply)}
                  >
                    Delete
                  </button>
                )}
              </div>
            </div>
          ))
        )}

        {thread.is_locked && !canModerate ? (
          <p className="erean-card__meta mt-3 mb-0">
            <i className="bi bi-lock" aria-hidden="true" /> This thread is locked.
          </p>
        ) : (
          <form className="mt-3" onSubmit={handleReply}>
            <label className="form-label" htmlFor="reply-body">Your reply</label>
            <textarea
              id="reply-body"
              rows={3}
              required
              className="form-control"
              value={body}
              onChange={(e) => setBody(e.target.value)}
            />
            <button type="submit" className="btn btn-primary btn-sm mt-2" disabled={saving}>
              {saving ? 'Posting…' : 'Post reply'}
            </button>
          </form>
        )}
      </div>
    </>
  );
}

export default function DiscussionsTab({ courseId, canManage }) {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [filter, setFilter] = useState('');
  const [openId, setOpenId] = useState(null);
  const [showForm, setShowForm] = useState(false);
  const [draft, setDraft] = useState({ title: '', body: '', kind: 'discussion' });
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError('');
    const params =
      filter === 'unanswered' ? { unanswered: 'true' } : filter ? { kind: filter } : {};
    const result = await listThreads(courseId, params);
    if (result.ok) setRows(result.data.results);
    else setLoadError(errorMessage(result.error));
    setLoading(false);
  }, [courseId, filter]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleCreate(event) {
    event.preventDefault();
    setSaving(true);
    const result = await createThread(courseId, draft);
    if (result.ok) {
      setDraft({ title: '', body: '', kind: 'discussion' });
      setShowForm(false);
      await load();
    } else {
      setLoadError(errorMessage(result.error));
    }
    setSaving(false);
  }

  if (openId) {
    return (
      <ThreadView
        courseId={courseId}
        threadId={openId}
        canManage={canManage}
        onBack={() => setOpenId(null)}
        onChanged={load}
      />
    );
  }

  return (
    <>
      <div className="d-flex justify-content-between align-items-center gap-3 flex-wrap mb-3">
        <div className="erean-tabs mb-0">
          {FILTERS.map((item) => (
            <button
              key={item.key || 'all'}
              type="button"
              className={`erean-tab${filter === item.key ? ' is-active' : ''}`}
              onClick={() => setFilter(item.key)}
            >
              {item.label}
            </button>
          ))}
        </div>
        <button
          type="button"
          className="btn btn-primary btn-sm"
          onClick={() => setShowForm((open) => !open)}
        >
          {showForm ? 'Cancel' : 'Start a thread'}
        </button>
      </div>

      <ErrorAlert message={loadError} onRetry={load} />

      {showForm && (
        <form className="erean-card mb-3" onSubmit={handleCreate}>
          <div className="row g-2">
            <div className="col-12 col-md-8">
              <label className="form-label" htmlFor="th-title">Title</label>
              <input
                id="th-title"
                required
                className="form-control"
                value={draft.title}
                onChange={(e) => setDraft({ ...draft, title: e.target.value })}
              />
            </div>
            <div className="col-12 col-md-4">
              <label className="form-label" htmlFor="th-kind">Type</label>
              <select
                id="th-kind"
                className="form-select"
                value={draft.kind}
                onChange={(e) => setDraft({ ...draft, kind: e.target.value })}
              >
                <option value="discussion">Discussion</option>
                <option value="question">Question</option>
              </select>
            </div>
            <div className="col-12">
              <label className="form-label" htmlFor="th-body">Message</label>
              <textarea
                id="th-body"
                rows={4}
                required
                className="form-control"
                value={draft.body}
                onChange={(e) => setDraft({ ...draft, body: e.target.value })}
              />
            </div>
          </div>
          <button type="submit" className="btn btn-primary mt-3" disabled={saving}>
            {saving ? 'Posting…' : 'Post'}
          </button>
        </form>
      )}

      {loading ? (
        <Spinner label="Loading discussions…" />
      ) : rows.length === 0 ? (
        <EmptyState
          icon="bi-chat-left-text"
          title="Nothing posted yet"
          hint="Start a thread to ask a question or get a conversation going."
        />
      ) : (
        <div className="erean-card">
          {rows.map((thread) => (
            <button
              type="button"
              className="erean-list-row erean-list-row--button"
              key={thread.id}
              onClick={() => setOpenId(thread.id)}
            >
              <div className="erean-list-row__main">
                <p className="erean-list-row__title">
                  {thread.is_pinned && (
                    <i className="bi bi-pin-angle-fill erean-thread__pin" aria-label="pinned" />
                  )}
                  {thread.title}
                  {thread.kind === 'question' && (
                    <span
                      className={`erean-badge ${
                        thread.is_answered ? 'erean-badge--success' : 'erean-badge--warning'
                      }`}
                    >
                      {thread.is_answered ? 'Answered' : 'Question'}
                    </span>
                  )}
                  {thread.is_locked && (
                    <i className="bi bi-lock erean-thread__lock" aria-label="locked" />
                  )}
                </p>
                <span className="erean-card__meta">
                  {thread.author_detail?.full_name || 'Unknown'} ·{' '}
                  {formatDateTime(thread.created_at)}
                </span>
              </div>
              <span className="erean-card__meta">
                {plural(thread.reply_count, 'reply', 'replies')}
              </span>
            </button>
          ))}
        </div>
      )}
    </>
  );
}
