import 'dart:async';
import 'dart:math';

import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_core/flutter_core.dart';
import 'package:flutter_design_system/flutter_design_system.dart';
import 'package:flutter_networking/flutter_networking.dart';
import 'package:go_router/go_router.dart';

final tokenStore = SecureTokenStore();
final transportProvider = Provider((ref) => createTransport(tokenStore));
final selectedBranchStore = ValueNotifier<Map<String, dynamic>?>(null);

final router = GoRouter(
  initialLocation: '/',
  routes: [
    ShellRoute(
      builder: (context, state, child) => MerchantShell(path: state.uri.path, child: child),
      routes: [
        GoRoute(path: '/', builder: (_, __) => const MerchantStartupScreen()),
        GoRoute(path: '/sign-in', builder: (_, __) => const MerchantSignInScreen()),
        GoRoute(path: '/onboarding', builder: (_, __) => const MerchantOnboardingScreen()),
        GoRoute(path: '/dashboard', builder: (_, __) => const MerchantDashboardScreen()),
        GoRoute(path: '/orders', builder: (_, __) => const MerchantOrdersScreen()),
        GoRoute(path: '/orders/:id', builder: (_, state) => MerchantOrderScreen(id: state.pathParameters['id']!)),
        GoRoute(path: '/kitchen', builder: (_, __) => const KitchenScreen()),
        GoRoute(path: '/menu', builder: (_, __) => const MenuManagementScreen()),
        GoRoute(path: '/inventory', builder: (_, __) => const InventoryScreen()),
        GoRoute(path: '/settings', builder: (_, __) => const BranchSettingsScreen()),
        GoRoute(path: '/promotions', builder: (_, __) => const UnavailableFeatureScreen(title: 'Promotions', detail: 'The shared backend does not yet expose merchant campaign management.')),
        GoRoute(path: '/analytics', builder: (_, __) => const UnavailableFeatureScreen(title: 'Analytics', detail: 'Merchant-scoped analytics endpoints are not available yet. No sample revenue is shown.')),
        GoRoute(path: '/settlements', builder: (_, __) => const UnavailableFeatureScreen(title: 'Settlements', detail: 'The finance ledger exists, but a merchant settlement summary/history endpoint is not available.')),
      ],
    ),
  ],
);

void main() => runApp(ProviderScope(child: QuickbuddyApp(
  title: 'Quickbuddy Restaurant Partner',
  theme: quickbuddyTheme().copyWith(scaffoldBackgroundColor: const Color(0xFFFAFAFC)),
  router: router,
)));

List<Map<String, dynamic>> _rows(dynamic response) {
  final items = response is Map ? response['items'] : null;
  return items is List ? items.whereType<Map>().map((e) => Map<String, dynamic>.from(e)).toList() : [];
}

T? _firstOrNull<T>(Iterable<T> values) {
  final iterator = values.iterator;
  return iterator.moveNext() ? iterator.current : null;
}

String _error(Object error) {
  if (error is DioException) {
    final detail = error.response?.data;
    if (detail is Map && detail['detail'] is String) return detail['detail'] as String;
    if (error.response?.statusCode == 401) return 'Your session expired. Sign in again.';
    return error.message ?? 'The service is temporarily unavailable.';
  }
  return error.toString();
}

String _key() => List.generate(32, (_) => Random.secure().nextInt(16).toRadixString(16)).join();
void _toast(BuildContext context, String message) => ScaffoldMessenger.of(context)
  ..hideCurrentSnackBar()
  ..showSnackBar(SnackBar(content: Text(message)));

class MerchantShell extends StatelessWidget {
  const MerchantShell({super.key, required this.path, required this.child});
  final String path;
  final Widget child;
  @override
  Widget build(BuildContext context) {
    final login = path == '/sign-in' || path == '/onboarding';
    final selected = path.startsWith('/orders') || path == '/kitchen' ? 1 : path == '/menu' || path == '/inventory' ? 2 : path == '/settings' ? 3 : 0;
    return Scaffold(
      body: SafeArea(child: child),
      bottomNavigationBar: login ? null : NavigationBar(
        height: 66,
        selectedIndex: selected,
        backgroundColor: Colors.white,
        indicatorColor: QuickbuddyColors.orange.withValues(alpha: .12),
        onDestinationSelected: (i) => context.go(switch (i) {1 => '/orders', 2 => '/menu', 3 => '/settings', _ => '/dashboard'}),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.receipt_long_outlined), label: 'Orders'),
          NavigationDestination(icon: Icon(Icons.restaurant_menu_outlined), label: 'Menu'),
          NavigationDestination(icon: Icon(Icons.tune), label: 'More'),
        ],
      ),
    );
  }
}

class MerchantSignInScreen extends ConsumerStatefulWidget {
  const MerchantSignInScreen({super.key});
  @override ConsumerState<MerchantSignInScreen> createState() => _MerchantSignInScreenState();
}

