import 'dart:convert';
import 'dart:typed_data';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_core/flutter_core.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pilot_app/main.dart' as app;

class AssignmentAdapter implements HttpClientAdapter {
  @override
  void close({bool force = false}) {}
  @override
  Future<ResponseBody> fetch(RequestOptions options, Stream<Uint8List>? requestStream,
      Future<void>? cancelFuture) async {
    final profile = {'verified': true, 'state': 'offline', 'location_consent': false};
    final data = options.path.contains('assignments') ? {
      'items': [
        {'assignment_id': 'offer-1', 'order_reference': 'QA-001',
          'merchant_name': 'QA Kitchen', 'assignment_status': 'offered'},
        {'assignment_id': 'active-1', 'order_reference': 'QA-002',
          'merchant_name': 'QA Market', 'assignment_status': 'accepted'},
      ],
    } : profile;
    return ResponseBody.fromString(jsonEncode(data), 200,
      headers: {Headers.contentTypeHeader: ['application/json']});
  }
}

void main() {
  testWidgets('dashboard renders offered and accepted assignments', (tester) async {
    final api = Dio()..httpClientAdapter = AssignmentAdapter();
    await tester.pumpWidget(ProviderScope(overrides: [
      app.transportProvider.overrideWithValue(api),
    ], child: const MaterialApp(home: Scaffold(body: app.PilotDashboardScreen()))));
    await tester.pumpAndSettle();
    expect(find.text('Order QA-001'), findsOneWidget);
    expect(find.text('Order QA-002'), findsOneWidget);
    expect(find.text('QA Kitchen'), findsOneWidget);
    expect(find.text('OFFERED'), findsOneWidget);
    expect(find.text('ACCEPTED'), findsOneWidget);
    expect(tester.takeException(), isNull);
  });
}
