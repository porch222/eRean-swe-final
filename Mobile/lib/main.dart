import 'package:flutter/material.dart';

import 'screens/login.dart';
import 'screens/shell.dart';
import 'state/session.dart';
import 'theme/tokens.dart';
import 'widgets/common.dart';

void main() {
  runApp(const EReanApp());
}

class SessionScope extends InheritedNotifier<Session> {
  const SessionScope({
    super.key,
    required Session session,
    required super.child,
  }) : super(notifier: session);

  static Session of(BuildContext context) {
    final scope =
        context.dependOnInheritedWidgetOfExactType<SessionScope>();
    assert(scope != null, 'No SessionScope above this widget');
    return scope!.notifier!;
  }
}

class EReanApp extends StatefulWidget {
  const EReanApp({super.key});

  @override
  State<EReanApp> createState() => _EReanAppState();
}

class _EReanAppState extends State<EReanApp> {
  final _session = Session();

  @override
  void initState() {
    super.initState();
    _session.restore();
  }

  @override
  void dispose() {
    _session.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return SessionScope(
      session: _session,
      child: MaterialApp(
        title: 'eRean',
        debugShowCheckedModeBanner: false,
        theme: buildTheme(),
        home: const _Root(),
      ),
    );
  }
}

class _Root extends StatelessWidget {
  const _Root();

  @override
  Widget build(BuildContext context) {
    final session = SessionScope.of(context);
    if (session.loading) {
      return const Scaffold(body: Loading(label: 'Starting…'));
    }
    return session.signedIn ? const AppShell() : const LoginScreen();
  }
}