class _MerchantSignInScreenState extends ConsumerState<MerchantSignInScreen> {
  final email = TextEditingController();
  final password = TextEditingController();
  final form = GlobalKey<FormState>();
  bool busy = false;
  bool create = false;
  @override void dispose() { email.dispose(); password.dispose(); super.dispose(); }
  Future<void> _submit() async {
    if (!form.currentState!.validate() || busy) return;
    setState(() => busy = true);
    try {
      final api = ref.read(transportProvider);
      if (create) await api.post('/api/v1/auth/register', data: {'email': email.text.trim(), 'password': password.text});
      final result = await api.post('/api/v1/auth/login', data: {'email': email.text.trim(), 'password': password.text});
      await tokenStore.saveTokens(result.data['access_token'] as String, result.data['refresh_token'] as String);
      if (mounted) context.go('/dashboard');
    } catch (e) { if (mounted) _toast(context, _error(e)); }
    finally { if (mounted) setState(() => busy = false); }
  }
  @override
  Widget build(BuildContext context) => Center(child: SingleChildScrollView(padding: const EdgeInsets.all(22), child: ConstrainedBox(constraints: const BoxConstraints(maxWidth: 440), child: Form(key: form, child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
    const QbBrand(),
    const SizedBox(height: 22),
    Text(create ? 'Start your merchant account' : 'Welcome back', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: QuickbuddyColors.indigo)),
    const SizedBox(height: 5),
    Text(create ? 'Create a secure account to begin organization onboarding.' : 'Sign in to your authorized merchant workspace.', style: const TextStyle(color: QuickbuddyColors.muted)),
    const SizedBox(height: 22),
    TextFormField(controller: email, keyboardType: TextInputType.emailAddress, decoration: const InputDecoration(labelText: 'Email address'), validator: (v) => v == null || !RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$').hasMatch(v.trim()) ? 'Enter a valid email.' : null),
    const SizedBox(height: 12),
    TextFormField(controller: password, obscureText: true, decoration: InputDecoration(labelText: 'Password', helperText: create ? 'At least 12 characters' : null), validator: (v) => v == null || (create ? v.length < 12 : v.isEmpty) ? (create ? 'Use at least 12 characters.' : 'Enter your password.') : null),
    const SizedBox(height: 18),
    QbPrimaryButton(label: busy ? 'Please wait…' : create ? 'Create account' : 'Sign in', enabled: !busy, onPressed: _submit),
    TextButton(onPressed: busy ? null : () => setState(() => create = !create), child: Text(create ? 'Already registered? Sign in' : 'New partner? Create an account')),
  ])))));
}

class MerchantStartupScreen extends ConsumerStatefulWidget {
  const MerchantStartupScreen({super.key});
  @override ConsumerState<MerchantStartupScreen> createState() => _MerchantStartupScreenState();
}
class _MerchantStartupScreenState extends ConsumerState<MerchantStartupScreen> {
  @override void initState() { super.initState(); _open(); }
  Future<void> _open() async { String? token; try { token = await tokenStore.accessToken(); } catch (_) { token = null; } if (!mounted) return; context.go(token == null ? '/sign-in' : '/dashboard'); }
  @override Widget build(BuildContext context) => const Center(child: CircularProgressIndicator());
}

class MerchantOnboardingScreen extends ConsumerStatefulWidget {
  const MerchantOnboardingScreen({super.key});
  @override ConsumerState<MerchantOnboardingScreen> createState() => _MerchantOnboardingScreenState();
}

class _MerchantOnboardingScreenState extends ConsumerState<MerchantOnboardingScreen> {
  final organization = TextEditingController();
  final brand = TextEditingController();
  final branch = TextEditingController();
  final lat = TextEditingController(text: '12.9716');
  final lon = TextEditingController(text: '77.5946');
  final form = GlobalKey<FormState>();
  List<Map<String, dynamic>> cities = [];
  List<Map<String, dynamic>> branches = [];
  List<Map<String, dynamic>> organizations = [];
  String? cityId;
  String? organizationId;
  String kind = 'food';
  bool createOrganization = true;
  bool loading = true, saving = false;
  @override void initState() { super.initState(); _loadCities(); }
  @override void dispose() { organization.dispose(); brand.dispose(); branch.dispose(); lat.dispose(); lon.dispose(); super.dispose(); }
  Future<void> _loadCities() async {
    try {
      final api = ref.read(transportProvider);
      final data = await api.get('/api/v1/geo/cities?limit=100');
      List<Map<String, dynamic>> ownedBranches = [];
      try { ownedBranches = _rows((await api.get('/api/v1/merchant/branches?limit=100')).data); } catch (_) {}
      final orgIds = ownedBranches.map((b) => b['organization_id'].toString()).toSet();
      final currentOrg = selectedBranchStore.value?['organization_id']?.toString();
      if (mounted) setState(() {
        cities = _rows(data.data);
        cityId = cities.isEmpty ? null : cities.first['id'] as String;
        branches = ownedBranches;
        organizations = {for (final b in ownedBranches) b['organization_id'].toString(): b}.values.toList();
        organizationId = currentOrg != null && orgIds.contains(currentOrg) ? currentOrg : _firstOrNull(orgIds);
        createOrganization = orgIds.isEmpty;
        loading = false;
      });
    }
    catch (e) { if (mounted) setState(() => loading = false); }
  }
  Future<void> _create() async {
    if (!form.currentState!.validate() || cityId == null || saving) return;
    setState(() => saving = true);
    try {
      final api = ref.read(transportProvider);
      final result = await api.post('/api/v1/merchant/onboarding', data: {
        if (createOrganization) 'organization_name': organization.text.trim() else 'organization_id': organizationId,
        'brand_name': brand.text.trim(),
        'merchant_type': kind,
        'branch_name': branch.text.trim(),
        'city_id': cityId,
        'latitude': lat.text.trim(),
        'longitude': lon.text.trim(),
      });
      if (mounted) { _toast(context, 'Branch submitted as ${result.data['status']}. Final approval is performed by an authorized administrator.'); context.go('/dashboard'); }
    } catch (e) { if (mounted) _toast(context, 'Onboarding stopped: ${_error(e)}'); }
    finally { if (mounted) setState(() => saving = false); }
  }
  @override
  Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(18), children: [
    const _Header('Partner onboarding', 'Create organization, brand and a branch submission'),
    const QbPreviewNotice(message: 'This API captures only the initial organization/brand/branch records. KYC, tax/FSSAI documents, banking, operating hours, images and secure uploads are not implemented by the shared backend.'),
    const SizedBox(height: 12),
    if (loading) const Center(child: CircularProgressIndicator()) else Form(key: form, child: Column(children: [
      if (branches.isNotEmpty) SwitchListTile(title: const Text('Create a new organization'), value: createOrganization, onChanged: (v) => setState(() => createOrganization = v)),
      if (createOrganization) _field(organization, 'Merchant organization name') else DropdownButtonFormField<String>(initialValue: organizationId, decoration: const InputDecoration(labelText: 'Organization'), items: organizations.map((b) => DropdownMenuItem(value: b['organization_id'] as String, child: Text('${b['name']} · ${b['status']}'))).toList(), onChanged: (v) => setState(() => organizationId = v)),
      _field(brand, 'Brand name'), _field(branch, 'Branch/store name'),
      DropdownButtonFormField<String>(initialValue: kind, decoration: const InputDecoration(labelText: 'Business category'), items: const [DropdownMenuItem(value: 'food', child: Text('Restaurant / food')), DropdownMenuItem(value: 'grocery', child: Text('Grocery')), DropdownMenuItem(value: 'retail', child: Text('Retail')), DropdownMenuItem(value: 'pharmacy', child: Text('Pharmacy')), DropdownMenuItem(value: 'parcel', child: Text('Other / parcel'))], onChanged: (v) => setState(() => kind = v ?? 'food')),
      const SizedBox(height: 8),
      DropdownButtonFormField<String>(initialValue: cityId, decoration: const InputDecoration(labelText: 'Operating city'), items: cities.map((c) => DropdownMenuItem(value: c['id'] as String, child: Text('${c['name']}'))).toList(), onChanged: (v) => setState(() => cityId = v)),
      Row(children: [Expanded(child: _field(lat, 'Latitude', numeric: true)), const SizedBox(width: 10), Expanded(child: _field(lon, 'Longitude', numeric: true))]),
      const SizedBox(height: 12),
      QbPrimaryButton(label: saving ? 'Submitting…' : 'Submit branch for review', enabled: !saving && cityId != null, onPressed: _create),
      TextButton(onPressed: () => context.go('/dashboard'), child: const Text('Back to workspace')),
    ])),
  ]);
}

