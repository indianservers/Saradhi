import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:flutter_networking/flutter_networking.dart';
import 'package:customer_app/main.dart' as app;

Future<void> until(
  WidgetTester tester,
  bool Function() condition,
  String stage,
) async {
  for (var i = 0; i < 180; i++) {
    await tester.pump(const Duration(milliseconds: 500));
    expect(tester.takeException(), isNull, reason: stage);
    if (condition()) return;
    if (stage.startsWith('connected') && app.deliveryCalls.error != null) {
      fail('Call failed at $stage: ${app.deliveryCalls.error}');
    }
  }
  fail(
    'Timed out: $stage; call status ${app.deliveryCalls.status}; ${app.deliveryCalls.error}',
  );
}

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  testWidgets('two-device bidirectional audio call', (tester) async {
    final api = createTransport(app.tokenStore);
    final auth = await api.post(
      '/api/v1/auth/login',
      data: {
        'email': const String.fromEnvironment('QA_EMAIL'),
        'password': const String.fromEnvironment('QA_PASSWORD'),
      },
    );
    await app.tokenStore.saveTokens(
      auth.data['access_token'],
      auth.data['refresh_token'],
    );
    app.deliveryCalls.debugTracing = true;
    app.main();
    app.router.go(
      '/orders/${const String.fromEnvironment('QA_ORDER_ID')}/tracking',
    );
    for (var i = 0; i < 10; i++) {
      await tester.pump(const Duration(milliseconds: 200));
    }
    for (var round = 0; round < 2; round++) {
      final initiate = round == 0 ? true : !true;
      if (initiate) {
        await until(
          tester,
          () => find.text('Call delivery partner').evaluate().isNotEmpty,
          'call button',
        );
        await tester.ensureVisible(find.text('Call delivery partner'));
        await tester.pump(const Duration(seconds: 1));
        await tester.tap(find.text('Call delivery partner'));
      } else {
        await until(
          tester,
          () => find.text('Answer').evaluate().isNotEmpty,
          'incoming call',
        );
        await tester.tap(find.text('Answer'));
      }
      await until(
        tester,
        () => app.deliveryCalls.connected,
        'connected round $round',
      );
      for (var i = 0; i < 12; i++) {
        await tester.pump(const Duration(milliseconds: 500));
      }
      final packets = await app.deliveryCalls.audioPacketCounts();
      expect(packets['sent'], greaterThan(0));
      expect(packets['received'], greaterThan(0));
      debugPrint(
        'QA AUDIO ROUND $round: sent=${packets['sent']} received=${packets['received']}',
      );
      await tester.tap(find.byTooltip('Mute'));
      await tester.pump(const Duration(milliseconds: 500));
      expect(app.deliveryCalls.muted, true);
      await tester.tap(find.byTooltip('Unmute'));
      await tester.tap(find.byTooltip('Use speaker'));
      await tester.pump(const Duration(milliseconds: 500));
      expect(app.deliveryCalls.speaker, true);
      await tester.tap(find.byTooltip('Use earpiece'));
      if (initiate) {
        for (var i = 0; i < 12; i++) {
          await tester.pump(const Duration(milliseconds: 500));
        }
        await tester.tap(find.text('End call'));
      }
      await until(
        tester,
        () => app.deliveryCalls.call == null,
        'hangup round $round',
      );
      debugPrint('QA HANGUP ROUND $round passed');
    }
  });
}
