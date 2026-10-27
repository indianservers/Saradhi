import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:merchant_app/main.dart' as app;

void main() {
  testWidgets('merchant workspace requires sign in instead of showing preview orders', (tester) async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger.setMockMethodCallHandler(
      const MethodChannel('plugins.it_nomads.com/flutter_secure_storage'), (_) async => null);
    app.main();
    await tester.pumpAndSettle();
    expect(find.text('Welcome back'), findsOneWidget);
    expect(find.text('Quick'), findsOneWidget);
    expect(find.text('Rohit Sharma'), findsNothing);
  });
}
