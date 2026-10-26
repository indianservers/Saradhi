import 'dart:async';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_core/flutter_core.dart';
import 'package:flutter_design_system/flutter_design_system.dart';
import 'package:flutter_networking/flutter_networking.dart';
import 'package:geolocator/geolocator.dart';
import 'package:go_router/go_router.dart';
import 'package:url_launcher/url_launcher.dart';

const previewMode = String.fromEnvironment('APP_ENV', defaultValue: 'development') != 'production';
final pilotTokenStore = SecureTokenStore();
final transportProvider = Provider((ref) => createTransport(pilotTokenStore));
final pilotProfileStore = ValueNotifier<Map<String, dynamic>?>(null);
final pilotLocationReporter = PilotLocationReporter();

final router = GoRouter(initialLocation: '/login', routes: [
  ShellRoute(builder: (context, state, child) => PilotShell(path: state.uri.path, child: child), routes: [
    GoRoute(path: '/login', builder: (_, __) => const PilotLoginScreen()),
    GoRoute(path: '/setup', builder: (_, __) => const PilotSetupScreen()),
    GoRoute(path: '/dashboard', builder: (_, __) => const PilotDashboardScreen()),
    GoRoute(path: '/requests', builder: (_, __) => const PilotRequestScreen()),
    GoRoute(path: '/pickup', builder: (_, __) => const PickupVerificationScreen()),
    GoRoute(path: '/routes', builder: (_, __) => const MultiStopScreen()),
    GoRoute(path: '/navigation', builder: (_, __) => const CustomerNavigationScreen()),
    GoRoute(path: '/complete', builder: (_, __) => const CompleteDeliveryScreen()),
    GoRoute(path: '/incident', builder: (_, __) => const PilotIncidentScreen()),
    GoRoute(path: '/earnings', builder: (_, __) => const PilotEarningsScreen()),
    GoRoute(path: '/operations', builder: (_, __) => const PilotOperationsScreen()),
    GoRoute(path: '/profile', builder: (_, __) => const PilotProfileScreen()),
  ]),
]);

void main() => runApp(ProviderScope(child: QuickbuddyApp(
  title: 'Quickbuddy Pilot', theme: quickbuddyTheme(), router: router,
)));

List<Map<String, dynamic>> _rows(dynamic response) {
  final items = response is Map ? response['items'] : null;
  return items is List ? items.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList() : [];
}

String _error(Object error) {
  if (error is DioException) {
    final body = error.response?.data;
    if (body is Map && body['error'] is Map && body['error']['message'] is String) {
      return body['error']['message'] as String;
    }
    if (error.response?.statusCode == 401) return 'Your session expired. Sign in again.';
    return error.message ?? 'The service is temporarily unavailable.';
  }
  return error.toString();
}

void _toast(BuildContext context, String message) => ScaffoldMessenger.of(context)
  ..hideCurrentSnackBar()
  ..showSnackBar(SnackBar(content: Text(message)));

class PilotLocationReporter with WidgetsBindingObserver {
  StreamSubscription<Position>? _subscription;
  bool _sending = false;
  bool _started = false;
  bool _foreground = true;
  bool _activeWork = false;
  Dio? _api;
  String? lastError;

  Future<void> start(Dio api, {bool activeWork = false}) async {
    if (_started) {
      if (_activeWork != activeWork) {
        _activeWork = activeWork;
        await _subscription?.cancel();
        _listen(api);
      }
      return;
    }
    if (!await Geolocator.isLocationServiceEnabled()) {
      throw StateError('Turn on device location before going online.');
    }
    var permission = await Geolocator.checkPermission();
    if (permission == LocationPermission.denied) permission = await Geolocator.requestPermission();
    if (permission == LocationPermission.denied || permission == LocationPermission.deniedForever) {
      throw StateError('Location permission is required while you are online.');
    }
    _api = api;
    _foreground = true;
    WidgetsBinding.instance.addObserver(this);
    final first = await Geolocator.getCurrentPosition(
      locationSettings: const LocationSettings(accuracy: LocationAccuracy.high),
    );
    await _send(api, first);
    _started = true;
    _activeWork = activeWork;
    _listen(api);
  }

  void _listen(Dio api) {
    _subscription = Geolocator.getPositionStream(
      locationSettings: LocationSettings(
        accuracy: _activeWork ? LocationAccuracy.high : LocationAccuracy.medium,
        distanceFilter: _activeWork ? 25 : 100,
      ),
    ).listen((position) => unawaited(_send(api, position)));
  }

  Future<void> _send(Dio api, Position position) async {
    if (!_foreground) return;
    if (position.accuracy > 100) {
      lastError = 'Waiting for a more accurate GPS reading.';
      return;
    }
    if (_sending) return;
    _sending = true;
    try {
      final previous = int.tryParse(await pilotTokenStore.readValue('pilot_location_sequence') ?? '') ?? 0;
      final sequence = previous + 1;
      final result = await api.post('/api/v1/pilots/me/location', data: {
        'latitude': position.latitude.toStringAsFixed(7),
        'longitude': position.longitude.toStringAsFixed(7),
        'observed_at': position.timestamp.toUtc().toIso8601String(),
        'accuracy_m': position.accuracy.toStringAsFixed(2),
        'heading_degrees': position.heading >= 0 ? position.heading.toStringAsFixed(2) : null,
        'speed_mps': position.speed >= 0 ? position.speed.toStringAsFixed(2) : null,
        'client_sequence': sequence,
        'app_state': 'foreground',
      });
      if (result.data is Map && result.data['accepted'] == true) {
        await pilotTokenStore.writeValue('pilot_location_sequence', '$sequence');
        lastError = null;
      } else {
        lastError = 'The backend ignored an out-of-order or low-quality location sample.';
      }
    } catch (e) {
      lastError = _error(e);
    } finally {
      _sending = false;
    }
  }

  Future<void> stop() async {
    await _subscription?.cancel();
    _subscription = null;
    _started = false;
    _activeWork = false;
    _api = null;
    WidgetsBinding.instance.removeObserver(this);
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    _foreground = state == AppLifecycleState.resumed;
    final api = _api;
    if (_foreground && _started && api != null) {
      unawaited(() async {
        try {
          final position = await Geolocator.getCurrentPosition(
            locationSettings: const LocationSettings(accuracy: LocationAccuracy.high),
          );
          await _send(api, position);
        } catch (error) { lastError = _error(error); }
      }());
    }
  }
}

