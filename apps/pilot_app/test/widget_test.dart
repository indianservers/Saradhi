import 'package:flutter_test/flutter_test.dart';
import 'package:pilot_app/main.dart' as app;

void main() {
  testWidgets('pilot login screen renders', (tester) async {
    app.main();
    await tester.pumpAndSettle();
    expect(find.text('Delivering opportunities, a brighter tomorrow'), findsOneWidget);
    expect(find.text('Go online'), findsOneWidget);
  });
}
