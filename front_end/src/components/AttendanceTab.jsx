import { useCallback, useEffect, useState } from 'react';

import {
  createAttendanceSession,
  getAttendanceSummary,
  getMyAttendance,
  listAttendanceSessions,
  markAttendance,
} from '../api/resources';
import { useAuth } from '../context/AuthContext';
import { errorMessage } from '../utils/formErrors';
import {
  EmptyState,
  ErrorAlert,
  Spinner,
  Stat,
  formatDate,
} from './common';

const STATUSES = [
  ['present', 'Present'],
  ['late', 'Late'],
  ['absent', 'Absent'],
  ['excused', 'Excused'],
];

function StudentAttendance({ courseId }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');

  useEffect(() => {
    getMyAttendance(courseId).then((result) => {
      if (result.ok) setData(result.data);
      else setLoadError(errorMessage(result.error));
      setLoading(false);
    });
  }, [courseId]);

  if (loading) return <Spinner label="Loading your attendance…" />;
  if (!data) return <ErrorAlert message={loadError} />;

  if (data.sessions_held === 0) {
    return (
      <EmptyState
        icon="bi-calendar-check"
        title="No classes recorded yet"
        hint="Attendance appears once your instructor starts taking it."
      />
    );
  }

  return (
    <>
      <div className="erean-stats">
        <Stat value={data.sessions_held} label="Classes held" icon="bi-calendar3" />
        <Stat value={data.attended} label="Attended" icon="bi-check2-circle" />
        <Stat
          value={data.attendance_rate === null ? '—' : `${data.attendance_rate}%`}
          label="Attendance"
          icon="bi-graph-up"
        />
      </div>

      <div className="erean-card">
        {data.records.length === 0 ? (
          <p className="erean-card__meta mb-0">
            Nothing recorded against your name yet.
          </p>
        ) : (
          data.records.map((record) => (
            <div className="erean-list-row" key={record.session}>
              <div className="erean-list-row__main">
                <p className="erean-list-row__title">{record.title || 'Class'}</p>
                <span className="erean-card__meta">{formatDate(record.date)}</span>
              </div>
              <span className={`erean-badge erean-attendance--${record.status}`}>
                {record.status}
              </span>
            </div>
          ))
        )}
      </div>
    </>
  );
}

