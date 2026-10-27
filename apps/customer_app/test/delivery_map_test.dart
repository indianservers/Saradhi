import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:customer_app/delivery_map.dart';

class TestTiles extends TileProvider {
  @override
  ImageProvider getImage(
    TileCoordinates coordinates,
    TileLayer options,
  ) => MemoryImage(
    base64Decode(
      'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=',
    ),
  );
}

void main() {
  for (final invalid in ['NaN', 'Infinity', '91', '-91', '', 'bad']) {
    testWidgets('invalid partner latitude $invalid cannot crash the map', (
      tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: DeliveryPartnerMap(
              location: {'latitude': invalid, 'longitude': '78.4867'},
            ),
          ),
        ),
      );
      expect(find.text('Partner location unavailable'), findsOneWidget);
      expect(find.byType(FlutterMap), findsNothing);
      expect(tester.takeException(), isNull);
    });
  }
  testWidgets('expired partner position is hidden during a reconnect', (tester) async {
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: DeliveryPartnerMap(
      location: {'latitude': '17.385', 'longitude': '78.4867',
        'valid_until': DateTime.now().subtract(const Duration(seconds: 1)).toIso8601String()},
    ))));
    expect(find.text('Waiting for a fresh partner location'), findsOneWidget);
    expect(find.byType(FlutterMap), findsNothing);
    expect(tester.takeException(), isNull);
  });
  testWidgets(
    'live updates move the partner marker without recreating the map',
    (tester) async {
      final tiles = TestTiles();
      Widget screen(String latitude) => MaterialApp(
        home: Scaffold(
          body: DeliveryPartnerMap(
            location: {'latitude': latitude, 'longitude': '78.4867'},
            tileProvider: tiles,
          ),
        ),
      );
      await tester.pumpWidget(screen('17.385'));
      await tester.pumpAndSettle();
      final initial = tester.state(find.byType(FlutterMap));
      expect(find.byTooltip('Delivery partner'), findsOneWidget);
      await tester.pumpWidget(screen('17.386'));
      await tester.pumpAndSettle();
      expect(identical(initial, tester.state(find.byType(FlutterMap))), true);
      final map = tester.widget<FlutterMap>(find.byType(FlutterMap));
      expect(
        map.mapController!.camera.center.latitude,
        closeTo(17.386, .000001),
      );
      expect(tester.takeException(), isNull);
      await tester.pumpWidget(const SizedBox.shrink());
    },
  );
}
