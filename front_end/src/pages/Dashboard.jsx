import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

import {
  listAssignments,
  listCourses,
  listEnrollments,
  listMySubmissions,
  listUsers,
} from '../api/resources';
import { useAuth } from '../context/AuthContext';
import {
  EmptyState,
  PageHeader,
  ProgressBar,
  Spinner,
  Stat,
  StatusBadge,
  formatDateTime,
  plural,
} from '../components/common';

function daysUntil(dueDate) {
  const day = 24 * 60 * 60 * 1000;
  const due = new Date(dueDate);
  const startOfToday = new Date();
  startOfToday.setHours(0, 0, 0, 0);
  return Math.ceil((due - startOfToday) / day) - 1;
}

function dueLabel(days) {
  if (days < 0) return { text: `${Math.abs(days)}d late`, tone: 'late' };
  if (days === 0) return { text: 'Today', tone: 'today' };
  if (days === 1) return { text: 'Tomorrow', tone: 'soon' };
  return { text: `${days} days`, tone: days <= 3 ? 'soon' : 'later' };
}

function NextDue({ items }) {
  if (items.length === 0) {
    return (
      <div className="erean-due erean-due--clear">
        <span className="erean-eyebrow">Next due</span>
        <p className="erean-due__title">Nothing outstanding</p>
        <p className="erean-due__meta">Everything in your active courses is handed in.</p>
      </div>
    );
  }

  const [next, ...rest] = items;
  const days = daysUntil(next.due_date);
  const { text, tone } = dueLabel(days);

  return (
    <div className="erean-due">
      <div className="erean-due__head">
        <div className="erean-due__what">
          <span className="erean-eyebrow">Next due</span>
          <h2 className="erean-due__title">
            <Link to={`/courses/${next.course}/assignments/${next.id}`}>{next.title}</Link>
          </h2>
          <p className="erean-due__meta">
            {next.course_title} · {next.max_score} points · due {formatDateTime(next.due_date)}
          </p>
        </div>
        <div className={`erean-due__when erean-due__when--${tone}`}>
          <span className="erean-due__count">{text}</span>
        </div>
      </div>

      {rest.length > 0 && (
        <ul className="erean-due__rest">
          {rest.slice(0, 3).map((item) => {
            const label = dueLabel(daysUntil(item.due_date));
            return (
              <li key={item.id}>
                <Link to={`/courses/${item.course}/assignments/${item.id}`}>{item.title}</Link>
                <span className="erean-due__rest-course">{item.course_title}</span>
                <span className={`erean-due__rest-when erean-due__rest-when--${label.tone}`}>
                  {label.text}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

export default function Dashboard() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({});
  const [enrollments, setEnrollments] = useState([]);
  const [courses, setCourses] = useState([]);
  const [due, setDue] = useState([]);

  useEffect(() => {
    let live = true;

    async function load() {
      setLoading(true);

      if (user.role === 'student') {
        const [enrollRes, gradeRes] = await Promise.all([
          listEnrollments(),
          listMySubmissions(),
        ]);
        if (!live) return;
        const rows = enrollRes.ok ? enrollRes.data.results : [];
        const grades = gradeRes.ok ? gradeRes.data.results : [];
        const graded = grades.filter((g) => g.grade !== null);
        setEnrollments(rows);

        const active = rows.filter((r) => r.status === 'active');
        const lists = await Promise.all(active.map((r) => listAssignments(r.course)));
        const handedIn = new Set(grades.map((g) => g.assignment));
        const outstanding = lists
          .flatMap((res, i) =>
            (res.ok ? res.data.results : []).map((a) => ({
              ...a,
              course_title: active[i].course_title,
            })),
          )
          .filter((a) => a.due_date && !handedIn.has(a.id))
          .sort((a, b) => new Date(a.due_date) - new Date(b.due_date));
        setDue(outstanding);
        setStats({
          enrolled: rows.filter((r) => r.status === 'active').length,
          submitted: grades.length,
          graded: graded.length,

          average: graded.length
            ? `${Math.round(
                graded.reduce((sum, g) => sum + (parseFloat(g.grade) / g.max_score) * 100, 0) /
                  graded.length,
              )}%`
            : '—',
        });
      } else if (user.role === 'instructor') {
        const courseRes = await listCourses();
        if (!live) return;
        const rows = courseRes.ok ? courseRes.data.results : [];
        setCourses(rows);
        setStats({
          courses: rows.length,
          published: rows.filter((c) => c.status === 'published').length,
          drafts: rows.filter((c) => c.status === 'draft').length,
          students: rows.reduce((sum, c) => sum + (c.enrolled_count || 0), 0),
        });
      } else {
        const [courseRes, userRes] = await Promise.all([listCourses(), listUsers()]);
        if (!live) return;
        const rows = courseRes.ok ? courseRes.data.results : [];
        setCourses(rows);
        setStats({
          users: userRes.ok ? userRes.data.count : 0,
          courses: courseRes.ok ? courseRes.data.count : 0,
          pending: rows.filter((c) => c.status === 'draft').length,
          published: rows.filter((c) => c.status === 'published').length,
        });
      }
      setLoading(false);
    }

    load();
    return () => {
      live = false;
    };
  }, [user.role]);

  if (loading) return <Spinner />;

  return (
    <>
      <PageHeader
        title={`Welcome back, ${user.first_name || user.username}`}
        subtitle={
          user.role === 'student'
            ? 'Your courses, deadlines and results at a glance.'
            : user.role === 'instructor'
              ? 'Manage your courses, coursework and grading.'
              : 'Platform overview and administration.'
        }
      />

      {user.role === 'student' && <NextDue items={due} />}

      <div className="erean-stats">
        {user.role === 'student' && (
          <>
            <Stat value={stats.enrolled} label="Active courses" icon="bi-journal-bookmark" />
            <Stat value={stats.submitted} label="Submissions" icon="bi-upload" />
            <Stat value={stats.graded} label="Graded" icon="bi-check2-circle" />
            <Stat value={stats.average} label="Average grade" icon="bi-bar-chart" />
          </>
        )}
        {user.role === 'instructor' && (
          <>
            <Stat value={stats.courses} label="Courses" icon="bi-journals" />
            <Stat value={stats.published} label="Published" icon="bi-broadcast" />
            <Stat value={stats.drafts} label="Awaiting approval" icon="bi-hourglass-split" />
            <Stat value={stats.students} label="Enrolled students" icon="bi-people" />
          </>
        )}
        {user.role === 'admin' && (
          <>
            <Stat value={stats.users} label="Users" icon="bi-people" />
            <Stat value={stats.courses} label="Courses" icon="bi-journals" />
            <Stat value={stats.pending} label="Pending approval" icon="bi-hourglass-split" />
            <Stat value={stats.published} label="Published" icon="bi-broadcast" />
          </>
        )}
      </div>

      {user.role === 'student' && (
        <div className="erean-card">
          <h2 className="erean-card__title mb-3">My courses</h2>
          {enrollments.length === 0 ? (
            <EmptyState
              icon="bi-mortarboard"
              title="You haven't enrolled in anything yet"
              hint="Browse the catalogue to find a course."
              action={
                <Link to="/courses" className="btn btn-primary btn-sm mt-2">
                  Browse courses
                </Link>
              }
            />
          ) : (
            enrollments.map((enrollment) => (
              <div className="erean-list-row" key={enrollment.id}>
                <div className="erean-list-row__main">
                  <p className="erean-list-row__title">
                    <Link to={`/courses/${enrollment.course}`}>
                      {enrollment.course_title}
                    </Link>
                  </p>
                  <StatusBadge status={enrollment.status} />
                </div>
                <ProgressBar value={enrollment.progress} />
              </div>
            ))
          )}
        </div>
      )}

      {user.role !== 'student' && (
        <div className="erean-card">
          <h2 className="erean-card__title mb-3">
            {user.role === 'admin' ? 'Recent courses' : 'My courses'}
          </h2>
          {courses.length === 0 ? (
            <EmptyState
              icon="bi-journals"
              title="No courses yet"
              hint="Create your first course to get started."
              action={
                <Link to="/courses" className="btn btn-primary btn-sm mt-2">
                  Go to courses
                </Link>
              }
            />
          ) : (
            courses.slice(0, 6).map((course) => (
              <div className="erean-list-row" key={course.id}>
                <div className="erean-list-row__main">
                  <p className="erean-list-row__title">
                    <Link to={`/courses/${course.id}`}>{course.title}</Link>
                  </p>
                  <span className="erean-card__meta">
                    {course.enrolled_count} enrolled ·{' '}
                    {plural(course.assignment_count, 'assignment')}
                  </span>
                </div>
                <StatusBadge status={course.status} />
              </div>
            ))
          )}
        </div>
      )}
    </>
  );
}
