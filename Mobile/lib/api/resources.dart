import 'client.dart';

class Api {
  static final _c = ApiClient.instance;

  static Future<ApiResult> _get(String path, [Map<String, String>? q]) =>
      _c.send('GET', path, query: q);

  static Future<ApiResult> login(String username, String password) =>
      _c.send('POST', '/api/auth/token/',
          body: {'username': username, 'password': password});

  static Future<ApiResult> register(Map<String, String> form) =>
      _c.send('POST', '/api/auth/register/', body: form);

  static Future<ApiResult> me() => _get('/api/users/me/');

  static Future<ApiResult> updateProfile(Map<String, String> form) =>
      _c.send('PATCH', '/api/users/me/', body: form);

  static Future<ApiResult> changePassword(Map<String, String> form) =>
      _c.send('POST', '/api/users/me/password/', body: form);

  static Future<ApiResult> courses({String? search}) => _get(
        '/api/courses/',
        {'status': 'published', if (search != null && search.isNotEmpty) 'search': search},
      );

  static Future<ApiResult> course(int id) => _get('/api/courses/$id/');

  static Future<ApiResult> materials(int courseId) =>
      _get('/api/courses/$courseId/materials/');

  static Future<ApiResult> announcements(int courseId) =>
      _get('/api/courses/$courseId/announcements/');

  static Future<ApiResult> assignments(int courseId) =>
      _get('/api/courses/$courseId/assignments/');

  static Future<ApiResult> assignment(int courseId, int id) =>
      _get('/api/courses/$courseId/assignments/$id/');

  static Future<ApiResult> myEnrollments() => _get('/api/enrollments/');

  static Future<ApiResult> enrol(int courseId) =>
      _c.send('POST', '/api/enrollments/', body: {'course': courseId});

  static Future<ApiResult> requestDrop(int enrollmentId, String reason) =>
      _c.send('POST', '/api/enrollments/drop-requests/',
          body: {'enrollment': enrollmentId, 'reason': reason});

  static Future<ApiResult> myDropRequests() =>
      _get('/api/enrollments/drop-requests/');

  static Future<ApiResult> mySubmissions() => _get('/api/my-submissions/');

  static Future<ApiResult> transcript() => _get('/api/enrollments/transcript/');

  static Future<ApiResult> curricula(int majorId) =>
      _get('/api/courses/curricula/', {'major': '$majorId', 'active': 'true'});

  static Future<ApiResult> curriculumProgress(int id) =>
      _get('/api/courses/curricula/$id/progress/');

  static Future<ApiResult> submitWork(
    int courseId,
    int assignmentId, {
    String? text,
    String? filePath,
  }) =>
      _c.upload(
        '/api/courses/$courseId/assignments/$assignmentId/submissions/',
        fields: {if (text != null && text.isNotEmpty) 'text_answer': text},
        filePath: filePath,
      );

  static Future<ApiResult> mySubmissionsFor(int courseId, int assignmentId) =>
      _get('/api/courses/$courseId/assignments/$assignmentId/submissions/');

  static Future<ApiResult> quizQuestions(int courseId, int assignmentId) =>
      _get('/api/courses/$courseId/assignments/$assignmentId/questions/');

  static Future<ApiResult> submitQuiz(
    int courseId,
    int assignmentId,
    List<Map<String, dynamic>> answers,
  ) =>
      _c.send('POST',
          '/api/courses/$courseId/assignments/$assignmentId/attempts/',
          body: {'answers': answers});

  static Future<ApiResult> threads(int courseId) =>
      _get('/api/courses/$courseId/discussions/');

  static Future<ApiResult> thread(int courseId, int id) =>
      _get('/api/courses/$courseId/discussions/$id/');

  static Future<ApiResult> createThread(
          int courseId, String title, String body, String kind) =>
      _c.send('POST', '/api/courses/$courseId/discussions/',
          body: {'title': title, 'body': body, 'kind': kind});

  static Future<ApiResult> reply(int courseId, int threadId, String body) =>
      _c.send('POST', '/api/courses/$courseId/discussions/$threadId/replies/',
          body: {'body': body});

  static Future<ApiResult> myAttendance(int courseId) =>
      _get('/api/courses/$courseId/attendance/me/');

  static Future<ApiResult> notifications() => _get('/api/notifications/');

  static Future<ApiResult> unreadCount() =>
      _get('/api/notifications/unread-count/');

  static Future<ApiResult> markAllRead() =>
      _c.send('POST', '/api/notifications/read-all/', body: const {});
}