Widget _field(TextEditingController controller, String label, {bool numeric = false}) => Padding(padding: const EdgeInsets.only(bottom: 8), child: TextFormField(controller: controller, keyboardType: numeric ? const TextInputType.numberWithOptions(decimal: true, signed: true) : TextInputType.text, decoration: InputDecoration(labelText: label), validator: (v) { if (v == null || v.trim().isEmpty) return 'Required.'; if (numeric && double.tryParse(v.trim()) == null) return 'Enter a number.'; return null; }));

class MerchantDashboardScreen extends ConsumerStatefulWidget {
  const MerchantDashboardScreen({super.key});
  @override ConsumerState<MerchantDashboardScreen> createState() => _MerchantDashboardScreenState();
}

class _MerchantDashboardScreenState extends ConsumerState<MerchantDashboardScreen> {
  List<Map<String, dynamic>> branches = [], queue = [];
  String? error;
  bool loading = true, busy = false;
  Timer? timer;
  @override void initState() { super.initState(); _load(); timer = Timer.periodic(const Duration(seconds: 15), (_) => _refreshQueue()); }
  @override void dispose() { timer?.cancel(); super.dispose(); }
  Future<void> _load() async {
    try {
      final api = ref.read(transportProvider);
      final token = await tokenStore.accessToken();
      if (token == null) { if (mounted) context.go('/sign-in'); return; }
      branches = _rows((await api.get('/api/v1/merchant/branches?limit=100')).data);
      final saved = await tokenStore.readValue('merchant_branch_id');
      var selected = _firstOrNull(branches.where((b) => b['id'] == saved));
      selected ??= branches.isEmpty ? null : branches.first;
      if (selected != null) { await tokenStore.writeValue('merchant_branch_id', selected['id'] as String); selectedBranchStore.value = selected; await _refreshQueue(); }
      if (mounted) setState(() { loading = false; error = null; });
    } catch (e) { if (mounted) setState(() { loading = false; error = _error(e); }); }
  }
  Future<void> _refreshQueue() async {
    final branch = selectedBranchStore.value;
    if (branch == null) return;
    try { final rows = _rows((await ref.read(transportProvider).get('/api/v1/merchant/branches/${branch['id']}/orders?limit=100')).data); if (mounted) setState(() { queue = rows; error = null; }); }
    catch (e) { if (mounted) setState(() => error = _error(e)); }
  }
  Future<void> _selectBranch(Map<String, dynamic> value) async {
    await tokenStore.writeValue('merchant_branch_id', value['id'] as String);
    selectedBranchStore.value = value;
    if (mounted) setState(() { queue = []; busy = true; });
    await _refreshQueue();
    if (mounted) setState(() => busy = false);
  }
  Future<void> _availability(bool accepting) async {
    final branch = selectedBranchStore.value;
    if (branch == null) return;
    try {
      final r = await ref.read(transportProvider).put('/api/v1/merchant/branches/${branch['id']}/availability', data: {'accepting_orders': accepting, 'expected_version': branch['version']});
      final updated = Map<String, dynamic>.from(r.data);
      selectedBranchStore.value = updated;
      branches = branches.map((b) => b['id'] == updated['id'] ? updated : b).toList();
      if (mounted) setState(() {});
    } catch (e) { if (mounted) _toast(context, _error(e)); await _load(); }
  }
  @override
  Widget build(BuildContext context) {
    final branch = selectedBranchStore.value;
    final active = queue.where((o) => const {'pending', 'accepted', 'preparing', 'ready'}.contains(o['status'])).length;
    final preparing = queue.where((o) => o['status'] == 'preparing').length;
    final ready = queue.where((o) => o['status'] == 'ready').length;
    return RefreshIndicator(onRefresh: _load, child: ListView(padding: const EdgeInsets.fromLTRB(16, 12, 16, 22), children: [
      Row(children: [const Expanded(child: QbBrand()), IconButton(tooltip: 'Sign out', onPressed: _signOut, icon: const Icon(Icons.logout))]),
      const Text('Restaurant partner workspace', style: TextStyle(fontSize: 11, color: QuickbuddyColors.muted)),
      const SizedBox(height: 12),
      if (loading) const Center(child: CircularProgressIndicator()) else if (error != null && branch == null) _Notice(error!, action: TextButton(onPressed: _load, child: const Text('Retry'))) else if (branches.isEmpty) _Notice('No authorized branches are linked to this account yet.', action: TextButton(onPressed: () => context.go('/onboarding'), child: const Text('Start onboarding')))
      else ...[
        DropdownButtonFormField<String>(key: ValueKey(branch?['id']), initialValue: branch?['id'] as String?, decoration: const InputDecoration(labelText: 'Active branch', prefixIcon: Icon(Icons.storefront)), items: branches.map((b) => DropdownMenuItem(value: b['id'] as String, child: Text('${b['name']} · ${b['status']}'))).toList(), onChanged: (id) { final next = _firstOrNull(branches.where((b) => b['id'] == id)); if (next != null) _selectBranch(next); }),
        const SizedBox(height: 12),
        if (branch?['status'] != 'approved') const QbPreviewNotice(message: 'This branch is not approved yet. It cannot accept customer orders; an authorized administrator controls approval.'),
        Card(child: SwitchListTile(title: const Text('Accepting orders', style: TextStyle(fontWeight: FontWeight.w700)), subtitle: Text(branch?['accepting_orders'] == true ? 'Customers can place orders at this approved branch.' : 'New ordering is paused.'), value: branch?['accepting_orders'] == true, onChanged: busy || branch?['status'] != 'approved' ? null : _availability)),
        Row(children: [Expanded(child: _CountTile('Active', '$active', Icons.receipt_long, QuickbuddyColors.orange)), const SizedBox(width: 8), Expanded(child: _CountTile('Preparing', '$preparing', Icons.timer_outlined, QuickbuddyColors.violet)), const SizedBox(width: 8), Expanded(child: _CountTile('Ready', '$ready', Icons.check_circle_outline, QuickbuddyColors.green))]),
        const SizedBox(height: 14),
        Row(children: [const Expanded(child: _Section('Incoming order queue')), TextButton(onPressed: _refreshQueue, child: const Text('Refresh'))]),
        if (error != null) _Notice('Could not refresh order queue: $error', action: TextButton(onPressed: _refreshQueue, child: const Text('Retry'))),
        if (queue.isEmpty) const _Notice('No orders are currently assigned to this branch.') else ...queue.take(4).map((o) => _QueueCard(order: o, compact: true, onTap: () => context.push('/orders/${o['id']}'))),
        QbPrimaryButton(label: 'Open live orders', icon: Icons.receipt_long, onPressed: () => context.go('/orders')),
        Row(children: [Expanded(child: _ActionTile('Kitchen display', Icons.soup_kitchen_outlined, () => context.go('/kitchen'))), const SizedBox(width: 8), Expanded(child: _ActionTile('Inventory', Icons.inventory_2_outlined, () => context.go('/inventory')))]),
        Row(children: [Expanded(child: _ActionTile('Menu', Icons.restaurant_menu, () => context.go('/menu'))), const SizedBox(width: 8), Expanded(child: _ActionTile('Settlements', Icons.account_balance_wallet_outlined, () => context.go('/settlements')))]),
      ],
      if (branches.isNotEmpty) TextButton.icon(onPressed: () => context.go('/onboarding'), icon: const Icon(Icons.add_business), label: const Text('Add another branch (starts admin review)')),
    ]));
  }
  Future<void> _signOut() async { try { final refresh = await tokenStore.refreshToken(); if (refresh != null) await ref.read(transportProvider).post('/api/v1/auth/logout', data: {'refresh_token': refresh}); } catch (_) {} await tokenStore.clear(); await tokenStore.deleteValue('merchant_branch_id'); selectedBranchStore.value = null; if (mounted) context.go('/sign-in'); }
}