class PilotShell extends StatelessWidget {
  const PilotShell({super.key, required this.path, required this.child});
  final String path;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final login = path == '/login' || path == '/setup';
    final selected = path == '/earnings' ? 3 : path == '/profile' ? 4 :
        path == '/requests' || path == '/pickup' || path == '/complete' ? 1 :
        path == '/routes' || path == '/navigation' ? 2 : 0;
    return Scaffold(
      body: SafeArea(child: child),
      bottomNavigationBar: login ? null : NavigationBar(
        height: 64,
        selectedIndex: selected,
        backgroundColor: Colors.white,
        indicatorColor: QuickbuddyColors.orange.withValues(alpha: .1),
        onDestinationSelected: (i) => context.go(switch (i) {
          1 => '/requests', 2 => '/routes', 3 => '/earnings', 4 => '/profile', _ => '/dashboard',
        }),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.receipt_long_outlined), label: 'Work'),
          NavigationDestination(icon: Icon(Icons.map_outlined), label: 'Route'),
          NavigationDestination(icon: Icon(Icons.account_balance_wallet_outlined), label: 'Earnings'),
          NavigationDestination(icon: Icon(Icons.person_outline), label: 'Profile'),
        ],
      ),
    );
  }
}

class PilotLoginScreen extends ConsumerStatefulWidget {
  const PilotLoginScreen({super.key});
  @override ConsumerState<PilotLoginScreen> createState() => _PilotLoginScreenState();
}

class _PilotLoginScreenState extends ConsumerState<PilotLoginScreen> {
  final email = TextEditingController();
  final password = TextEditingController();
  bool busy = false, createAccount = false;
  String? error;

  @override
  void initState() { super.initState(); WidgetsBinding.instance.addPostFrameCallback((_) => _restore()); }
  @override
  void dispose() { email.dispose(); password.dispose(); super.dispose(); }

  Future<void> _restore() async {
    if (await pilotTokenStore.accessToken() == null || !mounted) return;
    try {
      final result = await ref.read(transportProvider).get('/api/v1/pilots/me');
      pilotProfileStore.value = Map<String, dynamic>.from(result.data);
      if (mounted) context.go('/dashboard');
    } on DioException catch (e) {
      if (e.response?.statusCode == 403 && mounted) context.go('/setup');
    }
  }

  Future<void> _submit() async {
    if (busy || email.text.trim().isEmpty || password.text.isEmpty) return;
    setState(() { busy = true; error = null; });
    final api = ref.read(transportProvider);
    try {
      if (createAccount) {
        await api.post('/api/v1/auth/register', data: {
          'email': email.text.trim(), 'password': password.text,
        });
      }
      final response = await api.post('/api/v1/auth/login', data: {
        'email': email.text.trim(), 'password': password.text,
      });
      await pilotTokenStore.saveTokens(
        response.data['access_token'] as String,
        response.data['refresh_token'] as String,
      );
      try {
        final profile = await api.get('/api/v1/pilots/me');
        pilotProfileStore.value = Map<String, dynamic>.from(profile.data);
        if (mounted) context.go('/dashboard');
      } on DioException catch (e) {
        if (e.response?.statusCode == 403 && mounted) context.go('/setup') else rethrow;
      }
    } catch (e) { if (mounted) setState(() => error = _error(e)); }
    finally { if (mounted) setState(() => busy = false); }
  }

  @override
  Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(18), children: [
    const Center(child: QbBrand(pilot: true)),
    const SizedBox(height: 22),
    const Text('Your deliveries, in one place', style: TextStyle(
      color: QuickbuddyColors.indigo, fontSize: 22, fontWeight: FontWeight.w800,
    )),
    const SizedBox(height: 6),
    const Text('Sign in to view assignments and manage your pilot availability.'),
    if (previewMode) const QbPreviewNotice(message: 'Use a registered Quickbuddy account. Pilot approval is required before going online.'),
    const SizedBox(height: 14),
    TextField(controller: email, keyboardType: TextInputType.emailAddress,
      decoration: const InputDecoration(labelText: 'Email', prefixIcon: Icon(Icons.email_outlined))),
    const SizedBox(height: 10),
    TextField(controller: password, obscureText: true,
      decoration: const InputDecoration(labelText: 'Password', prefixIcon: Icon(Icons.lock_outline))),
    if (error != null) _Notice(error!),
    const SizedBox(height: 14),
    QbPrimaryButton(label: busy ? 'Connecting…' : createAccount ? 'Create account' : 'Sign in',
      icon: Icons.login, enabled: !busy, onPressed: _submit),
    TextButton(onPressed: busy ? null : () => setState(() => createAccount = !createAccount),
      child: Text(createAccount ? 'Already registered? Sign in' : 'New to Quickbuddy? Create an account')),
  ]);
}

class PilotSetupScreen extends ConsumerStatefulWidget {
  const PilotSetupScreen({super.key});
  @override ConsumerState<PilotSetupScreen> createState() => _PilotSetupScreenState();
}

class _PilotSetupScreenState extends ConsumerState<PilotSetupScreen> {
  List<Map<String, dynamic>> cities = [];
  String? cityId, error;
  bool loading = true, busy = false;
  @override
  void initState() { super.initState(); _loadCities(); }
  Future<void> _loadCities() async {
    try {
      final result = await ref.read(transportProvider).get('/api/v1/geo/cities?limit=100');
      if (mounted) setState(() { cities = _rows(result.data); cityId = cities.isEmpty ? null : cities.first['id'] as String; loading = false; });
    } catch (e) { if (mounted) setState(() { error = _error(e); loading = false; }); }
  }
  Future<void> _create() async {
    if (cityId == null || busy) return;
    setState(() { busy = true; error = null; });
    try {
      await ref.read(transportProvider).post('/api/v1/pilots', data: {'city_id': cityId});
      final profile = await ref.read(transportProvider).get('/api/v1/pilots/me');
      pilotProfileStore.value = Map<String, dynamic>.from(profile.data);
      if (mounted) context.go('/dashboard');
    } catch (e) { if (mounted) setState(() => error = _error(e)); }
    finally { if (mounted) setState(() => busy = false); }
  }
  @override
  Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(18), children: [
    const Center(child: QbBrand(pilot: true)), const SizedBox(height: 20),
    const _ScreenTitle('Pilot profile setup', 'Choose the city where you will operate'),
    const QbPreviewNotice(message: 'The current shared API only collects a city. It does not yet support KYC documents, vehicle registration, emergency contact, or payout details.'),
    if (loading) const Center(child: CircularProgressIndicator()) else if (cities.isEmpty)
      const _Notice('No active cities are configured. Contact Quickbuddy operations.')
    else DropdownButtonFormField<String>(initialValue: cityId,
      decoration: const InputDecoration(labelText: 'Operating city'),
      items: cities.map((city) => DropdownMenuItem(value: city['id'] as String,
        child: Text('${city['name']}'))).toList(), onChanged: (v) => setState(() => cityId = v)),
    if (error != null) _Notice(error!),
    const SizedBox(height: 12),
    QbPrimaryButton(label: busy ? 'Creating…' : 'Create pilot profile', icon: Icons.person_add_alt,
      enabled: !busy && cityId != null, onPressed: _create),
    TextButton(onPressed: () async { await pilotTokenStore.clear(); if (context.mounted) context.go('/login'); }, child: const Text('Sign out')),
  ]);
}

