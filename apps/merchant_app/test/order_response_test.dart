import 'dart:convert';
import 'dart:typed_data';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_core/flutter_core.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:merchant_app/main.dart' as app;

class OrderAdapter implements HttpClientAdapter {
  @override void close({bool force = false}) {}
  @override Future<ResponseBody> fetch(RequestOptions options,
      Stream<Uint8List>? requestStream, Future<void>? cancelFuture) async {
    final path = options.uri.path;
    final Object data = path.endsWith('/catalog') ? {'items': [
      {'name': 'QA meal', 'variant_name': 'Regular', 'currency': 'XTS',
       'unit_price': '10.00', 'unit': 'each', 'on_hand': '10.0000', 'reserved': '2.0000'},
    ]} : path.endsWith('/categories') ? {'items': []} : {
      'id': 'child-1', 'status': 'pending', 'version': 1, 'currency': 'XTS', 'total': '20.00',
      'created_at': '2026-10-27T12:00:00Z', 'customer': {'display_name': 'QA customer'},
      'fulfillment': [], 'items': [
        {'product_name': 'QA meal', 'variant_name': 'Regular', 'quantity': '2', 'unit': 'each',
         'unit_price': '10.00', 'total': '20.00', 'preparation_notes': 'Mild please',
         'addons': [{'name': 'Extra portion', 'quantity': 1}]},
      ],
    };
    return ResponseBody.fromString(jsonEncode(data), 200,
      headers: {Headers.contentTypeHeader: ['application/json']});
  }
}

void main() {
  Future<void> show(WidgetTester tester, Widget screen) async {
    app.selectedBranchStore.value = {'id': 'shop-1'};
    final api = Dio()..httpClientAdapter = OrderAdapter();
    await tester.pumpWidget(ProviderScope(overrides: [
      app.transportProvider.overrideWithValue(api),
    ], child: MaterialApp(home: Scaffold(body: screen))));
    await tester.pumpAndSettle();
  }
  testWidgets('merchant stock uses on-hand minus reserved from its actual contract', (tester) async {
    await show(tester, const app.MenuManagementScreen());
    expect(find.text('XTS 10.00 · 8 each available'), findsOneWidget);
    expect(find.textContaining('null'), findsNothing);
    expect(tester.takeException(), isNull);
  });
  testWidgets('restaurant displays customer notes and extras from order response', (tester) async {
    await show(tester, const app.MerchantOrderScreen(id: 'child-1'));
    expect(find.text('QA customer'), findsOneWidget);
    expect(find.textContaining('Notes: Mild please'), findsOneWidget);
    expect(find.textContaining('Extras: 1 × Extra portion'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
