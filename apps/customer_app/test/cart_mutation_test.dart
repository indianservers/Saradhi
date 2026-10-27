import 'dart:async';
import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_core/flutter_core.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:customer_app/main.dart' as app;

class CartAdapter implements HttpClientAdapter {
  final release = Completer<void>();
  int writes = 0, quantity = 1;
  final requests = <String>[];
  @override
  void close({bool force = false}) {}
  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    requests.add('${options.method} ${options.path}');
    if (options.method == 'PATCH') {
      writes++;
      await release.future;
      quantity = 2;
    }
    final data = options.uri.path.endsWith('/items')
        ? {
            'items': [
              {
                'id': 'line-1',
                'branch_id': 'shop-1',
                'branch_name': 'QA restaurant',
                'product_name': 'QA meal',
                'variant_name': 'Regular',
                'quantity': quantity.toString(),
                'delivery_method': 'pickup',
              },
            ],
          }
        : {'version': quantity};
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
  testWidgets('rapid quantity taps issue one version-checked write', (
    tester,
  ) async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.it_nomads.com/flutter_secure_storage'),
          (_) async => 'test-token',
        );
    app.cartIdStore.value = 'cart-1';
    final adapter = CartAdapter();
    final api = Dio(BaseOptions(baseUrl: 'http://qa.test'))
      ..httpClientAdapter = adapter;
    api.transformer = SyncTransformer();
    await tester.pumpWidget(
      ProviderScope(
        overrides: [app.transportProvider.overrideWithValue(api)],
        child: const MaterialApp(home: Scaffold(body: app.CartScreen())),
      ),
    );
    await tester.pumpAndSettle();
    expect(find.text('Qty 1'), findsOneWidget);
    final increase = tester
        .widget<IconButton>(
          find.widgetWithIcon(IconButton, Icons.add_circle_outline),
        )
        .onPressed!;
    increase();
    increase();
    await tester.pump();
    await tester.runAsync(() async {
      await Future<void>.delayed(const Duration(milliseconds: 30));
    });
    for (var i = 0; i < 20 && adapter.writes == 0; i++) {
      await tester.pump(const Duration(milliseconds: 100));
    }
    expect(
      adapter.writes,
      1,
      reason:
          '${adapter.requests} / ${tester.widgetList<Text>(find.byType(Text)).map((t) => t.data).toList()}',
    );
    expect(
      tester
          .widget<IconButton>(
            find.widgetWithIcon(IconButton, Icons.delete_outline),
          )
          .onPressed,
      isNull,
    );
    adapter.release.complete();
    await tester.pumpAndSettle();
    expect(find.text('Qty 2'), findsOneWidget);
    expect(app.cartCountStore.value, 2);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox.shrink());
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('plugins.it_nomads.com/flutter_secure_storage'),
          null,
        );
  });
}
