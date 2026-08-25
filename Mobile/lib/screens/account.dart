import 'package:flutter/material.dart';

import '../api/resources.dart';
import '../main.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';

class AccountScreen extends StatefulWidget {
  const AccountScreen({super.key});

  @override
  State<AccountScreen> createState() => _AccountScreenState();
}

class _AccountScreenState extends State<AccountScreen> {
  late final TextEditingController _first;
  late final TextEditingController _last;
  late final TextEditingController _email;
  bool _busy = false;
  Map<String, String> _errors = {};

  @override
  void initState() {
    super.initState();
    final user = SessionScope.of(context).user ?? const {};
    _first = TextEditingController(text: '${user['first_name'] ?? ''}');
    _last = TextEditingController(text: '${user['last_name'] ?? ''}');
    _email = TextEditingController(text: '${user['email'] ?? ''}');
  }

  @override
  void dispose() {
    _first.dispose();
    _last.dispose();
    _email.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    setState(() {
      _busy = true;
      _errors = {};
    });

    final result = await Api.updateProfile({
      'first_name': _first.text.trim(),
      'last_name': _last.text.trim(),
      'email': _email.text.trim(),
    });

    if (!mounted) return;

    if (!result.ok) {
      setState(() {
        _busy = false;
        _errors = result.fieldErrors;
      });
      if (_errors.isEmpty) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text(result.message)));
      }
      return;
    }

    await SessionScope.of(context).restore();
    if (!mounted) return;
    Navigator.of(context).pop();
    ScaffoldMessenger.of(context)
        .showSnackBar(const SnackBar(content: Text('Details saved.')));
  }

  @override
  Widget build(BuildContext context) {
    final session = SessionScope.of(context);
    return Scaffold(
      appBar: AppBar(title: const Text('Edit details')),
      body: ListView(
        padding: const EdgeInsets.all(T.s4),
        children: [
          TextField(
            controller: _first,
            decoration: InputDecoration(
                labelText: 'First name', errorText: _errors['first_name']),
          ),
          const SizedBox(height: T.s3),
          TextField(
            controller: _last,
            decoration: InputDecoration(
                labelText: 'Last name', errorText: _errors['last_name']),
          ),
          const SizedBox(height: T.s3),
          TextField(
            controller: _email,
            keyboardType: TextInputType.emailAddress,
            decoration:
                InputDecoration(labelText: 'Email', errorText: _errors['email']),
          ),
          const SizedBox(height: T.s5),
          FilledButton(
            onPressed: _busy ? null : _save,
            child: Text(_busy ? 'Saving…' : 'Save changes'),
          ),
          const SizedBox(height: T.s5),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(T.s4),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Eyebrow('Set by the registrar'),
                  const SizedBox(height: T.s2),
                  Text('Major: ${session.majorName ?? 'not assigned'}',
                      style: const TextStyle(color: T.n600)),
                  const SizedBox(height: 4),
                  const Text(
                    'Only an administrator can change your major.',
                    style: TextStyle(color: T.n500, fontSize: 12.5),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class PasswordScreen extends StatefulWidget {
  const PasswordScreen({super.key});

  @override
  State<PasswordScreen> createState() => _PasswordScreenState();
}

class _PasswordScreenState extends State<PasswordScreen> {
  final _current = TextEditingController();
  final _next = TextEditingController();
  final _confirm = TextEditingController();
  bool _busy = false;
  Map<String, String> _errors = {};

  @override
  void dispose() {
    _current.dispose();
    _next.dispose();
    _confirm.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    setState(() {
      _busy = true;
      _errors = {};
    });

    final result = await Api.changePassword({
      'current_password': _current.text,
      'new_password': _next.text,
      'new_password_confirm': _confirm.text,
    });

    if (!mounted) return;
    setState(() {
      _busy = false;
      _errors = result.fieldErrors;
    });

    if (result.ok) {
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context)
          .showSnackBar(const SnackBar(content: Text('Password changed.')));
    } else if (_errors.isEmpty) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(result.message)));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Change password')),
      body: ListView(
        padding: const EdgeInsets.all(T.s4),
        children: [
          TextField(
            controller: _current,
            obscureText: true,
            decoration: InputDecoration(
                labelText: 'Current password',
                errorText: _errors['current_password']),
          ),
          const SizedBox(height: T.s3),
          TextField(
            controller: _next,
            obscureText: true,
            decoration: InputDecoration(
                labelText: 'New password', errorText: _errors['new_password']),
          ),
          const SizedBox(height: T.s3),
          TextField(
            controller: _confirm,
            obscureText: true,
            decoration: InputDecoration(
                labelText: 'Confirm new password',
                errorText: _errors['new_password_confirm']),
          ),
          const SizedBox(height: T.s5),
          FilledButton(
            onPressed: _busy ? null : _save,
            child: Text(_busy ? 'Saving…' : 'Change password'),
          ),
        ],
      ),
    );
  }
}
