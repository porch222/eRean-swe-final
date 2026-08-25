import 'package:flutter/material.dart';

import '../api/client.dart';
import '../api/resources.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  bool _loading = true;
  String? _error;
  List<Map<String, dynamic>> _rows = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    final result = await Api.notifications();
    if (!mounted) return;
    setState(() {
      _loading = false;
      if (result.ok) {
        _rows = asList(result.data);
      } else {
        _error = result.message;
      }
    });
  }

  Future<void> _markAll() async {
    final result = await Api.markAllRead();
    if (!mounted) return;
    if (result.ok) {
      _load();
    } else {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(result.message)));
    }
  }

  IconData _icon(String? kind) => switch (kind) {
        'announcement' => Icons.campaign_outlined,
        'grade' => Icons.grade_outlined,
        'drop_request' => Icons.logout_outlined,
        'discussion' => Icons.forum_outlined,
        _ => Icons.notifications_none,
      };

  @override
  Widget build(BuildContext context) {
    final unread = _rows.where((r) => r['is_read'] == false).length;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Notifications'),
        actions: [
          if (unread > 0)
            TextButton(
                onPressed: _markAll, child: const Text('Mark all read')),
        ],
      ),
      body: _loading
          ? const Loading()
          : _error != null
              ? ErrorView(message: _error!, onRetry: _load)
              : _rows.isEmpty
                  ? const EmptyView(
                      icon: Icons.notifications_none,
                      title: 'Nothing yet',
                      hint: 'Announcements, grades and decisions on your '
                          'requests appear here.',
                    )
                  : RefreshIndicator(
                      onRefresh: _load,
                      child: ListView.separated(
                        padding: const EdgeInsets.all(T.s4),
                        itemCount: _rows.length,
                        separatorBuilder: (_, _) =>
                            const SizedBox(height: T.s2),
                        itemBuilder: (_, i) {
                          final n = _rows[i];
                          final isUnread = n['is_read'] == false;
                          return Card(
                            color: isUnread ? T.brand50 : null,
                            child: Padding(
                              padding: const EdgeInsets.all(T.s4),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Icon(_icon(n['kind'] as String?),
                                      size: 20,
                                      color: isUnread ? T.brand600 : T.n400),
                                  const SizedBox(width: T.s3),
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text('${n['message']}',
                                            style: TextStyle(
                                              fontSize: 14,
                                              height: 1.4,
                                              fontWeight: isUnread
                                                  ? FontWeight.w600
                                                  : FontWeight.w400,
                                            )),
                                        const SizedBox(height: 4),
                                        Text(
                                            formatDateTime(n['created_at']),
                                            style: const TextStyle(
                                                color: T.n500,
                                                fontSize: 12)),
                                      ],
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
                    ),
    );
  }
}