class PilotDashboardScreen extends ConsumerStatefulWidget {
  const PilotDashboardScreen({super.key});
  @override ConsumerState<PilotDashboardScreen> createState() => _PilotDashboardScreenState();
}

class _PilotDashboardScreenState extends ConsumerState<PilotDashboardScreen> {
  Map<String, dynamic>? profile;
  List<Map<String, dynamic>> assignments = [];
  bool loading = true, busy = false;
  String? error;
  @override void initState() { super.initState(); _load(); }

  Future<void> _load({bool silent = false}) async {
    try {
      final api = ref.read(transportProvider);
      final results = await Future.wait([
        api.get('/api/v1/pilots/me'), api.get('/api/v1/pilots/me/assignments?limit=50'),
      ]);
      if (!mounted) return;
      setState(() {
        profile = Map<String, dynamic>.from(results[0].data);
        pilotProfileStore.value = profile;
        assignments = _rows(results[1].data);
        loading = false; error = null;
      });
      if (profile?['state'] == 'online_available' || profile?['state'] == 'assigned') {
        final activeWork = assignments.any((a) => const {'accepted', 'picked_up'}.contains(a['assignment_status']));
        await pilotLocationReporter.start(api, activeWork: activeWork);
      }
    } catch (e) { if (mounted) setState(() { loading = false; error = _error(e); }); }
  }

  Future<void> _availability(bool online) async {
    if (busy) return;
    setState(() { busy = true; error = null; });
    final api = ref.read(transportProvider);
    try {
      if (online) {
        if (profile?['location_consent'] != true) {
          final accepted = await showDialog<bool>(context: context, builder: (ctx) => AlertDialog(
            title: const Text('Location while online'),
            content: const Text('Quickbuddy will send your foreground location while you are online so dispatch and active customers can see delivery progress. Tracking stops when you go offline. Background tracking is not enabled.'),
            actions: [TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Not now')),
              FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Agree and continue'))],
          ));
          if (accepted != true) return;
          await api.post('/api/v1/pilots/me/location-consent', data: {
            'accepted': true, 'policy_version': 'pilot-location-v1',
          });
        }
        await pilotLocationReporter.start(api);
      }
      await api.post('/api/v1/pilots/me/availability', data: {
        'state': online ? 'online_available' : 'offline',
      });
      if (!online) await pilotLocationReporter.stop();
      final result = await api.get('/api/v1/pilots/me');
      profile = Map<String, dynamic>.from(result.data);
      if (mounted) setState(() => pilotProfileStore.value = profile);
      await _load(silent: true);
    } catch (e) {
      if (online) await pilotLocationReporter.stop();
      if (mounted) setState(() => error = _error(e));
    } finally { if (mounted) setState(() => busy = false); }
  }

  @override
  Widget build(BuildContext context) {
    final state = profile?['state'] as String? ?? 'offline';
    final offers = assignments.where((a) => a['assignment_status'] == 'offered').length;
    final active = assignments.where((a) => const {'accepted', 'picked_up'}.contains(a['assignment_status'])).length;
    return RefreshIndicator(onRefresh: _load, child: ListView(padding: const EdgeInsets.all(16), children: [
      const _ScreenTitle('Pilot home', 'Your live Quickbuddy delivery workspace'),
      if (loading) const Center(child: CircularProgressIndicator()),
      if (error != null) _Notice(error!, action: TextButton(onPressed: _load, child: const Text('Retry'))),
      if (!loading && profile != null) ...[
        Card(child: SwitchListTile(value: state == 'online_available' || state == 'assigned',
          onChanged: busy || state == 'assigned' || profile?['verified'] != true ? null : _availability,
          activeThumbColor: QuickbuddyColors.green,
          title: Text(state == 'assigned' ? 'Working on an assignment' : state == 'offer_pending' ? 'Delivery offer pending' : state == 'online_available' ? 'You are online' : 'You are offline', style: const TextStyle(fontWeight: FontWeight.w800)),
          subtitle: Text(pilotLocationReporter.lastError ?? (profile?['verified'] == true ? 'Availability is confirmed by Quickbuddy' : 'Pilot approval is required before going online')),
          secondary: Icon(Icons.circle, size: 13, color: state == 'online_available' || state == 'assigned' ? QuickbuddyColors.green : QuickbuddyColors.muted))),
        const SizedBox(height: 10),
        _MetricStrip(items: [('Offers', '$offers'), ('Active deliveries', '$active'), ('Approval', profile?['verified'] == true ? 'Approved' : 'Pending')]),
        const SizedBox(height: 12),
        if (assignments.isNotEmpty) ...[
          const QbSectionTitle('Current work'),
          ...assignments.map((a) => _AssignmentCard(assignment: a, onOpen: () => context.go(a['assignment_status'] == 'offered' ? '/requests' : '/pickup'))),
        ] else const _UnavailablePanel('No offers or active deliveries right now.'),
        const SizedBox(height: 10),
        _QuickAction(icon: Icons.receipt_long, title: 'Delivery offers', subtitle: '$offers waiting', onTap: () => context.go('/requests')),
        _QuickAction(icon: Icons.map_outlined, title: 'Active route', subtitle: active == 0 ? 'No active route' : '$active assigned delivery(s)', onTap: () => context.go('/routes')),
        _QuickAction(icon: Icons.insights_outlined, title: 'Fleet outlook', subtitle: 'Your shift and authorized zone forecasts', onTap: () => context.go('/operations')),
        _QuickAction(icon: Icons.report_problem_outlined, title: 'Report an operational issue', subtitle: 'Safety, vehicle, road or delivery exception', onTap: () => context.go('/incident')),
      ],
    ]));
  }
}

class PilotRequestScreen extends ConsumerStatefulWidget {
  const PilotRequestScreen({super.key});
  @override ConsumerState<PilotRequestScreen> createState() => _PilotRequestScreenState();
}

class _PilotRequestScreenState extends ConsumerState<PilotRequestScreen> {
  List<Map<String, dynamic>> assignments = [];
  bool loading = true;
  String? error;
  Timer? timer;
  @override void initState() { super.initState(); _load(); timer = Timer.periodic(const Duration(seconds: 8), (_) => _load(silent: true)); }
  @override void dispose() { timer?.cancel(); super.dispose(); }
  Future<void> _load({bool silent = false}) async {
    try {
      final result = await ref.read(transportProvider).get('/api/v1/pilots/me/assignments?limit=50');
      if (mounted) setState(() { assignments = _rows(result.data).where((a) => a['assignment_status'] == 'offered').toList(); loading = false; error = null; });
    } catch (e) { if (mounted) setState(() { loading = false; error = _error(e); }); }
  }
  Future<void> _respond(Map<String, dynamic> assignment, bool accept) async {
    try {
      await ref.read(transportProvider).post('/api/v1/pilot-assignments/${assignment['assignment_id']}/${accept ? 'accept' : 'reject'}');
      await _load();
      if (accept && mounted) context.go('/pickup');
    } catch (e) { if (mounted) _toast(context, _error(e)); await _load(); }
  }
  @override
  Widget build(BuildContext context) {
    final offers = assignments.where((a) => DateTime.tryParse('${a['expires_at']}')?.isAfter(DateTime.now().toUtc()) ?? false).toList();
    return RefreshIndicator(onRefresh: _load, child: ListView(padding: const EdgeInsets.all(16), children: [
      const _ScreenTitle('Delivery offers', 'Only server-issued offers can be accepted'),
      if (error != null) _Notice(error!, action: TextButton(onPressed: _load, child: const Text('Retry'))),
      if (loading) const Center(child: CircularProgressIndicator())
      else if (offers.isEmpty) const _UnavailablePanel('No active offers. Pull to refresh or wait for dispatch.'),
      ...offers.map((a) => _OfferCard(assignment: a, onAccept: () => _respond(a, true), onReject: () => _respond(a, false))),
      const QbPreviewNotice(message: 'Offer expiry and assignment are checked by the backend. Estimated payout is not exposed by the current dispatch API and is not shown here.'),
    ]));
  }
}

class _OfferCard extends StatelessWidget {
  const _OfferCard({required this.assignment, required this.onAccept, required this.onReject});
  final Map<String, dynamic> assignment;
  final VoidCallback onAccept, onReject;
  @override
  Widget build(BuildContext context) {
    final expires = DateTime.tryParse('${assignment['expires_at']}')?.toLocal();
    final pickup = assignment['pickup'] as Map? ?? const {};
    return Card(child: Padding(padding: const EdgeInsets.all(14), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [Expanded(child: Text('Order ${assignment['order_reference']}', style: const TextStyle(fontWeight: FontWeight.w800))), const QbStatusChip('OFFER', tone: 'warning')]),
      const SizedBox(height: 8),
      Text('${assignment['merchant_name']} · ${assignment['merchant_type']}'),
      Text('Pickup: ${pickup['latitude']}, ${pickup['longitude']}', style: const TextStyle(fontSize: 11, color: QuickbuddyColors.muted)),
      Text('Expires ${expires == null ? 'soon' : TimeOfDay.fromDateTime(expires).format(context)} · customer address after acceptance', style: const TextStyle(fontSize: 11)),
      const SizedBox(height: 10),
      Row(children: [Expanded(child: OutlinedButton(onPressed: onReject, child: const Text('Decline'))), const SizedBox(width: 8), Expanded(child: FilledButton.icon(onPressed: onAccept, icon: const Icon(Icons.check), label: const Text('Accept')))]),
    ])));
  }
}