class MerchantOrdersScreen extends ConsumerStatefulWidget {
  const MerchantOrdersScreen({super.key});
  @override ConsumerState<MerchantOrdersScreen> createState() => _MerchantOrdersScreenState();
}
class _MerchantOrdersScreenState extends ConsumerState<MerchantOrdersScreen> {
  List<Map<String, dynamic>> orders = [];
  String filter = 'All';
  bool loading = true;
  String? error;
  Timer? timer;
  @override void initState() { super.initState(); _load(); timer = Timer.periodic(const Duration(seconds: 12), (_) => _load(silent: true)); }
  @override void dispose() { timer?.cancel(); super.dispose(); }
  Future<void> _load({bool silent = false}) async {
    final branch = selectedBranchStore.value;
    if (branch == null) { if (mounted) setState(() { loading = false; error = 'Choose an authorized branch on the dashboard.'; }); return; }
    if (!silent && mounted) setState(() => loading = true);
    try { final r = await ref.read(transportProvider).get('/api/v1/merchant/branches/${branch['id']}/orders?limit=100'); if (mounted) setState(() { orders = _rows(r.data); error = null; loading = false; }); }
    catch (e) { if (mounted) setState(() { error = _error(e); loading = false; }); }
  }
  @override Widget build(BuildContext context) {
    final visible = filter == 'All' ? orders : orders.where((o) => o['status'].toString().toLowerCase() == filter.toLowerCase()).toList();
    return RefreshIndicator(onRefresh: _load, child: ListView(padding: const EdgeInsets.all(16), children: [
      const _Header('Live orders', 'Branch-scoped queue · refreshes every 12 seconds'),
      if (error != null) _Notice(error!, action: TextButton(onPressed: _load, child: const Text('Retry'))),
      SingleChildScrollView(scrollDirection: Axis.horizontal, child: Row(children: ['All', 'pending', 'accepted', 'preparing', 'ready', 'fulfilled', 'rejected'].map((v) => Padding(padding: const EdgeInsets.only(right: 6), child: ChoiceChip(label: Text(v == 'All' ? 'All' : v[0].toUpperCase() + v.substring(1)), selected: filter == v, onSelected: (_) => setState(() => filter = v))).toList())),
      if (loading) const Center(child: Padding(padding: EdgeInsets.all(28), child: CircularProgressIndicator())) else if (visible.isEmpty) const _Notice('No orders in this queue state.') else ...visible.map((o) => _QueueCard(order: o, onTap: () => context.push('/orders/${o['id']}'))),
    ]));
  }
}

class _QueueCard extends StatelessWidget {
  const _QueueCard({required this.order, required this.onTap, this.compact = false});
  final Map<String, dynamic> order;
  final VoidCallback onTap;
  final bool compact;
  @override
  Widget build(BuildContext context) {
    final items = order['items'] is List ? (order['items'] as List) : const [];
    final status = '${order['status'] ?? 'unknown'}';
    return Card(child: InkWell(onTap: onTap, borderRadius: BorderRadius.circular(14), child: Padding(padding: const EdgeInsets.all(12), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [Expanded(child: Text('Order ${order['id']}', maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w800, color: QuickbuddyColors.indigo))), QbStatusChip(status.toUpperCase(), tone: status == 'pending' ? 'warning' : status == 'ready' ? 'success' : 'brand')]),
      const SizedBox(height: 6),
      Text('${order['currency']} ${order['total']} · ${items.length} item${items.length == 1 ? '' : 's'}', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
      if (!compact) ...items.map((i) => Padding(padding: const EdgeInsets.only(top: 6), child: Text('${i['quantity']} × ${i['product_name']} · ${i['variant_name']}', style: const TextStyle(fontSize: 12)))),
      const SizedBox(height: 4),
      Text('Received ${MaterialLocalizations.of(context).formatMediumDate(DateTime.parse('${order['created_at']}').toLocal())}', style: const TextStyle(fontSize: 10, color: QuickbuddyColors.muted)),
    ]))));
  }
}

