import { useEffect, useState } from 'react';

import {
  createAnnouncement,
  deleteAnnouncement,
  listAnnouncements,
  markAnnouncementRead,
  updateAnnouncement,
} from '../api/resources';
import { useAuth } from '../context/AuthContext';
import { useConfirm } from './ConfirmDialog';
import { errorMessage, parseApiError } from '../utils/formErrors';
import { EmptyState, ErrorAlert, FieldError, Spinner, formatDateTime } from './common';

export default function AnnouncementsTab({ courseId, canManage }) {
  const confirm = useConfirm();
  const { user } = useAuth();

  const [announcements, setAnnouncements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  const [showForm, setShowForm] = useState(false);

  const [editingId, setEditingId] = useState(null);
  const [draft, setDraft] = useState({ title: '', content: '' });
  const [formErrors, setFormErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    setLoadError('');
    const result = await listAnnouncements(courseId);
    if (result.ok) setAnnouncements(result.data.results);
    else setLoadError(errorMessage(result.error));
    setLoading(false);
  }

  useEffect(() => {
    load();

  }, [courseId]);

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setFormErrors({});
    setFormError('');

    const result = editingId
      ? await updateAnnouncement(courseId, editingId, draft)
      : await createAnnouncement(courseId, draft);
    if (result.ok) {
      closeForm();
      load();
    } else {
      const { fieldErrors, generalError } = parseApiError(result.error);
      setFormErrors(fieldErrors);
      setFormError(generalError);
    }
    setSaving(false);
  }

  function closeForm() {
    setShowForm(false);
    setEditingId(null);
    setDraft({ title: '', content: '' });
    setFormErrors({});
    setFormError('');
  }

  function startEdit(announcement) {
    setEditingId(announcement.id);
    setDraft({ title: announcement.title, content: announcement.content });
    setShowForm(true);
    setFormErrors({});
    setFormError('');
  }

  async function handleMarkRead(announcement) {
    if (announcement.is_read) return;
    const result = await markAnnouncementRead(courseId, announcement.id);
    if (result.ok) {

      setAnnouncements((rows) =>
        rows.map((row) => (row.id === announcement.id ? { ...row, is_read: true } : row)),
      );
    }
  }

  async function handleDelete(announcement) {
    const ok = await confirm({
      title: `Delete "${announcement.title}"?`,
      confirmLabel: 'Delete',
      tone: 'danger',
    });
    if (!ok) return;
    const result = await deleteAnnouncement(courseId, announcement.id);
    if (result.ok) {
      setAnnouncements((rows) => rows.filter((row) => row.id !== announcement.id));
    } else {
      setLoadError(errorMessage(result.error));
    }
  }

  return (
    <>
      {canManage && (
        <div className="mb-3">
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={() => (showForm ? closeForm() : setShowForm(true))}
          >
            {showForm ? 'Cancel' : 'Post announcement'}
          </button>
        </div>
      )}

      {showForm && (
        <div className="erean-card mb-3">
          {formError && <div className="alert alert-danger">{formError}</div>}
          <form onSubmit={handleSubmit} noValidate>
            <div className="mb-3">
              <label className="form-label" htmlFor="a-title">Title</label>
              <input
                id="a-title"
                className={`form-control${formErrors.title ? ' is-invalid' : ''}`}
                value={draft.title}
                onChange={(e) => setDraft({ ...draft, title: e.target.value })}
              />
              <FieldError message={formErrors.title} />
            </div>
            <div className="mb-3">
              <label className="form-label" htmlFor="a-content">Message</label>
              <textarea
                id="a-content"
                rows={4}
                className={`form-control${formErrors.content ? ' is-invalid' : ''}`}
                value={draft.content}
                onChange={(e) => setDraft({ ...draft, content: e.target.value })}
              />
              <FieldError message={formErrors.content} />
            </div>
            <button type="submit" className="btn btn-primary" disabled={saving}>
              {saving
                ? editingId
                  ? 'Saving…'
                  : 'Posting…'
                : editingId
                  ? 'Save changes'
                  : 'Post'}
            </button>
          </form>
        </div>
      )}

      <ErrorAlert message={loadError} onRetry={load} />

      {loading ? (
        <Spinner label="Loading announcements…" />
      ) : announcements.length === 0 ? (
        <EmptyState icon="bi-megaphone" title="No announcements" hint="Nothing has been posted yet." />
      ) : (
        announcements.map((announcement) => {

          const mine = user.role === 'admin' || announcement.author === user.id;
          return (
          <div
            className={`erean-card${announcement.is_read ? '' : ' erean-unread'}`}
            key={announcement.id}
          >
            <div className="d-flex justify-content-between align-items-start gap-2">
              <div>
                <h3 className="erean-card__title">{announcement.title}</h3>
                <p className="erean-card__meta mb-2">
                  {announcement.author_detail?.full_name} ·{' '}
                  {formatDateTime(announcement.created_at)}
                  {announcement.is_edited && (
                    <> · edited {formatDateTime(announcement.edited_at)}</>
                  )}
                  {!announcement.is_read && (
                    <span className="erean-badge erean-badge--info ms-2">New</span>
                  )}
                </p>
              </div>
              <div className="d-flex gap-2">
                {!announcement.is_read && (
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-secondary"
                    onClick={() => handleMarkRead(announcement)}
                  >
                    Mark as read
                  </button>
                )}
                {mine && (
                  <>
                    <button
                      type="button"
                      className="btn btn-sm btn-outline-secondary"
                      onClick={() => startEdit(announcement)}
                    >
                      Edit
                    </button>
                    <button
                      type="button"
                      className="btn btn-sm btn-outline-danger"
                      onClick={() => handleDelete(announcement)}
                    >
                      Delete
                    </button>
                  </>
                )}
              </div>
            </div>
            <p className="mb-0 erean-prewrap">{announcement.content}</p>
          </div>
          );
        })
      )}
    </>
  );
}
