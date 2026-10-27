import 'dart:convert';
import 'dart:typed_data';
import 'package:dio/dio.dart';
import 'package:flutter_networking/flutter_networking.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:pilot_app/location_sender.dart';

class SequenceStore extends SecureTokenStore {
  String? value;
  @override
  Future<String?> readValue(String key) async => value;
  @override
  Future<void> writeValue(String key, String value) async {
    this.value = value;
  }
}

class LocationAdapter implements HttpClientAdapter {
  LocationAdapter(this.serverSequence, {this.staleTime = false});
  final int serverSequence;
  final bool staleTime;
  final samples = <Map<String, dynamic>>[];
  @override
  void close({bool force = false}) {}
  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    final sample = Map<String, dynamic>.from(options.data);
    samples.add(sample);
    final accepted = !staleTime && sample['client_sequence'] > serverSequence;
    return ResponseBody.fromString(
      jsonEncode({
        'accepted': accepted,
        'reason': accepted ? null : 'out_of_order',
        'sequence': accepted ? sample['client_sequence'] : serverSequence,
      }),
      200,
      headers: {
        Headers.contentTypeHeader: ['application/json'],
      },
    );
  }
}

void main() {
  test(
    'cleared storage resynchronizes sequence and retries the same GPS sample once',
    () async {
      final store = SequenceStore();
      final adapter = LocationAdapter(17);
      final api = Dio(BaseOptions(baseUrl: 'http://qa.test'))
        ..httpClientAdapter = adapter;
      final result = await uploadPilotPosition(api, store, {
        'observed_at': '2026-10-27T12:00:00Z',
      });
      expect(result['accepted'], true);
      expect(adapter.samples.map((s) => s['client_sequence']).toList(), [
        1,
        18,
      ]);
      expect(
        adapter.samples[0]['observed_at'],
        adapter.samples[1]['observed_at'],
      );
      expect(store.value, '18');
    },
  );
  test(
    'stale observation cannot create a retry loop or a fabricated timestamp',
    () async {
      final store = SequenceStore()..value = '20';
      final adapter = LocationAdapter(19, staleTime: true);
      final api = Dio(BaseOptions(baseUrl: 'http://qa.test'))
        ..httpClientAdapter = adapter;
      final result = await uploadPilotPosition(api, store, {
        'observed_at': '2026-10-27T11:00:00Z',
      });
      expect(result['accepted'], false);
      expect(adapter.samples.length, 1);
      expect(store.value, '20');
    },
  );
}
