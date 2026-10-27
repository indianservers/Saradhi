import 'package:dio/dio.dart';
import 'package:flutter_networking/flutter_networking.dart';

/// Recover after app storage was cleared or another device advanced this pilot's
/// sequence. The GPS observation timestamp is never altered or fabricated.
Future<Map<String, dynamic>> uploadPilotPosition(
  Dio api,
  SecureTokenStore store,
  Map<String, dynamic> sample,
) async {
  const key = 'pilot_location_sequence';
  final previous = int.tryParse(await store.readValue(key) ?? '') ?? 0;
  var sequence = previous + 1;
  Future<Map<String, dynamic>> send() async {
    final response = await api.post(
      '/api/v1/pilots/me/location',
      data: {...sample, 'client_sequence': sequence},
    );
    return Map<String, dynamic>.from(response.data);
  }

  var result = await send();
  final serverSequence = result['sequence'];
  if (result['accepted'] != true &&
      result['reason'] == 'out_of_order' &&
      serverSequence is int &&
      serverSequence >= sequence) {
    await store.writeValue(key, '$serverSequence');
    sequence = serverSequence + 1;
    result = await send();
  }
  if (result['accepted'] == true) await store.writeValue(key, '$sequence');
  return result;
}