class PickupVerificationScreen extends ConsumerStatefulWidget {
  const PickupVerificationScreen({super.key});
  @override ConsumerState<PickupVerificationScreen> createState() => _PickupVerificationScreenState();
}

class _PickupVerificationScreenState extends ConsumerState<PickupVerificationScreen> {
  List<Map<String, dynamic>> assignments = [];
  bool loading = true;
  String? error;
  @override void initState() { super.initState(); _load(); }
  Future<void> _load() async {
    try {
      final result = await ref.read(transportProvider).get('/api/v1/pilots/me/assignments?limit=50');
      if (mounted) setState(() { assignments = _rows(result.data).where((a) => const {'accepted', 'picked_up'}.contains(a['assignment_status'])).toList(); loading = false; error = null; });
    } catch (e) { if (mounted) setState(() { loading = false; error = _error(e); }); }
  }
  Future<void> _pickup(Map<String, dynamic> assignment) async {
    if (assignment['merchant_order_status'] != 'ready') { _toast(context, 'Merchant preparation is not ready yet.'); return; }
    try {
      await ref.read(transportProvider).post('/api/v1/delivery-tasks/${assignment['delivery_task_id']}/pickup', data: {'expected_version': assignment['task_version']});
      await _load();
    } catch (e) { if (mounted) _toast(context, _error(e)); await _load(); }
  }
  @override
  Widget build(BuildContext context) => RefreshIndicator(onRefresh: _load, child: ListView(padding: const EdgeInsets.all(16), children: [
    const _ScreenTitle('Your deliveries', 'Pickup and recipient details from the assigned order'),
    if (error != null) _Notice(error!, action: TextButton(onPressed: _load, child: const Text('Retry'))),
    if (loading) const Center(child: CircularProgressIndicator()) else if (assignments.isEmpty) const _UnavailablePanel('No accepted deliveries. Check delivery offers.'),
    ...assignments.map((a) => _DeliveryCard(assignment: a, onPickup: () => _pickup(a), onRefresh: _load)),
  ]));
}

class _DeliveryCard extends StatelessWidget {
  const _DeliveryCard({required this.assignment, required this.onPickup, required this.onRefresh});
  final Map<String, dynamic> assignment;
  final VoidCallback onPickup;
  final Future<void> Function() onRefresh;
  @override
  Widget build(BuildContext context) {
    final pickup = assignment['pickup'] as Map? ?? const {};
    final dropoff = assignment['dropoff'] as Map?;
    final pickedUp = assignment['task_status'] == 'picked_up';
    final orderItems = assignment['order_items'] as List? ?? const [];
    return Card(child: Padding(padding: const EdgeInsets.all(14), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [Expanded(child: Text('Order ${assignment['order_reference']} · ${assignment['merchant_name']}', style: const TextStyle(fontWeight: FontWeight.w800))), QbStatusChip(assignment['task_status'].toString().toUpperCase(), tone: pickedUp ? 'success' : 'warning')]),
      const SizedBox(height: 6),
      Text('Pickup: ${pickup['name']} · ${pickup['latitude']}, ${pickup['longitude']}'),
      if (pickedUp) Text('Drop-off: ${dropoff?['address_text'] ?? dropoff?['label'] ?? 'Address unavailable'}'),
      ...orderItems.map((i) => Text('${i['quantity']} ${i['unit']} × ${i['name']} · ${i['variant']}', style: const TextStyle(fontSize: 12))),
      if (!pickedUp) Text(assignment['merchant_order_status'] == 'ready' ? 'Merchant order is ready for pickup.' : 'Waiting for merchant preparation.', style: const TextStyle(fontSize: 12, color: QuickbuddyColors.muted)),
      const SizedBox(height: 8),
      Wrap(spacing: 8, children: [
        OutlinedButton.icon(onPressed: () => _openMaps(pickup['latitude'], pickup['longitude']), icon: const Icon(Icons.navigation), label: const Text('Navigate to pickup')),
        if (!pickedUp) FilledButton.icon(onPressed: assignment['merchant_order_status'] == 'ready' ? onPickup : null, icon: const Icon(Icons.inventory_2_outlined), label: const Text('Confirm pickup')),
        if (pickedUp) OutlinedButton.icon(onPressed: () => context.go('/incident'), icon: const Icon(Icons.report_problem_outlined), label: const Text('Delivery issue')),
        if (pickedUp) OutlinedButton.icon(onPressed: () => _openMaps(dropoff?['latitude'], dropoff?['longitude']), icon: const Icon(Icons.navigation), label: const Text('Navigate to customer')),
      ]),
      if (pickedUp) const Text('Delivery completion requires recipient proof. The current backend has no pilot-side OTP/proof endpoint, so this app will not mark it delivered.', style: TextStyle(fontSize: 11, color: QuickbuddyColors.muted)),
      TextButton(onPressed: onRefresh, child: const Text('Refresh assignment')),
    ])));
  }
}

