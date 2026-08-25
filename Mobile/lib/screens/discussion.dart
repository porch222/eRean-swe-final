import 'package:flutter/material.dart';

import '../api/client.dart';
import '../api/resources.dart';
import '../theme/tokens.dart';
import '../widgets/common.dart';

class DiscussionsTab extends StatefulWidget {
  const DiscussionsTab({super.key, required this.courseId});
  final int courseId;

  @override
  State<DiscussionsTab> createState() => _DiscussionsTabState();
}

class _DiscussionsTabState extends State<DiscussionsTab> {
  bool _loading = true;
  String? _error;
  List<Map<String, dynamic>> _threads = [];

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
    final result = await Api.threads(widget.courseId);
    if (!mounted) return;
    setState(() {
      _loading = false;
      if (result.ok) {
        _threads = asList(result.data);
      } else {
        _error = result.message;
      }
    });
  }

  Future<void> _compose() async {
    final title = TextEditingController();
    final body = TextEditingController();
    var kind = 'question';

    final ok = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      builder: (ctx) => Padding(
        padding: EdgeInsets.only(
          left: T.s4,
          right: T.s4,
          top: T.s4,
          bottom: MediaQuery.of(ctx).viewInsets.bottom + T.s4,
        ),
        child: StatefulBuilder(
          builder: (ctx, setSheet) => Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text('Start a thread',
                  style:
                      TextStyle(fontSize: 17, fontWeight: FontWeight.w600)),
              const SizedBox(height: T.s4),
              SegmentedButton<String>(
                segments: const [
                  ButtonSegment(value: 'question', label: Text('Question')),
                  ButtonSegment(
                      value: 'discussion', label: Text('Discussion')),
                ],
                selected: {kind},
                onSelectionChanged: (s) => setSheet(() => kind = s.first),
              ),
              const SizedBox(height: T.s3),
              TextField(
                controller: title,
                decoration: const InputDecoration(labelText: 'Title'),
              ),
              const SizedBox(height: T.s3),
              TextField(
                controller: body,
                maxLines: 4,
                decoration: const InputDecoration(
                    labelText: 'What would you like to ask?'),
              ),
              const SizedBox(height: T.s4),
              FilledButton(
                onPressed: () => Navigator.pop(ctx, true),
                child: const Text('Post'),
              ),
            ],
          ),
        ),
      ),
    );

    if (ok != true || !mounted) return;
    if (title.text.trim().isEmpty) return;

    final result = await Api.createThread(
        widget.courseId, title.text.trim(), body.text.trim(), kind);
    if (!mounted) return;
    if (result.ok) {
      _load();
    } else {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(result.message)));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.transparent,
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _compose,
        backgroundColor: T.brand600,
        foregroundColor: Colors.white,
        icon: const Icon(Icons.add_comment_outlined, size: 20),
        label: const Text('Ask'),
      ),
      body: _loading
          ? const Loading()
          : _error != null
              ? ErrorView(message: _error!, onRetry: _load)
              : _threads.isEmpty
                  ? const EmptyView(
                      icon: Icons.forum_outlined,
                      title: 'No discussions yet',
                      hint: 'Be the first to ask something.',
                    )
                  : RefreshIndicator(
                      onRefresh: _load,
                      child: ListView.separated(
                        padding: const EdgeInsets.fromLTRB(
                            T.s4, T.s4, T.s4, 88),
                        itemCount: _threads.length,
                        separatorBuilder: (_, _) =>
                            const SizedBox(height: T.s2),
                        itemBuilder: (_, i) {
                          final t = _threads[i];
                          final author =
                              (t['author_detail'] as Map<String, dynamic>?)?[
                                  'full_name'];
                          return Card(
                            child: NavRow(
                              icon: t['kind'] == 'question'
                                  ? Icons.help_outline
                                  : Icons.forum_outlined,
                              title: '${t['title']}',
                              subtitle:
                                  '${author ?? ''} · ${formatDate(t['created_at'])}',
                              trailing: t['is_answered'] == true
                                  ? const Pill('Answered',
                                      tone: PillTone.success)
                                  : null,
                              onTap: () async {
                                await Navigator.of(context).push(
                                  MaterialPageRoute(
                                    builder: (_) => ThreadScreen(
                                      courseId: widget.courseId,
                                      threadId: t['id'] as int,
                                    ),
                                  ),
                                );
                                _load();
                              },
                            ),
                          );
                        },
                      ),
                    ),
    );
  }
}

