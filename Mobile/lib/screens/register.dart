import 'package:flutter/material.dart';

import '../api/resources.dart';
import '../theme/tokens.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _fields = {
    'username': TextEditingController(),
    'email': TextEditingController(),
    'first_name': TextEditingController(),
    'last_name': TextEditingController(),
    'password': TextEditingController(),
    'password_confirm': TextEditingController(),
  };

  bool _busy = false;
  String? _formError;
  Map<String, String> _errors = {};

  @override
  void dispose() {
    for (final c in _fields.values) {
      c.dispose();
    }
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() {
      _busy = true;
      _errors = {};
      _formError = null;
    });

    final result = await Api.register(
      _fields.map((key, c) => MapEntry(key, c.text.trim())),
    );

    if (!mounted) return;

    if (result.ok) {
      Navigator.of(context).pop();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Account created. You can sign in now.')),
      );
      return;
    }

    setState(() {
      _busy = false;
      _errors = result.fieldErrors;
      _formError = result.status == 429
          ? 'Too many sign-up attempts. Try again later.'
          : (_errors.isEmpty ? result.message : null);
    });
  }

  Widget _input(
    String key,
    String label, {
    bool obscure = false,
    TextInputType? type,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: T.s3),
      child: TextField(
        controller: _fields[key],
        obscureText: obscure,
        keyboardType: type,
        autocorrect: false,
        enableSuggestions: false,
        decoration: InputDecoration(
          labelText: label,
          errorText: _errors[key],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Create account')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(T.s4),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (_formError != null) ...[
                Container(
                  padding: const EdgeInsets.all(T.s3),
                  decoration: BoxDecoration(
                    color: T.bad50,
                    borderRadius: BorderRadius.circular(T.radius),
                  ),
                  child: Text(_formError!,
                      style: const TextStyle(color: T.bad600)),
                ),
                const SizedBox(height: T.s4),
              ],
              _input('username', 'Username'),
              _input('email', 'Email', type: TextInputType.emailAddress),
              Row(children: [
                Expanded(child: _input('first_name', 'First name')),
                const SizedBox(width: T.s3),
                Expanded(child: _input('last_name', 'Last name')),
              ]),
              _input('password', 'Password', obscure: true),
              _input('password_confirm', 'Confirm password', obscure: true),
              const SizedBox(height: T.s2),
              FilledButton(
                onPressed: _busy ? null : _submit,
                child: Text(_busy ? 'Creating…' : 'Create account'),
              ),
              const SizedBox(height: T.s3),
              const Text(
                'Your major is assigned by the registrar after your account is '
                'created.',
                textAlign: TextAlign.center,
                style: TextStyle(color: T.n400, fontSize: 12.5, height: 1.4),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
