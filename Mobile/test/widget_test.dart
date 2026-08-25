import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:erean_mobile/api/client.dart';
import 'package:erean_mobile/theme/tokens.dart';
import 'package:erean_mobile/widgets/common.dart';

void main() {
  group('ApiResult', () {
    test('reads a DRF detail message', () {
      const r = ApiResult.failure(403, {'detail': 'Not allowed.'});
      expect(r.ok, isFalse);
      expect(r.message, 'Not allowed.');
    });

    test('reads the first field error when there is no detail', () {
      const r = ApiResult.failure(400, {
        'credits_to_graduate': ['Cannot be below the required total.'],
      });
      expect(r.message, 'Cannot be below the required total.');
    });

    test('flattens field errors for a form, ignoring detail', () {
      const r = ApiResult.failure(400, {
        'detail': 'Invalid.',
        'username': ['Already taken.'],
        'email': ['Enter a valid email.'],
      });
      expect(r.fieldErrors, {
        'username': 'Already taken.',
        'email': 'Enter a valid email.',
      });
    });

    test('falls back to a usable message when the body is empty', () {
      const r = ApiResult.failure(500, {});
      expect(r.message, isNotEmpty);
    });
  });

  group('asList', () {
    test('unwraps a paginated response', () {
      final rows = asList({
        'count': 2,
        'results': [
          {'id': 1},
          {'id': 2},
        ],
      });
      expect(rows.length, 2);
      expect(rows.first['id'], 1);
    });

    test('passes a bare list straight through', () {
      expect(asList([{'id': 9}]).first['id'], 9);
    });

    test('returns empty rather than throwing on an unexpected shape', () {
      expect(asList(null), isEmpty);
      expect(asList('nonsense'), isEmpty);
    });
  });

  group('relativeDue', () {
    test('reports an overdue date as overdue', () {
      final past = DateTime.now().subtract(const Duration(days: 3));
      expect(relativeDue(past.toIso8601String()), contains('Overdue'));
    });

    test('reports a future date as remaining', () {
      final future = DateTime.now().add(const Duration(days: 4));
      expect(relativeDue(future.toIso8601String()), 'Due in 4 days');
    });

    test('handles a missing due date without throwing', () {
      expect(relativeDue(null), 'No due date');
    });

    test('counts calendar days, not elapsed hours', () {

      final now = DateTime.now();
      final tomorrowEarly =
          DateTime(now.year, now.month, now.day).add(const Duration(days: 1, hours: 1));
      expect(relativeDue(tomorrowEarly.toIso8601String()), 'Due tomorrow');
    });

    test('today is today whatever the time', () {
      final later = DateTime.now().add(const Duration(minutes: 5));
      final sameDay = DateTime(later.year, later.month, later.day, 23, 59);
      expect(relativeDue(sameDay.toIso8601String()), 'Due today');
    });
  });

  group('plural', () {
    test('keeps the singular at one', () => expect(plural(1, 'credit'), '1 credit'));
    test('adds s otherwise', () => expect(plural(3, 'credit'), '3 credits'));
    test('takes an irregular plural', () {
      expect(plural(2, 'reply', 'replies'), '2 replies');
    });
  });

  group('Grade', () {
    testWidgets('shows "Not graded" when there is no mark', (tester) async {
      await tester.pumpWidget(const MaterialApp(
        home: Scaffold(body: Grade(value: null, outOf: 100)),
      ));
      expect(find.text('Not graded'), findsOneWidget);
    });

    testWidgets('renders the score against its maximum', (tester) async {
      await tester.pumpWidget(const MaterialApp(
        home: Scaffold(body: Grade(value: 45, outOf: 50)),
      ));

      expect(find.textContaining('45', findRichText: true), findsOneWidget);
      expect(find.textContaining('/50', findRichText: true), findsOneWidget);
    });
  });

  testWidgets('EmptyView shows its title and hint', (tester) async {
    await tester.pumpWidget(const MaterialApp(
      home: Scaffold(
        body: EmptyView(
          icon: Icons.inbox,
          title: 'Nothing here',
          hint: 'Come back later.',
        ),
      ),
    ));
    expect(find.text('Nothing here'), findsOneWidget);
    expect(find.text('Come back later.'), findsOneWidget);
  });

  testWidgets('ErrorView offers a retry that fires', (tester) async {
    var tapped = 0;
    await tester.pumpWidget(MaterialApp(
      home: Scaffold(
        body: ErrorView(message: 'Boom', onRetry: () => tapped++),
      ),
    ));
    await tester.tap(find.text('Try again'));
    expect(tapped, 1);
  });

  testWidgets('Meter clamps a value above one hundred', (tester) async {
    await tester.pumpWidget(const MaterialApp(
      home: Scaffold(body: Meter(percent: 250)),
    ));
    expect(find.text('100%'), findsOneWidget);
  });

  test('theme builds without error', () {
    expect(buildTheme().useMaterial3, isTrue);
  });
}