class MerchantOrderScreen extends ConsumerStatefulWidget {
  const MerchantOrderScreen({super.key, required this.id});
  final String id;
  @override ConsumerState<MerchantOrderScreen> createState() => _MerchantOrderScreenState();
}
class _MerchantOrderScreenState extends ConsumerState<MerchantOrderScreen> {
  Map<String, dynamic>? order;
  bool loading = true, busy = false;
  String? error;
  @override void initState() { super.initState(); _load(); }
  Future<void> _load() async {
    final branch = selectedBranchStore.value;
    if (branch == null) return;
    try {
      final rows = _rows((await ref.read(transportProvider).get('/api/v1/merchant/branches/${branch['id']}/orders?limit=100')).data);
      final match = _firstOrNull(rows.where((o) => o['id'] == widget.id));
      if (mounted) setState(() { order = match; loading = false; error = match == null ? 'Order not found in the selected branch.' : null; });
    } catch (e) { if (mounted) setState(() { loading = false; error = _error(e); }); }
  }
  Future<void> _transition(String target) async {
    final current = order;
    if (current == null || busy) return;
    setState(() => busy = true);
    try {
      await ref.read(transportProvider).post('/api/v1/merchant-orders/${current['id']}/transition', data: {'target': target, 'expected_version': current['version']});
      await _load();
      if (mounted) _toast(context, 'Order updated to $target.');
    } catch (e) { if (mounted) _toast(context, 'Order was not changed: ${_error(e)}'); await _load(); }
    finally { if (mounted) setState(() => busy = false); }
  }
  @override
  Widget build(BuildContext context) {
    final o = order;
    final status = o?['status'];
    return ListView(padding: const EdgeInsets.all(16), children: [
      _Header('Order details', 'Merchant order status is controlled by the backend'),
      if (loading) const Center(child: CircularProgressIndicator()) else if (error != null) _Notice(error!, action: TextButton(onPressed: _load, child: const Text('Retry'))) else if (o != null) ...[
        _QueueCard(order: o, onTap: () {},),
        const _Section('Items'),
        ...(o['items'] as List? ?? const []).map((i) => Card(child: ListTile(leading: const Icon(Icons.restaurant_menu, color: QuickbuddyColors.orange), title: Text('${i['product_name']} · ${i['variant_name']}'), subtitle: Text('${i['quantity']} ${i['unit']} × ${i['currency'] ?? o['currency']} ${i['unit_price']}'), trailing: Text('${o['currency']} ${i['total']}'))),
        const SizedBox(height: 14),
        if (status == 'pending') QbPrimaryButton(label: busy ? 'Updating…' : 'Accept order', icon: Icons.check, enabled: !busy, onPressed: () => _transition('accepted')),
        if (status == 'accepted') QbPrimaryButton(label: busy ? 'Updating…' : 'Start preparing', icon: Icons.soup_kitchen_outlined, enabled: !busy, onPressed: () => _transition('preparing')),
        if (status == 'preparing') QbPrimaryButton(label: busy ? 'Updating…' : 'Mark ready for pickup', icon: Icons.check_circle_outline, enabled: !busy, onPressed: () => _transition('ready')),
        if (status == 'ready') const QbPreviewNotice(message: 'Ready for handover. Pilot assignment and pickup confirmation are tracked in fulfillment; merchant pickup confirmation is not available yet.'),
        const SizedBox(height: 8),
        const QbPreviewNotice(message: 'Customer notes/modifiers are not present in the order contract. Order transitions are version-checked by the backend.'),
      ],
    ]);
  }
}

class KitchenScreen extends ConsumerStatefulWidget {
  const KitchenScreen({super.key});
  @override ConsumerState<KitchenScreen> createState() => _KitchenScreenState();
}
class _KitchenScreenState extends ConsumerState<KitchenScreen> {
  List<Map<String, dynamic>> orders = [];
  bool loading = true;
  String? error;
  Timer? timer;
  @override void initState() { super.initState(); _load(); timer = Timer.periodic(const Duration(seconds: 10), (_) => _load(silent: true)); }
  @override void dispose() { timer?.cancel(); super.dispose(); }
  Future<void> _load({bool silent = false}) async {
    final branch = selectedBranchStore.value;
    if (branch == null) { if (mounted) setState(() { loading = false; error = 'Select a branch first.'; }); return; }
    try { final r = await ref.read(transportProvider).get('/api/v1/merchant/branches/${branch['id']}/orders?limit=100'); if (mounted) setState(() { orders = _rows(r.data).where((o) => const {'pending', 'accepted', 'preparing', 'ready'}.contains(o['status'])).toList(); error = null; loading = false; }); }
    catch (e) { if (mounted) setState(() { loading = false; error = _error(e); }); }
  }
  @override Widget build(BuildContext context) => RefreshIndicator(onRefresh: _load, child: ListView(padding: const EdgeInsets.all(16), children: [
    const _Header('Kitchen display', 'New · accepted · preparing · ready'),
    const Text('Queue refreshes every 10 seconds. Timers do not auto-complete kitchen work.', style: TextStyle(fontSize: 11, color: QuickbuddyColors.muted)),
    if (error != null) _Notice(error!, action: TextButton(onPressed: _load, child: const Text('Retry'))),
    if (loading) const Center(child: Padding(padding: EdgeInsets.all(24), child: CircularProgressIndicator())) else if (orders.isEmpty) const _Notice('No active kitchen tickets.') else ...orders.map((o) => _KitchenTicket(order: o, onTap: () => context.push('/orders/${o['id']}'))),
    const QbPreviewNotice(message: 'Station assignment, recipe/allergen notes, sound alerts and pilot handover are not in the current backend contract.'),
  ]));
}

class _KitchenTicket extends StatelessWidget {
  const _KitchenTicket({required this.order, required this.onTap});
  final Map<String, dynamic> order;
  final VoidCallback onTap;
  @override Widget build(BuildContext context) {
    final items = order['items'] as List? ?? const [];
    return Card(child: Padding(padding: const EdgeInsets.all(13), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(children: [Expanded(child: Text('Order ${order['id']}', style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w800))), QbStatusChip('${order['status']}'.toUpperCase(), tone: order['status'] == 'ready' ? 'success' : 'warning')]),
      const SizedBox(height: 6),
      ...items.map((i) => Padding(padding: const EdgeInsets.symmetric(vertical: 3), child: Text('${i['quantity']} × ${i['product_name']} · ${i['variant_name']}', style: const TextStyle(fontSize: 13)))),
      const SizedBox(height: 8),
      OutlinedButton.icon(onPressed: onTap, icon: const Icon(Icons.open_in_new), label: const Text('Open ticket')),
    ])));
  }
}

