import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:flutter_networking/flutter_networking.dart';
import 'package:merchant_app/main.dart' as app;

Future<void> settle(WidgetTester tester) async {
  for (var i = 0; i < 12; i++) {
    await tester.pump(const Duration(milliseconds: 250));
  }
  expect(tester.takeException(), isNull);
  expect(find.byType(ErrorWidget), findsNothing);
}

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  testWidgets('restaurant screens and customer status round trip', (
    tester,
  ) async {
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
    final branches =
        (await api.get('/api/v1/merchant/branches')).data['items'] as List;
    app.selectedBranchStore.value = Map<String, dynamic>.from(
      branches.singleWhere(
        (b) => b['id'] == const String.fromEnvironment('QA_BRANCH_ID'),
      ),
    );
    app.main();
    for (final route in [
      '/dashboard',
      '/orders',
      '/kitchen',
      '/menu',
      '/inventory',
      '/settings',
      '/promotions',
      '/analytics',
      '/settlements',
    ]) {
      app.router.go(route);
      await settle(tester);
      debugPrint('QA MERCHANT SCREEN PASSED: $route');
    }
    app.router.go('/menu');
    await settle(tester);
    await tester.tap(find.text('Add product'));
    await settle(tester);
    expect(find.text('Add menu product'), findsOneWidget);
    await tester.tap(find.text('Cancel'));
    await settle(tester);
    const child = String.fromEnvironment('QA_CHILD_ID');
    app.router.go('/orders/$child');
    await settle(tester);
    expect(find.text('Customer for this order'), findsOneWidget);
    final customer = Dio(
      BaseOptions(baseUrl: const String.fromEnvironment('API_BASE_URL')),
    );
    final login = await customer.post(
      '/api/v1/auth/login',
      data: {
        'email': const String.fromEnvironment('QA_CUSTOMER_EMAIL'),
        'password': const String.fromEnvironment('QA_CUSTOMER_PASSWORD'),
      },
    );
    customer.options.headers['Authorization'] =
        'Bearer ${login.data['access_token']}';
    for (final action in [
      ('Accept order', 'accepted'),
      ('Start preparing', 'preparing'),
    ]) {
      await tester.tap(find.text(action.$1));
      await settle(tester);
      final response = await customer.get(
        '/api/v1/orders/${const String.fromEnvironment('QA_ORDER_ID')}/merchant-orders',
      );
      expect(
        (response.data['items'] as List).singleWhere(
          (o) => o['id'] == child,
        )['status'],
        action.$2,
      );
      debugPrint('QA CUSTOMER RECEIVED MERCHANT STATUS: ${action.$2}');
    }
    app.router.go('/settings');
    await settle(tester);
    await tester.ensureVisible(find.text('Sign out'));
    await tester.tap(find.text('Sign out'));
    await settle(tester);
    expect(await app.tokenStore.accessToken(), isNull);
    debugPrint('QA MERCHANT LOGOUT PASSED');
  });
}