class MultiStopScreen extends ConsumerStatefulWidget {
  const MultiStopScreen({super.key});
  @override ConsumerState<MultiStopScreen> createState() => _MultiStopScreenState();
}

class _MultiStopScreenState extends ConsumerState<MultiStopScreen> {
  List<Map<String, dynamic>> assignments = [];
  final Map<String, Map<String, dynamic>> etaByTask = {};
  final Set<String> etaUnavailable = {};
  bool loading = true;
  @override void initState() { super.initState(); _load(); }
  Future<void> _load() async {
    try {
      final r = await ref.read(transportProvider).get('/api/v1/pilots/me/assignments?limit=50');
      final active = _rows(r.data).where((a) => const {'accepted', 'picked_up'}.contains(a['assignment_status'])).toList();
      if (!mounted) return;
      final nextTaskId = active.isEmpty ? null : '${active.first['delivery_task_id']}';
      setState(() { assignments = active; loading = false; etaByTask.clear(); etaUnavailable.clear(); });
      if (nextTaskId != null) await _loadEta(nextTaskId);
    } catch (_) { if (mounted) setState(() => loading = false); }
  }

  Future<void> _loadEta(String taskId) async {
    try {
      final eta = await ref.read(transportProvider).get('/api/v1/deliveries/$taskId/eta');
      if (mounted) setState(() => etaByTask[taskId] = Map<String, dynamic>.from(eta.data));
    } catch (_) {
      if (mounted) setState(() => etaUnavailable.add(taskId));
    }
  }

  Future<void> _primaryAction(Map<String, dynamic> a) async {
    final pickup = a['pickup'] as Map? ?? const {};
    final drop = a['dropoff'] as Map?;
    if (a['task_status'] == 'picked_up') {
      await _openMaps(drop?['latitude'], drop?['longitude']);
    } else if (a['merchant_order_status'] == 'ready') {
      try {
        await ref.read(transportProvider).post('/api/v1/delivery-tasks/${a['delivery_task_id']}/pickup', data: {'expected_version': a['task_version']});
        await _load();
      } catch (e) { if (mounted) _toast(context, _error(e)); await _load(); }
    } else {
      await _openMaps(pickup['latitude'], pickup['longitude']);
    }
  }
  @override
  Widget build(BuildContext context) => RefreshIndicator(onRefresh: _load, child: ListView(padding: const EdgeInsets.all(16), children: [
    const _ScreenTitle('Active route', 'Follow the next required stop'),
    if (loading) const Center(child: CircularProgressIndicator()) else if (assignments.isEmpty) const _UnavailablePanel('No active route.'),
    ...assignments.asMap().entries.map((entry) {
      final index = entry.key;
      final a = entry.value;
      final pickup = a['pickup'] as Map? ?? const {};
      final drop = a['dropoff'] as Map?;
      final id = '${a['delivery_task_id']}';
      final pickedUp = a['task_status'] == 'picked_up';
      final eta = etaByTask[id];
      final packageCount = (a['order_items'] as List? ?? const []).fold<int>(0, (sum, item) => sum + (int.tryParse('${(item as Map)['quantity']}') ?? 0));
      final destinationName = pickedUp ? (drop?['label'] ?? 'Customer drop-off') : pickup['name'];
      final etaTime = DateTime.tryParse('${eta?['delivery_at']}')?.toLocal();
      final distanceMeters = double.tryParse('${eta?['distance_m']}');
      final etaText = eta != null
          ? 'ETA ${etaTime == null ? 'unavailable' : TimeOfDay.fromDateTime(etaTime).format(context)} · ${eta['source']} (${eta['confidence']} confidence)${distanceMeters == null ? '' : ' · ${(distanceMeters / 1000).toStringAsFixed(1)} km'}'
          : etaUnavailable.contains(id) ? 'Road ETA unavailable; use the map provider estimate.' : 'No provider ETA requested for this stop.';
      return Card(child: Padding(padding: const EdgeInsets.all(14), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [Expanded(child: Text('Order ${a['order_reference']}', style: const TextStyle(fontWeight: FontWeight.w800))), QbStatusChip(pickedUp ? 'DELIVERY' : 'PICKUP', tone: pickedUp ? 'info' : 'warning')]),
        const SizedBox(height: 8),
        Text('Next stop · $destinationName', style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
        Text('$packageCount order line item(s) · ${a['merchant_name']} · $etaText', style: const TextStyle(fontSize: 11, color: QuickbuddyColors.muted)),
        if (eta == null && !etaUnavailable.contains(id)) Align(alignment: Alignment.centerLeft, child: TextButton(onPressed: () => _loadEta(id), child: const Text('Load ETA for this stop'))),
        const SizedBox(height: 10),
        SizedBox(width: double.infinity, child: FilledButton.icon(
          onPressed: () => _primaryAction(a),
          icon: Icon(pickedUp ? Icons.navigation : a['merchant_order_status'] == 'ready' ? Icons.inventory_2_outlined : Icons.navigation),
          label: Text(pickedUp ? 'Navigate to customer' : a['merchant_order_status'] == 'ready' ? 'Verify pickup' : 'Navigate to merchant'),
        )),
        ExpansionTile(
          tilePadding: EdgeInsets.zero,
          title: const Text('Remaining stops'),
          children: [
            _StopCard(number: '${index * 2 + 1}', type: 'Pickup', title: '${pickup['name']}', status: pickedUp ? 'Completed' : 'Next', onTap: () => _openMaps(pickup['latitude'], pickup['longitude'])),
            _StopCard(number: '${index * 2 + 2}', type: 'Drop-off', title: drop?['label'] ?? (drop?['address_text'] ?? 'Available after pickup'), status: pickedUp ? 'Next' : 'Waiting for pickup', onTap: () => _openMaps(drop?['latitude'], drop?['longitude'])),
          ],
        ),
      ])));
    }),
    const QbPreviewNotice(message: 'Stop numbers follow the server assignment list; they do not represent an optimized multi-order route. Batched assignments and configured road routing are not available. ETA is shown only when the backend routing provider returns a result.'),
  ]));
}