class MenuManagementScreen extends ConsumerStatefulWidget {
  const MenuManagementScreen({super.key});
  @override ConsumerState<MenuManagementScreen> createState() => _MenuManagementScreenState();
}
class _MenuManagementScreenState extends ConsumerState<MenuManagementScreen> {
  List<Map<String, dynamic>> products = [], categories = [];
  bool loading = true;
  String? error;
  @override void initState() { super.initState(); _load(); }
  Future<void> _load() async {
    final branch = selectedBranchStore.value;
    if (branch == null) { if (mounted) setState(() { loading = false; error = 'Select a branch first.'; }); return; }
    try {
      final api = ref.read(transportProvider);
      final p = await api.get('/api/v1/merchant/branches/${branch['id']}/catalog?limit=100');
      final c = await api.get('/api/v1/catalog/categories?limit=100');
      if (mounted) setState(() { products = _rows(p.data); categories = _rows(c.data); error = null; loading = false; });
    } catch (e) { if (mounted) setState(() { error = _error(e); loading = false; }); }
  }
  Future<void> _addProduct() async {
    if (categories.isEmpty) { _toast(context, 'No configured product categories are available.'); return; }
    final name = TextEditingController(), sku = TextEditingController(), variant = TextEditingController(text: 'Regular'), price = TextEditingController();
    String categoryId = categories.first['id'] as String;
    final data = await showDialog<Map<String, String>>(context: context, builder: (ctx) => StatefulBuilder(builder: (ctx, setDialog) => AlertDialog(title: const Text('Add menu product'), content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [TextField(controller: name, decoration: const InputDecoration(labelText: 'Product name')), DropdownButtonFormField<String>(initialValue: categoryId, decoration: const InputDecoration(labelText: 'Category'), items: categories.map((c) => DropdownMenuItem(value: c['id'] as String, child: Text('${c['name']}'))).toList(), onChanged: (v) => setDialog(() => categoryId = v ?? categoryId)), TextField(controller: variant, decoration: const InputDecoration(labelText: 'Variant')), TextField(controller: sku, decoration: const InputDecoration(labelText: 'SKU')), TextField(controller: price, keyboardType: const TextInputType.numberWithOptions(decimal: true), decoration: const InputDecoration(labelText: 'Price (INR)'))])), actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')), FilledButton(onPressed: () { if (name.text.trim().isNotEmpty && sku.text.trim().isNotEmpty && double.tryParse(price.text) != null) Navigator.pop(ctx, {'name': name.text.trim(), 'category_id': categoryId, 'variant': variant.text.trim(), 'sku': sku.text.trim(), 'price': price.text.trim()}); }, child: const Text('Create'))]));
    name.dispose(); sku.dispose(); variant.dispose(); price.dispose();
    if (data == null) return;
    final branch = selectedBranchStore.value!;
    try {
      final api = ref.read(transportProvider);
      final product = await api.post('/api/v1/catalog/products', data: {'organization_id': branch['organization_id'], 'category_id': data['category_id'], 'name': data['name'], 'unit': 'each', 'variable_weight': false});
      final v = await api.post('/api/v1/catalog/products/${product.data['id']}/variants', data: {'sku': data['sku'], 'name': data['variant']});
      await api.post('/api/v1/merchants/branches/${branch['id']}/prices', data: {'variant_id': v.data['id'], 'currency': 'INR', 'amount': data['price'], 'starts_at': DateTime.now().toUtc().toIso8601String()});
      if (mounted) _toast(context, 'Product and branch price created.');
      await _load();
    } catch (e) { if (mounted) _toast(context, 'Catalogue update: ${_error(e)}. A preceding API step may have succeeded; reload before retrying.'); await _load(); }
  }
  @override Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(16), children: [
    _Header('Menu management', 'Branch-priced products from the shared catalogue'),
    QbPrimaryButton(label: 'Add product', icon: Icons.add, onPressed: _addProduct),
    if (error != null) _Notice(error!, action: TextButton(onPressed: _load, child: const Text('Retry'))),
    if (loading) const Center(child: CircularProgressIndicator()) else if (products.isEmpty) const _Notice('No branch products are configured yet.') else ...products.map((p) => Card(child: ListTile(leading: const CircleAvatar(backgroundColor: Color(0xFFF0EDFF), child: Icon(Icons.restaurant_menu, color: QuickbuddyColors.violet)), title: Text('${p['name']} · ${p['variant_name']}'), subtitle: Text('${p['currency']} ${p['unit_price']} · ${p['available_quantity']} ${p['unit']} available'), trailing: const Icon(Icons.chevron_right)))) ,
    const QbPreviewNotice(message: 'This flow creates a product, variant and branch price. Editing, image upload, modifiers, tax setup and branch visibility controls require additional backend APIs.'),
  ]);
}

