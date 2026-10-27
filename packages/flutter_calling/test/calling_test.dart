import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_calling/flutter_calling.dart';
import 'package:flutter_networking/flutter_networking.dart';
import 'package:flutter_test/flutter_test.dart';

class Tokens implements TokenStore {
  @override
  Future<String?> accessToken() async => 'qa-token';
  @override
  Future<String?> refreshToken() async => null;
  @override
  Future<void> saveTokens(String access, String refresh) async {}
  @override
  Future<void> clear() async {}
}

class SignalingAdapter implements HttpClientAdapter {
  final List<RequestOptions> requests = [];
  bool ended = false;
  final incoming = {
    'id': 'qa-call',
    'delivery_id': 'qa-delivery',
    'status': 'ringing',
    'incoming': true,
  };
  @override
  void close({bool force = false}) {}
  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    requests.add(options);
    Object data = {};
    if (options.path.endsWith('/active'))
      data = {
        'items': ended ? [] : [incoming],
      };
    if (options.path.endsWith('/signals'))
      data = {'call': incoming, 'items': []};
    if (options.path.endsWith('/actions')) {
      ended = true;
      data = {...incoming, 'status': 'declined'};
    }
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
  testWidgets('incoming call can be declined without opening the microphone', (
    tester,
  ) async {
    final adapter = SignalingAdapter();
    final controller = DeliveryCallController(
      api: Dio()..httpClientAdapter = adapter,
      tokens: Tokens(),
    );
    await tester.pumpWidget(
      MaterialApp(
        home: DeliveryCallOverlay(
          controller: controller,
          peerLabel: 'Customer',
          child: const Scaffold(body: Text('Delivery')),
        ),
      ),
    );
    for (var i = 0; i < 5; i++) {
      await tester.pump(const Duration(seconds: 1));
    }
    await tester.pump();
    expect(find.text('Answer'), findsOneWidget);
    expect(find.text('Customer'), findsOneWidget);
    await tester.tap(find.text('Decline'));
    await tester.pumpAndSettle();
    expect(controller.call, isNull);
    expect(adapter.ended, true);
    expect(
      adapter.requests
          .where((r) => r.path.endsWith('/actions'))
          .single
          .data['action'],
      'decline',
    );
    await tester.pumpWidget(const SizedBox());
    await tester.pumpAndSettle();
    controller.dispose();
  });

  testWidgets('active controls render above the root navigator', (
    tester,
  ) async {
    final controller = DeliveryCallController(
      api: Dio()..httpClientAdapter = SignalingAdapter(),
      tokens: Tokens(),
    );
    controller.call = {'id': 'qa-call', 'status': 'active', 'incoming': false};
    controller.status = 'Connected';
    controller.error = 'Call notice';
    await tester.pumpWidget(
      MaterialApp(
        builder: (context, child) => DeliveryCallOverlay(
          controller: controller,
          peerLabel: 'Customer',
          child: child!,
        ),
        home: const Scaffold(body: Text('Delivery')),
      ),
    );
    expect(find.byTooltip('Mute'), findsOneWidget);
    expect(find.byTooltip('Use speaker'), findsOneWidget);
    expect(find.byTooltip('Dismiss call message'), findsOneWidget);
    expect(tester.takeException(), isNull);
    await tester.pumpWidget(const SizedBox());
    await tester.pumpAndSettle();
    controller.dispose();
  });

  testWidgets('microphone denial does not ring the recipient', (tester) async {
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(const MethodChannel('FlutterWebRTC.Method'), (
          call,
        ) async {
          if (call.method == 'getUserMedia')
            throw PlatformException(code: 'NotAllowedError');
          return null;
        });
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger.setMockMethodCallHandler(
      const MethodChannel('quickbuddy/calling'), (call) async => call.method == 'requestMicrophone' ? false : null);
    final adapter = SignalingAdapter();
    final controller = DeliveryCallController(
      api: Dio()..httpClientAdapter = adapter,
      tokens: Tokens(),
    );
    await controller.startCall('qa-delivery');
    expect(controller.call, isNull);
    expect(controller.busy, false);
    expect(controller.error?.toLowerCase(), contains('microphone'));
    expect(adapter.requests, isEmpty);
    controller.dispose();
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMethodCallHandler(
          const MethodChannel('FlutterWebRTC.Method'),
          null,
        );
  });
}
