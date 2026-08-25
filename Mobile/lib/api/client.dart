import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:http/http.dart' as http;

const String kApiBase = String.fromEnvironment(
  'EREAN_API',
  defaultValue: 'https://erean-server.onrender.com',
);

class ApiResult {
  final bool ok;
  final int status;
  final dynamic data;
  final Map<String, dynamic> error;

  const ApiResult.success(this.data, [this.status = 200])
    : ok = true,
      error = const {};

  const ApiResult.failure(this.status, this.error) : ok = false, data = null;

  String get message {
    if (error['detail'] is String) return error['detail'] as String;
    for (final value in error.values) {
      if (value is String) return value;
      if (value is List && value.isNotEmpty) return '${value.first}';
    }
    return 'Something went wrong. Please try again.';
  }

  Map<String, String> get fieldErrors {
    final out = <String, String>{};
    error.forEach((key, value) {
      if (key == 'detail') return;
      if (value is List && value.isNotEmpty) out[key] = '${value.first}';
      if (value is String) out[key] = value;
    });
    return out;
  }
}

class ApiClient {
  ApiClient._();
  static final ApiClient instance = ApiClient._();

  static const _storage = FlutterSecureStorage();
  static const _accessKey = 'erean_access';
  static const _refreshKey = 'erean_refresh';

  final ValueNotifier<int> sessionExpired = ValueNotifier(0);

  String? _access;
  String? _refresh;

  Future<String?>? _refreshing;

  Future<void> loadTokens() async {
    _access = await _storage.read(key: _accessKey);
    _refresh = await _storage.read(key: _refreshKey);
  }

  bool get hasSession => _refresh != null;

  Future<void> setTokens(String? access, String? refresh) async {
    if (access != null) {
      _access = access;
      await _storage.write(key: _accessKey, value: access);
    }
    if (refresh != null) {
      _refresh = refresh;
      await _storage.write(key: _refreshKey, value: refresh);
    }
  }

  Future<void> clearTokens() async {
    _access = null;
    _refresh = null;
    await _storage.delete(key: _accessKey);
    await _storage.delete(key: _refreshKey);
  }

  Future<String?> _refreshAccess() {
    final refresh = _refresh;
    if (refresh == null) return Future.value(null);

    return _refreshing ??= http
        .post(
          Uri.parse('$kApiBase/api/auth/token/refresh/'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'refresh': refresh}),
        )
        .then<String?>((response) async {
          if (response.statusCode != 200) return null;
          final body = jsonDecode(response.body) as Map<String, dynamic>;
          final access = body['access'] as String?;
          if (access != null) await setTokens(access, null);
          return access;
        })
        .catchError((_) => null)
        .whenComplete(() => _refreshing = null);
  }

  Future<ApiResult> send(
    String method,
    String path, {
    Object? body,
    Map<String, String>? query,
  }) async {
    final uri = Uri.parse(
      '$kApiBase$path',
    ).replace(queryParameters: query == null || query.isEmpty ? null : query);

    Future<http.Response> attempt(String? token) {
      final headers = <String, String>{
        if (body != null) 'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token',
      };
      final encoded = body == null ? null : jsonEncode(body);
      switch (method) {
        case 'POST':
          return http.post(uri, headers: headers, body: encoded);
        case 'PATCH':
          return http.patch(uri, headers: headers, body: encoded);
        case 'DELETE':
          return http.delete(uri, headers: headers);
        default:
          return http.get(uri, headers: headers);
      }
    }

    http.Response response;
    try {
      response = await attempt(_access);
    } catch (_) {
      return const ApiResult.failure(0, {
        'detail': 'Cannot reach the server. Check your connection.',
      });
    }

    if (response.statusCode == 401 && _refresh != null) {
      final fresh = await _refreshAccess();
      if (fresh == null) {
        await clearTokens();
        sessionExpired.value++;
        return const ApiResult.failure(401, {
          'detail': 'Your session has expired. Please sign in again.',
        });
      }
      try {
        response = await attempt(fresh);
      } catch (_) {
        return const ApiResult.failure(0, {
          'detail': 'Cannot reach the server. Check your connection.',
        });
      }
      if (response.statusCode == 401) {
        await clearTokens();
        sessionExpired.value++;
        return const ApiResult.failure(401, {
          'detail': 'Your session has expired. Please sign in again.',
        });
      }
    }

    return _decode(response);
  }

  Future<ApiResult> upload(
    String path, {
    Map<String, String> fields = const {},
    String? filePath,
    String fileField = 'file_url',
  }) async {
    final uri = Uri.parse('$kApiBase$path');

    Future<http.Response> attempt(String? token) async {
      final request = http.MultipartRequest('POST', uri)..fields.addAll(fields);
      if (filePath != null) {
        request.files.add(
          await http.MultipartFile.fromPath(fileField, filePath),
        );
      }
      if (token != null) request.headers['Authorization'] = 'Bearer $token';
      return http.Response.fromStream(await request.send());
    }

    http.Response response;
    try {
      response = await attempt(_access);
      if (response.statusCode == 401 && _refresh != null) {
        final fresh = await _refreshAccess();
        if (fresh == null) {
          await clearTokens();
          sessionExpired.value++;
          return const ApiResult.failure(401, {
            'detail': 'Your session has expired. Please sign in again.',
          });
        }
        response = await attempt(fresh);
      }
    } catch (_) {
      return const ApiResult.failure(0, {
        'detail': 'Upload failed. Check your connection.',
      });
    }

    return _decode(response);
  }

  Future<ApiResult> download(String path) async {
    try {
      final response = await http.get(
        Uri.parse('$kApiBase$path'),
        headers: {if (_access != null) 'Authorization': 'Bearer $_access'},
      );
      if (response.statusCode >= 400) return _decode(response);

      final type = response.headers['content-type'] ?? '';
      if (type.contains('application/json')) return _decode(response);
      return ApiResult.success(response.bodyBytes, response.statusCode);
    } catch (_) {
      return const ApiResult.failure(0, {'detail': 'Download failed.'});
    }
  }

  ApiResult _decode(http.Response response) {
    if (response.statusCode == 204 || response.body.isEmpty) {
      return ApiResult.success(null, response.statusCode);
    }

    dynamic body;
    try {
      body = jsonDecode(utf8.decode(response.bodyBytes));
    } catch (_) {
      body = null;
    }

    if (response.statusCode >= 400) {
      return ApiResult.failure(
        response.statusCode,
        body is Map<String, dynamic> ? body : const {},
      );
    }
    return ApiResult.success(body, response.statusCode);
  }
}

List<Map<String, dynamic>> asList(dynamic data) {
  if (data is List) return data.cast<Map<String, dynamic>>();
  if (data is Map && data['results'] is List) {
    return (data['results'] as List).cast<Map<String, dynamic>>();
  }
  return const [];
}