class InventoryScreen extends ConsumerStatefulWidget {
  const InventoryScreen({super.key});
  @override ConsumerState<InventoryScreen> createState() => _InventoryScreenState();
}
class _InventoryScreenState extends ConsumerState<InventoryScreen> {
  List<Map<String, dynamic>> stocks = [];
  bool loading = true;
  String? error;
  @override void initState() { super.initState(); _load(); }
  Future<void> _load() async {
    final branch = selectedBranchStore.value;
    if (branch == null) { if (mounted) setState(() { loading = false; error = 'Select a branch first.'; }); return; }
    try { final r = await ref.read(transportProvider).get('/api/v1/inventory/branches/${branch['id']}?limit=100'); if (mounted) setState(() { stocks = _rows(r.data); loading = false; error = null; }); }
    catch (e) { if (mounted) setState(() { loading = false; error = _error(e); }); }
  }
  Future<void> _adjust(Map<String, dynamic> stock) async {
    final delta = TextEditingController();
    final input = await showDialog<String>(context: context, builder: (ctx) => AlertDialog(title: const Text('Adjust stock'), content: TextField(controller: delta, keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true), decoration: const InputDecoration(labelText: 'Quantity change', helperText: 'Use a positive or negative amount')), actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')), FilledButton(onPressed: () { if (double.tryParse(delta.text) != null && double.parse(delta.text) != 0) Navigator.pop(ctx, delta.text.trim()); }, child: const Text('Submit'))]));
    delta.dispose();
    if (input == null) return;
    try { await ref.read(transportProvider).post('/api/v1/inventory/branches/${selectedBranchStore.value!['id']}/adjustments', data: {'variant_id': stock['variant_id'], 'delta': input, 'idempotency_key': _key()}); await _load(); }
    catch (e) { if (mounted) _toast(context, _error(e)); }
  }
  @override Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(16), children: [
    const _Header('Inventory & availability', 'Backend stock balances · adjustments are attributed to your account'),
    if (error != null) _Notice(error!, action: TextButton(onPressed: _load, child: const Text('Retry'))),
    if (loading) const Center(child: CircularProgressIndicator()) else if (stocks.isEmpty) const _Notice('No stock balances exist for this branch.') else ...stocks.map((s) { final onHand = double.tryParse('${s['on_hand']}') ?? 0; final reserved = double.tryParse('${s['reserved']}') ?? 0; return Card(child: ListTile(title: Text('Variant ${s['variant_id']}', maxLines: 1, overflow: TextOverflow.ellipsis), subtitle: Text('On hand $onHand · Reserved $reserved · Sellable ${onHand - reserved}'), trailing: IconButton(tooltip: 'Adjust stock', onPressed: () => _adjust(s), icon: const Icon(Icons.tune, color: QuickbuddyColors.orange)))); }),
    const QbPreviewNotice(message: 'Stock movement history is available separately. This screen does not invent ingredient/BOM quantities, product names, expiry lots or low-stock thresholds.'),
  ]);
}

