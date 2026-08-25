import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../theme/tokens.dart';

class Loading extends StatelessWidget {
  const Loading({super.key, this.label});
  final String? label;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          const CircularProgressIndicator(strokeWidth: 2.5),
          if (label != null) ...[
            const SizedBox(height: T.s4),
            Text(label!, style: const TextStyle(color: T.n500)),
          ],
        ],
      ),
    );
  }
}

class ErrorView extends StatelessWidget {
  const ErrorView({super.key, required this.message, this.onRetry});
  final String message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(T.s5),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, color: T.bad600, size: 36),
            const SizedBox(height: T.s3),
            Text(message,
                textAlign: TextAlign.center,
                style: const TextStyle(color: T.n600)),
            if (onRetry != null) ...[
              const SizedBox(height: T.s4),
              SizedBox(
                width: 160,
                child: OutlinedButton(
                    onPressed: onRetry, child: const Text('Try again')),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

class EmptyView extends StatelessWidget {
  const EmptyView({
    super.key,
    required this.icon,
    required this.title,
    this.hint,
    this.action,
  });
  final IconData icon;
  final String title;
  final String? hint;
  final Widget? action;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(T.s5),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 40, color: T.n400),
            const SizedBox(height: T.s3),
            Text(title,
                textAlign: TextAlign.center,
                style: const TextStyle(
                    fontSize: 16, fontWeight: FontWeight.w600, color: T.n800)),
            if (hint != null) ...[
              const SizedBox(height: T.s2),
              Text(hint!,
                  textAlign: TextAlign.center,
                  style: const TextStyle(color: T.n500, height: 1.4)),
            ],
            if (action != null) ...[const SizedBox(height: T.s4), action!],
          ],
        ),
      ),
    );
  }
}

class Eyebrow extends StatelessWidget {
  const Eyebrow(this.text, {super.key});
  final String text;

  @override
  Widget build(BuildContext context) => Text(
        text.toUpperCase(),
        style: const TextStyle(
          fontSize: 11,
          letterSpacing: 0.8,
          fontWeight: FontWeight.w600,
          color: T.brass600,
        ),
      );
}

class Pill extends StatelessWidget {
  const Pill(this.text, {super.key, this.tone = PillTone.muted});
  final String text;
  final PillTone tone;

  @override
  Widget build(BuildContext context) {
    final (bg, fg) = switch (tone) {
      PillTone.success => (T.ok50, T.ok600),
      PillTone.warning => (T.warn50, T.warn600),
      PillTone.danger => (T.bad50, T.bad600),
      PillTone.info => (T.info50, T.info600),
      PillTone.muted => (T.n100, T.n500),
    };
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(text,
          style: TextStyle(
              fontSize: 11.5, fontWeight: FontWeight.w600, color: fg)),
    );
  }
}

enum PillTone { success, warning, danger, info, muted }

Pill statusPill(String? status) {
  return switch (status) {
    'active' => const Pill('Active', tone: PillTone.info),
    'completed' => const Pill('Completed', tone: PillTone.success),
    'dropped' => const Pill('Dropped', tone: PillTone.danger),
    'pending' => const Pill('Pending', tone: PillTone.warning),
    'approved' => const Pill('Approved', tone: PillTone.success),
    'rejected' => const Pill('Rejected', tone: PillTone.danger),
    'published' => const Pill('Published', tone: PillTone.success),
    _ => Pill(status ?? '—'),
  };
}

class Grade extends StatelessWidget {
  const Grade({super.key, required this.value, this.outOf, this.large = false});
  final dynamic value;
  final dynamic outOf;
  final bool large;

