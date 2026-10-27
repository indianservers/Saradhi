import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_core/flutter_core.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:merchant_app/main.dart' as app;

class MerchantAdapter implements HttpClientAdapter {
  @override
  void close({bool force = false}) {}
  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    final data = options.uri.path == '/api/v1/merchant/branches'
        ? {
            'items': [
              {
                'id': 'shop-1',
                'name':
                    'A very long restaurant branch name that must fit on a phone',
                'status': 'approved',
                'accepting_orders': true,
                'version': 1,
              },
            ],
          }
        : {'items': []};
    return ResponseBody.fromString(
      jsonEncode(data),
      200,
      headers: {
        Headers.contentTypeHeader: ['application/json'],
      },
    );
  }
}

void main() {
  testWidgets(
    'restaurant dashboard tiles have one flex parent and fit phone width',
    (tester) async {
      tester.view.physicalSize = const Size(393, 852);
      tester.view.devicePixelRatio = 1;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);
      TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
          .setMockMethodCallHandler(
            const MethodChannel('plugins.it_nomads.com/flutter_secure_storage'),
            (call) async => call.method == 'read' ? 'test-token' : null,
          );
      final api = Dio()..httpClientAdapter = MerchantAdapter();
      await tester.pumpWidget(
        ProviderScope(
          overrides: [app.transportProvider.overrideWithValue(api)],
          child: const MaterialApp(
            home: Scaffold(body: app.MerchantDashboardScreen()),
          ),
        ),
      );
      await tester.pumpAndSettle();
      expect(find.text('Active'), findsOneWidget);
      expect(find.text('Preparing'), findsOneWidget);
      expect(tester.takeException(), isNull);
      await tester.scrollUntilVisible(
        find.text('Kitchen display'),
        150,
        scrollable: find.byType(Scrollable).first,
      );
      await tester.pumpAndSettle();
      expect(find.text('Kitchen display'), findsOneWidget);
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
    },
  );
}
