import 'package:flutter/material.dart';

import '../api/client.dart';
import '../api/resources.dart';
import '../main.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';
import 'assignment_detail.dart';
import 'course_detail.dart';
import 'notifications.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _loading = true;
  String? _error;

  List<Map<String, dynamic>> _enrolments = [];
  List<Map<String, dynamic>> _due = [];
  List<Map<String, dynamic>> _submissions = [];
  int _unread = 0;

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

    final enrolments = await Api.myEnrollments();
    if (!enrolments.ok) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _error = enrolments.message;
      });
      return;
    }

    final rows = asList(enrolments.data)
        .where((e) => e['status'] == 'active')
        .toList();

    final due = <Map<String, dynamic>>[];
    for (final e in rows) {
      final courseId = e['course'] as int;
      final result = await Api.assignments(courseId);
      if (!result.ok) continue;
      for (final a in asList(result.data)) {
        if (a['due_date'] == null) continue;
        due.add({...a, 'course': courseId, 'course_title': e['course_title']});
      }
    }
    due.sort((a, b) => '${a['due_date']}'.compareTo('${b['due_date']}'));

    final submissions = await Api.mySubmissions();
    final unread = await Api.unreadCount();

    if (!mounted) return;
    setState(() {
      _loading = false;
      _enrolments = rows;
      _due = due.take(5).toList();
      _submissions = submissions.ok ? asList(submissions.data) : [];
      _unread = unread.ok ? (unread.data['count'] as int? ?? 0) : 0;
    });
  }

  @override
  Widget build(BuildContext context) {
    final session = SessionScope.of(context);
    final firstName = session.displayName.split(' ').first;
    final graded =
        _submissions.where((s) => s['grade'] != null).toList();

    return Scaffold(
      appBar: AppBar(
        title: Text(firstName.isEmpty ? 'Home' : 'Hello, $firstName'),
        actions: [_bell(context)],
      ),
      body: _loading
          ? const Loading(label: 'Loading your day…')
          : _error != null
              ? ErrorView(message: _error!, onRetry: _load)
              : RefreshIndicator(
                  onRefresh: _load,
                  child: ListView(
                    padding: const EdgeInsets.all(T.s4),
                    children: [
                      _dueCard(),
                      const SizedBox(height: T.s4),
                      Row(children: [
                        Expanded(
                          child: StatTile(
                            value: '${_enrolments.length}',
                            label: 'Active courses',
                            icon: Icons.menu_book,
                          ),
                        ),
                        const SizedBox(width: T.s3),
                        Expanded(
                          child: StatTile(
                            value: '${graded.length}',
                            label: 'Graded',
                            icon: Icons.check_circle_outline,
                          ),
                        ),
                      ]),
                      const SizedBox(height: T.s5),
                      const Eyebrow('Your courses'),
                      const SizedBox(height: T.s2),
                      if (_enrolments.isEmpty)
                        const EmptyView(
                          icon: Icons.explore_outlined,
                          title: 'Not enrolled yet',
                          hint: 'Open Courses to browse what is on offer.',
                        )
                      else
                        ..._enrolments.map(_courseRow),
                    ],
                  ),
                ),
    );
  }

  Widget _bell(BuildContext context) {
    return Stack(alignment: Alignment.center, children: [
      IconButton(

        iconSize: 24,
        tooltip: 'Notifications',
        icon: const Icon(Icons.notifications_none),
        onPressed: () async {
          await Navigator.of(context).push(MaterialPageRoute(
              builder: (_) => const NotificationsScreen()));
          _load();
        },
      ),
      if (_unread > 0)
        Positioned(
          top: 8,
          right: 8,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
            decoration: BoxDecoration(
              color: T.brand600,
              borderRadius: BorderRadius.circular(999),
            ),
            child: Text(
              _unread > 9 ? '9+' : '$_unread',
              style: const TextStyle(
                  color: Colors.white,
                  fontSize: 10,
                  fontWeight: FontWeight.w700),
            ),
          ),
        ),
    ]);
  }

  Widget _dueCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(T.s4),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Eyebrow('Due next'),
            const SizedBox(height: T.s3),
            if (_due.isEmpty)
              const Text('Nothing due. Enjoy it while it lasts.',
                  style: TextStyle(color: T.n500))
            else
              ..._due.map((a) {
                final overdue =
                    DateTime.tryParse('${a['due_date']}')?.isBefore(
                          DateTime.now(),
                        ) ??
                        false;
                return InkWell(
                  onTap: () => Navigator.of(context).push(MaterialPageRoute(
                    builder: (_) => AssignmentDetailScreen(
                      courseId: a['course'] as int,
                      assignmentId: a['id'] as int,
                    ),
                  )),
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: T.s2),
                    child: Row(children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('${a['title']}',
                                style: const TextStyle(
                                    fontWeight: FontWeight.w600, fontSize: 15)),
                            const SizedBox(height: 2),
                            Text('${a['course_title']}',
                                style: const TextStyle(
                                    color: T.n500, fontSize: 13)),
                          ],
                        ),
                      ),
                      const SizedBox(width: T.s2),
                      Pill(relativeDue(a['due_date']),
                          tone: overdue ? PillTone.danger : PillTone.warning),
                    ]),
                  ),
                );
              }),
          ],
        ),
      ),
    );
  }

  Widget _courseRow(Map<String, dynamic> e) {
    final progress = double.tryParse('${e['progress'] ?? 0}') ?? 0;
    return Padding(
      padding: const EdgeInsets.only(bottom: T.s3),
      child: Card(
        child: InkWell(
          borderRadius: BorderRadius.circular(T.radiusLg),
          onTap: () => Navigator.of(context).push(MaterialPageRoute(
            builder: (_) => CourseDetailScreen(courseId: e['course'] as int),
          )),
          child: Padding(
            padding: const EdgeInsets.all(T.s4),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('${e['course_title']}',
                    style: const TextStyle(
                        fontWeight: FontWeight.w600, fontSize: 15.5)),
                const SizedBox(height: T.s1),
                Text(plural(e['course_credits'] as int? ?? 0, 'credit'),
                    style: const TextStyle(color: T.n500, fontSize: 13)),
                const SizedBox(height: T.s3),
                Meter(percent: progress),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
