import 'dart:convert';
import 'dart:typed_data';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_core/flutter_core.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pilot_app/main.dart' as app;

class ConsentAdapter implements HttpClientAdapter {
  bool consent = true;
  int revocations = 0;
  @override
  void close({bool force = false}) {}
  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    if (options.method == 'POST') {
      expect(options.data['accepted'], false);
      consent = false;
      revocations++;
    }
    return ResponseBody.fromString(
      jsonEncode({
        'verified': true,
        'state': 'offline',
        'vehicle_type': 'bike',
        'location_consent': consent,
      }),
      200,
      headers: {
        Headers.contentTypeHeader: ['application/json'],
      },
    );
  }
}

void main() {
  testWidgets('partner can cancel or confirm location consent revocation', (
    tester,
  ) async {
    final adapter = ConsentAdapter();
    final api = Dio(BaseOptions(baseUrl: 'http://qa.test'))
      ..transformer = SyncTransformer()
      ..httpClientAdapter = adapter;
    await tester.pumpWidget(
      ProviderScope(
        overrides: [app.transportProvider.overrideWithValue(api)],
        child: const MaterialApp(
          home: Scaffold(body: app.PilotProfileScreen()),
        ),
      ),
    );
    await tester.pumpAndSettle();
    await tester.tap(find.text('Stop location sharing'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Keep sharing'));
    await tester.pumpAndSettle();
    expect(adapter.revocations, 0);
    await tester.tap(find.text('Stop location sharing'));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Stop sharing'));
    await tester.pumpAndSettle();
    expect(adapter.revocations, 1);
    expect(find.text('Stop location sharing'), findsNothing);
    expect(app.pilotProfileStore.value?['location_consent'], false);
    expect(find.text('Location permission settings'), findsOneWidget);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
  });
}