  @override
  Widget build(BuildContext context) {
    if (value == null || value == '') {
      return const Text('Not graded',
          style: TextStyle(color: T.n400, fontSize: 13));
    }
    final n = double.tryParse('$value') ?? 0;
    return RichText(
      text: TextSpan(
        style: kNumeric.copyWith(
          fontSize: large ? 26 : 16,
          fontWeight: FontWeight.w600,
          color: T.n900,
        ),
        children: [
          TextSpan(text: n.toStringAsFixed(0)),
          if (outOf != null)
            TextSpan(
              text: '/$outOf',
              style: kNumeric.copyWith(
                fontSize: large ? 15 : 12.5,
                fontWeight: FontWeight.w500,
                color: T.n400,
              ),
            ),
        ],
      ),
    );
  }
}

class StatTile extends StatelessWidget {
  const StatTile({
    super.key,
    required this.value,
    required this.label,
    required this.icon,
  });
  final String value;
  final String label;
  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(T.s3),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(children: [
              Icon(icon, size: 14, color: T.n400),
              const SizedBox(width: 5),
              Expanded(
                child: Text(label.toUpperCase(),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 10,
                      letterSpacing: 0.6,
                      fontWeight: FontWeight.w600,
                      color: T.n500,
                    )),
              ),
            ]),
            const SizedBox(height: T.s2),
            Text(value,
                style: kNumeric.copyWith(
                    fontSize: 22, fontWeight: FontWeight.w600, color: T.n900)),
          ],
        ),
      ),
    );
  }
}

class Meter extends StatelessWidget {
  const Meter({super.key, required this.percent, this.height = 7});
  final double percent;
  final double height;

  @override
  Widget build(BuildContext context) {
    final p = percent.clamp(0, 100) / 100;
    return Row(children: [
      Expanded(
        child: ClipRRect(
          borderRadius: BorderRadius.circular(999),
          child: LinearProgressIndicator(
            value: p.toDouble(),
            minHeight: height,
            backgroundColor: T.n200,
            valueColor: AlwaysStoppedAnimation(
                p >= 1 ? T.ok600 : T.brand500),
          ),
        ),
      ),
      const SizedBox(width: T.s2),
      Text('${percent.clamp(0, 100).toStringAsFixed(0)}%',
          style: kNumeric.copyWith(
              fontSize: 12, fontWeight: FontWeight.w600, color: T.n600)),
    ]);
  }
}

class NavRow extends StatelessWidget {
  const NavRow({
    super.key,
    required this.icon,
    required this.title,
    this.subtitle,
    this.trailing,
    required this.onTap,
  });
  final IconData icon;
  final String title;
  final String? subtitle;
  final Widget? trailing;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      onTap: onTap,

      minVerticalPadding: 14,
      leading: Icon(icon, color: T.brand600, size: 22),
      title: Text(title,
          style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 15)),
      subtitle: subtitle == null
          ? null
          : Text(subtitle!, style: const TextStyle(color: T.n500)),
      trailing: trailing ??
          const Icon(Icons.chevron_right, color: T.n400, size: 22),
    );
  }
}

String formatDate(dynamic iso) {
  final d = DateTime.tryParse('$iso');
  if (d == null) return '—';
  return DateFormat('d MMM yyyy').format(d.toLocal());
}

String formatDateTime(dynamic iso) {
  final d = DateTime.tryParse('$iso');
  if (d == null) return '—';
  return DateFormat('d MMM yyyy, HH:mm').format(d.toLocal());
}

String relativeDue(dynamic iso) {
  final parsed = DateTime.tryParse('$iso');
  if (parsed == null) return 'No due date';

  final due = parsed.toLocal();
  final now = DateTime.now();
  final dueDay = DateTime(due.year, due.month, due.day);
  final today = DateTime(now.year, now.month, now.day);
  final days = dueDay.difference(today).inDays;

  if (days == 0) return 'Due today';
  if (days == 1) return 'Due tomorrow';
  if (days > 1) return 'Due in $days days';
  final ago = -days;
  return ago == 1 ? 'Overdue by 1 day' : 'Overdue by $ago days';
}

String plural(int n, String singular, [String? pluralForm]) =>
    '$n ${n == 1 ? singular : (pluralForm ?? '${singular}s')}';
