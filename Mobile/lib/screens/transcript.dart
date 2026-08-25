import 'package:flutter/material.dart';

import '../api/client.dart';
import '../api/resources.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';

class TranscriptScreen extends StatefulWidget {
  const TranscriptScreen({super.key});

  @override
  State<TranscriptScreen> createState() => _TranscriptScreenState();
}

class _TranscriptScreenState extends State<TranscriptScreen> {
  late Future<ApiResult> _future;

  @override
  void initState() {
    super.initState();
    _future = Api.transcript();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Transcript')),
      body: FutureBuilder<ApiResult>(
        future: _future,
        builder: (context, snap) {
          if (!snap.hasData) return const Loading();
          final result = snap.data!;
          if (!result.ok) {
            return ErrorView(
              message: result.message,
              onRetry: () => setState(() => _future = Api.transcript()),
            );
          }

          final data = result.data as Map<String, dynamic>;
          final terms = asList(data['terms']);

          if (terms.isEmpty) {
            return const EmptyView(
              icon: Icons.receipt_long_outlined,
              title: 'Nothing on your record yet',
              hint: 'Courses appear here once they are graded.',
            );
          }

          return ListView(
            padding: const EdgeInsets.all(T.s4),
            children: [
              Row(children: [
                Expanded(
                  child: StatTile(
                    value: '${data['credits_earned'] ?? 0}',
                    label: 'Credits earned',
                    icon: Icons.workspace_premium_outlined,
                  ),
                ),
                const SizedBox(width: T.s2),
                Expanded(
                  child: StatTile(
                    value: '${data['credits_attempted'] ?? 0}',
                    label: 'Attempted',
                    icon: Icons.menu_book_outlined,
                  ),
                ),
                const SizedBox(width: T.s2),
                Expanded(
                  child: StatTile(
                    value: '${data['gpa'] ?? '—'}',
                    label: 'GPA',
                    icon: Icons.analytics_outlined,
                  ),
                ),
              ]),
              const SizedBox(height: T.s5),
              ...terms.map((term) {
                final entries = asList(term['entries']);
                return Padding(
                  padding: const EdgeInsets.only(bottom: T.s4),
                  child: Card(
                    child: Padding(
                      padding: const EdgeInsets.all(T.s4),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(children: [
                            Expanded(
                              child: Text('${term['term_name']}',
                                  style: const TextStyle(
                                      fontSize: 16,
                                      fontWeight: FontWeight.w600)),
                            ),
                            Text(
                              '${plural(term['credits_earned'] as int? ?? 0, 'credit')} earned',
                              style: kNumeric.copyWith(
                                  color: T.n500, fontSize: 12.5),
                            ),
                          ]),
                          const Divider(height: T.s5),
                          ...entries.map((e) => Padding(
                                padding:
                                    const EdgeInsets.symmetric(vertical: 7),
                                child: Row(children: [
                                  Expanded(
                                    child: Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.start,
                                      children: [
                                        Text('${e['course_title']}',
                                            style: const TextStyle(
                                                fontWeight: FontWeight.w500,
                                                fontSize: 14)),
                                        const SizedBox(height: 2),
                                        Text(
                                          '${e['credits_earned']}/${e['credits']} credits'
                                          '${e['final_score'] == null ? '' : ' · ${e['final_score']}%'}',
                                          style: kNumeric.copyWith(
                                              color: T.n500, fontSize: 12),
                                        ),
                                      ],
                                    ),
                                  ),
                                  const SizedBox(width: T.s2),
                                  if (e['letter_grade'] != null &&
                                      '${e['letter_grade']}'.isNotEmpty)
                                    Text('${e['letter_grade']}',
                                        style: kNumeric.copyWith(
                                          fontSize: 18,
                                          fontWeight: FontWeight.w600,
                                          color: e['is_passed'] == false
                                              ? T.bad600
                                              : T.ok600,
                                        ))
                                  else
                                    const Text('in progress',
                                        style: TextStyle(
                                            color: T.n400, fontSize: 12)),
                                ]),
                              )),
                        ],
                      ),
                    ),
                  ),
                );
              }),
            ],
          );
        },
      ),
    );
  }
}
