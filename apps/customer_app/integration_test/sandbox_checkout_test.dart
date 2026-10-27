import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:flutter_networking/flutter_networking.dart';
import 'package:customer_app/main.dart' as app;
import 'device_flows_test.dart' show settle;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  testWidgets('local sandbox order placement and payment', (tester) async {
    final api = createTransport(app.tokenStore);
    final auth = await api.post('/api/v1/auth/login', data: {
      'email': const String.fromEnvironment('QA_EMAIL'),
      'password': const String.fromEnvironment('QA_PASSWORD'),
    });
    await app.tokenStore.saveTokens(auth.data['access_token'], auth.data['refresh_token']);
    final config = (await api.get('/api/v1/payments/configuration')).data;
    expect(config['sandbox_payment_available'], true);
    expect(config['online_payment_available'], false);
    final products = (await api.get('/api/v1/catalog/products?limit=10')).data['items'] as List;
    final product = products.first;
    final windows = (await api.get('/api/v1/merchants/branches/${product['branch_id']}/windows?limit=10')).data['items'] as List;
    final cart = (await api.post('/api/v1/carts')).data;
    final cartId = cart['id'] as String;
    await api.post('/api/v1/carts/$cartId/items', data: {
      'branch_id': product['branch_id'], 'variant_id': product['variant_id'],
      'quantity': 1, 'window_id': windows.first['id'], 'delivery_method': 'pickup',
    });
    await app.tokenStore.writeValue('qb_cart', cartId);
    app.cartIdStore.value = cartId;
    app.main();
    app.router.go('/checkout/address-payment');
    await settle(tester);
    await tester.scrollUntilVisible(find.text('Place sandbox order'), 200, scrollable: find.byType(Scrollable).first);
    await settle(tester);
    await tester.tap(find.text('Place sandbox order'));
    await settle(tester);
    expect(app.router.routeInformationProvider.value.uri.path, contains('/complete'));
    expect(find.text('Payment confirmed'), findsOneWidget);
    debugPrint('QA SANDBOX order and payment confirmed');
    expect(await app.tokenStore.readValue('qb_cart'), isNull);
    expect(app.cartIdStore.value, isNull);
    expect(app.cartCountStore.value, 0);
    debugPrint('QA CONFIRMED CART cleanup passed');
  });
}
