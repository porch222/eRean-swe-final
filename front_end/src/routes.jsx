import { Navigate, Route, Routes } from 'react-router-dom';

import AppLayout from './components/AppLayout';
import ProtectedRoute from './components/ProtectedRoute';
import AdminAcademics from './pages/AdminAcademics';
import AdminActivity from './pages/AdminActivity';
import AdminApprovals from './pages/AdminApprovals';
import AdminUsers from './pages/AdminUsers';
import AssignmentDetail from './pages/AssignmentDetail';
import CourseDetail from './pages/CourseDetail';
import CourseList from './pages/CourseList';
import Curriculum from './pages/Curriculum';
import Dashboard from './pages/Dashboard';
import DropRequests from './pages/DropRequests';
import Gradebook from './pages/Gradebook';
import Login from './pages/Login';
import MyEnrollments from './pages/MyEnrollments';
import MyGrades from './pages/MyGrades';
import NotFound from './pages/NotFound';
import Notifications from './pages/Notifications';
import Profile from './pages/Profile';
import Register from './pages/Register';
import Transcript from './pages/Transcript';

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<AppLayout><Dashboard /></AppLayout>} />
        <Route path="/profile" element={<AppLayout><Profile /></AppLayout>} />
        <Route path="/notifications" element={<AppLayout><Notifications /></AppLayout>} />
        <Route path="/courses" element={<AppLayout><CourseList /></AppLayout>} />
        <Route path="/courses/:courseId" element={<AppLayout><CourseDetail /></AppLayout>} />
        <Route
          path="/courses/:courseId/assignments/:assignmentId"
          element={<AppLayout><AssignmentDetail /></AppLayout>}
        />
      </Route>

      <Route element={<ProtectedRoute allowedRoles={['student']} />}>
        <Route path="/enrollments" element={<AppLayout><MyEnrollments /></AppLayout>} />
        <Route path="/grades" element={<AppLayout><MyGrades /></AppLayout>} />
        <Route path="/transcript" element={<AppLayout><Transcript /></AppLayout>} />
        <Route path="/curriculum" element={<AppLayout><Curriculum /></AppLayout>} />
      </Route>

      <Route element={<ProtectedRoute allowedRoles={['admin', 'instructor']} />}>
        <Route
          path="/courses/:courseId/gradebook"
          element={<AppLayout><Gradebook /></AppLayout>}
        />
        <Route path="/drop-requests" element={<AppLayout><DropRequests /></AppLayout>} />
      </Route>

      <Route element={<ProtectedRoute allowedRoles={['admin']} />}>
        <Route path="/admin/users" element={<AppLayout><AdminUsers /></AppLayout>} />
        <Route path="/admin/approvals" element={<AppLayout><AdminApprovals /></AppLayout>} />
        <Route path="/admin/activity" element={<AppLayout><AdminActivity /></AppLayout>} />
        <Route path="/admin/academics" element={<AppLayout><AdminAcademics /></AppLayout>} />
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
