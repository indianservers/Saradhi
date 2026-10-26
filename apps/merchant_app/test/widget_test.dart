import 'package:flutter_test/flutter_test.dart';
import 'package:merchant_app/main.dart' as app;

void main() {
  testWidgets('foundation shell renders', (tester) async {
    app.main();
    await tester.pumpAndSettle();
    expect(find.text('Your business, connected'), findsOneWidget);
    expect(find.text('quickbuddy.'), findsOneWidget);
  });
}
