import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:customer_app/main.dart' as app;
import 'package:flutter_networking/flutter_networking.dart';

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
// Authenticate through the real sign-in form.
    app.router.push('/sign-in');
    await settle(tester);
    await tester.enterText(find.byType(TextFormField).at(0), const String.fromEnvironment('QA_EMAIL'));
    await tester.enterText(find.byType(TextFormField).at(1), const String.fromEnvironment('QA_PASSWORD'));
    await tester.testTextInput.receiveAction(TextInputAction.done);
    await settle(tester);
    expect(await app.tokenStore.accessToken(), isNotNull);
    for (final route in ['/', '/restaurants', '/search', '/cart', '/orders', '/account', '/onboarding']) {
      app.router.go(route);
      await settle(tester);
      expect(find.byType(ErrorWidget), findsNothing, reason: route);
      debugPrint('QA SCREEN PASSED: $route');
    }
    app.router.go('/account');
    await settle(tester);
    await tester.tap(find.text('Add address'));
    await settle(tester);
    expect(find.text('Add delivery address'), findsOneWidget);
    await tester.tap(find.text('Cancel'));
    await settle(tester);
    await tester.scrollUntilVisible(find.text('Contact support'), 200, scrollable: find.byType(Scrollable).first);
    await tester.tap(find.text('Contact support'));
    await settle(tester);
    expect(find.text('Create ticket'), findsOneWidget);
    await tester.tap(find.text('Cancel'));
    await settle(tester);
    final api = createTransport(app.tokenStore);
    final branches = (await api.get('/api/v1/merchants/branches?limit=12')).data['items'] as List;
    expect(branches, isNotEmpty);
    for (final branch in branches) {
      app.router.go('/restaurant/${branch['id']}');
      await settle(tester);
      debugPrint('QA BRANCH PASSED: ${branch['id']}');
    }
    final firstBranch = branches.first;
    app.router.go('/restaurant/${firstBranch['id']}');
    await settle(tester);
    final addButton = find.byIcon(Icons.add_circle);
    if (addButton.evaluate().isNotEmpty) {
      await tester.tap(addButton.first);
      await settle(tester);
      if (find.text('Add to cart').evaluate().isNotEmpty) {
        await tester.scrollUntilVisible(find.text('Add to cart'), 150, scrollable: find.byType(Scrollable).last);
        await settle(tester);
        await tester.tap(find.text('Add to cart'));
        await settle(tester);
      }
      expect(app.cartCountStore.value, greaterThan(0));
      app.router.go('/cart');
      await settle(tester);
      final beforeIncrease = app.cartCountStore.value;
      await tester.tap(find.byTooltip('Increase quantity').first);
      await settle(tester);
      expect(app.cartCountStore.value, beforeIncrease + 1);
      await tester.tap(find.byTooltip('Decrease quantity').first);
      await settle(tester);
      expect(app.cartCountStore.value, beforeIncrease);
      app.router.go('/checkout/address-payment');
      await settle(tester);
      expect(find.text('Payment unavailable'), findsWidgets);
      app.router.go('/cart');
      await settle(tester);
      await tester.tap(find.byTooltip('Remove item').first);
      await settle(tester);
      debugPrint('QA CART: add, increase, decrease, quote, remove passed');
    }
    final orders = (await api.get('/api/v1/orders?limit=10')).data['items'] as List;
    for (final order in orders.take(2)) {
      for (final suffix in ['complete', 'tracking']) {
        app.router.go('/orders/${order['id']}/$suffix');
        await settle(tester);
        debugPrint('QA ORDER SCREEN PASSED: $suffix');
      }
    }
    app.router.go('/');
    await settle(tester);
  });
}
