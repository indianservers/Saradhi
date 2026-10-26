import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

abstract interface class TokenStore {
  Future<String?> accessToken();
  Future<void> clear();
}

class SecureTokenStore implements TokenStore {
  final FlutterSecureStorage _storage = const FlutterSecureStorage();
  @override
  Future<String?> accessToken() => _storage.read(key: 'qb_access');
  @override
  Future<void> clear() async {
    await _storage.delete(key: 'qb_access');
    await _storage.delete(key: 'qb_refresh');
  }
}

Dio createTransport(TokenStore tokens) {
  const base = String.fromEnvironment('API_BASE_URL', defaultValue: 'http://localhost:8000');
  const environment = String.fromEnvironment('APP_ENV', defaultValue: 'development');
  if (environment == 'production' && Uri.parse(base).scheme != 'https') {
    throw StateError('Production API requires HTTPS');
  }
  final dio = Dio(BaseOptions(baseUrl: base, connectTimeout: const Duration(seconds: 5),
      receiveTimeout: const Duration(seconds: 10)));
  dio.interceptors.add(InterceptorsWrapper(onRequest: (options, handler) async {
    final token = await tokens.accessToken();
    if (token != null) options.headers['Authorization'] = 'Bearer $token';
    // API supplies a cryptographically random request ID if absent.
    handler.next(options);
  }));
  return dio;
}
