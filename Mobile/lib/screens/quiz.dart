import 'package:flutter/material.dart';

import '../api/client.dart';
import '../api/resources.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';

class QuizScreen extends StatefulWidget {
  const QuizScreen({
    super.key,
    required this.courseId,
    required this.assignment,
  });
  final int courseId;
  final Map<String, dynamic> assignment;

  @override
  State<QuizScreen> createState() => _QuizScreenState();
}

class _QuizScreenState extends State<QuizScreen> {
  bool _loading = true;
  String? _error;
  bool _sending = false;

  List<Map<String, dynamic>> _questions = [];

  final Map<int, int> _single = {};

  final Map<int, Set<int>> _multiple = {};

  final Map<int, TextEditingController> _written = {};

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    for (final c in _written.values) {
      c.dispose();
    }
    super.dispose();
  }

  int get _assignmentId => widget.assignment['id'] as int;

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });

    final result = await Api.quizQuestions(widget.courseId, _assignmentId);
    if (!mounted) return;

    if (!result.ok) {
      setState(() {
        _loading = false;

        _error = result.message;
      });
      return;
    }

    final questions = asList(result.data);
    for (final q in questions) {
      if (q['type'] == 'written') {
        _written[q['id'] as int] = TextEditingController();
      }
    }

    setState(() {
      _loading = false;
      _questions = questions;
    });
  }

  List<Map<String, dynamic>> _collectAnswers() {
    return _questions.map((q) {
      final id = q['id'] as int;
      return switch (q['type']) {
        'multiple' => {
            'question': id,
            'selected_choices': (_multiple[id] ?? <int>{}).toList(),
          },
        'written' => {
            'question': id,
            'text_answer': _written[id]?.text.trim() ?? '',
          },

        _ => {'question': id, 'selected_choice': _single[id]},
      };
    }).toList();
  }

  bool get _complete {
    for (final q in _questions) {
      final id = q['id'] as int;
      switch (q['type']) {
        case 'multiple':
          if ((_multiple[id] ?? const <int>{}).isEmpty) return false;
        case 'written':
          if ((_written[id]?.text.trim() ?? '').isEmpty) return false;
        default:
          if (_single[id] == null) return false;
      }
    }
    return _questions.isNotEmpty;
  }

  Future<void> _submit() async {
    final unanswered = !_complete;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Submit this quiz?'),
        content: Text(unanswered
            ? 'Some questions are unanswered, and they will score nothing. '
                'You only get one attempt, so this cannot be undone.'
            : 'You only get one attempt, so this cannot be undone.'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Keep working')),
          FilledButton(
              onPressed: () => Navigator.pop(ctx, true),
              child: const Text('Submit')),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;

    setState(() => _sending = true);
    final result =
        await Api.submitQuiz(widget.courseId, _assignmentId, _collectAnswers());
    if (!mounted) return;
    setState(() => _sending = false);

    if (!result.ok) {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(result.message)));
      return;
    }

    final attempt = result.data as Map<String, dynamic>;
    await showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Quiz submitted'),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          Grade(
              value: attempt['score'],
              outOf: widget.assignment['max_score'],
              large: true),
          const SizedBox(height: T.s3),
          Text(
            attempt['needs_manual_grading'] == true
                ? 'This is provisional. Your written answers still need to be '
                    'marked by your instructor, and your score will go up once '
                    'they are.'
                : 'This is your final score for the quiz.',
            textAlign: TextAlign.center,
            style: const TextStyle(color: T.n600, height: 1.4),
          ),
        ]),
        actions: [
          FilledButton(
              onPressed: () => Navigator.pop(ctx), child: const Text('Done')),
        ],
      ),
    );

    if (mounted) Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('${widget.assignment['title']}',
            maxLines: 1, overflow: TextOverflow.ellipsis),
      ),
      body: _loading
          ? const Loading()
          : _error != null
              ? _alreadyDone()
              : _questions.isEmpty
                  ? const EmptyView(
                      icon: Icons.quiz_outlined,
                      title: 'No questions yet',
                      hint: 'Your instructor has not added any questions.')
                  : _form(),
      bottomNavigationBar: (_loading || _error != null || _questions.isEmpty)
          ? null
          : SafeArea(
              child: Padding(
                padding: const EdgeInsets.all(T.s4),
                child: FilledButton(
                  onPressed: _sending ? null : _submit,
                  child: Text(_sending ? 'Submitting…' : 'Submit quiz'),
                ),
              ),
            ),
    );
  }

  Widget _alreadyDone() => EmptyView(
        icon: Icons.check_circle_outline,
        title: 'Already submitted',
        hint: _error,
        action: OutlinedButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Back to coursework'),
        ),
      );

  Widget _form() {
    return ListView.separated(
      padding: const EdgeInsets.all(T.s4),
      itemCount: _questions.length,
      separatorBuilder: (_, _) => const SizedBox(height: T.s3),
      itemBuilder: (_, i) {
        final q = _questions[i];
        final id = q['id'] as int;
        final choices = asList(q['choices']);

        return Card(
          child: Padding(
            padding: const EdgeInsets.all(T.s4),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(children: [
                  Eyebrow('Question ${i + 1}'),
                  const Spacer(),
                  Text(plural(q['points'] as int? ?? 0, 'point'),
                      style: const TextStyle(color: T.n500, fontSize: 12.5)),
                ]),
                const SizedBox(height: T.s2),
                Text('${q['text']}',
                    style: const TextStyle(
                        fontSize: 15.5, height: 1.4, color: T.n900)),
                const SizedBox(height: T.s3),

                if (q['type'] == 'written')
                  TextField(
                    controller: _written[id],
                    maxLines: 5,
                    onChanged: (_) => setState(() {}),
                    decoration: const InputDecoration(
                      hintText: 'Type your answer',
                      alignLabelWithHint: true,
                    ),
                  )
                else if (q['type'] == 'multiple')
                  ...choices.map((c) {
                    final cid = c['id'] as int;
                    final chosen = _multiple[id]?.contains(cid) ?? false;
                    return CheckboxListTile(
                      value: chosen,
                      contentPadding: EdgeInsets.zero,
                      controlAffinity: ListTileControlAffinity.leading,
                      title: Text('${c['text']}'),
                      onChanged: (v) => setState(() {
                        final set = _multiple.putIfAbsent(id, () => <int>{});
                        v == true ? set.add(cid) : set.remove(cid);
                      }),
                    );
                  })
                else

                  RadioGroup<int>(
                    groupValue: _single[id],
                    onChanged: (v) => setState(() {
                      if (v != null) _single[id] = v;
                    }),
                    child: Column(
                      children: choices.map((c) {
                        return RadioListTile<int>(
                          value: c['id'] as int,
                          contentPadding: EdgeInsets.zero,
                          title: Text('${c['text']}'),
                        );
                      }).toList(),
                    ),
                  ),

                if (q['type'] == 'multiple')
                  const Padding(
                    padding: EdgeInsets.only(top: T.s1),
                    child: Text('Select all that apply.',
                        style: TextStyle(color: T.n400, fontSize: 12)),
                  ),
              ],
            ),
          ),
        );
      },
    );
  }
}
