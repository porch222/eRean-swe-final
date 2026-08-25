import 'package:flutter/material.dart';

import '../api/client.dart';
import '../api/resources.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';
import 'course_detail.dart';

class CoursesScreen extends StatefulWidget {
  const CoursesScreen({super.key});

  @override
  State<CoursesScreen> createState() => _CoursesScreenState();
}

class _CoursesScreenState extends State<CoursesScreen> {
  bool _browsing = false;
  bool _loading = true;
  String? _error;

  List<Map<String, dynamic>> _enrolments = [];
  List<Map<String, dynamic>> _catalogue = [];
  final _search = TextEditingController();

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _search.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    final mine = await Api.myEnrollments();
    final all = await Api.courses(search: _search.text.trim());

    if (!mounted) return;
    if (!mine.ok) {
      setState(() {
        _loading = false;
        _error = mine.message;
      });
      return;
    }

    setState(() {
      _loading = false;
      _enrolments = asList(mine.data);
      _catalogue = all.ok ? asList(all.data) : [];
    });
  }

  Future<void> _enrol(Map<String, dynamic> course) async {
    final result = await Api.enrol(course['id'] as int);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(result.ok
          ? 'Enrolled in ${course['title']}.'
          : result.message),
    ));
    if (result.ok) _load();
  }

  @override
  Widget build(BuildContext context) {

    final enrolledIds =
        _enrolments.map((e) => e['course']).whereType<int>().toSet();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Courses'),
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(56),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(T.s4, 0, T.s4, T.s3),
            child: SegmentedButton<bool>(
              segments: const [
                ButtonSegment(value: false, label: Text('My courses')),
                ButtonSegment(value: true, label: Text('Browse')),
              ],
              selected: {_browsing},
              onSelectionChanged: (s) =>
                  setState(() => _browsing = s.first),
            ),
          ),
        ),
      ),
      body: _loading
          ? const Loading()
          : _error != null
              ? ErrorView(message: _error!, onRetry: _load)
              : RefreshIndicator(
                  onRefresh: _load,
                  child: _browsing
                      ? _browseList(enrolledIds)
                      : _myList(),
                ),
    );
  }

  Widget _myList() {
    if (_enrolments.isEmpty) {
      return ListView(children: const [
        SizedBox(height: 80),
        EmptyView(
          icon: Icons.menu_book_outlined,
          title: 'No courses yet',
          hint: 'Switch to Browse to find one and enrol.',
        ),
      ]);
    }
    return ListView.builder(
      padding: const EdgeInsets.all(T.s4),
      itemCount: _enrolments.length,
      itemBuilder: (_, i) {
        final e = _enrolments[i];
        final progress = double.tryParse('${e['progress'] ?? 0}') ?? 0;
        return Padding(
          padding: const EdgeInsets.only(bottom: T.s3),
          child: Card(
            child: InkWell(
              borderRadius: BorderRadius.circular(T.radiusLg),
              onTap: () => Navigator.of(context).push(MaterialPageRoute(
                builder: (_) =>
                    CourseDetailScreen(courseId: e['course'] as int),
              )),
              child: Padding(
                padding: const EdgeInsets.all(T.s4),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(children: [
                      Expanded(
                        child: Text('${e['course_title']}',
                            style: const TextStyle(
                                fontWeight: FontWeight.w600, fontSize: 15.5)),
                      ),
                      statusPill(e['status'] as String?),
                    ]),
                    const SizedBox(height: T.s1),
                    Text(
                      '${plural(e['course_credits'] as int? ?? 0, 'credit')}'
                      ' · enrolled ${formatDate(e['enrolled_at'])}',
                      style: const TextStyle(color: T.n500, fontSize: 13),
                    ),
                    const SizedBox(height: T.s3),
                    if (e['letter_grade'] != null &&
                        '${e['letter_grade']}'.isNotEmpty)
                      Row(children: [
                        const Text('Final grade  ',
                            style: TextStyle(color: T.n500, fontSize: 13)),
                        Text('${e['letter_grade']}',
                            style: kNumeric.copyWith(
                              fontSize: 17,
                              fontWeight: FontWeight.w600,
                              color: e['is_passed'] == false
                                  ? T.bad600
                                  : T.ok600,
                            )),
                      ])
                    else
                      Meter(percent: progress),
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }

  Widget _browseList(Set<int> enrolledIds) {
    return Column(children: [
      Padding(
        padding: const EdgeInsets.fromLTRB(T.s4, T.s3, T.s4, 0),
        child: TextField(
          controller: _search,
          textInputAction: TextInputAction.search,
          onSubmitted: (_) => _load(),
          decoration: InputDecoration(
            hintText: 'Search courses',
            prefixIcon: const Icon(Icons.search, color: T.n400),
            suffixIcon: _search.text.isEmpty
                ? null
                : IconButton(
                    icon: const Icon(Icons.close, color: T.n400),
                    onPressed: () {
                      _search.clear();
                      _load();
                    },
                  ),
          ),
        ),
      ),
      Expanded(
        child: _catalogue.isEmpty
            ? const EmptyView(
                icon: Icons.search_off,
                title: 'Nothing found',
                hint: 'No published courses match that search.',
              )
            : ListView.builder(
                padding: const EdgeInsets.all(T.s4),
                itemCount: _catalogue.length,
                itemBuilder: (_, i) {
                  final c = _catalogue[i];
                  final joined = enrolledIds.contains(c['id']);
                  final major =
                      (c['major_detail'] as Map<String, dynamic>?)?['name'];
                  return Padding(
                    padding: const EdgeInsets.only(bottom: T.s3),
                    child: Card(
                      child: Padding(
                        padding: const EdgeInsets.all(T.s4),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('${c['title']}',
                                style: const TextStyle(
                                    fontWeight: FontWeight.w600,
                                    fontSize: 15.5)),
                            const SizedBox(height: T.s1),
                            Text(
                              '${major ?? 'Unassigned'} · '
                              '${plural(c['credits'] as int? ?? 0, 'credit')}',
                              style: const TextStyle(
                                  color: T.n500, fontSize: 13),
                            ),
                            const SizedBox(height: T.s2),
                            Text(
                              '${c['description'] ?? ''}',
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(
                                  color: T.n600, fontSize: 13.5, height: 1.4),
                            ),
                            const SizedBox(height: T.s3),
                            Row(children: [
                              Expanded(
                                child: OutlinedButton(
                                  onPressed: () =>
                                      Navigator.of(context).push(
                                    MaterialPageRoute(
                                      builder: (_) => CourseDetailScreen(
                                          courseId: c['id'] as int),
                                    ),
                                  ),
                                  child: const Text('Details'),
                                ),
                              ),
                              const SizedBox(width: T.s3),
                              Expanded(
                                child: joined
                                    ? const Center(
                                        child: Pill('Enrolled',
                                            tone: PillTone.success))
                                    : FilledButton(
                                        onPressed: () => _enrol(c),
                                        child: const Text('Enrol'),
                                      ),
                              ),
                            ]),
                          ],
                        ),
                      ),
                    ),
                  );
                },
              ),
      ),
    ]);
  }
}
