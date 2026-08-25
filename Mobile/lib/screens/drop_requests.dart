import 'package:flutter/material.dart';

import '../api/client.dart';
import '../api/resources.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';

class DropRequestsScreen extends StatefulWidget {
  const DropRequestsScreen({super.key});

  @override
  State<DropRequestsScreen> createState() => _DropRequestsScreenState();
}

class _DropRequestsScreenState extends State<DropRequestsScreen> {
  late Future<ApiResult> _future;

  @override
  void initState() {
    super.initState();
    _future = Api.myDropRequests();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Drop requests')),
      body: FutureBuilder<ApiResult>(
        future: _future,
        builder: (context, snap) {
          if (!snap.hasData) return const Loading();
          final result = snap.data!;
          if (!result.ok) {
            return ErrorView(
              message: result.message,
              onRetry: () => setState(() => _future = Api.myDropRequests()),
            );
          }

          final rows = asList(result.data);
          if (rows.isEmpty) {
            return const EmptyView(
              icon: Icons.logout_outlined,
              title: 'No requests',
              hint: 'To leave a course, open it and choose "Request to drop".',
            );
          }

          return ListView.separated(
            padding: const EdgeInsets.all(T.s4),
            itemCount: rows.length,
            separatorBuilder: (_, _) => const SizedBox(height: T.s2),
            itemBuilder: (_, i) {
              final r = rows[i];
              return Card(
                child: Padding(
                  padding: const EdgeInsets.all(T.s4),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(children: [
                        Expanded(
                          child: Text('${r['course_title']}',
                              style: const TextStyle(
                                  fontWeight: FontWeight.w600, fontSize: 15)),
                        ),
                        statusPill(r['status'] as String?),
                      ]),
                      const SizedBox(height: T.s2),
                      Text('Raised ${formatDate(r['created_at'])}',
                          style:
                              const TextStyle(color: T.n500, fontSize: 12.5)),
                      if ('${r['reason'] ?? ''}'.isNotEmpty) ...[
                        const SizedBox(height: T.s3),
                        const Eyebrow('Your reason'),
                        const SizedBox(height: 4),
                        Text('${r['reason']}',
                            style: const TextStyle(
                                color: T.n600, height: 1.4, fontSize: 13.5)),
                      ],
                      if ('${r['decision_note'] ?? ''}'.isNotEmpty) ...[
                        const SizedBox(height: T.s3),
                        const Eyebrow('Decision'),
                        const SizedBox(height: 4),
                        Text('${r['decision_note']}',
                            style: const TextStyle(
                                color: T.n600, height: 1.4, fontSize: 13.5)),
                      ],
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}
