import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';

import '../api/client.dart';
import '../api/resources.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';
import 'quiz.dart';

class AssignmentDetailScreen extends StatefulWidget {
  const AssignmentDetailScreen({
    super.key,
    required this.courseId,
    required this.assignmentId,
  });
  final int courseId;
  final int assignmentId;

  @override
  State<AssignmentDetailScreen> createState() => _AssignmentDetailScreenState();
}

class _AssignmentDetailScreenState extends State<AssignmentDetailScreen> {
  bool _loading = true;
  String? _error;
  Map<String, dynamic>? _assignment;
  List<Map<String, dynamic>> _submissions = [];

  final _text = TextEditingController();
  PlatformFile? _file;
  bool _sending = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _text.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    final assignment = await Api.assignment(widget.courseId, widget.assignmentId);
    if (!mounted) return;
    if (!assignment.ok) {
      setState(() {
        _loading = false;
        _error = assignment.message;
      });
      return;
    }

    final mine =
        await Api.mySubmissionsFor(widget.courseId, widget.assignmentId);
    if (!mounted) return;

    setState(() {
      _loading = false;
      _assignment = assignment.data as Map<String, dynamic>;
      _submissions = mine.ok ? asList(mine.data) : [];
    });
  }

  Future<void> _pickFile() async {
    final picked = await FilePicker.pickFiles();
    if (picked == null || picked.files.isEmpty) return;
    setState(() => _file = picked.files.first);
  }

  Future<void> _submit() async {
    if (_text.text.trim().isEmpty && _file == null) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
        content: Text('Attach a file or type an answer first.'),
      ));
      return;
    }

    setState(() => _sending = true);
    final result = await Api.submitWork(
      widget.courseId,
      widget.assignmentId,
      text: _text.text.trim(),
      filePath: _file?.path,
    );

    if (!mounted) return;
    setState(() => _sending = false);

    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(result.ok ? 'Submitted.' : result.message),
    ));

    if (result.ok) {
      _text.clear();
      setState(() => _file = null);
      _load();
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Scaffold(body: Loading());
    if (_error != null) {
      return Scaffold(
        appBar: AppBar(),
        body: ErrorView(message: _error!, onRetry: _load),
      );
    }

    final a = _assignment!;
    if (a['type'] == 'quiz') {
      return QuizScreen(
        courseId: widget.courseId,
        assignment: a,
      );
    }

    final latest = _submissions.isEmpty ? null : _submissions.first;
    final overdue =
        DateTime.tryParse('${a['due_date']}')?.isBefore(DateTime.now()) ?? false;

    return Scaffold(
      appBar: AppBar(
          title: Text('${a['title']}',
              maxLines: 1, overflow: TextOverflow.ellipsis)),
      body: ListView(
        padding: const EdgeInsets.all(T.s4),
        children: [
          Card(
            child: Padding(
              padding: const EdgeInsets.all(T.s4),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(children: [
                    const Eyebrow('Assignment'),
                    const Spacer(),
                    Pill(relativeDue(a['due_date']),
                        tone: overdue ? PillTone.danger : PillTone.warning),
                  ]),
                  const SizedBox(height: T.s2),
                  Text('${a['description'] ?? ''}',
                      style: const TextStyle(height: 1.5, color: T.n600)),
                  const SizedBox(height: T.s3),
                  Text('Worth ${a['max_score']} points',
                      style: const TextStyle(color: T.n500, fontSize: 13)),
                ],
              ),
            ),
          ),
          const SizedBox(height: T.s4),

          if (latest != null) ...[
            const Eyebrow('Your latest attempt'),
            const SizedBox(height: T.s2),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(T.s4),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(children: [
                      Text('Attempt ${latest['attempt']}',
                          style:
                              const TextStyle(fontWeight: FontWeight.w600)),
                      const SizedBox(width: T.s2),
                      if (latest['is_late'] == true)
                        const Pill('Late', tone: PillTone.danger),
                      const Spacer(),
                      Grade(
                          value: latest['grade'],
                          outOf: latest['max_score']),
                    ]),
                    const SizedBox(height: T.s2),
                    Text('Submitted ${formatDateTime(latest['submitted_at'])}',
                        style:
                            const TextStyle(color: T.n500, fontSize: 12.5)),
                    if (latest['feedback'] != null &&
                        '${latest['feedback']}'.isNotEmpty) ...[
                      const Divider(height: T.s5),
                      const Eyebrow('Feedback'),
                      const SizedBox(height: T.s2),
                      Text('${latest['feedback']}',
                          style:
                              const TextStyle(height: 1.5, color: T.n600)),
                    ],
                  ],
                ),
              ),
            ),
            if (_submissions.length > 1) ...[
              const SizedBox(height: T.s2),
              Text(
                '${_submissions.length} attempts in total. Only the latest '
                'counts towards your grade.',
                style: const TextStyle(color: T.n500, fontSize: 12.5),
              ),
            ],
            const SizedBox(height: T.s5),
          ],

          Eyebrow(latest == null ? 'Hand in' : 'Hand in again'),
          const SizedBox(height: T.s2),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(T.s4),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  TextField(
                    controller: _text,
                    maxLines: 5,
                    decoration: const InputDecoration(
                      labelText: 'Your answer (optional if attaching a file)',
                      alignLabelWithHint: true,
                    ),
                  ),
                  const SizedBox(height: T.s3),
                  OutlinedButton.icon(
                    onPressed: _pickFile,
                    icon: const Icon(Icons.attach_file, size: 18),
                    label: Text(_file == null
                        ? 'Attach a file'
                        : _file!.name),
                  ),
                  if (_file != null)
                    TextButton(
                      onPressed: () => setState(() => _file = null),
                      child: const Text('Remove attachment'),
                    ),
                  const SizedBox(height: T.s3),
                  FilledButton(
                    onPressed: _sending ? null : _submit,
                    child: Text(_sending ? 'Sending…' : 'Submit'),
                  ),
                  if (overdue) ...[
                    const SizedBox(height: T.s2),
                    const Text(
                      'This is past its due date. It will still be accepted, '
                      'but marked late.',
                      style: TextStyle(color: T.warn600, fontSize: 12.5),
                    ),
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
