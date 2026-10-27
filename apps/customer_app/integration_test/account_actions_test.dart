import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:flutter_networking/flutter_networking.dart';
import 'package:customer_app/main.dart' as app;
import 'device_flows_test.dart' show settle;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  testWidgets('saved address, support, address management and logout', (tester) async {
    final api = createTransport(app.tokenStore);
    final auth = await api.post('/api/v1/auth/login', data: {
      'email': const String.fromEnvironment('QA_EMAIL'),
      'password': const String.fromEnvironment('QA_PASSWORD'),
    });
    await app.tokenStore.saveTokens(auth.data['access_token'], auth.data['refresh_token']);
    app.main();
    app.router.go('/account');
    await settle(tester);
    await tester.tap(find.text('Add address'));
    await settle(tester);
    final marker = 'Device QA ${DateTime.now().millisecondsSinceEpoch}';
    await tester.enterText(find.byType(TextField).at(0), marker);
    await tester.enterText(find.byType(TextField).at(1), 'Synthetic device QA address, Demo City');
    await tester.enterText(find.byType(TextField).at(2), '18.5204');
    await tester.enterText(find.byType(TextField).at(3), '73.8567');
    FocusManager.instance.primaryFocus?.unfocus();
    await settle(tester);
    await tester.tap(find.text('Save'));
    await settle(tester);
    expect(find.text(marker), findsOneWidget);
    debugPrint('QA ADDRESS creation passed');
    await tester.scrollUntilVisible(find.text('Contact support'), 200, scrollable: find.byType(Scrollable).first);
    await tester.tap(find.text('Contact support'));
    await settle(tester);
    await tester.enterText(find.byType(TextField).at(0), marker);
    await tester.enterText(find.byType(TextField).at(1), 'Synthetic local device QA support request.');
    FocusManager.instance.primaryFocus?.unfocus();
    await settle(tester);
    await tester.tap(find.text('Create ticket'));
    await settle(tester);
    final tickets = (await api.get('/api/v1/me/support/tickets?limit=50')).data['items'] as List;
    expect(tickets.any((ticket) => ticket['subject'] == marker), isTrue);
    debugPrint('QA SUPPORT creation passed');
    app.router.go('/');
    await settle(tester);
    await tester.tap(find.text('Deliver to'));
    await settle(tester);
    await tester.tap(find.text('Manage addresses'));
    await settle(tester);
    expect(find.text('Saved addresses'), findsOneWidget);
    debugPrint('QA MANAGE ADDRESSES navigation passed');
    await tester.scrollUntilVisible(find.text('Sign out'), 250, scrollable: find.byType(Scrollable).first);
    await tester.tap(find.text('Sign out'));
    await settle(tester);
    expect(await app.tokenStore.accessToken(), isNull);
    expect(app.cartCountStore.value, 0);
    expect(find.text('Sign in / create account'), findsOneWidget);
    debugPrint('QA LOGOUT passed');
  });
}
