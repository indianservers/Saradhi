import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:pilot_app/main.dart' as app;

Future<void> settle(WidgetTester tester) async {
  for (var i = 0; i < 10; i++) {
    await tester.pump(const Duration(milliseconds: 200));
  }
  expect(tester.takeException(), isNull);
  debugPrint('QA settled screen');
}

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  testWidgets('physical device live workflows', (tester) async {
    app.main();
    await settle(tester);
await tester.enterText(find.byType(TextField).at(0), const String.fromEnvironment('QA_EMAIL'));
    await tester.enterText(find.byType(TextField).at(1), const String.fromEnvironment('QA_PASSWORD'));
    await tester.tap(find.text('Sign in').last);
    await settle(tester);
    expect(await app.pilotTokenStore.accessToken(), isNotNull);
    expect(app.pilotProfileStore.value, isNotNull);
    for (final route in ['/dashboard', '/requests', '/pickup', '/routes', '/navigation', '/complete', '/incident', '/earnings', '/operations', '/profile']) {
      app.router.go(route);
      await settle(tester);
      expect(find.byType(ErrorWidget), findsNothing, reason: route);
      debugPrint('QA SCREEN PASSED: $route');
    }
    app.router.go('/dashboard');
    await settle(tester);
    await tester.tap(find.byType(SwitchListTile).first);
    await settle(tester);
    if (find.text('Not now').evaluate().isNotEmpty) {
      await tester.tap(find.text('Not now'));
      await settle(tester);
      expect(app.pilotProfileStore.value?['state'], 'offline');
      debugPrint('QA LOCATION consent cancel passed');
    }
    app.router.go('/incident');
    await settle(tester);
    final summary = 'Synthetic device QA report ${DateTime.now().millisecondsSinceEpoch}';
    await tester.enterText(find.byType(TextField).first, summary);
    FocusManager.instance.primaryFocus?.unfocus();
    await settle(tester);
    await settle(tester);
    await tester.scrollUntilVisible(find.text('Send to Quickbuddy operations'), 200, scrollable: find.byType(Scrollable).first);
    await tester.tap(find.text('Send to Quickbuddy operations'));
    await settle(tester);
    expect(find.textContaining('Report ID'), findsOneWidget);
    debugPrint('QA INCIDENT submission passed');
    app.router.go('/profile');
    await settle(tester);
    await tester.tap(find.text('Sign out'));
    await settle(tester);
    expect(await app.pilotTokenStore.accessToken(), isNull);
    expect(find.text('Your deliveries, in one place'), findsOneWidget);
    debugPrint('QA LOGOUT passed');
  });
}
