import { del, downloadFile, get, patch, post, postForm } from './client';

function query(params = {}) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      search.append(key, value);
    }
  });
  const asString = search.toString();
  return asString ? `?${asString}` : '';
}

export const login = (username, password) =>
  post('/api/auth/token/', { username, password });

export const register = (payload) => post('/api/auth/register/', payload);

export const logout = (refresh) => post('/api/auth/logout/', { refresh });

export const fetchMe = () => get('/api/users/me/');

export const updateMe = (payload) => patch('/api/users/me/', payload);

export const changePassword = (payload) => post('/api/users/me/password/', payload);

export const listUsers = (params) => get(`/api/users/${query(params)}`);

export const createUser = (payload) => post('/api/users/', payload);

export const updateUser = (id, payload) => patch(`/api/users/${id}/`, payload);

export const deleteUser = (id) => del(`/api/users/${id}/`);

export const listCourses = (params) => get(`/api/courses/${query(params)}`);

export const getCourse = (id) => get(`/api/courses/${id}/`);

export const createCourse = (payload) => post('/api/courses/', payload);

export const updateCourse = (id, payload) => patch(`/api/courses/${id}/`, payload);

export const deleteCourse = (id) => del(`/api/courses/${id}/`);

export const approveCourse = (id, status) =>
  patch(`/api/courses/${id}/approve/`, { status });

export const getCoursePerformance = (id) => get(`/api/courses/${id}/performance/`);

export const listActivityLogs = (params) =>
  get(`/api/courses/activity-logs/${query(params)}`);

export const listMaterials = (courseId) => get(`/api/courses/${courseId}/materials/`);

export const createMaterial = (courseId, formData) =>
  postForm(`/api/courses/${courseId}/materials/`, formData);

export const deleteMaterial = (courseId, id) =>
  del(`/api/courses/${courseId}/materials/${id}/`);

export const downloadMaterial = (courseId, id, filename) =>
  downloadFile(`/api/courses/${courseId}/materials/${id}/download/`, filename);

export const listAnnouncements = (courseId) =>
  get(`/api/courses/${courseId}/announcements/`);

export const createAnnouncement = (courseId, payload) =>
  post(`/api/courses/${courseId}/announcements/`, payload);

export const updateAnnouncement = (courseId, id, payload) =>
  patch(`/api/courses/${courseId}/announcements/${id}/`, payload);

export const deleteAnnouncement = (courseId, id) =>
  del(`/api/courses/${courseId}/announcements/${id}/`);

export const markAnnouncementRead = (courseId, id) =>
  post(`/api/courses/${courseId}/announcements/${id}/read/`, {});

export const listAssignments = (courseId) =>
  get(`/api/courses/${courseId}/assignments/`);

export const getAssignment = (courseId, id) =>
  get(`/api/courses/${courseId}/assignments/${id}/`);

export const createAssignment = (courseId, payload) =>
  post(`/api/courses/${courseId}/assignments/`, payload);

export const updateAssignment = (courseId, id, payload) =>
  patch(`/api/courses/${courseId}/assignments/${id}/`, payload);

export const deleteAssignment = (courseId, id) =>
  del(`/api/courses/${courseId}/assignments/${id}/`);

export const listSubmissions = (courseId, assignmentId) =>
  get(`/api/courses/${courseId}/assignments/${assignmentId}/submissions/`);

export const createSubmission = (courseId, assignmentId, formData) =>
  postForm(`/api/courses/${courseId}/assignments/${assignmentId}/submissions/`, formData);

export const gradeSubmission = (courseId, assignmentId, id, payload) =>
  patch(`/api/courses/${courseId}/assignments/${assignmentId}/submissions/${id}/`, payload);

export const downloadSubmission = (courseId, assignmentId, id, filename) =>
  downloadFile(
    `/api/courses/${courseId}/assignments/${assignmentId}/submissions/${id}/download/`,
    filename,
  );

export const listMySubmissions = () => get('/api/my-submissions/');

export const listQuestions = (courseId, assignmentId) =>
  get(`/api/courses/${courseId}/assignments/${assignmentId}/questions/`);

export const createQuestion = (courseId, assignmentId, payload) =>
  post(`/api/courses/${courseId}/assignments/${assignmentId}/questions/`, payload);

export const deleteQuestion = (courseId, assignmentId, id) =>
  del(`/api/courses/${courseId}/assignments/${assignmentId}/questions/${id}/`);

export const createChoice = (courseId, assignmentId, questionId, payload) =>
  post(
    `/api/courses/${courseId}/assignments/${assignmentId}/questions/${questionId}/choices/`,
    payload,
  );

export const deleteChoice = (courseId, assignmentId, questionId, id) =>
  del(
    `/api/courses/${courseId}/assignments/${assignmentId}/questions/${questionId}/choices/${id}/`,
  );

export const listAttempts = (courseId, assignmentId) =>
  get(`/api/courses/${courseId}/assignments/${assignmentId}/attempts/`);

