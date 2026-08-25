import { useEffect, useState } from 'react';

import { createMaterial, deleteMaterial, downloadMaterial, listMaterials } from '../api/resources';
import { useConfirm } from './ConfirmDialog';
import { errorMessage, parseApiError } from '../utils/formErrors';
import { EmptyState, ErrorAlert, FieldError, Spinner, formatDate } from './common';

const MAX_MB = 100;
const EXTENSIONS = {
  pdf: ['.pdf'],
  video: ['.mp4', '.mpeg', '.mov', '.avi'],
};

const TYPE_ICON = { pdf: 'bi-file-earmark-pdf', video: 'bi-play-btn', link: 'bi-link-45deg' };

export default function MaterialsTab({ courseId, canManage }) {
  const confirm = useConfirm();
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  const [showForm, setShowForm] = useState(false);
  const [draft, setDraft] = useState({ title: '', type: 'pdf', link_url: '' });
  const [file, setFile] = useState(null);
  const [formErrors, setFormErrors] = useState({});
  const [formError, setFormError] = useState('');
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    setLoadError('');
    const result = await listMaterials(courseId);
    if (result.ok) setMaterials(result.data.results);
    else setLoadError(errorMessage(result.error));
    setLoading(false);
  }

  useEffect(() => {
    load();

  }, [courseId]);

  function validateFile() {
    if (draft.type === 'link') return null;
    if (!file) return 'Please choose a file.';
    if (file.size > MAX_MB * 1024 * 1024) return `File must not exceed ${MAX_MB}MB.`;
    const allowed = EXTENSIONS[draft.type] || [];
    const name = file.name.toLowerCase();
    if (!allowed.some((ext) => name.endsWith(ext))) {
      return `A "${draft.type}" material must be one of: ${allowed.join(', ')}.`;
    }
    return null;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setFormErrors({});
    setFormError('');

    const fileProblem = validateFile();
    if (fileProblem) {
      setFormErrors({ file_url: fileProblem });
      return;
    }

    setSaving(true);
    const formData = new FormData();
    formData.append('title', draft.title);
    formData.append('type', draft.type);
    if (draft.type === 'link') formData.append('link_url', draft.link_url);
    else formData.append('file_url', file);

    const result = await createMaterial(courseId, formData);
    if (result.ok) {
      setDraft({ title: '', type: 'pdf', link_url: '' });
      setFile(null);
      setShowForm(false);
      load();
    } else {
      const { fieldErrors, generalError } = parseApiError(result.error);
      setFormErrors(fieldErrors);
      setFormError(generalError);
    }
    setSaving(false);
  }

  async function handleDelete(material) {
    const ok = await confirm({
      title: `Delete "${material.title}"?`,
      body: 'This cannot be undone.',
      confirmLabel: 'Delete',
      tone: 'danger',
    });
    if (!ok) return;
    const result = await deleteMaterial(courseId, material.id);
    if (result.ok) setMaterials((rows) => rows.filter((m) => m.id !== material.id));
    else setLoadError(errorMessage(result.error));
  }

  async function handleDownload(material) {
    const result = await downloadMaterial(courseId, material.id, material.filename);
    if (!result.ok) setLoadError(errorMessage(result.error));
  }

  return (
    <>
      {canManage && (
        <div className="mb-3">
          <button
            type="button"
            className="btn btn-primary btn-sm"
            onClick={() => setShowForm((open) => !open)}
          >
            {showForm ? 'Cancel' : 'Upload material'}
          </button>
        </div>
      )}

      {showForm && (
        <div className="erean-card mb-3">
          {formError && <div className="alert alert-danger">{formError}</div>}
          <form onSubmit={handleSubmit} noValidate>
            <div className="row g-3">
              <div className="col-12 col-md-6">
                <label className="form-label" htmlFor="m-title">Title</label>
                <input
                  id="m-title"
                  className={`form-control${formErrors.title ? ' is-invalid' : ''}`}
                  value={draft.title}
                  onChange={(e) => setDraft({ ...draft, title: e.target.value })}
                />
                <FieldError message={formErrors.title} />
              </div>
              <div className="col-12 col-md-3">
                <label className="form-label" htmlFor="m-type">Type</label>
                <select
                  id="m-type"
                  className="form-select"
                  value={draft.type}
                  onChange={(e) => setDraft({ ...draft, type: e.target.value })}
                >
                  <option value="pdf">PDF</option>
                  <option value="video">Video</option>
                  <option value="link">External link</option>
                </select>
              </div>
              <div className="col-12 col-md-3">
                {draft.type === 'link' ? (
                  <>
                    <label className="form-label" htmlFor="m-link">Link URL</label>
                    <input
                      id="m-link"
                      type="url"
                      className={`form-control${formErrors.link_url ? ' is-invalid' : ''}`}
                      value={draft.link_url}
                      onChange={(e) => setDraft({ ...draft, link_url: e.target.value })}
                    />
                    <FieldError message={formErrors.link_url} />
                  </>
                ) : (
                  <>
                    <label className="form-label" htmlFor="m-file">File</label>
                    <input
                      id="m-file"
                      type="file"
                      className={`form-control${formErrors.file_url ? ' is-invalid' : ''}`}
                      accept={(EXTENSIONS[draft.type] || []).join(',')}
                      onChange={(e) => setFile(e.target.files[0] || null)}
                    />
                    <FieldError message={formErrors.file_url} />
                  </>
                )}
              </div>
            </div>
            <button type="submit" className="btn btn-primary mt-3" disabled={saving}>
              {saving ? 'Uploading…' : 'Upload'}
            </button>
          </form>
        </div>
      )}

      <ErrorAlert message={loadError} onRetry={load} />

      {loading ? (
        <Spinner label="Loading materials…" />
      ) : materials.length === 0 ? (
        <EmptyState
          icon="bi-folder2-open"
          title="No materials yet"
          hint={canManage ? 'Upload lecture notes, slides or videos.' : 'Your instructor has not posted any materials.'}
        />
      ) : (
        <div className="erean-card">
          {materials.map((material) => (
            <div className="erean-list-row" key={material.id}>
              <div className="erean-list-row__main">
                <p className="erean-list-row__title">
                  <i className={`bi ${TYPE_ICON[material.type] || 'bi-file-earmark'}`} aria-hidden="true" />{' '}
                  {material.title}
                </p>
                <span className="erean-card__meta">
                  {material.type} · added {formatDate(material.uploaded_at)}
                </span>
              </div>
              <div className="d-flex gap-2">
                <button
                  type="button"
                  className="btn btn-sm btn-outline-primary"
                  onClick={() => handleDownload(material)}
                >
                  {material.type === 'link' ? 'Open' : 'Download'}
                </button>
                {canManage && (
                  <button
                    type="button"
                    className="btn btn-sm btn-outline-danger"
                    onClick={() => handleDelete(material)}
                  >
                    Delete
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