class PilotOperationsScreen extends ConsumerStatefulWidget {
  const PilotOperationsScreen({super.key});
  @override ConsumerState<PilotOperationsScreen> createState() => _PilotOperationsScreenState();
}

class _PilotOperationsScreenState extends ConsumerState<PilotOperationsScreen> {
  Map<String, dynamic>? operations, outlook;
  bool loading = true;
  String? error;
  @override void initState() { super.initState(); _load(); }
  Future<void> _load() async {
    try {
      final api = ref.read(transportProvider);
      final values = await Future.wait([api.get('/api/v1/pilots/me/operations'), api.get('/api/v1/pilots/me/supply-demand')]);
      if (mounted) setState(() { operations = Map<String, dynamic>.from(values[0].data); outlook = Map<String, dynamic>.from(values[1].data); loading = false; error = null; });
    } catch (e) { if (mounted) setState(() { loading = false; error = _error(e); }); }
  }
  @override Widget build(BuildContext context) {
    final capabilities = (operations?['capabilities'] as List? ?? const []).join(', ');
    final shift = operations?['shift'] as Map?;
    final signals = (outlook?['signals'] as List? ?? const []);
    return RefreshIndicator(onRefresh: _load, child: ListView(padding: const EdgeInsets.all(16), children: [
      const _ScreenTitle('Fleet outlook', 'Your own shift and authorized operating zones'),
      if (loading) const Center(child: CircularProgressIndicator()),
      if (error != null) _Notice(error!, action: TextButton(onPressed: _load, child: const Text('Retry'))),
      if (!loading && operations != null) ...[
        Card(child: ListTile(
          leading: const Icon(Icons.schedule, color: QuickbuddyColors.violet),
          title: Text(shift == null ? 'No upcoming shift' : shift['status'] == 'active' ? 'Shift in progress' : 'Upcoming shift'),
          subtitle: Text(shift == null ? 'Shift scheduling is not configured for your profile.' : '${shift['starts_at']} – ${shift['ends_at']}${shift['remaining_minutes'] == null ? '' : ' · ${shift['remaining_minutes']} min remaining'}'),
        )),
        Text('Vehicle · ${operations?['vehicle_type']}  |  Capabilities · ${capabilities.isEmpty ? 'none recorded' : capabilities}', style: const TextStyle(fontSize: 12)),
        const SizedBox(height: 12),
        const QbSectionTitle('Zone demand outlook'),
        if (signals.isEmpty) const _UnavailablePanel('No authorized service zones are assigned to your pilot profile.'),
        ...signals.map((raw) {
          final signal = raw as Map;
          final band = '${signal['demand_band']}';
          return Card(child: ListTile(
            leading: Icon(band == 'high' ? Icons.trending_up : band == 'moderate' ? Icons.trending_flat : Icons.info_outline, color: band == 'high' ? QuickbuddyColors.orange : QuickbuddyColors.violet),
            title: Text('${signal['zone_name']} · ${band.replaceAll('_', ' ')}'),
            subtitle: Text('${signal['recommendation']}\nForecast only · ${signal['model_status']} · ${signal['provenance']}'),
            isThreeLine: true,
          ));
        }),
        const QbPreviewNotice(message: 'These are advisory forecasts for zones authorized to your pilot profile. They are not confirmed orders. Zone-level pilot supply, travel time, incentive eligibility, and trained model outputs are not currently available.'),
      ],
    ]));
  }
}

class _StopCard extends StatelessWidget {
  const _StopCard({required this.number, required this.type, required this.title, required this.status, required this.onTap});
  final String number, type, title, status;
  final VoidCallback onTap;
  @override Widget build(BuildContext context) => Card(child: ListTile(
    leading: CircleAvatar(backgroundColor: QuickbuddyColors.violet.withValues(alpha: .1), child: Text(number)),
    title: Text('$type · $title'), subtitle: Text('Server stop status: $status'),
    trailing: IconButton(onPressed: onTap, icon: const Icon(Icons.navigation)),
  ));
}

class CustomerNavigationScreen extends StatelessWidget {
  const CustomerNavigationScreen({super.key});
  @override
  Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(16), children: [
    const _ScreenTitle('Navigation', 'Open the assigned stop in a map app'),
    const _UnavailablePanel('Quickbuddy does not have a configured in-app road-routing provider. External navigation opens the coordinates supplied by the shared backend.'),
    const SizedBox(height: 10),
    OutlinedButton.icon(onPressed: () => context.go('/pickup'), icon: const Icon(Icons.list_alt), label: const Text('View assigned stops')),
  ]);
}

class PilotIncidentScreen extends ConsumerStatefulWidget {
  const PilotIncidentScreen({super.key});
  @override ConsumerState<PilotIncidentScreen> createState() => _PilotIncidentScreenState();
}

class _PilotIncidentScreenState extends ConsumerState<PilotIncidentScreen> {
  static const categories = <(String, String)>[
    ('vehicle_breakdown', 'Vehicle breakdown'),
    ('road_blockage', 'Road blockage'),
    ('accident', 'Accident'),
    ('unsafe_pickup_area', 'Unsafe pickup area'),
    ('unsafe_delivery_area', 'Unsafe delivery area'),
    ('customer_unavailable', 'Customer unavailable'),
    ('merchant_closed', 'Merchant closed'),
    ('package_damaged', 'Package damaged'),
    ('wrong_package', 'Wrong package'),
    ('medical_emergency', 'Medical emergency'),
    ('severe_weather', 'Severe weather'),
    ('navigation_failure', 'Navigation failure'),
    ('low_battery', 'Phone battery critically low'),
    ('other', 'Other'),
  ];
  final summary = TextEditingController();
  List<Map<String, dynamic>> incidents = [];
  List<Map<String, dynamic>> activeAssignments = [];
  String category = 'vehicle_breakdown';
  String? taskId, message, error;
  bool emergency = false, loading = true, busy = false;
  @override void initState() { super.initState(); _load(); }
  @override void dispose() { summary.dispose(); super.dispose(); }