export const submitAttempt = (courseId, assignmentId, answers) =>
  post(`/api/courses/${courseId}/assignments/${assignmentId}/attempts/`, { answers });

export const listEnrollments = (params) => get(`/api/enrollments/${query(params)}`);

export const enroll = (courseId) => post('/api/enrollments/', { course: courseId });

export const updateEnrollment = (id, payload) => patch(`/api/enrollments/${id}/`, payload);

export const listDropRequests = (params) =>
  get(`/api/enrollments/drop-requests/${query(params)}`);

export const requestDrop = (enrollmentId, reason) =>
  post('/api/enrollments/drop-requests/', { enrollment: enrollmentId, reason });

export const decideDropRequest = (id, payload) =>
  post(`/api/enrollments/drop-requests/${id}/decide/`, payload);

export const finalizeGrade = (enrollmentId) =>
  post(`/api/enrollments/${enrollmentId}/finalize/`, {});

export const getTranscript = (params) =>
  get(`/api/enrollments/transcript/${query(params)}`);

export const getGradebook = (courseId) => get(`/api/courses/${courseId}/gradebook/`);

export const listTerms = () => get('/api/courses/terms/');
export const getCurrentTerm = () => get('/api/courses/terms/current/');
export const createTerm = (payload) => post('/api/courses/terms/', payload);
export const updateTerm = (id, payload) => patch(`/api/courses/terms/${id}/`, payload);
export const deleteTerm = (id) => del(`/api/courses/terms/${id}/`);

export const listMajors = () => get('/api/courses/majors/');
export const createMajor = (payload) => post('/api/courses/majors/', payload);
export const updateMajor = (id, payload) => patch(`/api/courses/majors/${id}/`, payload);
export const deleteMajor = (id) => del(`/api/courses/majors/${id}/`);

export const listCurricula = (params) => get(`/api/courses/curricula/${query(params)}`);
export const getCurriculum = (id) => get(`/api/courses/curricula/${id}/`);
export const createCurriculum = (payload) => post('/api/courses/curricula/', payload);
export const updateCurriculum = (id, payload) =>
  patch(`/api/courses/curricula/${id}/`, payload);
export const deleteCurriculum = (id) => del(`/api/courses/curricula/${id}/`);
export const getCurriculumProgress = (id, params) =>
  get(`/api/courses/curricula/${id}/progress/${query(params)}`);
export const addCourseToCurriculum = (curriculumId, payload) =>
  post(`/api/courses/curricula/${curriculumId}/courses/`, payload);
export const removeCourseFromCurriculum = (curriculumId, id) =>
  del(`/api/courses/curricula/${curriculumId}/courses/${id}/`);

export const listAttendanceSessions = (courseId) =>
  get(`/api/courses/${courseId}/attendance/`);
export const createAttendanceSession = (courseId, payload) =>
  post(`/api/courses/${courseId}/attendance/`, payload);
export const markAttendance = (courseId, sessionId, records) =>
  post(`/api/courses/${courseId}/attendance/${sessionId}/mark/`, { records });
export const getMyAttendance = (courseId, params) =>
  get(`/api/courses/${courseId}/attendance/me/${query(params)}`);
export const getAttendanceSummary = (courseId) =>
  get(`/api/courses/${courseId}/attendance/summary/`);

export const listThreads = (courseId, params) =>
  get(`/api/courses/${courseId}/discussions/${query(params)}`);
export const getThread = (courseId, id) =>
  get(`/api/courses/${courseId}/discussions/${id}/`);
export const createThread = (courseId, payload) =>
  post(`/api/courses/${courseId}/discussions/`, payload);
export const deleteThread = (courseId, id) =>
  del(`/api/courses/${courseId}/discussions/${id}/`);
export const moderateThread = (courseId, id, payload) =>
  patch(`/api/courses/${courseId}/discussions/${id}/moderate/`, payload);
export const createReply = (courseId, threadId, body) =>
  post(`/api/courses/${courseId}/discussions/${threadId}/replies/`, { body });
export const deleteReply = (courseId, threadId, id) =>
  del(`/api/courses/${courseId}/discussions/${threadId}/replies/${id}/`);
export const acceptAnswer = (courseId, threadId, id) =>
  post(`/api/courses/${courseId}/discussions/${threadId}/replies/${id}/accept/`, {});

export const listNotifications = (params) => get(`/api/notifications/${query(params)}`);
export const getUnreadCount = () => get('/api/notifications/unread-count/');
export const markNotificationRead = (id) => patch(`/api/notifications/${id}/`, { is_read: true });
export const markAllNotificationsRead = () => post('/api/notifications/read-all/', {});

export const listPendingWrittenAnswers = (courseId, assignmentId) =>
  get(`/api/courses/${courseId}/assignments/${assignmentId}/written-answers/`);
export const gradeWrittenAnswer = (courseId, assignmentId, id, points) =>
  post(
    `/api/courses/${courseId}/assignments/${assignmentId}/written-answers/${id}/grade/`,
    { awarded_points: points },
  );