class ThreadScreen extends StatefulWidget {
  const ThreadScreen({
    super.key,
    required this.courseId,
    required this.threadId,
  });
  final int courseId;
  final int threadId;

  @override
  State<ThreadScreen> createState() => _ThreadScreenState();
}

class _ThreadScreenState extends State<ThreadScreen> {
  bool _loading = true;
  String? _error;
  Map<String, dynamic>? _thread;
  final _reply = TextEditingController();
  bool _sending = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _reply.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    final result = await Api.thread(widget.courseId, widget.threadId);
    if (!mounted) return;
    setState(() {
      _loading = false;
      if (result.ok) {
        _thread = result.data as Map<String, dynamic>;
      } else {
        _error = result.message;
      }
    });
  }

  Future<void> _send() async {
    if (_reply.text.trim().isEmpty) return;
    setState(() => _sending = true);
    final result =
        await Api.reply(widget.courseId, widget.threadId, _reply.text.trim());
    if (!mounted) return;
    setState(() => _sending = false);
    if (result.ok) {
      _reply.clear();
      _load();
    } else {
      ScaffoldMessenger.of(context)
          .showSnackBar(SnackBar(content: Text(result.message)));
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

    final t = _thread!;
    final replies = asList(t['replies']);
    final locked = t['is_locked'] == true;
    final author = (t['author_detail'] as Map<String, dynamic>?)?['full_name'];

    return Scaffold(
      appBar: AppBar(
          title: Text('${t['title']}',
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
                  Text('${author ?? ''} · ${formatDateTime(t['created_at'])}',
                      style:
                          const TextStyle(color: T.n500, fontSize: 12.5)),
                  const SizedBox(height: T.s2),
                  Text('${t['body']}',
                      style: const TextStyle(height: 1.5, color: T.n600)),
                ],
              ),
            ),
          ),
          const SizedBox(height: T.s4),
          Eyebrow(plural(replies.length, 'reply', 'replies')),
          const SizedBox(height: T.s2),
          ...replies.map((r) {
            final accepted = r['is_answer'] == true;
            final name =
                (r['author_detail'] as Map<String, dynamic>?)?['full_name'];
            return Padding(
              padding: const EdgeInsets.only(bottom: T.s2),
              child: Card(
                color: accepted ? T.ok50 : null,
                child: Padding(
                  padding: const EdgeInsets.all(T.s4),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(children: [
                        Expanded(
                          child: Text(
                            '${name ?? ''} · ${formatDateTime(r['created_at'])}',
                            style: const TextStyle(
                                color: T.n500, fontSize: 12.5),
                          ),
                        ),
                        if (accepted)
                          const Pill('Accepted answer',
                              tone: PillTone.success),
                      ]),
                      const SizedBox(height: T.s2),
                      Text('${r['body']}',
                          style:
                              const TextStyle(height: 1.5, color: T.n600)),
                    ],
                  ),
                ),
              ),
            );
          }),
          const SizedBox(height: T.s3),
          if (locked)
            const Card(
              child: Padding(
                padding: EdgeInsets.all(T.s4),
                child: Text('This thread is locked. No new replies.',
                    style: TextStyle(color: T.n500)),
              ),
            )
          else
            Card(
              child: Padding(
                padding: const EdgeInsets.all(T.s4),
                child: Column(children: [
                  TextField(
                    controller: _reply,
                    maxLines: 3,
                    decoration:
                        const InputDecoration(labelText: 'Write a reply'),
                  ),
                  const SizedBox(height: T.s3),
                  FilledButton(
                    onPressed: _sending ? null : _send,
                    child: Text(_sending ? 'Posting…' : 'Post reply'),
                  ),
                ]),
              ),
            ),
        ],
      ),
    );
  }
}
