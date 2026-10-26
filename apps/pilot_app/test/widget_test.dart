import 'package:flutter_test/flutter_test.dart';
import 'package:pilot_app/main.dart' as app;

void main() {
  testWidgets('foundation shell renders', (tester) async {
    app.main();
    await tester.pumpAndSettle();
    expect(find.text('Ready for your next route'), findsOneWidget);
    expect(find.text('quickbuddy.'), findsOneWidget);
  });
}