  Future<void> _load() async {
    try {
      final api = ref.read(transportProvider);
      final results = await Future.wait([
        api.get('/api/v1/pilots/me/incidents?limit=50'),
        api.get('/api/v1/pilots/me/assignments?limit=50'),
      ]);
      if (!mounted) return;
      final assignments = _rows(results[1].data).where((a) => const {'accepted', 'picked_up'}.contains(a['assignment_status'])).toList();
      setState(() {
        incidents = _rows(results[0].data);
        activeAssignments = assignments;
        if (!assignments.any((a) => a['delivery_task_id'] == taskId)) taskId = null;
        loading = false;
        error = null;
      });
    } catch (e) { if (mounted) setState(() { loading = false; error = _error(e); }); }
  }

  Future<void> _submit() async {
    if (busy || summary.text.trim().length < 10) return;
    setState(() { busy = true; error = null; message = null; });
    try {
      final result = await ref.read(transportProvider).post('/api/v1/pilots/me/incidents', data: {
        'category': category,
        'summary': summary.text.trim(),
        'delivery_task_id': taskId,
        'safety_emergency': emergency,
      });
      final incident = result.data as Map;
      summary.clear();
      setState(() { message = '${incident['next_step']} Report ID ${incident['id']}'; emergency = false; });
      if (incident['safety_emergency'] == true) {
        await pilotLocationReporter.stop();
        try {
          final profile = await ref.read(transportProvider).get('/api/v1/pilots/me');
          pilotProfileStore.value = Map<String, dynamic>.from(profile.data);
        } catch (_) { /* The incident POST is already authoritative. */ }
      }
      await _load();
    } catch (e) { if (mounted) setState(() => error = _error(e)); }
    finally { if (mounted) setState(() => busy = false); }
  }

  @override Widget build(BuildContext context) => RefreshIndicator(onRefresh: _load, child: ListView(padding: const EdgeInsets.all(16), children: [
    const _ScreenTitle('Operational issue', 'Report a safety, vehicle, road or delivery exception'),
    const QbPreviewNotice(message: 'If you are in immediate danger, move to safety and contact local emergency services. The app is not an emergency dispatch service.'),
    if (message != null) _Notice(message!),
    if (error != null) _Notice(error!, action: TextButton(onPressed: _load, child: const Text('Retry'))),
    DropdownButtonFormField<String>(
      initialValue: category,
      decoration: const InputDecoration(labelText: 'Issue type'),
      items: categories.map((item) => DropdownMenuItem(value: item.$1, child: Text(item.$2))).toList(),
      onChanged: busy ? null : (value) { if (value != null) setState(() => category = value); },
    ),
    if (activeAssignments.isNotEmpty) DropdownButtonFormField<String>(
      initialValue: taskId,
      decoration: const InputDecoration(labelText: 'Related active delivery (optional)'),
      items: [const DropdownMenuItem<String>(value: null, child: Text('No delivery selected')),
        ...activeAssignments.map((a) => DropdownMenuItem<String>(value: '${a['delivery_task_id']}', child: Text('Order ${a['order_reference']}')))],
      onChanged: busy ? null : (value) => setState(() => taskId = value),
    ),
    TextField(controller: summary, minLines: 3, maxLines: 5, maxLength: 1000,
      onChanged: (_) => setState(() {}),
      decoration: const InputDecoration(labelText: 'What happened?', hintText: 'Describe the issue. Avoid customer address or payment details.')),
    SwitchListTile(
      contentPadding: EdgeInsets.zero,
      value: emergency,
      onChanged: busy ? null : (value) => setState(() => emergency = value),
      title: const Text('I am in immediate danger or unsafe to continue'),
      subtitle: const Text('This pauses new offers until operations reviews and resolves the report.'),
    ),
    QbPrimaryButton(label: busy ? 'Sending report…' : 'Send to Quickbuddy operations', icon: Icons.support_agent,
      enabled: !busy && summary.text.trim().length >= 10, onPressed: _submit),
    const SizedBox(height: 12),
    const QbSectionTitle('Your reports'),
    if (loading) const Center(child: CircularProgressIndicator()) else if (incidents.isEmpty) const _UnavailablePanel('No incident reports have been submitted.'),
    ...incidents.map((incident) => Card(child: ListTile(
      leading: Icon(incident['safety_emergency'] == true ? Icons.health_and_safety : Icons.report_outlined, color: incident['safety_emergency'] == true ? Colors.red : QuickbuddyColors.violet),
      title: Text('${incident['category']} · ${incident['status']}'),
      subtitle: Text('${incident['summary']}\n${incident['resolution_summary'] ?? ''}'),
      isThreeLine: true,
    ))),
  ]));
}

class CompleteDeliveryScreen extends ConsumerStatefulWidget {
  const CompleteDeliveryScreen({super.key});
  @override ConsumerState<CompleteDeliveryScreen> createState() => _CompleteDeliveryScreenState();
}

class _CompleteDeliveryScreenState extends ConsumerState<CompleteDeliveryScreen> {
  List<Map<String, dynamic>> assignments = [];
  bool loading = true, busy = false;
  @override void initState() { super.initState(); _load(); }
  Future<void> _load() async {
    try { final r = await ref.read(transportProvider).get('/api/v1/pilots/me/assignments?limit=50'); if (mounted) setState(() { assignments = _rows(r.data).where((a) => a['assignment_status'] == 'picked_up').toList(); loading = false; }); }
    catch (_) { if (mounted) setState(() => loading = false); }
  }
  Future<void> _reportFailure(Map<String, dynamic> a) async {
    final confirm = await showDialog<bool>(context: context, builder: (ctx) => AlertDialog(
      title: const Text('Report delivery failure?'),
      content: const Text('Quickbuddy will record a failed delivery attempt. This backend endpoint does not record a reason or start a return workflow.'),
      actions: [TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')),
        FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Report failure'))],
    ));
    if (confirm != true || busy) return;
    setState(() => busy = true);
    try {
      await ref.read(transportProvider).post('/api/v1/delivery-tasks/${a['delivery_task_id']}/fail', data: {'expected_version': a['task_version']});
      await _load();
    } catch (e) { if (mounted) _toast(context, _error(e)); await _load(); }
    finally { if (mounted) setState(() => busy = false); }
  }
  @override
  Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(16), children: [
    const _ScreenTitle('Delivery proof', 'Follow the recipient verification policy'),
    if (loading) const Center(child: CircularProgressIndicator()),
    const QbPreviewNotice(message: 'The current backend accepts delivery completion only from the customer acknowledgment flow. No pilot-side OTP validation, proof upload, or cash collection API exists; completed status is intentionally unavailable here.'),
    ...assignments.map((a) => Card(child: ListTile(
      title: Text('Order ${a['order_reference']} · ${a['merchant_name']}'),
      subtitle: const Text('Customer proof required; do not close this delivery in the app.'),
      trailing: TextButton(onPressed: busy ? null : () => _reportFailure(a), child: const Text('Report issue')),
    ))),
  ]);
}

