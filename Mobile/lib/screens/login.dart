import 'package:flutter/material.dart';

import '../main.dart';
import '../theme/tokens.dart';
import 'register.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _username = TextEditingController();
  final _password = TextEditingController();
  bool _busy = false;
  bool _obscure = true;
  String? _error;

  @override
  void dispose() {
    _username.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (_username.text.trim().isEmpty || _password.text.isEmpty) {
      setState(() => _error = 'Enter your username and password.');
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });

    final message = await SessionScope.of(context)
        .signIn(_username.text.trim(), _password.text);

    if (!mounted) return;
    setState(() {
      _busy = false;
      _error = message;
    });

  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: T.n50,
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(T.s5),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [

                  Align(
                    alignment: Alignment.centerLeft,
                    child: Container(
                      width: 52,
                      height: 52,
                      decoration: BoxDecoration(
                        color: T.brand600,
                        borderRadius: BorderRadius.circular(T.radius),
                      ),
                      child: const Icon(Icons.school, color: Colors.white),
                    ),
                  ),
                  const SizedBox(height: T.s5),
                  const Text('eRean',
                      style: TextStyle(
                          fontSize: 30,
                          fontWeight: FontWeight.w700,
                          color: T.n900)),
                  const SizedBox(height: T.s1),
                  const Text('Sign in to your student account',
                      style: TextStyle(color: T.n500, fontSize: 15)),
                  const SizedBox(height: T.s6),

                  if (_error != null) ...[
                    Container(
                      padding: const EdgeInsets.all(T.s3),
                      decoration: BoxDecoration(
                        color: T.bad50,
                        borderRadius: BorderRadius.circular(T.radius),
                      ),
                      child: Row(children: [
                        const Icon(Icons.error_outline,
                            color: T.bad600, size: 18),
                        const SizedBox(width: T.s2),
                        Expanded(
                          child: Text(_error!,
                              style: const TextStyle(
                                  color: T.bad600, fontSize: 13.5)),
                        ),
                      ]),
                    ),
                    const SizedBox(height: T.s4),
                  ],

                  TextField(
                    controller: _username,
                    autocorrect: false,
                    enableSuggestions: false,
                    textInputAction: TextInputAction.next,
                    decoration: const InputDecoration(labelText: 'Username'),
                  ),
                  const SizedBox(height: T.s3),
                  TextField(
                    controller: _password,
                    obscureText: _obscure,
                    textInputAction: TextInputAction.done,
                    onSubmitted: (_) => _submit(),
                    decoration: InputDecoration(
                      labelText: 'Password',
                      suffixIcon: IconButton(

                        tooltip: _obscure ? 'Show password' : 'Hide password',
                        icon: Icon(
                            _obscure ? Icons.visibility_off : Icons.visibility,
                            color: T.n500),
                        onPressed: () => setState(() => _obscure = !_obscure),
                      ),
                    ),
                  ),
                  const SizedBox(height: T.s5),

                  FilledButton(
                    onPressed: _busy ? null : _submit,
                    child: _busy
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                                strokeWidth: 2, color: Colors.white),
                          )
                        : const Text('Sign in'),
                  ),
                  const SizedBox(height: T.s3),
                  TextButton(
                    onPressed: _busy
                        ? null
                        : () => Navigator.of(context).push(MaterialPageRoute(
                            builder: (_) => const RegisterScreen())),
                    child: const Text('Create a student account'),
                  ),
                  const SizedBox(height: T.s2),
                  const Text(
                    'Forgot your password? eRean does not send email, so ask an '
                    'administrator to reset it for you.',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: T.n400, fontSize: 12.5, height: 1.4),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
