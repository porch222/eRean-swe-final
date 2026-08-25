import 'package:flutter/material.dart';

import '../api/resources.dart';
import '../main.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';
import 'account.dart';
import 'curriculum.dart';
import 'drop_requests.dart';
import 'notifications.dart';
import 'transcript.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  int _unread = 0;

  @override
  void initState() {
    super.initState();
    _loadUnread();
  }

  Future<void> _loadUnread() async {
    final result = await Api.unreadCount();
    if (!mounted || !result.ok) return;
    setState(() => _unread = result.data['count'] as int? ?? 0);
  }

  Future<void> _signOut() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Sign out?'),
        content: const Text('You will need your password to sign back in.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancel')),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: T.bad600),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Sign out'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    await SessionScope.of(context).signOut();
  }

  @override
  Widget build(BuildContext context) {
    final session = SessionScope.of(context);
    final user = session.user ?? const {};

    return Scaffold(
      appBar: AppBar(title: const Text('Profile')),
      body: ListView(
        padding: const EdgeInsets.all(T.s4),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(T.s4),
              child: Row(children: [
                CircleAvatar(
                  radius: 26,
                  backgroundColor: T.brand50,
                  child: Text(
                    _initials(session.displayName),
                    style: const TextStyle(
                        color: T.brand700,
                        fontWeight: FontWeight.w700,
                        fontSize: 17),
                  ),
                ),
                const SizedBox(width: T.s4),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(session.displayName,
                          style: const TextStyle(
                              fontSize: 17, fontWeight: FontWeight.w600)),
                      const SizedBox(height: 2),
                      Text('${user['email'] ?? ''}',
                          style: const TextStyle(
                              color: T.n500, fontSize: 13)),
                      const SizedBox(height: T.s2),
                      Pill(session.majorName ?? 'No major assigned',
                          tone: session.majorName == null
                              ? PillTone.warning
                              : PillTone.info),
                    ],
                  ),
                ),
              ]),
            ),
          ),
          const SizedBox(height: T.s5),

          const Eyebrow('Academic record'),
          const SizedBox(height: T.s2),
          Card(
            child: Column(children: [
              NavRow(
                icon: Icons.receipt_long_outlined,
                title: 'Transcript',
                subtitle: 'Results by term, credits and GPA',
                onTap: () => Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) => const TranscriptScreen())),
              ),
              const Divider(height: 1),
              NavRow(
                icon: Icons.account_tree_outlined,
                title: 'My curriculum',
                subtitle: 'Progress towards graduation',
                onTap: () => Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) => const CurriculumScreen())),
              ),
              const Divider(height: 1),
              NavRow(
                icon: Icons.logout_outlined,
                title: 'Drop requests',
                subtitle: 'Requests you have raised',
                onTap: () => Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) => const DropRequestsScreen())),
              ),
            ]),
          ),
          const SizedBox(height: T.s5),

          const Eyebrow('Account'),
          const SizedBox(height: T.s2),
          Card(
            child: Column(children: [
              NavRow(
                icon: Icons.notifications_none,
                title: 'Notifications',
                subtitle: _unread == 0
                    ? 'Nothing unread'
                    : plural(_unread, 'unread notification'),
                trailing: _unread == 0
                    ? const Icon(Icons.chevron_right,
                        color: T.n400, size: 22)
                    : Pill('$_unread', tone: PillTone.info),
                onTap: () async {
                  await Navigator.of(context).push(MaterialPageRoute(
                      builder: (_) => const NotificationsScreen()));
                  _loadUnread();
                },
              ),
              const Divider(height: 1),
              NavRow(
                icon: Icons.person_outline,
                title: 'Edit details',
                subtitle: 'Name and email',
                onTap: () async {
                  await Navigator.of(context).push(MaterialPageRoute(
                      builder: (_) => const AccountScreen()));
                  if (mounted) setState(() {});
                },
              ),
              const Divider(height: 1),
              NavRow(
                icon: Icons.lock_outline,
                title: 'Change password',
                onTap: () => Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) => const PasswordScreen())),
              ),
            ]),
          ),
          const SizedBox(height: T.s5),

          OutlinedButton.icon(
            onPressed: _signOut,
            icon: const Icon(Icons.logout, size: 18),
            style: OutlinedButton.styleFrom(foregroundColor: T.bad600),
            label: const Text('Sign out'),
          ),
          const SizedBox(height: T.s5),
          const Text(
            'eRean student app · version 1.0',
            textAlign: TextAlign.center,
            style: TextStyle(color: T.n400, fontSize: 12),
          ),
        ],
      ),
    );
  }

  String _initials(String name) {
    final parts = name.trim().split(RegExp(r'\s+'));
    if (parts.isEmpty || parts.first.isEmpty) return '?';
    if (parts.length == 1) return parts.first[0].toUpperCase();
    return (parts.first[0] + parts.last[0]).toUpperCase();
  }
}