class PilotEarningsScreen extends ConsumerStatefulWidget {
  const PilotEarningsScreen({super.key});
  @override ConsumerState<PilotEarningsScreen> createState() => _PilotEarningsScreenState();
}

class _PilotEarningsScreenState extends ConsumerState<PilotEarningsScreen> {
  List<Map<String, dynamic>> items = [];
  bool loading = true;
  String? error;
  @override void initState() { super.initState(); _load(); }
  Future<void> _load() async {
    try { final r = await ref.read(transportProvider).get('/api/v1/pilots/me/earnings?limit=100'); if (mounted) setState(() { items = _rows(r.data); loading = false; error = null; }); }
    catch (e) { if (mounted) setState(() { loading = false; error = _error(e); }); }
  }
  @override
  Widget build(BuildContext context) => RefreshIndicator(onRefresh: _load, child: ListView(padding: const EdgeInsets.all(16), children: [
    const _ScreenTitle('Earnings ledger', 'Recorded pilot earnings from the shared backend'),
    if (error != null) _Notice(error!),
    if (loading) const Center(child: CircularProgressIndicator()) else if (items.isEmpty) const _UnavailablePanel('No pilot earnings have been recorded.'),
    ...items.map((e) => Card(child: ListTile(
      leading: const Icon(Icons.payments_outlined, color: QuickbuddyColors.violet),
      title: Text('${e['currency']} ${e['amount']}'),
      subtitle: Text('Delivery ${'${e['task_id']}'.substring(0, 8)} · ${e['recorded_at']}'),
    ))),
    const QbPreviewNotice(message: 'Offer estimates, incentive progress, payout status, and wallet balance are not exposed by current backend APIs and are not calculated in Flutter.'),
  ]));
}

class PilotProfileScreen extends ConsumerStatefulWidget {
  const PilotProfileScreen({super.key});
  @override ConsumerState<PilotProfileScreen> createState() => _PilotProfileScreenState();
}

class _PilotProfileScreenState extends ConsumerState<PilotProfileScreen> {
  Map<String, dynamic>? profile;
  bool loading = true;
  @override void initState() { super.initState(); _load(); }
  Future<void> _load() async {
    try { final r = await ref.read(transportProvider).get('/api/v1/pilots/me'); if (mounted) setState(() { profile = Map<String, dynamic>.from(r.data); loading = false; }); }
    catch (_) { if (mounted) setState(() => loading = false); }
  }
  Future<void> _logout() async {
    await pilotLocationReporter.stop();
    await pilotTokenStore.clear();
    pilotProfileStore.value = null;
    if (mounted) context.go('/login');
  }
  @override
  Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(16), children: [
    const _ScreenTitle('Pilot profile', 'Account state and operational readiness'),
    if (loading) const Center(child: CircularProgressIndicator()) else if (profile != null) Card(child: ListTile(
      leading: const CircleAvatar(child: Icon(Icons.person_outline)),
      title: Text(profile?['verified'] == true ? 'Approved pilot' : 'Approval pending'),
      subtitle: Text('State: ${profile?['state']} · Vehicle: ${profile?['vehicle_type']} · Location consent: ${profile?['location_consent'] == true ? 'on file' : 'not given'}'),
    )),
    const QbPreviewNotice(message: 'Identity documents, full KYC status history, vehicle details, emergency contact, bank payout, support tickets and shift scheduling are not writable/readable through current pilot APIs.'),
    TextButton.icon(onPressed: _logout, icon: const Icon(Icons.logout), label: const Text('Sign out')),
  ]);
}

Future<void> _openMaps(dynamic latitude, dynamic longitude) async {
  final lat = double.tryParse('$latitude'), lon = double.tryParse('$longitude');
  if (lat == null || lon == null) return;
  final uri = Uri.parse('https://www.google.com/maps/dir/?api=1&destination=$lat,$lon&travelmode=driving');
  await launchUrl(uri, mode: LaunchMode.externalApplication);
}

class _MetricStrip extends StatelessWidget {
  const _MetricStrip({required this.items});
  final List<(String, String)> items;
  @override
  Widget build(BuildContext context) => Row(children: items.map((x) => Expanded(child: Column(children: [
    Text(x.$2, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w800, color: QuickbuddyColors.indigo)),
    const SizedBox(height: 3), Text(x.$1, style: const TextStyle(fontSize: 10, color: QuickbuddyColors.muted)),
  ]))).toList());
}

class _PerkRow extends StatelessWidget {
  const _PerkRow({required this.icon, required this.title});
  final IconData icon; final String title;
  @override
  Widget build(BuildContext context) => ListTile(dense: true, leading: Icon(icon, color: QuickbuddyColors.orange), title: Text(title));
}

class _QuickAction extends StatelessWidget {
  const _QuickAction({required this.icon, required this.title, required this.subtitle, required this.onTap});
  final IconData icon; final String title, subtitle; final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => Card(child: ListTile(
    leading: Icon(icon, color: QuickbuddyColors.violet), title: Text(title), subtitle: Text(subtitle),
    trailing: const Icon(Icons.chevron_right), onTap: onTap,
  ));
}

class _ScreenTitle extends StatelessWidget {
  const _ScreenTitle(this.title, this.subtitle);
  final String title, subtitle;
  @override
  Widget build(BuildContext context) => Padding(padding: const EdgeInsets.only(bottom: 12), child: Column(
    crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(title, style: const TextStyle(color: QuickbuddyColors.indigo, fontSize: 20, fontWeight: FontWeight.w800)),
      const SizedBox(height: 4), Text(subtitle, style: const TextStyle(fontSize: 12, color: QuickbuddyColors.muted)),
    ],
  ));
}

class _UnavailablePanel extends StatelessWidget {
  const _UnavailablePanel(this.text);
  final String text;
  @override
  Widget build(BuildContext context) => QbPanel(child: Text(text, style: const TextStyle(color: QuickbuddyColors.muted, fontSize: 12)));
}

class _Notice extends StatelessWidget {
  const _Notice(this.message, {this.action});
  final String message; final Widget? action;
  @override
  Widget build(BuildContext context) => Card(color: const Color(0xFFFFF6E7), child: ListTile(
    leading: const Icon(Icons.info_outline, color: QuickbuddyColors.orange), title: Text(message, style: const TextStyle(fontSize: 12)), trailing: action,
  ));
}
