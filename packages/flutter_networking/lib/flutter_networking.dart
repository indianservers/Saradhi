import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

abstract interface class TokenStore {
  Future<String?> accessToken();
  Future<String?> refreshToken();
  Future<void> saveTokens(String access, String refresh);
  Future<void> clear();
}

class SecureTokenStore implements TokenStore {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  @override
  Future<String?> accessToken() => _storage.read(key: 'qb_access');
  @override
  Future<String?> refreshToken() => _storage.read(key: 'qb_refresh');
  @override
  Future<void> saveTokens(String access, String refresh) async {
    await _storage.write(key: 'qb_access', value: access);
    await _storage.write(key: 'qb_refresh', value: refresh);
  }
  Future<String?> readValue(String key) => _storage.read(key: key);
  Future<void> writeValue(String key, String value) => _storage.write(key: key, value: value);
  Future<void> deleteValue(String key) => _storage.delete(key: key);
  @override
  Future<void> clear() async {
    await _storage.delete(key: 'qb_access');
    await _storage.delete(key: 'qb_refresh');
  }
}

Dio createTransport(TokenStore tokens) {
  const configuredBase = String.fromEnvironment('API_BASE_URL');
  final base = configuredBase.isNotEmpty ? configuredBase :
      (Platform.isAndroid ? 'http://10.0.2.2:8000' : 'http://localhost:8000');
  const environment = String.fromEnvironment('APP_ENV', defaultValue: 'development');
  if (environment == 'production' && Uri.parse(base).scheme != 'https') {
    throw StateError('Production API requires HTTPS');
  }
  final dio = Dio(BaseOptions(baseUrl: base, connectTimeout: const Duration(seconds: 5),
      receiveTimeout: const Duration(seconds: 10)));
  Future<String?>? refreshInFlight;
  dio.interceptors.add(InterceptorsWrapper(onRequest: (options, handler) async {
    final token = await tokens.accessToken();
    if (token != null) options.headers['Authorization'] = 'Bearer $token';
    // API supplies a cryptographically random request ID if absent.
    handler.next(options);
  }, onError: (error, handler) async {
    final request = error.requestOptions;
    if (error.response?.statusCode != 401 || request.extra['qb_retried'] == true ||
        request.path.contains('/auth/')) {
      handler.next(error);
      return;
    }
    try {
      final refresh = await tokens.refreshToken();
      if (refresh == null) {
        await tokens.clear();
        handler.next(error);
        return;
      }
      refreshInFlight ??= () async {
        try {
          final auth = Dio(BaseOptions(baseUrl: base, connectTimeout: const Duration(seconds: 5),
              receiveTimeout: const Duration(seconds: 10)));
          final response = await auth.post('/api/v1/auth/refresh', data: {'refresh_token': refresh});
          await tokens.saveTokens(response.data['access_token'] as String,
              response.data['refresh_token'] as String);
          return response.data['access_token'] as String;
        } catch (_) {
          await tokens.clear();
          return null;
        } finally {
          refreshInFlight = null;
        }
      }();
      final refreshed = await refreshInFlight!;
      if (refreshed == null) {
        handler.next(error);
        return;
      }
      request.extra['qb_retried'] = true;
      request.headers['Authorization'] = 'Bearer $refreshed';
      handler.resolve(await dio.fetch(request));
    } catch (_) {
      handler.next(error);
    }
  }));
  return dio;
}
