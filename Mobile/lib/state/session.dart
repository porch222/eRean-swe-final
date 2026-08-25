import 'package:flutter/foundation.dart';

import '../api/client.dart';
import '../api/resources.dart';

class Session extends ChangeNotifier {
  Session() {

    ApiClient.instance.sessionExpired.addListener(() {
      _user = null;
      notifyListeners();
    });
  }

  Map<String, dynamic>? _user;
  bool _loading = true;

  Map<String, dynamic>? get user => _user;
  bool get loading => _loading;
  bool get signedIn => _user != null;

  String get displayName {
    final name = _user?['full_name'];
    if (name is String && name.trim().isNotEmpty) return name;
    return _user?['username'] as String? ?? '';
  }

  int? get majorId => _user?['major'] as int?;
  String? get majorName =>
      (_user?['major_detail'] as Map<String, dynamic>?)?['name'] as String?;

  Future<void> restore() async {
    await ApiClient.instance.loadTokens();
    if (ApiClient.instance.hasSession) {
      final result = await Api.me();
      if (result.ok) _user = result.data as Map<String, dynamic>;
    }
    _loading = false;
    notifyListeners();
  }

  Future<String?> signIn(String username, String password) async {
    final result = await Api.login(username, password);
    if (!result.ok) {
      if (result.status == 429) {
        return 'Too many attempts. Wait a minute and try again.';
      }
      if (result.status == 401) return 'Wrong username or password.';
      return result.message;
    }

    final data = result.data as Map<String, dynamic>;
    await ApiClient.instance
        .setTokens(data['access'] as String?, data['refresh'] as String?);

    final profile = await Api.me();
    if (!profile.ok) return profile.message;

    _user = profile.data as Map<String, dynamic>;

    if (_user!['role'] != 'student') {
      _user = null;
      await ApiClient.instance.clearTokens();
      return 'This app is for students. Staff should use the web version.';
    }

    notifyListeners();
    return null;
  }

  Future<void> signOut() async {
    await ApiClient.instance.clearTokens();
    _user = null;
    notifyListeners();
  }
}