function StaffAttendance({ courseId }) {
  const [sessions, setSessions] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [openId, setOpenId] = useState(null);
  const [marks, setMarks] = useState({});
  const [saving, setSaving] = useState(false);
  const [newDate, setNewDate] = useState('');
  const [newTitle, setNewTitle] = useState('');

  const load = useCallback(async () => {
    setLoading(true);
    const [sessionsResult, summaryResult] = await Promise.all([
      listAttendanceSessions(courseId),
      getAttendanceSummary(courseId),
    ]);
    if (sessionsResult.ok) setSessions(sessionsResult.data.results ?? sessionsResult.data);
    else setLoadError(errorMessage(sessionsResult.error));
    if (summaryResult.ok) setSummary(summaryResult.data);
    setLoading(false);
  }, [courseId]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleCreate(event) {
    event.preventDefault();
    setLoadError('');
    const result = await createAttendanceSession(courseId, {
      date: newDate,
      title: newTitle,
    });
    if (result.ok) {
      setNewDate('');
      setNewTitle('');
      load();
    } else {
      setLoadError(errorMessage(result.error));
    }
  }

  function openSession(session) {
    if (openId === session.id) {
      setOpenId(null);
      return;
    }
    setOpenId(session.id);

    const existing = {};
    for (const record of session.records) existing[record.student] = record.status;
    const seeded = {};
    for (const row of summary?.students ?? []) {
      seeded[row.student] = existing[row.student] || 'present';
    }
    setMarks(seeded);
  }

  async function handleSave(session) {
    setSaving(true);
    const records = Object.entries(marks).map(([student, status]) => ({
      student: Number(student),
      status,
    }));
    const result = await markAttendance(courseId, session.id, records);
    if (result.ok) {
      setOpenId(null);
      await load();
    } else {
      setLoadError(errorMessage(result.error));
    }
    setSaving(false);
  }

  if (loading) return <Spinner label="Loading the register…" />;

  return (
    <>
      <ErrorAlert message={loadError} onRetry={load} />

      <form className="erean-card mb-3" onSubmit={handleCreate}>
        <span className="erean-eyebrow">Take attendance</span>
        <div className="row g-2 align-items-end">
          <div className="col-12 col-md-4">
            <label className="form-label" htmlFor="att-date">Date</label>
            <input
              id="att-date"
              type="date"
              required
              className="form-control"
              value={newDate}
              onChange={(e) => setNewDate(e.target.value)}
            />
          </div>
          <div className="col-12 col-md-5">
            <label className="form-label" htmlFor="att-title">Label</label>
            <input
              id="att-title"
              className="form-control"
              placeholder="Week 3 — Functions"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
            />
          </div>
          <div className="col-12 col-md-3">
            <button type="submit" className="btn btn-primary w-100">Start a class</button>
          </div>
        </div>
      </form>

      {summary && summary.students.length > 0 && (
        <div className="erean-card mb-3">
          <span className="erean-eyebrow">Attendance rate</span>
          <div className="erean-table-wrap">
            <table className="table align-middle mb-0">
              <thead>
                <tr>
                  <th>Student</th>
                  <th className="text-end">Attended</th>
                  <th className="text-end">Rate</th>
                </tr>
              </thead>
              <tbody>
                {summary.students.map((row) => (
                  <tr key={row.student}>
                    <td>{row.name}</td>
                    <td className="text-end erean-num">
                      {row.attended}/{summary.sessions_held}
                    </td>
                    <td className="text-end erean-num">
                      {row.attendance_rate === null ? '—' : `${row.attendance_rate}%`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {sessions.length === 0 ? (
        <EmptyState
          icon="bi-calendar-check"
          title="No classes recorded"
          hint="Start one above to mark the roster."
        />
      ) : (
        <div className="erean-card">
          {sessions.map((session) => (
            <div key={session.id}>
              <div className="erean-list-row">
                <div className="erean-list-row__main">
                  <p className="erean-list-row__title">{session.title || 'Class'}</p>
                  <span className="erean-card__meta">
                    {formatDate(session.date)} · {session.present_count}/{session.total_count}{' '}
                    present
                  </span>
                </div>
                <button
                  type="button"
                  className="btn btn-sm btn-outline-secondary"
                  onClick={() => openSession(session)}
                >
                  {openId === session.id ? 'Close' : 'Mark roster'}
                </button>
              </div>

              {openId === session.id && (
                <div className="erean-roster">
                  {(summary?.students ?? []).map((row) => (
                    <div className="erean-roster__row" key={row.student}>
                      <span className="erean-roster__name">{row.name}</span>
                      <div className="erean-roster__choices">
                        {STATUSES.map(([value, label]) => (
                          <label key={value} className="erean-roster__choice">
                            <input
                              type="radio"
                              name={`att-${session.id}-${row.student}`}
                              value={value}
                              checked={marks[row.student] === value}
                              onChange={() =>
                                setMarks((current) => ({ ...current, [row.student]: value }))
                              }
                            />
                            {label}
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                  <button
                    type="button"
                    className="btn btn-primary btn-sm mt-2"
                    onClick={() => handleSave(session)}
                    disabled={saving}
                  >
                    {saving ? 'Saving…' : 'Save roster'}
                  </button>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </>
  );
}

export default function AttendanceTab({ courseId, canManage }) {
  const { user } = useAuth();
  if (canManage || user.role !== 'student') {
    return <StaffAttendance courseId={courseId} />;
  }
  return <StudentAttendance courseId={courseId} />;
}
