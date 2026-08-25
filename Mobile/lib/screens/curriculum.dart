import 'package:flutter/material.dart';

import '../api/client.dart';
import '../api/resources.dart';
import '../main.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';

class CurriculumScreen extends StatefulWidget {
  const CurriculumScreen({super.key});

  @override
  State<CurriculumScreen> createState() => _CurriculumScreenState();
}

class _CurriculumScreenState extends State<CurriculumScreen> {
  bool _loading = true;
  String? _error;
  Map<String, dynamic>? _progress;
  bool _noMajor = false;
  bool _noCurriculum = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final majorId = SessionScope.of(context).majorId;
    if (majorId == null) {
      setState(() {
        _loading = false;
        _noMajor = true;
      });
      return;
    }

    setState(() {
      _loading = true;
      _error = null;
    });

    final list = await Api.curricula(majorId);
    if (!mounted) return;
    if (!list.ok) {
      setState(() {
        _loading = false;
        _error = list.message;
      });
      return;
    }

    final rows = asList(list.data);
    if (rows.isEmpty) {
      setState(() {
        _loading = false;
        _noCurriculum = true;
      });
      return;
    }

    final progress = await Api.curriculumProgress(rows.first['id'] as int);
    if (!mounted) return;
    setState(() {
      _loading = false;
      if (progress.ok) {
        _progress = progress.data as Map<String, dynamic>;
      } else {
        _error = progress.message;
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('My curriculum')),
      body: _body(),
    );
  }

  Widget _body() {
    if (_loading) return const Loading();
    if (_noMajor) {
      return const EmptyView(
        icon: Icons.account_tree_outlined,
        title: 'No programme assigned',
        hint: 'Your account is not attached to a major yet. The registrar '
            'assigns this — ask an administrator.',
      );
    }
    if (_noCurriculum) {
      return const EmptyView(
        icon: Icons.account_tree_outlined,
        title: 'No active curriculum',
        hint: 'Your major has no published course plan yet.',
      );
    }
    if (_error != null) return ErrorView(message: _error!, onRetry: _load);

    final p = _progress!;
    final target = p['credits_to_graduate'] as int? ?? 0;
    final earnedTotal = p['credits_earned_total'] as int? ?? 0;
    final requiredTotal = p['credits_required'] as int? ?? 0;
    final earnedRequired = p['credits_earned_required'] as int? ?? 0;
    final percent = (p['percent_complete'] as num?)?.toDouble() ?? 0;

    final remaining = (target - earnedTotal).clamp(0, target);
    final requiredLeft = (requiredTotal - earnedRequired).clamp(0, requiredTotal);
    final complete = p['is_complete'] == true;

    final byYear = <int, Map<int, List<Map<String, dynamic>>>>{};
    for (final e in asList(p['entries'])) {
      final year = e['year_level'] as int? ?? 1;
      final term = e['term'] as int? ?? 1;
      byYear.putIfAbsent(year, () => {}).putIfAbsent(term, () => []).add(e);
    }
    final years = byYear.keys.toList()..sort();

    return ListView(
      padding: const EdgeInsets.all(T.s4),
      children: [
        Text('${p['major']} · ${p['curriculum_name']}',
            style: const TextStyle(color: T.n500, fontSize: 13)),
        const SizedBox(height: T.s3),
        Card(
          child: Padding(
            padding: const EdgeInsets.all(T.s4),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Eyebrow('Progress towards the degree'),
                const SizedBox(height: T.s2),
                Text(
                  complete
                      ? 'Every requirement met.'
                      : remaining > 0
                          ? '${plural(remaining, 'credit')} to go.'
                          : '${plural(requiredLeft, 'required credit')} still outstanding.',
                  style: const TextStyle(
                      fontSize: 19, fontWeight: FontWeight.w600, color: T.n900),
                ),
                if (!complete && remaining > 0 && requiredLeft > 0) ...[
                  const SizedBox(height: 4),
                  Text(
                    '${plural(requiredLeft, 'credit')} of that must come from '
                    'required courses.',
                    style: const TextStyle(color: T.n500, fontSize: 12.5),
                  ),
                ],
                const SizedBox(height: T.s4),
                Meter(percent: percent, height: 9),
              ],
            ),
          ),
        ),
        const SizedBox(height: T.s3),
        Row(children: [
          Expanded(
            child: StatTile(
              value: '$earnedTotal/$target',
              label: 'To graduate',
              icon: Icons.school_outlined,
            ),
          ),
          const SizedBox(width: T.s2),
          Expanded(
            child: StatTile(
              value: '$earnedRequired/$requiredTotal',
              label: 'Required',
              icon: Icons.workspace_premium_outlined,
            ),
          ),
          const SizedBox(width: T.s2),
          Expanded(
            child: StatTile(
              value:
                  '${p['credits_earned_elective'] ?? 0}/${p['credits_elective_available'] ?? 0}',
              label: 'Elective',
              icon: Icons.auto_awesome_outlined,
            ),
          ),
        ]),
        const SizedBox(height: T.s5),
        ...years.map((year) {
          final terms = byYear[year]!.keys.toList()..sort();
          return Padding(
            padding: const EdgeInsets.only(bottom: T.s4),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(T.s4),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Year $year',
                        style: const TextStyle(
                            fontSize: 16, fontWeight: FontWeight.w600)),
                    ...terms.map((term) {
                      final rows = byYear[year]![term]!;
                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const SizedBox(height: T.s3),
                          Eyebrow('Term $term'),
                          const SizedBox(height: T.s1),
                          ...rows.map((e) {
                            final passed = e['passed'] == true;
                            return Padding(
                              padding:
                                  const EdgeInsets.symmetric(vertical: 6),
                              child: Row(children: [
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text('${e['course_title']}',
                                          style: TextStyle(
                                            fontSize: 14,
                                            fontWeight: FontWeight.w500,
                                            color:
                                                passed ? T.n500 : T.n900,
                                          )),
                                      const SizedBox(height: 2),
                                      Text(
                                        '${e['is_required'] == true ? 'Required' : 'Elective'}'
                                        ' · ${plural(e['credits'] as int? ?? 0, 'credit')}',
                                        style: const TextStyle(
                                            color: T.n500, fontSize: 12),
                                      ),
                                    ],
                                  ),
                                ),
                                const SizedBox(width: T.s2),
                                Pill(
                                  switch (e['status']) {
                                    'completed' => 'Completed',
                                    'active' => 'In progress',
                                    'dropped' => 'Dropped',
                                    _ => 'Not taken',
                                  },
                                  tone: passed
                                      ? PillTone.success
                                      : switch (e['status']) {
                                          'active' => PillTone.info,
                                          'dropped' => PillTone.danger,
                                          _ => PillTone.muted,
                                        },
                                ),
                              ]),
                            );
                          }),
                        ],
                      );
                    }),
                  ],
                ),
              ),
            ),
          );
        }),
      ],
    );
  }
}
