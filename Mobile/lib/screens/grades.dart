import 'package:flutter/material.dart';

import '../api/client.dart';
import '../api/resources.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';

class GradesScreen extends StatefulWidget {
  const GradesScreen({super.key});

  @override
  State<GradesScreen> createState() => _GradesScreenState();
}

class _GradesScreenState extends State<GradesScreen> {
  bool _loading = true;
  String? _error;
  List<Map<String, dynamic>> _rows = [];
  int? _courseFilter;

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
    final result = await Api.mySubmissions();
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

  @override
  Widget build(BuildContext context) {

    final courseIds = _rows.map((r) => r['course']).whereType<int>().toSet();
    final active =
        _courseFilter != null && courseIds.contains(_courseFilter)
            ? _courseFilter
            : null;

    final shown =
        active == null ? _rows : _rows.where((r) => r['course'] == active).toList();
    final graded = shown.where((r) => r['grade'] != null).toList();

    double? average;
    if (graded.isNotEmpty) {
      var total = 0.0;
      for (final r in graded) {
        final score = double.tryParse('${r['grade']}') ?? 0;
        final max = double.tryParse('${r['max_score']}') ?? 0;
        if (max > 0) total += score / max * 100;
      }
      average = total / graded.length;
    }

    return Scaffold(
      appBar: AppBar(title: const Text('My grades')),
      body: _loading
          ? const Loading()
          : _error != null
              ? ErrorView(message: _error!, onRetry: _load)
              : _rows.isEmpty
                  ? const EmptyView(
                      icon: Icons.bar_chart,
                      title: 'Nothing handed in yet',
                      hint: 'Your results appear here once you submit work.',
                    )
                  : RefreshIndicator(
                      onRefresh: _load,
                      child: ListView(
                        padding: const EdgeInsets.all(T.s4),
                        children: [
                          _filters(courseIds, active),
                          const SizedBox(height: T.s4),
                          Row(children: [
                            Expanded(
                              child: StatTile(
                                value: '${shown.length}',
                                label: 'Submitted',
                                icon: Icons.upload_outlined,
                              ),
                            ),
                            const SizedBox(width: T.s2),
                            Expanded(
                              child: StatTile(
                                value: '${graded.length}',
                                label: 'Graded',
                                icon: Icons.check_circle_outline,
                              ),
                            ),
                            const SizedBox(width: T.s2),
                            Expanded(
                              child: StatTile(
                                value: average == null
                                    ? '—'
                                    : '${average.toStringAsFixed(0)}%',
                                label: 'Average',
                                icon: Icons.show_chart,
                              ),
                            ),
                          ]),
                          const SizedBox(height: T.s5),
                          ...shown.map(_row),
                        ],
                      ),
                    ),
    );
  }

  Widget _filters(Set<int> courseIds, int? active) {

    final titles = <int, String>{};
    for (final r in _rows) {
      final id = r['course'];
      if (id is int) titles[id] = '${r['course_title']}';
    }

    return SizedBox(
      height: 38,
      child: ListView(
        scrollDirection: Axis.horizontal,
        children: [
          Padding(
            padding: const EdgeInsets.only(right: T.s2),
            child: ChoiceChip(
              label: const Text('All'),
              selected: active == null,
              onSelected: (_) => setState(() => _courseFilter = null),
            ),
          ),
          ...titles.entries.map((e) => Padding(
                padding: const EdgeInsets.only(right: T.s2),
                child: ChoiceChip(
                  label: Text(e.value),
                  selected: active == e.key,
                  onSelected: (_) => setState(() => _courseFilter = e.key),
                ),
              )),
        ],
      ),
    );
  }

  Widget _row(Map<String, dynamic> r) {
    return Padding(
      padding: const EdgeInsets.only(bottom: T.s2),
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(T.s4),
          child: Row(children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('${r['assignment_title']}',
                      style: const TextStyle(
                          fontWeight: FontWeight.w600, fontSize: 14.5)),
                  const SizedBox(height: 3),
                  Text('${r['course_title']}',
                      style: const TextStyle(color: T.n500, fontSize: 12.5)),
                  const SizedBox(height: T.s1),
                  Row(children: [
                    Text('Attempt ${r['attempt']}',
                        style:
                            const TextStyle(color: T.n400, fontSize: 11.5)),
                    if (r['is_late'] == true) ...[
                      const SizedBox(width: T.s2),
                      const Pill('Late', tone: PillTone.danger),
                    ],
                  ]),
                ],
              ),
            ),
            const SizedBox(width: T.s3),
            Grade(value: r['grade'], outOf: r['max_score']),
          ]),
        ),
      ),
    );
  }
}
