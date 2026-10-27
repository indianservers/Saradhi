import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:flutter_networking/flutter_networking.dart';
import 'package:pilot_app/main.dart' as app;
import 'device_flows_test.dart' show settle;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  testWidgets('physical foreground location and availability', (tester) async {
    final api = createTransport(app.pilotTokenStore);
    final auth = await api.post('/api/v1/auth/login', data: {
      'email': const String.fromEnvironment('QA_EMAIL'),
      'password': const String.fromEnvironment('QA_PASSWORD'),
    });
    await app.pilotTokenStore.saveTokens(auth.data['access_token'], auth.data['refresh_token']);
    app.main();
    app.router.go('/dashboard');
    await settle(tester);
    await tester.tap(find.byType(SwitchListTile).first);
    await settle(tester);
    if (find.text('Agree and continue').evaluate().isNotEmpty) {
      await tester.tap(find.text('Agree and continue'));
    }
    for (var i = 0; i < 100; i++) {
      await tester.pump(const Duration(milliseconds: 500));
    }
    expect(tester.takeException(), isNull);
    final toggle = tester.widget<SwitchListTile>(find.byType(SwitchListTile).first);
    expect(toggle.onChanged, isNotNull, reason: 'GPS attempt must finish or time out');
    if (app.pilotProfileStore.value?['state'] == 'online_available') {
      debugPrint('QA REAL DEVICE LOCATION: online availability succeeded');
      await tester.tap(find.byType(SwitchListTile).first);
      await settle(tester);
      expect(app.pilotProfileStore.value?['state'], 'offline');
      debugPrint('QA OFFLINE transition passed');
    } else {
      debugPrint('QA REAL DEVICE LOCATION: unavailable; online request recovered without hanging');
      for (final text in tester.widgetList<Text>(find.byType(Text))) {
        final value = text.data ?? '';
        if (value.contains('permission') || value.contains('Timeout') || value.contains('location')) debugPrint('QA LOCATION MESSAGE: $value');
      }
      expect(app.pilotProfileStore.value?['state'], 'offline');
    }
    app.router.go('/profile');
    await settle(tester);
    await tester.tap(find.text('Stop location sharing'));
    await settle(tester);
    await tester.tap(find.text('Stop sharing'));
    await settle(tester);
    final revoked = await api.get('/api/v1/pilots/me');
    expect(revoked.data['location_consent'], false);
    expect(revoked.data['state'], 'offline');
    debugPrint('QA LOCATION REVOCATION passed');
    await app.pilotLocationReporter.stop();
  });
}