class BranchSettingsScreen extends ConsumerWidget {
  const BranchSettingsScreen({super.key});
  @override Widget build(BuildContext context, WidgetRef ref) => ListView(padding: const EdgeInsets.all(16), children: [
    const _Header('Branch settings', 'Switch authorized branches and manage availability'),
    ValueListenableBuilder<Map<String, dynamic>?>(valueListenable: selectedBranchStore, builder: (context, branch, _) => branch == null ? const _Notice('No active branch selected.') : Card(child: ListTile(leading: const Icon(Icons.storefront, color: QuickbuddyColors.violet), title: Text('${branch['name']}'), subtitle: Text('Status: ${branch['status']} · Orders ${branch['accepting_orders'] == true ? 'open' : 'paused'}'))),
    _FeatureRow('Business hours', 'No read/update hours UI is available yet.', Icons.schedule),
    _FeatureRow('Pilot handover', 'Pickup verification is not exposed for merchant users.', Icons.delivery_dining),
    _FeatureRow('Staff permissions', 'Organization membership administration is restricted to the existing API policy.', Icons.people_outline),
    _FeatureRow('Payout account', 'Sensitive banking changes are not available in this app.', Icons.account_balance),
    TextButton.icon(onPressed: () async { await tokenStore.clear(); await tokenStore.deleteValue('merchant_branch_id'); selectedBranchStore.value = null; if (context.mounted) context.go('/sign-in'); }, icon: const Icon(Icons.logout), label: const Text('Sign out')),
  ]);
}

class UnavailableFeatureScreen extends StatelessWidget {
  const UnavailableFeatureScreen({super.key, required this.title, required this.detail});
  final String title, detail;
  @override Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(18), children: [_Header(title, 'Backend capability not connected'), _Notice(detail)]);
}

class _Header extends StatelessWidget {
  const _Header(this.title, this.subtitle);
  final String title, subtitle;
  @override Widget build(BuildContext context) => Padding(padding: const EdgeInsets.only(bottom: 12), child: Row(children: [Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(title, style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w800, color: QuickbuddyColors.indigo)), const SizedBox(height: 4), Text(subtitle, style: const TextStyle(fontSize: 11, color: QuickbuddyColors.muted))])), IconButton(tooltip: 'Dashboard', onPressed: () => context.go('/dashboard'), icon: const Icon(Icons.home_outlined))]));
}

class _Section extends StatelessWidget { const _Section(this.text); final String text; @override Widget build(BuildContext context) => Padding(padding: const EdgeInsets.symmetric(vertical: 8), child: Text(text, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800, color: QuickbuddyColors.indigo))); }
class _Notice extends StatelessWidget { const _Notice(this.text, {this.action}); final String text; final Widget? action; @override Widget build(BuildContext context) => QbPanel(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(text, style: const TextStyle(fontSize: 12, height: 1.4)), if (action != null) Align(alignment: Alignment.centerRight, child: action!)])); }
class _CountTile extends StatelessWidget { const _CountTile(this.label, this.count, this.icon, this.color); final String label, count; final IconData icon; final Color color; @override Widget build(BuildContext context) => Expanded(child: QbPanel(padding: const EdgeInsets.all(11), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Icon(icon, color: color, size: 18), const SizedBox(height: 8), Text(count, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: QuickbuddyColors.indigo)), Text(label, style: const TextStyle(fontSize: 10, color: QuickbuddyColors.muted))]))); }
class _ActionTile extends StatelessWidget { const _ActionTile(this.label, this.icon, this.onTap); final String label; final IconData icon; final VoidCallback onTap; @override Widget build(BuildContext context) => Expanded(child: Padding(padding: const EdgeInsets.only(top: 8), child: Card(child: ListTile(onTap: onTap, leading: Icon(icon, color: QuickbuddyColors.violet), title: Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700)), trailing: const Icon(Icons.chevron_right))))); }
class _FeatureRow extends StatelessWidget { const _FeatureRow(this.title, this.detail, this.icon); final String title, detail; final IconData icon; @override Widget build(BuildContext context) => Card(child: ListTile(leading: Icon(icon, color: QuickbuddyColors.violet), title: Text(title), subtitle: Text(detail, style: const TextStyle(fontSize: 11)))); }
