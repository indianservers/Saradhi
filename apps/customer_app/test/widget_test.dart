import 'package:flutter_test/flutter_test.dart';
import 'package:customer_app/main.dart' as app;

void main() {
  testWidgets('customer shell renders live discovery states without fixture merchants', (tester) async {
    app.main();
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 100));
    expect(find.text('Top merchants near you'), findsOneWidget);
    expect(find.text('Deliver to'), findsOneWidget);
    expect(find.text('Cravings? We’ll be there.'), findsOneWidget);
    expect(find.text('Burger Bliss'), findsNothing);
  });
}
