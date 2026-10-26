import 'package:flutter_test/flutter_test.dart';
import 'package:pilot_app/main.dart' as app;

void main() {
  testWidgets('pilot sign-in screen renders', (tester) async {
    app.main();
    await tester.pumpAndSettle();
    expect(find.text('Your deliveries, in one place'), findsOneWidget);
    expect(find.text('Sign in'), findsOneWidget);
    expect(find.text('Email'), findsOneWidget);
  });
}
