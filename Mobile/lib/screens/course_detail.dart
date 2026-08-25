import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../api/client.dart';
import '../api/resources.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';
import 'assignment_detail.dart';
import 'discussion.dart';

class CourseDetailScreen extends StatefulWidget {
  const CourseDetailScreen({super.key, required this.courseId});
  final int courseId;

  @override
  State<CourseDetailScreen> createState() => _CourseDetailScreenState();
}

class _CourseDetailScreenState extends State<CourseDetailScreen> {
  bool _loading = true;
  String? _error;
  Map<String, dynamic>? _course;
  Map<String, dynamic>? _enrolment;

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

    final course = await Api.course(widget.courseId);
    if (!mounted) return;
    if (!course.ok) {
      setState(() {
        _loading = false;
        _error = course.message;
      });
      return;
    }

    final mine = await Api.myEnrollments();
    if (!mounted) return;

    Map<String, dynamic>? enrolment;
    if (mine.ok) {
      for (final e in asList(mine.data)) {
        if (e['course'] == widget.courseId) enrolment = e;
      }
    }

    setState(() {
      _loading = false;
      _course = course.data as Map<String, dynamic>;
      _enrolment = enrolment;
    });
  }

  Future<void> _enrol() async {
    final result = await Api.enrol(widget.courseId);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(result.ok ? 'Enrolled.' : result.message)),
    );
    if (result.ok) _load();
  }

  Future<void> _requestDrop() async {
    final reason = TextEditingController();
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Request to drop?'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              'You cannot drop a course yourself. This sends a request to your '
              'instructor or an administrator, who will decide.',
              style: TextStyle(fontSize: 13.5, height: 1.4),
            ),
            const SizedBox(height: T.s3),
            TextField(
              controller: reason,
              maxLines: 3,
              decoration: const InputDecoration(labelText: 'Reason (optional)'),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Send request'),
          ),
        ],
      ),
    );

    if (confirmed != true || !mounted) return;
    final result = await Api.requestDrop(
      _enrolment!['id'] as int,
      reason.text.trim(),
    );
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          result.ok
              ? 'Request sent. You will be notified of the decision.'
              : result.message,
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(body: Loading());
    }
    if (_error != null) {
      return Scaffold(
        appBar: AppBar(),
        body: ErrorView(message: _error!, onRetry: _load),
      );
    }

    final course = _course!;
    final active = _enrolment?['status'] == 'active';
    final completed = _enrolment?['status'] == 'completed';

    final canSeeContent = active || completed;
    final tabs = [
      'Overview',
      if (canSeeContent) ...[
        'Materials',
        'Announcements',
        'Coursework',
        'Discussions',
        'Attendance',
      ],
    ];

    return DefaultTabController(
      length: tabs.length,
      child: Scaffold(
        appBar: AppBar(
          title: Text(
            '${course['title']}',
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
          ),
        ),
        body: Column(
          children: [
            _CourseTabGrid(labels: tabs),
            Expanded(
              child: TabBarView(
                children: [
                  _overview(course, active),
                  if (canSeeContent) ...[
                    _MaterialsTab(courseId: widget.courseId),
                    _AnnouncementsTab(courseId: widget.courseId),
                    _CourseworkTab(courseId: widget.courseId),
                    DiscussionsTab(courseId: widget.courseId),
                    _AttendanceTab(courseId: widget.courseId),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _overview(Map<String, dynamic> course, bool active) {
    final major = (course['major_detail'] as Map<String, dynamic>?)?['name'];
    final term = (course['term_detail'] as Map<String, dynamic>?)?['name'];
    final instructor =
        (course['instructor_detail'] as Map<String, dynamic>?)?['full_name'];

    return ListView(
      padding: const EdgeInsets.all(T.s4),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(T.s4),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Eyebrow('About this course'),
                const SizedBox(height: T.s2),
                Text(
                  '${course['description'] ?? ''}',
                  style: const TextStyle(height: 1.5, color: T.n600),
                ),
                const Divider(height: T.s5),
                _fact('Major', major ?? '—'),
                _fact('Term', term ?? '—'),
                _fact('Instructor', instructor ?? '—'),
                _fact('Credits', '${course['credits'] ?? 0}'),
              ],
            ),
          ),
        ),
        const SizedBox(height: T.s4),
        if (_enrolment != null) ...[
          Card(
            child: Padding(
              padding: const EdgeInsets.all(T.s4),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Eyebrow('Your enrolment'),
                      const Spacer(),
                      statusPill(_enrolment!['status'] as String?),
                    ],
                  ),
                  const SizedBox(height: T.s3),
                  Meter(
                    percent:
                        double.tryParse('${_enrolment!['progress'] ?? 0}') ?? 0,
                  ),
                  if (_enrolment!['letter_grade'] != null &&
                      '${_enrolment!['letter_grade']}'.isNotEmpty) ...[
                    const SizedBox(height: T.s3),
                    Row(
                      children: [
                        const Text(
                          'Final grade  ',
                          style: TextStyle(color: T.n500),
                        ),
                        Text(
                          '${_enrolment!['letter_grade']}',
                          style: kNumeric.copyWith(
                            fontSize: 20,
                            fontWeight: FontWeight.w600,
                            color: _enrolment!['is_passed'] == false
                                ? T.bad600
                                : T.ok600,
                          ),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
          ),
          const SizedBox(height: T.s4),
          if (active)
            OutlinedButton.icon(
              onPressed: _requestDrop,
              icon: const Icon(Icons.logout, size: 18),
              style: OutlinedButton.styleFrom(foregroundColor: T.bad600),
              label: const Text('Request to drop'),
            ),
        ] else
          FilledButton(onPressed: _enrol, child: const Text('Enrol')),
      ],
    );
  }

  Widget _fact(String label, String value) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 5),
    child: Row(
      children: [
        SizedBox(
          width: 96,
          child: Text(
            label,
            style: const TextStyle(color: T.n500, fontSize: 13.5),
          ),
        ),
        Expanded(
          child: Text(
            value,
            style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 13.5),
          ),
        ),
      ],
    ),
  );
}

class _CourseTabGrid extends StatelessWidget {
  const _CourseTabGrid({required this.labels});

  final List<String> labels;

  @override
  Widget build(BuildContext context) {
    final controller = DefaultTabController.of(context);
    final width = MediaQuery.sizeOf(context).width;
    final columns = labels.length == 1
        ? 1
        : width < 320
        ? 1
        : width <= 768
        ? 2
        : labels.length;

    return Material(
      color: T.n0,
      child: Padding(
        padding: const EdgeInsets.fromLTRB(T.s4, T.s3, T.s4, T.s3),
        child: AnimatedBuilder(
          animation: controller.animation!,
          builder: (context, _) => GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: labels.length,
            gridDelegate: SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: columns,
              crossAxisSpacing: T.s1,
              mainAxisSpacing: T.s1,
              mainAxisExtent: 44,
            ),
            itemBuilder: (context, index) {
              final selected = controller.index == index;
              return Semantics(
                button: true,
                selected: selected,
                child: InkWell(
                  onTap: () => controller.animateTo(index),
                  borderRadius: BorderRadius.circular(T.radius),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 140),
                    alignment: Alignment.center,
                    padding: const EdgeInsets.symmetric(horizontal: T.s2),
                    decoration: BoxDecoration(
                      color: selected ? T.brand50 : T.n0,
                      border: Border.all(color: selected ? T.brand500 : T.n200),
                      borderRadius: BorderRadius.circular(T.radius),
                    ),
                    child: Text(
                      labels[index],
                      textAlign: TextAlign.center,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        color: selected ? T.brand700 : T.n500,
                        fontSize: 13,
                        fontWeight: selected
                            ? FontWeight.w600
                            : FontWeight.w500,
                      ),
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );
  }
}

class _MaterialsTab extends StatefulWidget {
  const _MaterialsTab({required this.courseId});
  final int courseId;

  @override
  State<_MaterialsTab> createState() => _MaterialsTabState();
}

class _MaterialsTabState extends State<_MaterialsTab> {
  late Future<ApiResult> _future;

  @override
  void initState() {
    super.initState();
    _future = Api.materials(widget.courseId);
  }

  Future<void> _open(Map<String, dynamic> m) async {
    if (m['type'] == 'link') {
      final result = await ApiClient.instance.download(
        '/api/courses/${widget.courseId}/materials/${m['id']}/download/',
      );
      if (!mounted) return;
      final url = result.ok && result.data is Map
          ? (result.data as Map)['link_url'] as String?
          : null;
      if (url != null) {
        await launchUrl(Uri.parse(url), mode: LaunchMode.externalApplication);
        return;
      }
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(result.message)));
      return;
    }

    ScaffoldMessenger.of(
      context,
    ).showSnackBar(const SnackBar(content: Text('Downloading…')));
    final result = await ApiClient.instance.download(
      '/api/courses/${widget.courseId}/materials/${m['id']}/download/',
    );
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(result.ok ? 'Downloaded ${m['title']}.' : result.message),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<ApiResult>(
      future: _future,
      builder: (context, snap) {
        if (!snap.hasData) return const Loading();
        final result = snap.data!;
        if (!result.ok) {
          return ErrorView(
            message: result.message,
            onRetry: () =>
                setState(() => _future = Api.materials(widget.courseId)),
          );
        }
        final rows = asList(result.data);
        if (rows.isEmpty) {
          return const EmptyView(
            icon: Icons.folder_open,
            title: 'No materials yet',
            hint:
                'Readings and links appear here once your instructor '
                'shares them.',
          );
        }
        return ListView.separated(
          padding: const EdgeInsets.all(T.s4),
          itemCount: rows.length,
          separatorBuilder: (_, _) => const SizedBox(height: T.s2),
          itemBuilder: (_, i) {
            final m = rows[i];
            final isLink = m['type'] == 'link';
            return Card(
              child: NavRow(
                icon: isLink ? Icons.link : Icons.description_outlined,
                title: '${m['title']}',
                subtitle:
                    '${isLink ? 'Link' : 'File'} · '
                    'added ${formatDate(m['uploaded_at'])}',
                trailing: Icon(
                  isLink ? Icons.open_in_new : Icons.download,
                  color: T.n400,
                  size: 20,
                ),
                onTap: () => _open(m),
              ),
            );
          },
        );
      },
    );
  }
}

class _AnnouncementsTab extends StatefulWidget {
  const _AnnouncementsTab({required this.courseId});
  final int courseId;

  @override
  State<_AnnouncementsTab> createState() => _AnnouncementsTabState();
}

class _AnnouncementsTabState extends State<_AnnouncementsTab> {
  late Future<ApiResult> _future;

  @override
  void initState() {
    super.initState();
    _future = Api.announcements(widget.courseId);
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<ApiResult>(
      future: _future,
      builder: (context, snap) {
        if (!snap.hasData) return const Loading();
        final result = snap.data!;
        if (!result.ok) {
          return ErrorView(
            message: result.message,
            onRetry: () =>
                setState(() => _future = Api.announcements(widget.courseId)),
          );
        }
        final rows = asList(result.data);
        if (rows.isEmpty) {
          return const EmptyView(
            icon: Icons.campaign_outlined,
            title: 'No announcements',
          );
        }
        return ListView.separated(
          padding: const EdgeInsets.all(T.s4),
          itemCount: rows.length,
          separatorBuilder: (_, _) => const SizedBox(height: T.s3),
          itemBuilder: (_, i) {
            final a = rows[i];
            final unread = a['is_read'] == false;
            final author =
                (a['author_detail'] as Map<String, dynamic>?)?['full_name'];
            return Card(
              color: unread ? T.brand50 : null,
              child: Padding(
                padding: const EdgeInsets.all(T.s4),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Expanded(
                          child: Text(
                            '${a['title']}',
                            style: const TextStyle(
                              fontWeight: FontWeight.w600,
                              fontSize: 15,
                            ),
                          ),
                        ),
                        if (unread) const Pill('New', tone: PillTone.info),
                      ],
                    ),
                    const SizedBox(height: 3),
                    Text(
                      '${author ?? ''} · ${formatDateTime(a['created_at'])}'
                      '${a['is_edited'] == true ? ' · edited' : ''}',
                      style: const TextStyle(color: T.n500, fontSize: 12.5),
                    ),
                    const SizedBox(height: T.s3),
                    Text(
                      '${a['content']}',
                      style: const TextStyle(height: 1.5, color: T.n600),
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }
}

class _CourseworkTab extends StatefulWidget {
  const _CourseworkTab({required this.courseId});
  final int courseId;

  @override
  State<_CourseworkTab> createState() => _CourseworkTabState();
}

class _CourseworkTabState extends State<_CourseworkTab> {
  late Future<ApiResult> _future;

  @override
  void initState() {
    super.initState();
    _future = Api.assignments(widget.courseId);
  }

  void _reload() => setState(() => _future = Api.assignments(widget.courseId));

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<ApiResult>(
      future: _future,
      builder: (context, snap) {
        if (!snap.hasData) return const Loading();
        final result = snap.data!;
        if (!result.ok) {
          return ErrorView(message: result.message, onRetry: _reload);
        }
        final rows = asList(result.data);
        if (rows.isEmpty) {
          return const EmptyView(
            icon: Icons.assignment_outlined,
            title: 'No coursework set',
          );
        }
        return ListView.separated(
          padding: const EdgeInsets.all(T.s4),
          itemCount: rows.length,
          separatorBuilder: (_, _) => const SizedBox(height: T.s2),
          itemBuilder: (_, i) {
            final a = rows[i];
            final isQuiz = a['type'] == 'quiz';
            final overdue =
                DateTime.tryParse(
                  '${a['due_date']}',
                )?.isBefore(DateTime.now()) ??
                false;
            return Card(
              child: NavRow(
                icon: isQuiz ? Icons.quiz_outlined : Icons.assignment_outlined,
                title: '${a['title']}',
                subtitle:
                    '${isQuiz ? 'Quiz' : 'Assignment'} · '
                    '${a['max_score']} points',
                trailing: Pill(
                  relativeDue(a['due_date']),
                  tone: overdue ? PillTone.danger : PillTone.muted,
                ),
                onTap: () async {
                  await Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => AssignmentDetailScreen(
                        courseId: widget.courseId,
                        assignmentId: a['id'] as int,
                      ),
                    ),
                  );
                  _reload();
                },
              ),
            );
          },
        );
      },
    );
  }
}

class _AttendanceTab extends StatefulWidget {
  const _AttendanceTab({required this.courseId});
  final int courseId;

  @override
  State<_AttendanceTab> createState() => _AttendanceTabState();
}

class _AttendanceTabState extends State<_AttendanceTab> {
  late Future<ApiResult> _future;

  @override
  void initState() {
    super.initState();
    _future = Api.myAttendance(widget.courseId);
  }

  @override
  Widget build(BuildContext context) {
    return FutureBuilder<ApiResult>(
      future: _future,
      builder: (context, snap) {
        if (!snap.hasData) return const Loading();
        final result = snap.data!;
        if (!result.ok) {
          return ErrorView(
            message: result.message,
            onRetry: () =>
                setState(() => _future = Api.myAttendance(widget.courseId)),
          );
        }

        final data = result.data;
        final rows = asList(data is Map ? data['records'] ?? data : data);
        if (rows.isEmpty) {
          return const EmptyView(
            icon: Icons.event_available_outlined,
            title: 'No attendance recorded',
            hint: 'Sessions appear here once your instructor marks a register.',
          );
        }

        final attended = rows.where((r) => r['status'] != 'absent').length;
        final rate = rows.isEmpty ? 0.0 : attended / rows.length * 100;

        return ListView(
          padding: const EdgeInsets.all(T.s4),
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(T.s4),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Eyebrow('Attendance rate'),
                    const SizedBox(height: T.s3),
                    Meter(percent: rate, height: 9),
                    const SizedBox(height: T.s2),
                    Text(
                      '$attended of ${rows.length} sessions attended',
                      style: const TextStyle(color: T.n500, fontSize: 13),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: T.s4),
            ...rows.map((r) {
              final status = '${r['status']}';
              return Card(
                margin: const EdgeInsets.only(bottom: T.s2),
                child: ListTile(
                  title: Text(
                    '${r['session_title'] ?? formatDate(r['session_date'] ?? r['date'])}',
                  ),
                  subtitle: Text(
                    formatDate(r['session_date'] ?? r['date']),
                    style: const TextStyle(color: T.n500),
                  ),
                  trailing: Pill(
                    status[0].toUpperCase() + status.substring(1),
                    tone: switch (status) {
                      'present' => PillTone.success,
                      'late' => PillTone.warning,
                      'excused' => PillTone.info,
                      _ => PillTone.danger,
                    },
                  ),
                ),
              );
            }),
          ],
        );
      },
    );
  }
}
