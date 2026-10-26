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
final cartIdStore = ValueNotifier<String?>(null);
final cartCountStore = ValueNotifier<int>(0);
const appEnvironment = String.fromEnvironment('APP_ENV', defaultValue: 'development');
bool get sandboxEnabled => appEnvironment == 'development' || appEnvironment == 'test';

final router = GoRouter(routes: [
  ShellRoute(
    builder: (context, state, child) => CustomerShell(path: state.uri.path, child: child),
    routes: [
      GoRoute(path: '/', builder: (_, __) => const HomeScreen()),
      GoRoute(path: '/onboarding', builder: (_, __) => const OnboardingScreen()),
      GoRoute(path: '/sign-in', builder: (_, __) => const SignInScreen()),
      GoRoute(path: '/restaurants', builder: (_, __) => const BranchesScreen()),
      GoRoute(path: '/restaurant/:id', builder: (_, s) => BranchScreen(id: s.pathParameters['id']!)),
      GoRoute(path: '/search', builder: (_, s) => CatalogScreen(merchantType: s.uri.queryParameters['type'])),
      GoRoute(path: '/cart', builder: (_, __) => const CartScreen()),
      GoRoute(path: '/checkout/address-payment', builder: (_, __) => const CheckoutScreen()),
      GoRoute(path: '/checkout/schedule', builder: (_, __) => const CheckoutScreen()),
      GoRoute(path: '/orders', builder: (_, __) => const OrdersScreen()),
      GoRoute(path: '/orders/:orderId/tracking', builder: (_, s) => TrackingScreen(orderId: s.pathParameters['orderId']!)),
      GoRoute(path: '/orders/:orderId/complete', builder: (_, s) => OrderScreen(orderId: s.pathParameters['orderId']!)),
      GoRoute(path: '/account', builder: (_, __) => const AccountScreen()),
    ],
  ),
]);

ThemeData customerTheme() => quickbuddyTheme().copyWith(
  scaffoldBackgroundColor: Colors.white,
  navigationBarTheme: const NavigationBarThemeData(
    backgroundColor: Colors.white,
    indicatorColor: Color(0xFFFFEEE5),
    height: 64,
    labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
  ),
);

void main() => runApp(ProviderScope(child: QuickbuddyApp(
  title: 'Quickbuddy', theme: customerTheme(), router: router)));

class CustomerShell extends StatelessWidget {
  const CustomerShell({super.key, required this.path, required this.child});
  final String path;
  final Widget child;
  @override
  Widget build(BuildContext context) {
    final selected = path == '/search' ? 1 : path.startsWith('/orders') ? 2 : path == '/account' ? 3 : 0;
    return Scaffold(
      body: SafeArea(child: child),
      bottomNavigationBar: path == '/onboarding' || path == '/sign-in' ? null : NavigationBar(
        height: 65, selectedIndex: selected, backgroundColor: Colors.white,
        indicatorColor: QuickbuddyColors.orange.withValues(alpha: .10),
        onDestinationSelected: (i) => context.go(switch (i) {1 => '/search', 2 => '/orders', 3 => '/account', _ => '/'}),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.search), label: 'Search'),
          NavigationDestination(icon: Icon(Icons.receipt_long_outlined), label: 'Orders'),
          NavigationDestination(icon: Icon(Icons.person_outline), label: 'Account'),
        ],
      ),
    );
  }
}

Future<bool> _signedIn() async => await tokenStore.accessToken() != null;
Future<void> _requireSignIn(BuildContext context) async {
  if (!await _signedIn() && context.mounted) await context.push('/sign-in');
}
String _message(Object error) {
  if (error is DioException) {
    final data = error.response?.data;
    if (data is Map && data['detail'] is String) return data['detail'] as String;
    if (error.response?.statusCode == 401) return 'Please sign in again to continue.';
    return error.message ?? 'The service is temporarily unavailable.';
  }
  return error.toString();
}
void _snack(BuildContext context, String message) => ScaffoldMessenger.of(context)
  ..hideCurrentSnackBar()
  ..showSnackBar(SnackBar(content: Text(message)));
List<Map<String, dynamic>> _items(dynamic data) => data is Map && data['items'] is List
    ? (data['items'] as List).whereType<Map>().map((x) => Map<String, dynamic>.from(x)).toList()
    : <Map<String, dynamic>>[];
String _uuidKey() {
  final random = Random.secure();
  return List.generate(32, (_) => random.nextInt(16).toRadixString(16)).join();
}
Future<int> _refreshCartCount(Dio api) async {
  if (!await _signedIn()) { cartCountStore.value = 0; return 0; }
  final id = cartIdStore.value ?? await tokenStore.readValue('qb_cart');
  if (id == null) { cartCountStore.value = 0; return 0; }
  cartIdStore.value = id;
  final response = await api.get('/api/v1/carts/$id/items?limit=100');
  final count = _items(response.data).fold<int>(0, (sum, item) => sum + num.parse('${item['quantity']}').ceil());
  cartCountStore.value = count;
  return count;
}
String _windowLabel(BuildContext context, dynamic start, dynamic end) {
  if (start is! String) return 'Scheduled delivery';
  final begins = DateTime.tryParse(start)?.toLocal();
  final ends = end is String ? DateTime.tryParse(end)?.toLocal() : null;
  if (begins == null) return 'Scheduled delivery';
  final localizations = MaterialLocalizations.of(context);
  final date = localizations.formatMediumDate(begins);
  final from = localizations.formatTimeOfDay(TimeOfDay.fromDateTime(begins));
  final to = ends == null ? '' : '–${localizations.formatTimeOfDay(TimeOfDay.fromDateTime(ends))}';
  return '$date · $from$to';
}

class HomeScreen extends ConsumerStatefulWidget {
  const HomeScreen({super.key});
  @override ConsumerState<HomeScreen> createState() => _HomeScreenState();
}
class _HomeScreenState extends ConsumerState<HomeScreen> {
  bool loading = true, addressLoading = false, picksLoading = false;
  String? error, selectedAddress, activeOrderId;
  List<Map<String, dynamic>> branches = [], picks = [];
  @override void initState() { super.initState(); _load(); }
  Future<void> _load() async {
    try {
      final response = await ref.read(transportProvider).get('/api/v1/merchants/branches?limit=12');
      if (mounted) setState(() { branches = _items(response.data); loading = false; error = null; });
      unawaited(_refreshCartCount(ref.read(transportProvider)).catchError((_) => 0));
    } catch (e) { if (mounted) setState(() { loading = false; error = _message(e); }); }
    unawaited(_loadAddress());
    unawaited(_loadActiveOrder());
  }
  Future<void> _loadAddress() async {
    if (!await _signedIn()) return;
    try {
      final api = ref.read(transportProvider);
      final savedId = await tokenStore.readValue('qb_home_address');
      final rows = _items((await api.get('/api/v1/addresses?limit=50')).data);
      if (!mounted || rows.isEmpty) return;
      final address = rows.firstWhere((a) => a['id'] == savedId, orElse: () => rows.first);
      await tokenStore.writeValue('qb_home_address', address['id'] as String);
      setState(() => selectedAddress = '${address['label']} · ${address['address_text']}');
      unawaited(_loadRecommendations(address['city_id'].toString()));
    } catch (_) { /* A public home remains usable when personal address lookup fails. */ }
  }
  Future<void> _loadRecommendations(String cityId) async {
    if (!await _signedIn()) return;
    if (mounted) setState(() => picksLoading = true);
    try {
      final response = await ref.read(transportProvider).post('/api/v1/ai/recommendations/products', data: {'city_id': cityId, 'limit': 8});
      if (mounted) setState(() { picks = _items(response.data); picksLoading = false; });
    } catch (_) { if (mounted) setState(() => picksLoading = false); }
  }
  Future<void> _loadActiveOrder() async {
    if (!await _signedIn()) return;
    try {
      final rows = _items((await ref.read(transportProvider).get('/api/v1/orders?limit=10')).data);
      final active = rows.where((o) => const {'confirmed', 'preparing', 'accepted', 'in_transit'}.contains(o['status']));
      if (mounted) setState(() => activeOrderId = active.isEmpty ? null : active.first['id']?.toString());
    } catch (_) { /* Home discovery does not wait for order history. */ }
  }
  Future<void> _chooseAddress() async {
    if (!await _signedIn()) { if (mounted) await context.push('/sign-in'); await _loadAddress(); return; }
    setState(() => addressLoading = true);
    try {
      final rows = _items((await ref.read(transportProvider).get('/api/v1/addresses?limit=50')).data);
      if (!mounted) return;
      if (rows.isEmpty) { await context.push('/account'); await _loadAddress(); return; }
      final selected = await showModalBottomSheet<Map<String, dynamic>>(context: context, showDragHandle: true, builder: (ctx) => SafeArea(child: ListView(shrinkWrap: true, padding: const EdgeInsets.all(16), children: [const Text('Deliver to', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)), const SizedBox(height: 8), ...rows.map((a) => ListTile(leading: const Icon(Icons.location_on_outlined), title: Text('${a['label']}'), subtitle: Text('${a['address_text']}'), onTap: () => Navigator.pop(ctx, a))), TextButton.icon(onPressed: () => Navigator.pop(ctx), icon: const Icon(Icons.add), label: const Text('Manage addresses'))])));
      if (selected != null) {
        await tokenStore.writeValue('qb_home_address', selected['id'] as String);
        if (mounted) setState(() => selectedAddress = '${selected['label']} · ${selected['address_text']}');
        unawaited(_loadRecommendations(selected['city_id'].toString()));
      }
    } catch (e) { if (mounted) _snack(context, _message(e)); }
    finally { if (mounted) setState(() => addressLoading = false); }
  }
  void _browseType(String type) => context.push('/search?type=$type');
  @override Widget build(BuildContext context) => RefreshIndicator(onRefresh: _load, child: ListView(padding: const EdgeInsets.fromLTRB(16, 8, 16, 22), children: [
    Row(children: [InkWell(onTap: () => context.push('/onboarding'), child: const QbBrand()), const Spacer(), ValueListenableBuilder<int>(valueListenable: cartCountStore, builder: (_, count, __) => IconButton(tooltip: 'Your cart', onPressed: () => context.push('/cart'), icon: Badge(isLabelVisible: count > 0, label: Text('$count'), child: const Icon(Icons.shopping_bag_outlined)))), IconButton(tooltip: 'Account', onPressed: () => context.go('/account'), icon: const Icon(Icons.person_outline))]),
    Row(children: [
      InkWell(onTap: _chooseAddress, borderRadius: BorderRadius.circular(12), child: Row(mainAxisSize: MainAxisSize.min, children: [
        const Icon(Icons.location_on_rounded, color: QuickbuddyColors.orange, size: 20), const SizedBox(width: 5),
        Column(crossAxisAlignment: CrossAxisAlignment.start, children: [const Text('Deliver to', style: TextStyle(fontSize: 10, color: QuickbuddyColors.muted)), Text(addressLoading ? 'Loading address…' : selectedAddress ?? 'Choose your location', maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700))]),
        const Icon(Icons.keyboard_arrow_down, size: 18),
      ])),
      const Spacer(),
    ]),
    const SizedBox(height: 10),
    InkWell(onTap: () => context.go('/search'), child: IgnorePointer(child: TextField(decoration: InputDecoration(prefixIcon: const Icon(Icons.search), hintText: 'Search restaurants, products…', filled: true, fillColor: Colors.white, border: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: QuickbuddyColors.line)))))),
    const SizedBox(height: 12),
    Row(children: [
      _HomeCategory(icon: Icons.restaurant, title: 'Food', tint: QuickbuddyColors.orange, onTap: () => _browseType('food')),
      _HomeCategory(icon: Icons.shopping_basket, title: 'Groceries', tint: QuickbuddyColors.green, onTap: () => _browseType('grocery')),
      _HomeCategory(icon: Icons.medical_services, title: 'Medicines', tint: QuickbuddyColors.violet, onTap: () => _browseType('pharmacy')),
      _HomeCategory(icon: Icons.local_mall, title: 'Essentials', tint: QuickbuddyColors.blue, onTap: () => _browseType('retail')),
    ]),
    const SizedBox(height: 12),
    _PromotionCard(onTap: () => context.go('/restaurants')),
    if (activeOrderId != null) ...[
      const SizedBox(height: 14),
      Card(child: ListTile(leading: const CircleAvatar(backgroundColor: Color(0xFFEAF8F1), child: Icon(Icons.delivery_dining, color: QuickbuddyColors.green)), title: const Text('Your order is in progress', style: TextStyle(fontWeight: FontWeight.w700)), subtitle: Text('Order ${activeOrderId!}', maxLines: 1, overflow: TextOverflow.ellipsis), trailing: const Icon(Icons.chevron_right), onTap: () => context.push('/orders/$activeOrderId/tracking'))),
    ],
    const SizedBox(height: 14),
    QbSectionTitle('Top merchants near you', action: 'See all', onAction: () => context.go('/restaurants')),
    if (loading) const _MerchantSkeletonRow()
    else if (error != null) _InfoCard(text: error!, action: TextButton(onPressed: _load, child: const Text('Retry')))
    else if (branches.isEmpty) const _InfoCard(text: 'No accepting merchants are available yet. Try again later.')
    else SizedBox(height: 178, child: ListView.separated(scrollDirection: Axis.horizontal, itemCount: branches.length.clamp(0, 12), separatorBuilder: (_, __) => const SizedBox(width: 10), itemBuilder: (context, index) => _MerchantTile(branch: branches[index]))),
    if (picksLoading || picks.isNotEmpty) ...[
      const SizedBox(height: 14),
      const QbSectionTitle('Quickbuddy picks'),
      const Text('Available nearby · deterministic suggestions, not personal-history predictions.', style: TextStyle(fontSize: 10, color: QuickbuddyColors.muted)),
      const SizedBox(height: 7),
      if (picksLoading) const _MerchantSkeletonRow() else SizedBox(height: 116, child: ListView.separated(scrollDirection: Axis.horizontal, itemCount: picks.length, separatorBuilder: (_, __) => const SizedBox(width: 8), itemBuilder: (context, index) {
        final item = picks[index];
        return SizedBox(width: 245, child: Card(child: ListTile(leading: const Icon(Icons.recommend_outlined, color: QuickbuddyColors.violet), title: Text('${item['product']} · ${item['variant']}', maxLines: 1, overflow: TextOverflow.ellipsis), subtitle: Text('${item['currency']} ${item['price']} · ${item['available_quantity']} available'), onTap: () => context.push('/restaurant/${item['branch_id']}'))));
      })),
    ],
    const SizedBox(height: 8),
    QbSectionTitle('Explore more', action: 'Browse', onAction: () => context.go('/restaurants')),
    Wrap(spacing: 8, runSpacing: 8, children: [
      _ExploreTile(icon: Icons.local_florist_outlined, label: 'Fresh produce', onTap: () => _browseType('grocery')),
      _ExploreTile(icon: Icons.health_and_safety_outlined, label: 'Health & wellness', onTap: () => _browseType('pharmacy')),
      _ExploreTile(icon: Icons.home_outlined, label: 'Home essentials', onTap: () => _browseType('retail')),
    ]),
    const SizedBox(height: 14),
    if (selectedAddress == null) TextButton.icon(onPressed: () => context.push('/sign-in'), icon: const Icon(Icons.lock_outline), label: const Text('Sign in for saved addresses and orders')),
  ]));
}

class _HomeCategory extends StatelessWidget {
  const _HomeCategory({required this.icon, required this.title, required this.tint, required this.onTap});
  final IconData icon; final String title; final Color tint; final VoidCallback onTap;
  @override Widget build(BuildContext context) => Expanded(child: Semantics(button: true, label: 'Browse $title', child: InkWell(onTap: onTap, borderRadius: BorderRadius.circular(13), child: Padding(padding: const EdgeInsets.symmetric(vertical: 4), child: Column(children: [Container(width: 48, height: 48, decoration: BoxDecoration(color: tint.withValues(alpha: .11), borderRadius: BorderRadius.circular(14)), child: Icon(icon, color: tint)), const SizedBox(height: 5), Text(title, maxLines: 1, style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w600))])))));
}

class _PromotionCard extends StatelessWidget {
  const _PromotionCard({required this.onTap}); final VoidCallback onTap;
  @override Widget build(BuildContext context) => Semantics(button: true, label: 'Browse nearby merchants', child: InkWell(onTap: onTap, borderRadius: BorderRadius.circular(15), child: ClipRRect(borderRadius: BorderRadius.circular(15), child: SizedBox(height: 142, child: Stack(fit: StackFit.expand, children: [
    Image.asset('packages/flutter_design_system/assets/images/burger.webp', fit: BoxFit.cover),
    Container(color: const Color(0x770E0B20)),
    Padding(padding: const EdgeInsets.all(15), child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.center, children: [
      const Text('Cravings? We’ll be there.', style: TextStyle(color: Colors.white, fontSize: 19, fontWeight: FontWeight.w800)),
      const SizedBox(height: 5), const Text('Discover local favorites for today.', style: TextStyle(color: Colors.white, fontSize: 11)),
      const SizedBox(height: 10), FilledButton.tonal(onPressed: onTap, child: const Text('Browse now')),
    ])),
  ])))));
}

class _MerchantTile extends StatelessWidget {
  const _MerchantTile({required this.branch}); final Map<String, dynamic> branch;
  @override Widget build(BuildContext context) => SizedBox(width: 148, child: Semantics(button: true, label: 'Open ${branch['name']}', child: InkWell(onTap: () => context.push('/restaurant/${branch['id']}'), borderRadius: BorderRadius.circular(13), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    ClipRRect(borderRadius: BorderRadius.circular(12), child: Image.asset('packages/flutter_design_system/assets/images/${_branchImage(branch)}.webp', width: 148, height: 102, fit: BoxFit.cover)),
    const SizedBox(height: 6), Text('${branch['name']}', maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700)),
    const SizedBox(height: 2), const Text('Accepting orders', style: TextStyle(fontSize: 10, color: QuickbuddyColors.muted)),
  ]))));
}
String _branchImage(Map<String, dynamic> branch) => switch (branch['merchant_type']) { 'grocery' => 'produce', 'retail' => 'pizza', 'pharmacy' => 'curry', 'parcel' => 'rider', _ => 'curry' };

class _ExploreTile extends StatelessWidget {
  const _ExploreTile({required this.icon, required this.label, required this.onTap}); final IconData icon; final String label; final VoidCallback onTap;
  @override Widget build(BuildContext context) => ActionChip(avatar: Icon(icon, size: 17, color: QuickbuddyColors.violet), label: Text(label), onPressed: onTap);
}
class _MerchantSkeletonRow extends StatelessWidget {
  const _MerchantSkeletonRow();
  @override Widget build(BuildContext context) => SizedBox(height: 174, child: ListView.separated(scrollDirection: Axis.horizontal, itemCount: 3, separatorBuilder: (_, __) => const SizedBox(width: 10), itemBuilder: (_, __) => SizedBox(width: 148, child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Container(height: 102, decoration: BoxDecoration(color: QuickbuddyColors.line, borderRadius: BorderRadius.circular(12))), const SizedBox(height: 8), Container(height: 10, width: 110, color: QuickbuddyColors.line), const SizedBox(height: 6), Container(height: 8, width: 75, color: QuickbuddyColors.line)]))));
}

class _CartSummaryBar extends StatelessWidget {
  const _CartSummaryBar({required this.count, required this.onTap});
  final int count;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => Material(
    color: Colors.white,
    elevation: 6,
    child: SafeArea(top: false, child: Padding(
      padding: const EdgeInsets.fromLTRB(16, 9, 16, 8),
      child: SizedBox(height: 46, child: FilledButton(
        onPressed: onTap,
        style: FilledButton.styleFrom(backgroundColor: QuickbuddyColors.orange, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
        child: Row(children: [Text('$count item${count == 1 ? '' : 's'} in cart', style: const TextStyle(fontWeight: FontWeight.w700)), const Spacer(), const Text('View cart'), const SizedBox(width: 7), const Icon(Icons.arrow_forward, size: 17)]),
      )),
    )),
  );
}

class BranchesScreen extends ConsumerStatefulWidget {
  const BranchesScreen({super.key});
  @override ConsumerState<BranchesScreen> createState() => _BranchesScreenState();
}
class _BranchesScreenState extends ConsumerState<BranchesScreen> {
  bool loading = true, loadingMore = false; String? error, nextCursor; List<Map<String, dynamic>> branches = [];
  @override void initState() { super.initState(); _load(); }
  Future<void> _load({bool more = false}) async {
    if (more && (nextCursor == null || loadingMore)) return;
    setState(() { if (more) { loadingMore = true; } else { loading = true; error = null; } });
    try {
      final response = await ref.read(transportProvider).get('/api/v1/merchants/branches', queryParameters: {'limit': 50, if (more) 'cursor': nextCursor});
      final batch = _items(response.data);
      if (mounted) setState(() { branches = more ? [...branches, ...batch] : batch; nextCursor = response.data['next_cursor'] as String?; loading = false; loadingMore = false; error = null; });
    } catch (e) { if (mounted) setState(() { loading = false; loadingMore = false; error = _message(e); }); }
  }
  @override Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(16), children: [const _PageHeader(title: 'Local merchants', subtitle: 'Accepting orders from the Quickbuddy network'), if (loading) const _MerchantSkeletonRow() else if (error != null && branches.isEmpty) _InfoCard(text: error!, action: TextButton(onPressed: _load, child: const Text('Retry'))) else if (branches.isEmpty) const _InfoCard(text: 'No merchants are open for orders right now.') else ...branches.map((b) => _BranchCard(branch: b)), if (loadingMore) const Center(child: CircularProgressIndicator()), if (nextCursor != null) TextButton(onPressed: () => _load(more: true), child: const Text('Load more merchants'))]);
}

class _BranchCard extends StatelessWidget {
  const _BranchCard({required this.branch}); final Map<String, dynamic> branch;
  @override Widget build(BuildContext context) => Card(child: ListTile(
    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
    leading: ClipRRect(borderRadius: BorderRadius.circular(10), child: Image.asset('packages/flutter_design_system/assets/images/${_branchImage(branch)}.webp', width: 68, height: 62, fit: BoxFit.cover)),
    title: Text('${branch['name'] ?? 'Merchant'}', style: const TextStyle(fontWeight: FontWeight.w700)),
    subtitle: Text('Verified merchant · ${branch['status'] ?? 'available'}'),
    trailing: const Icon(Icons.chevron_right), onTap: () => context.push('/restaurant/${branch['id']}'),
  ));
}

class BranchScreen extends ConsumerStatefulWidget {
  const BranchScreen({super.key, required this.id}); final String id;
  @override ConsumerState<BranchScreen> createState() => _BranchScreenState();
}
class _BranchScreenState extends ConsumerState<BranchScreen> {
  bool loading = true; String? error; String branchName = 'Merchant menu', merchantType = 'food'; List<Map<String, dynamic>> products = [];
  @override void initState() { super.initState(); _load(); }
  Future<void> _load() async {
    if (!await _signedIn()) { if (mounted) setState(() { loading = false; error = 'Sign in to load current products and prices.'; }); return; }
    try { final r = await ref.read(transportProvider).get('/api/v1/catalog/products', queryParameters: {'branch_id': widget.id, 'limit': 50}); if (mounted) setState(() { products = _items(r.data); if (products.isNotEmpty) { branchName = products.first['branch_name']?.toString() ?? branchName; merchantType = products.first['merchant_type']?.toString() ?? merchantType; } loading = false; error = null; }); }
    catch (e) { if (mounted) setState(() { loading = false; error = _message(e); }); }
  }
  Future<void> _add(Map<String, dynamic> product) async {
    try {
      await _requireSignIn(context);
      final dio = ref.read(transportProvider);
      String? cartId = cartIdStore.value;
      cartId ??= await tokenStore.readValue('qb_cart');
      if (cartId == null) {
        final c = await dio.post('/api/v1/carts');
        cartId = c.data['id'] as String;
        await tokenStore.writeValue('qb_cart', cartId);
        cartIdStore.value = cartId;
      }
      final windows = _items((await dio.get('/api/v1/merchants/branches/${widget.id}/windows?limit=30')).data);
      if (windows.isEmpty) throw Exception('This merchant has no future delivery windows configured.');
      final addresses = _items((await dio.get('/api/v1/addresses?limit=50')).data);
      final lastMethod = await tokenStore.readValue('qb_last_delivery_method');
      final lastAddressId = await tokenStore.readValue('qb_home_address');
      final lastWindowId = await tokenStore.readValue('qb_last_window_${widget.id}');
      final savedWindow = windows.where((w) => w['id'] == lastWindowId).firstOrNull;
      final savedAddress = addresses.where((a) => a['id'] == lastAddressId).firstOrNull;
      final savedMethod = lastMethod == 'courier' && savedAddress != null ? 'courier' : lastMethod == 'pickup' ? 'pickup' : null;
      if (savedWindow != null && savedMethod != null) {
        await dio.post('/api/v1/carts/$cartId/items', data: {
          'branch_id': widget.id,
          'variant_id': product['variant_id'],
          'quantity': 1,
          'window_id': savedWindow['id'],
          'delivery_method': savedMethod,
          if (savedMethod == 'courier') 'address_id': savedAddress!['id'],
        });
        await _refreshCartCount(dio);
        if (mounted) _snack(context, '${product['name']} added to your cart.');
        return;
      }
      if (!mounted) return;
      final chosen = await showModalBottomSheet<Map<String, dynamic>>(context: context, showDragHandle: true, builder: (ctx) {
        String method = addresses.isNotEmpty && lastMethod == 'courier' ? 'courier' : 'pickup';
        String? addressId = addresses.isEmpty ? null : addresses.firstWhere((a) => a['id'] == lastAddressId, orElse: () => addresses.first)['id'] as String;
        String windowId = windows.firstWhere((w) => w['id'] == lastWindowId, orElse: () => windows.first)['id'] as String;
        return StatefulBuilder(builder: (ctx, update) => SafeArea(child: ListView(padding: const EdgeInsets.all(16), shrinkWrap: true, children: [
          const Text('Choose a delivery option', style: TextStyle(fontWeight: FontWeight.w700, fontSize: 18)),
          RadioListTile<String>(value: 'pickup', groupValue: method, onChanged: (v) => update(() => method = v!), title: const Text('Pickup'), subtitle: const Text('Collect from the merchant')),
          if (addresses.isNotEmpty) RadioListTile<String>(value: 'courier', groupValue: method, onChanged: (v) => update(() => method = v!), title: const Text('Courier delivery'), subtitle: const Text('Serviceability is checked at checkout')),
          if (method == 'courier') ...addresses.map((a) => RadioListTile<String>(value: a['id'] as String, groupValue: addressId, onChanged: (v) => update(() => addressId = v), title: Text('${a['label']}'), subtitle: Text('${a['address_text']}'))),
          const SizedBox(height: 8), const Text('Select a future merchant window', style: TextStyle(fontWeight: FontWeight.w700)),
          ...windows.map((w) => RadioListTile<String>(value: w['id'] as String, groupValue: windowId, onChanged: (v) => update(() => windowId = v!), title: Text('${w['starts_at']}'), subtitle: Text('Ends ${w['ends_at']}'))),
          FilledButton(onPressed: method == 'courier' && addressId == null ? null : () => Navigator.pop(ctx, {'window_id': windowId, 'delivery_method': method, 'address_id': method == 'courier' ? addressId : null}), child: const Text('Add to cart')),
        ])));
      });
      if (chosen == null) return;
      await dio.post('/api/v1/carts/$cartId/items', data: {'branch_id': widget.id, 'variant_id': product['variant_id'], 'quantity': 1, ...chosen});
      await tokenStore.writeValue('qb_last_delivery_method', chosen['delivery_method'] as String);
      if (chosen['address_id'] is String) await tokenStore.writeValue('qb_home_address', chosen['address_id'] as String);
      await tokenStore.writeValue('qb_last_window_${widget.id}', chosen['window_id'] as String);
      await _refreshCartCount(dio);
      if (mounted) _snack(context, '${product['name']} added to your cart.');
    } catch (e) { if (mounted) _snack(context, _message(e)); }
  }
  @override Widget build(BuildContext context) => Column(children: [
    Expanded(child: ListView(padding: const EdgeInsets.all(16), children: [
    _PageHeader(title: branchName, subtitle: 'Current catalogue · prices checked again at checkout'),
    if (products.isNotEmpty) ClipRRect(borderRadius: BorderRadius.circular(14), child: Image.asset('packages/flutter_design_system/assets/images/${_branchImage({'merchant_type': merchantType})}.webp', height: 124, width: double.infinity, fit: BoxFit.cover)),
    if (products.isNotEmpty) const SizedBox(height: 10),
    const SizedBox(height: 10),
    if (loading) const _MerchantSkeletonRow() else if (error != null) _InfoCard(text: error!, action: TextButton(onPressed: error!.startsWith('Sign in') ? () => context.push('/sign-in').then((_) => _load()) : _load, child: Text(error!.startsWith('Sign in') ? 'Sign in' : 'Retry'))) else if (products.isEmpty) const _InfoCard(text: 'No currently priced, in-stock products are available for this branch.') else ...products.map((p) => Card(child: ListTile(
      leading: const CircleAvatar(backgroundColor: Color(0xFFF0EDFF), child: Icon(Icons.inventory_2_outlined, color: QuickbuddyColors.violet)),
      title: Text('${p['name']} · ${p['variant_name']}', style: const TextStyle(fontWeight: FontWeight.w700)),
      subtitle: Text('${p['available_quantity']} ${p['unit']} available · ${p['currency']} ${p['unit_price']}'),
      trailing: IconButton(onPressed: () => _add(p), icon: const Icon(Icons.add_circle, color: QuickbuddyColors.orange)),
    ))),
    OutlinedButton.icon(onPressed: () => context.push('/cart'), icon: const Icon(Icons.shopping_bag_outlined), label: const Text('View cart')),
    ])),
    ValueListenableBuilder<int>(valueListenable: cartCountStore, builder: (context, count, _) => count == 0 ? const SizedBox.shrink() : _CartSummaryBar(count: count, onTap: () => context.push('/checkout/address-payment'))),
  ]);
}

class CatalogScreen extends ConsumerStatefulWidget {
  const CatalogScreen({super.key, this.merchantType});
  final String? merchantType;
  @override ConsumerState<CatalogScreen> createState() => _CatalogScreenState();
}
class _CatalogScreenState extends ConsumerState<CatalogScreen> {
  final search = TextEditingController(); Timer? debounce; CancelToken? requestCancel; bool loading = false, loadingMore = false; String? error, selectedType, nextCursor; List<Map<String, dynamic>> products = [];
  @override void initState() { super.initState(); selectedType = widget.merchantType; _load(); }
  @override void dispose() { debounce?.cancel(); requestCancel?.cancel('Search screen disposed'); search.dispose(); super.dispose(); }
  Future<void> _load() async {
    if (!await _signedIn()) { if (mounted) setState(() { error = 'Sign in to search current products and prices.'; loading = false; }); return; }
    requestCancel?.cancel('New search query');
    final cancel = CancelToken();
    requestCancel = cancel;
    setState(() { loading = true; loadingMore = false; error = null; nextCursor = null; });
    try { final r = await ref.read(transportProvider).get('/api/v1/catalog/products', cancelToken: cancel, queryParameters: {'q': search.text.trim().isEmpty ? null : search.text.trim(), 'merchant_type': selectedType, 'limit': 50}); if (mounted && !cancel.isCancelled) setState(() { products = _items(r.data); nextCursor = r.data['next_cursor'] as String?; loading = false; }); }
    on DioException catch (e) { if (!CancelToken.isCancel(e) && mounted) setState(() { error = _message(e); loading = false; }); }
    catch (e) { if (mounted) setState(() { error = _message(e); loading = false; }); }
  }
  Future<void> _loadMore() async {
    if (nextCursor == null || loadingMore || loading) return;
    setState(() => loadingMore = true);
    final cancel = CancelToken();
    requestCancel = cancel;
    try {
      final r = await ref.read(transportProvider).get('/api/v1/catalog/products', cancelToken: cancel, queryParameters: {'q': search.text.trim().isEmpty ? null : search.text.trim(), 'merchant_type': selectedType, 'cursor': nextCursor, 'limit': 50});
      if (mounted && !cancel.isCancelled) setState(() { products = [...products, ..._items(r.data)]; nextCursor = r.data['next_cursor'] as String?; loadingMore = false; });
    } on DioException catch (e) { if (!CancelToken.isCancel(e) && mounted) setState(() { loadingMore = false; error = _message(e); }); }
    catch (e) { if (mounted) setState(() { loadingMore = false; error = _message(e); }); }
  }
  @override Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(16), children: [
    const _PageHeader(title: 'Search', subtitle: 'Merchants and products available now'),
    TextField(controller: search, onChanged: (_) { requestCancel?.cancel('Search changed'); debounce?.cancel(); debounce = Timer(const Duration(milliseconds: 300), _load); }, onSubmitted: (_) => _load(), decoration: InputDecoration(prefixIcon: const Icon(Icons.search), hintText: 'Search products and merchants', suffixIcon: IconButton(tooltip: 'Clear search', icon: const Icon(Icons.close), onPressed: () { search.clear(); _load(); }))),
    const SizedBox(height: 8),
    SizedBox(height: 40, child: ListView(scrollDirection: Axis.horizontal, children: [
      _SearchFilter(label: 'All', value: null, selected: selectedType, onTap: (v) => setState(() { selectedType = v; _load(); })),
      _SearchFilter(label: 'Food', value: 'food', selected: selectedType, onTap: (v) => setState(() { selectedType = v; _load(); })),
      _SearchFilter(label: 'Groceries', value: 'grocery', selected: selectedType, onTap: (v) => setState(() { selectedType = v; _load(); })),
      _SearchFilter(label: 'Medicines', value: 'pharmacy', selected: selectedType, onTap: (v) => setState(() { selectedType = v; _load(); })),
      _SearchFilter(label: 'Essentials', value: 'retail', selected: selectedType, onTap: (v) => setState(() { selectedType = v; _load(); })),
    ])),
    const SizedBox(height: 12),
    if (loading) const _MerchantSkeletonRow() else if (error != null && products.isEmpty) _InfoCard(text: error!, action: TextButton(onPressed: error!.startsWith('Sign in') ? () => context.push('/sign-in').then((_) => _load()) : _load, child: Text(error!.startsWith('Sign in') ? 'Sign in' : 'Retry'))) else if (products.isEmpty) _InfoCard(text: 'No matching products. Try another search or clear the filter.', action: TextButton(onPressed: () { search.clear(); setState(() => selectedType = null); _load(); }, child: const Text('Clear filters'))) else ...products.map((p) => Card(child: ListTile(leading: const Icon(Icons.shopping_basket_outlined, color: QuickbuddyColors.violet), title: Text('${p['name']} · ${p['variant_name']}'), subtitle: Text('${p['branch_name']} · ${p['currency']} ${p['unit_price']} · ${p['available_quantity']} ${p['unit']} left'), onTap: () => context.push('/restaurant/${p['branch_id']}')))),
    if (products.isNotEmpty && nextCursor != null) Center(child: loadingMore ? const CircularProgressIndicator() : TextButton(onPressed: _loadMore, child: const Text('Load more products'))),
  ]);
}

class _SearchFilter extends StatelessWidget {
  const _SearchFilter({required this.label, required this.value, required this.selected, required this.onTap});
  final String label; final String? value; final String? selected; final ValueChanged<String?> onTap;
  @override Widget build(BuildContext context) { final active = selected == value; return Padding(padding: const EdgeInsets.only(right: 6), child: ChoiceChip(label: Text(label, style: TextStyle(fontSize: 11, color: active ? Colors.white : QuickbuddyColors.ink)), selected: active, onSelected: (_) => onTap(value), selectedColor: QuickbuddyColors.orange, side: BorderSide(color: active ? QuickbuddyColors.orange : QuickbuddyColors.line))); }
}

class CartScreen extends ConsumerStatefulWidget {
  const CartScreen({super.key});
  @override ConsumerState<CartScreen> createState() => _CartScreenState();
}
class _CartScreenState extends ConsumerState<CartScreen> {
  bool loading = true; String? error, cartId; List<Map<String, dynamic>> lines = []; int version = 1;
  @override void initState() { super.initState(); _load(); }
  Future<void> _load() async {
    if (!await _signedIn()) { if (mounted) setState(() { loading = false; error = 'Sign in to access your saved cart.'; }); return; }
    try {
      final dio = ref.read(transportProvider); cartId = cartIdStore.value ?? await tokenStore.readValue('qb_cart');
      if (cartId == null) { if (mounted) setState(() { loading = false; lines = []; }); return; }
      final c = await dio.get('/api/v1/carts/$cartId'); version = c.data['version'] as int;
      final r = await dio.get('/api/v1/carts/$cartId/items?limit=100');
      final loadedLines = _items(r.data);
      cartCountStore.value = loadedLines.fold<int>(0, (sum, item) => sum + num.parse('${item['quantity']}').ceil());
      if (mounted) setState(() { lines = loadedLines; loading = false; error = null; });
    } catch (e) { if (mounted) setState(() { loading = false; error = _message(e); }); }
  }
  Future<void> _remove(Map<String, dynamic> item) async {
    try { await ref.read(transportProvider).delete('/api/v1/carts/$cartId/items/${item['id']}'); await _load(); }
    catch (e) { if (mounted) _snack(context, _message(e)); }
  }
  Future<void> _changeQuantity(Map<String, dynamic> item, int delta) async {
    final next = (num.parse('${item['quantity']}').toDouble() + delta);
    if (next <= 0) { await _remove(item); return; }
    try {
      final r = await ref.read(transportProvider).patch('/api/v1/carts/$cartId/items/${item['id']}', data: {'quantity': next, 'expected_version': version});
      version = r.data['version'] as int? ?? version + 1;
      await _load();
    } catch (e) { if (mounted) _snack(context, _message(e)); await _load(); }
  }
  @override Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(16), children: [
    _PageHeader(title: 'Your cart', subtitle: 'Items can come from multiple merchants'),
    if (loading) const Center(child: CircularProgressIndicator()) else if (error != null) _InfoCard(text: error!, action: TextButton(onPressed: error!.startsWith('Sign in') ? () => context.push('/sign-in').then((_) => _load()) : _load, child: Text(error!.startsWith('Sign in') ? 'Sign in' : 'Retry'))) else if (lines.isEmpty) const _InfoCard(text: 'Your cart is empty. Browse merchants to add an item.') else ...[
      ..._groupedLines().entries.map((group) => Card(child: ExpansionTile(
        initiallyExpanded: true,
        title: Text(group.value.first['branch_name']?.toString() ?? 'Merchant', style: const TextStyle(fontWeight: FontWeight.w700)),
        subtitle: Text('${group.value.length} item${group.value.length == 1 ? '' : 's'} · ${group.value.first['delivery_method']} · ${_windowLabel(context, group.value.first['window_starts_at'], group.value.first['window_ends_at'])}${group.value.first['delivery_address'] == null ? '' : '\n${group.value.first['delivery_address']}'}', maxLines: 2, overflow: TextOverflow.ellipsis),
        children: group.value.map((line) => ListTile(
          dense: true,
          leading: const Icon(Icons.shopping_bag_outlined, color: QuickbuddyColors.orange),
          title: Text('${line['product_name'] ?? 'Product'} · ${line['variant_name'] ?? ''}', maxLines: 1, overflow: TextOverflow.ellipsis),
          subtitle: Text('Qty ${line['quantity']}'),
          trailing: SizedBox(width: 124, child: Row(mainAxisAlignment: MainAxisAlignment.end, children: [
            IconButton(tooltip: 'Decrease quantity', onPressed: () => _changeQuantity(line, -1), icon: const Icon(Icons.remove_circle_outline, size: 20)),
            IconButton(tooltip: 'Increase quantity', onPressed: () => _changeQuantity(line, 1), icon: const Icon(Icons.add_circle_outline, color: QuickbuddyColors.orange, size: 20)),
            IconButton(tooltip: 'Remove item', onPressed: () => _remove(line), icon: const Icon(Icons.delete_outline, size: 20)),
          ])),
        )).toList(),
      ))),
      const SizedBox(height: 12),
      QbPrimaryButton(label: 'Review checkout quote', icon: Icons.arrow_forward, onPressed: () => context.push('/checkout/address-payment')),
    ],
    TextButton.icon(onPressed: () => context.go('/restaurants'), icon: const Icon(Icons.add), label: const Text('Browse more merchants')),
  ]);
  Map<String, List<Map<String, dynamic>>> _groupedLines() {
    final groups = <String, List<Map<String, dynamic>>>{};
    for (final line in lines) { (groups[line['branch_id'].toString()] ??= []).add(line); }
    return groups;
  }
}

class CheckoutScreen extends ConsumerStatefulWidget {
  const CheckoutScreen({super.key});
  @override ConsumerState<CheckoutScreen> createState() => _CheckoutScreenState();
}
class _CheckoutScreenState extends ConsumerState<CheckoutScreen> {
  bool loading = true, submitting = false; String? error, cartId; Map<String, dynamic>? quote; List<Map<String, dynamic>> lines = [];
  @override void initState() { super.initState(); _quote(); }
  Future<void> _quote() async {
    try {
      if (!await _signedIn()) { if (mounted) setState(() { loading = false; error = 'Sign in before checkout.'; }); return; }
      cartId = cartIdStore.value ?? await tokenStore.readValue('qb_cart');
      if (cartId == null) throw Exception('Your cart is empty.');
      final r = await ref.read(transportProvider).post('/api/v1/carts/$cartId/quote');
      if (mounted) setState(() { quote = Map<String, dynamic>.from(r.data); lines = _items({'items': r.data['lines']}); loading = false; error = null; });
    } catch (e) { if (mounted) setState(() { loading = false; error = _message(e); }); }
  }
  Future<void> _confirm() async {
    final q = quote;
    if (q == null || submitting) return;
    if (!sandboxEnabled) { _snack(context, 'A production payment provider is not configured. No order was placed.'); return; }
    setState(() => submitting = true);
    try {
      var key = await tokenStore.readValue('qb_idempotency_${q['id']}');
      key ??= _uuidKey();
      await tokenStore.writeValue('qb_idempotency_${q['id']}', key);
      final response = await ref.read(transportProvider).post('/api/v1/orders/confirm', data: {'quote_id': q['id']}, options: Options(headers: {'Idempotency-Key': key}));
      if (!mounted) return;
      final orderId = response.data['id'] as String;
      if (sandboxEnabled) {
        try {
          final api = ref.read(transportProvider);
          final intent = await api.post('/api/v1/finance/sandbox/payment-intents', data: {'order_id': orderId});
          final completed = await api.post('/api/v1/finance/sandbox/payments/${intent.data['id']}/complete');
          _snack(context, completed.data['status'] == 'confirmed'
            ? 'Order placed and sandbox payment confirmed. No real money was charged.'
            : 'Order placed. Sandbox payment status: ${completed.data['status']}.');
        } catch (e) {
          _snack(context, 'Order placed; sandbox payment did not complete: ${_message(e)}');
        }
      } else {
        _snack(context, 'Order placed. Production payment provider is not configured in this app.');
      }
      context.go('/orders/$orderId/complete');
    } catch (e) { if (mounted) { setState(() => submitting = false); _snack(context, 'Order was not confirmed: ${_message(e)}. Retry safely with the same checkout.'); } }
  }
  @override Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(16), children: [
    const _PageHeader(title: 'Review your order', subtitle: 'Each merchant and delivery slot is confirmed separately'),
    if (loading) const Center(child: CircularProgressIndicator()) else if (error != null) _InfoCard(text: error!, action: TextButton(onPressed: _quote, child: const Text('Refresh quote'))) else if (quote != null) ...[
      ..._quoteGroups().entries.map((group) => Card(child: ExpansionTile(
        initiallyExpanded: true,
        title: Text(group.value.first['branch_name']?.toString() ?? 'Merchant delivery', style: const TextStyle(fontWeight: FontWeight.w700)),
        subtitle: Text('${group.value.length} item${group.value.length == 1 ? '' : 's'} · ${group.value.first['delivery_method']} · ${_windowLabel(context, group.value.first['window_starts_at'], group.value.first['window_ends_at'])}'),
        children: [
          ...group.value.map((line) => ListTile(dense: true, contentPadding: const EdgeInsets.symmetric(horizontal: 14), title: Text('${line['product_name']} · ${line['variant_name']}'), subtitle: Text('Qty ${line['quantity']} · ${line['currency']} ${line['unit_price']} each'), trailing: Text('${line['currency']} ${line['total']}'))),
          _PriceLine('Merchant subtotal', '${group.value.first['currency']} ${group.value.fold<num>(0, (sum, line) => sum + num.parse('${line['total']}')).toStringAsFixed(2)}'),
        ],
      ))),
      const Divider(),
      _PriceLine('Server quoted total', '${quote!['currency']} ${quote!['total']}', bold: true),
      Text('Quote expires ${quote!['expires_at']}', style: const TextStyle(color: QuickbuddyColors.muted, fontSize: 11)),
      const SizedBox(height: 8),
      Card(child: ListTile(leading: const Icon(Icons.payment_outlined, color: QuickbuddyColors.violet), title: Text(sandboxEnabled ? 'Sandbox payment' : 'Payment unavailable'), subtitle: Text(sandboxEnabled ? 'Test simulation · no real money charged' : 'A production payment provider is not configured.'), trailing: Icon(sandboxEnabled ? Icons.check_circle : Icons.info_outline, color: QuickbuddyColors.violet))),
      const SizedBox(height: 10),
      const QbPreviewNotice(message: 'Separate merchant windows may mean separate deliveries. Only the quoted total is charged; unavailable taxes, fees or discounts are not estimated.'),
      const SizedBox(height: 12),
      QbPrimaryButton(label: submitting ? 'Confirming…' : sandboxEnabled ? 'Place sandbox order' : 'Payment unavailable', icon: Icons.lock_outline, enabled: !submitting && sandboxEnabled, onPressed: submitting || !sandboxEnabled ? null : _confirm),
    ],
  ]);
  Map<String, List<Map<String, dynamic>>> _quoteGroups() {
    final groups = <String, List<Map<String, dynamic>>>{};
    for (final line in lines) { (groups[line['branch_id'].toString()] ??= []).add(line); }
    return groups;
  }
}

class OrdersScreen extends ConsumerStatefulWidget {
  const OrdersScreen({super.key});
  @override ConsumerState<OrdersScreen> createState() => _OrdersScreenState();
}
class _OrdersScreenState extends ConsumerState<OrdersScreen> {
  bool loading = true; String? error; List<Map<String, dynamic>> orders = [];
  @override void initState() { super.initState(); _load(); }
  Future<void> _load() async { if (!await _signedIn()) { if (mounted) setState(() { loading = false; error = 'Sign in to view order history.'; }); return; } try { final r = await ref.read(transportProvider).get('/api/v1/orders?limit=50'); if (mounted) setState(() { orders = _items(r.data); loading = false; error = null; }); } catch (e) { if (mounted) setState(() { loading = false; error = _message(e); }); } }
  Future<void> _reorder(String orderId) async {
    try {
      final api = ref.read(transportProvider);
      final oldLines = (await api.get('/api/v1/orders/$orderId/reorder-lines')).data as List;
      if (oldLines.isEmpty) throw Exception('This order has no reorderable items.');
      String? cartId = cartIdStore.value ?? await tokenStore.readValue('qb_cart');
      if (cartId == null) {
        final created = await api.post('/api/v1/carts');
        cartId = created.data['id'] as String;
        cartIdStore.value = cartId;
        await tokenStore.writeValue('qb_cart', cartId);
      }
      final addressRows = _items((await api.get('/api/v1/addresses?limit=100')).data);
      final savedAddressIds = addressRows.map((a) => a['id'].toString()).toSet();
      final windowsByBranch = <String, List<Map<String, dynamic>>>{};
      var added = 0;
      var skipped = 0;
      for (final raw in oldLines.whereType<Map>()) {
        final line = Map<String, dynamic>.from(raw);
        final branchId = line['branch_id'].toString();
        final method = line['delivery_method'].toString();
        final addressId = line['address_id']?.toString();
        if (method != 'pickup' && (addressId == null || !savedAddressIds.contains(addressId))) { skipped++; continue; }
        final windows = windowsByBranch.putIfAbsent(branchId, () => <Map<String, dynamic>>[]);
        if (windows.isEmpty) windows.addAll(_items((await api.get('/api/v1/merchants/branches/$branchId/windows?limit=30')).data));
        if (windows.isEmpty) { skipped++; continue; }
        await api.post('/api/v1/carts/$cartId/items', data: {
          'branch_id': branchId,
          'variant_id': line['variant_id'],
          'quantity': line['quantity'],
          'address_id': method == 'pickup' ? null : addressId,
          'window_id': windows.first['id'],
          'delivery_method': method,
        });
        added++;
      }
      if (added == 0) throw Exception('No previous items could be added. Check saved delivery addresses and merchant windows.');
      await _refreshCartCount(api);
      if (mounted) { _snack(context, 'Added $added previous item${added == 1 ? '' : 's'} to your cart${skipped > 0 ? ' · $skipped skipped' : ''}. Review current prices and slots before ordering.'); context.push('/cart'); }
    } catch (e) { if (mounted) _snack(context, _message(e)); }
  }
  @override Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(16), children: [
    const _PageHeader(title: 'Your orders', subtitle: 'Order history from your account'),
    if (loading) const Center(child: CircularProgressIndicator())
    else if (error != null) _InfoCard(text: error!, action: TextButton(onPressed: error!.startsWith('Sign in') ? () => context.push('/sign-in').then((_) => _load()) : _load, child: Text(error!.startsWith('Sign in') ? 'Sign in' : 'Retry')))
    else if (orders.isEmpty) const _InfoCard(text: 'No orders yet. Your confirmed orders will appear here.')
    else ...orders.map((o) => Card(child: Column(children: [
      ListTile(leading: const Icon(Icons.receipt_long, color: QuickbuddyColors.violet), title: Text('Order ${o['id']}'), subtitle: Text('${o['status']} · ${o['currency']} ${o['total']}'), trailing: const Icon(Icons.chevron_right), onTap: () => context.push('/orders/${o['id']}/tracking')),
      Align(alignment: Alignment.centerRight, child: TextButton.icon(onPressed: () => _reorder(o['id'].toString()), icon: const Icon(Icons.replay, size: 17), label: const Text('Add items again'))),
    ]))),
  ]);
}

class TrackingScreen extends ConsumerStatefulWidget {
  const TrackingScreen({super.key, required this.orderId}); final String orderId;
  @override ConsumerState<TrackingScreen> createState() => _TrackingScreenState();
}
class _TrackingScreenState extends ConsumerState<TrackingScreen> {
  Timer? timer; bool loading = true, polling = false; String? error; Map<String, dynamic>? tracking;
  @override void initState() { super.initState(); _load(); timer = Timer.periodic(const Duration(seconds: 15), (_) => _load()); }
  @override void dispose() { timer?.cancel(); super.dispose(); }
  Future<void> _load() async {
    if (polling) return;
    polling = true;
    try {
      final r = await ref.read(transportProvider).get('/api/v1/orders/${widget.orderId}/tracking');
      if (mounted) setState(() { tracking = Map<String, dynamic>.from(r.data); loading = false; error = null; });
    } catch (e) { if (mounted) setState(() { loading = false; error = _message(e); }); }
    finally { polling = false; }
  }
  @override Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(16), children: [
    _PageHeader(title: 'Order tracking', subtitle: 'Each merchant delivery updates separately', action: TextButton(onPressed: () => context.go('/account'), child: const Text('Help'))),
    if (loading) const Center(child: CircularProgressIndicator()) else if (error != null) _InfoCard(text: error!, action: TextButton(onPressed: _load, child: const Text('Reconnect'))),
    if (tracking != null) ...[
      if (error != null) const QbStatusChip('Showing last known snapshot', tone: 'warning'),
      Container(height: 150, margin: const EdgeInsets.only(bottom: 10), decoration: BoxDecoration(color: const Color(0xFFF0F1F6), borderRadius: BorderRadius.circular(14), border: Border.all(color: QuickbuddyColors.line)), child: const Column(mainAxisAlignment: MainAxisAlignment.center, children: [Icon(Icons.map_outlined, color: QuickbuddyColors.muted, size: 30), SizedBox(height: 6), Text('Map provider unavailable', style: TextStyle(fontWeight: FontWeight.w700)), Text('No route or rider movement is simulated.', style: TextStyle(fontSize: 10, color: QuickbuddyColors.muted))])),
      if (tracking!['deliveries'] is List) ...(tracking!['deliveries'] as List).whereType<Map>().map((d) => Card(child: ListTile(leading: const Icon(Icons.local_shipping_outlined, color: QuickbuddyColors.violet), title: Text('Delivery · ${d['status']}'), subtitle: Text('${d['delivery_method']}${d['pilot_location'] == null ? ' · Location unavailable' : ' · Updated ${d['pilot_location']['observed_at']}'}'), trailing: const Icon(Icons.chevron_right)))) ,
      Text('Snapshot refreshed ${tracking!['generated_at'] ?? ''}', style: const TextStyle(fontSize: 10, color: QuickbuddyColors.muted)),
      const SizedBox(height: 6),
      const QbPreviewNotice(message: 'The authorized snapshot refreshes every 15 seconds. WebSocket, map tiles, ETA and route are not configured; pilot location appears only when returned as fresh by the backend.'),
    ],
  ]);
}

class OrderScreen extends ConsumerStatefulWidget {
  const OrderScreen({super.key, required this.orderId}); final String orderId;
  @override ConsumerState<OrderScreen> createState() => _OrderScreenState();
}
class _OrderScreenState extends ConsumerState<OrderScreen> {
  bool loading = true, paymentBusy = false; String? error; Map<String, dynamic>? order, payment;
  @override void initState() { super.initState(); _load(); }
  Future<void> _load() async {
    try {
      final api = ref.read(transportProvider);
      final result = await api.get('/api/v1/orders/${widget.orderId}');
      Map<String, dynamic>? currentPayment;
      try { currentPayment = Map<String, dynamic>.from((await api.get('/api/v1/orders/${widget.orderId}/payment')).data); }
      on DioException catch (e) { if (e.response?.statusCode != 404) rethrow; }
      if (mounted) setState(() { order = Map<String, dynamic>.from(result.data); payment = currentPayment; loading = false; error = null; });
    } catch (e) { if (mounted) setState(() { loading = false; error = _message(e); }); }
  }
  Future<void> _resumeSandboxPayment() async {
    if (!sandboxEnabled || paymentBusy) return;
    setState(() => paymentBusy = true);
    try {
      final api = ref.read(transportProvider);
      final intent = await api.post('/api/v1/finance/sandbox/payment-intents', data: {'order_id': widget.orderId});
      final response = await api.post('/api/v1/finance/sandbox/payments/${intent.data['id']}/complete');
      if (mounted) { setState(() => payment = Map<String, dynamic>.from(response.data)); _snack(context, 'Sandbox payment status: ${response.data['status']}. No real money was charged.'); }
    } catch (e) { if (mounted) _snack(context, 'Payment is still pending: ${_message(e)}'); }
    finally { if (mounted) setState(() => paymentBusy = false); }
  }
  @override Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(16), children: [
    const Icon(Icons.check_circle_outline, color: QuickbuddyColors.green, size: 58),
    const _PageHeader(title: 'Order received', subtitle: 'Order confirmation is loaded from Quickbuddy'),
    if (loading) const Center(child: CircularProgressIndicator()) else if (error != null) _InfoCard(text: error!, action: TextButton(onPressed: _load, child: const Text('Retry'))) else if (order != null) ...[
      Text('Order ${widget.orderId}', textAlign: TextAlign.center, style: const TextStyle(fontWeight: FontWeight.w700)),
      const SizedBox(height: 5), Text('Status: ${order!['status']} · ${order!['currency']} ${order!['total']}', textAlign: TextAlign.center),
      const SizedBox(height: 12),
      Card(child: ListTile(leading: Icon(payment?['status'] == 'confirmed' ? Icons.check_circle : Icons.pending_outlined, color: payment?['status'] == 'confirmed' ? QuickbuddyColors.green : QuickbuddyColors.amber), title: Text('Payment ${payment?['status'] ?? 'not started'}'), subtitle: Text(payment == null ? 'Use sandbox payment in development/test.' : 'Sandbox · ${payment!['currency']} ${payment!['amount']}'))),
      if (sandboxEnabled && payment?['status'] != 'confirmed') OutlinedButton.icon(onPressed: paymentBusy ? null : _resumeSandboxPayment, icon: const Icon(Icons.refresh), label: Text(paymentBusy ? 'Resuming payment…' : 'Continue sandbox payment')),
      QbPrimaryButton(label: 'Track order', onPressed: () => context.push('/orders/${widget.orderId}/tracking')),
      const QbPreviewNotice(message: 'Sandbox payment has no real-money effect. Customer reviews and reorder endpoints are not configured.'),
    ],
  ]);
}

class AccountScreen extends ConsumerStatefulWidget {
  const AccountScreen({super.key});
  @override ConsumerState<AccountScreen> createState() => _AccountScreenState();
}
class _AccountScreenState extends ConsumerState<AccountScreen> {
  bool loading = true, signedIn = false; String? error; List<Map<String, dynamic>> addresses = [];
  @override void initState() { super.initState(); _load(); }
  Future<void> _load() async { signedIn = await _signedIn(); if (!signedIn) { if (mounted) setState(() { loading = false; }); return; } try { final r = await ref.read(transportProvider).get('/api/v1/addresses?limit=50'); if (mounted) setState(() { addresses = _items(r.data); loading = false; error = null; }); } catch (e) { if (mounted) setState(() { loading = false; error = _message(e); }); } }
  Future<void> _signOut() async {
    try {
      final refresh = await tokenStore.refreshToken();
      if (refresh != null) await ref.read(transportProvider).post('/api/v1/auth/logout', data: {'refresh_token': refresh});
    } catch (_) {
      // Local credentials are always cleared even if revocation cannot reach the server.
    }
    await tokenStore.clear(); await tokenStore.deleteValue('qb_cart'); cartIdStore.value = null;
    if (mounted) setState(() { signedIn = false; addresses = []; });
  }
  @override Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(16), children: [const _PageHeader(title: 'Account', subtitle: 'Profile, addresses and help'), if (loading) const Center(child: CircularProgressIndicator()) else if (!signedIn) ...[const _InfoCard(text: 'Sign in with email and password to access your account.'), QbPrimaryButton(label: 'Sign in / create account', onPressed: () async { await context.push('/sign-in'); _load(); })] else ...[
    const ListTile(leading: CircleAvatar(child: Icon(Icons.person)), title: Text('Quickbuddy customer'), subtitle: Text('Authenticated account')),
    const QbSectionTitle('Saved addresses'),
    OutlinedButton.icon(onPressed: () => _addAddress(context), icon: const Icon(Icons.add_location_alt_outlined), label: const Text('Add address')),
    if (error != null) _InfoCard(text: error!) else if (addresses.isEmpty) const _InfoCard(text: 'No saved addresses. Address entry requires city, address text and coordinates; map/geocoding is not configured.'),
    ...addresses.map((a) => ListTile(leading: const Icon(Icons.location_on_outlined), title: Text('${a['label']}'), subtitle: Text('${a['address_text']}'))),
    const QbPreviewNotice(message: 'Address creation requires coordinates. Choose a city and enter a verified latitude/longitude when backend location setup is available.'),
    const SizedBox(height: 12),
    const QbSectionTitle('Customer services'),
    ListTile(leading: const Icon(Icons.support_agent), title: const Text('Contact support'), onTap: () => _createTicket(context)),
    const ListTile(leading: Icon(Icons.star_border), title: Text('Ratings and reviews'), subtitle: Text('Customer rating API is not configured')),
    const ListTile(leading: Icon(Icons.favorite_border), title: Text('Favorites'), subtitle: Text('Favorites API is not configured')),
    OutlinedButton.icon(onPressed: _signOut, icon: const Icon(Icons.logout), label: const Text('Sign out')),
  ]]);
  Future<void> _createTicket(BuildContext context) async {
    final subject = TextEditingController();
    final message = TextEditingController();
    final ok = await showDialog<bool>(context: context, builder: (ctx) => AlertDialog(title: const Text('Contact support'), content: Column(mainAxisSize: MainAxisSize.min, children: [TextField(controller: subject, decoration: const InputDecoration(labelText: 'Subject')), TextField(controller: message, decoration: const InputDecoration(labelText: 'How can we help?'))]), actions: [TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')), FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Create ticket'))]));
    if (ok == true) {
      try {
        final api = ref.read(transportProvider);
        final created = await api.post('/api/v1/support/tickets', data: {'subject': subject.text.trim()});
        if (message.text.trim().isNotEmpty) {
          await api.post('/api/v1/support/tickets/${created.data['id']}/messages', data: {'body': message.text.trim()});
        }
        if (context.mounted) _snack(context, 'Support ticket ${created.data['id']} created. Ticket progress is not exposed in the customer API.');
      } catch (e) { if (context.mounted) _snack(context, _message(e)); }
    }
    subject.dispose(); message.dispose();
  }
  Future<void> _addAddress(BuildContext context) async {
    final dio = ref.read(transportProvider);
    try {
      final cities = _items((await dio.get('/api/v1/geo/cities?limit=100')).data);
      if (cities.isEmpty) { if (context.mounted) _snack(context, 'No active cities are configured.'); return; }
      final label = TextEditingController();
      final text = TextEditingController();
      final latitude = TextEditingController();
      final longitude = TextEditingController();
      String cityId = cities.first['id'] as String;
      final saved = await showDialog<bool>(context: context, builder: (ctx) => StatefulBuilder(builder: (ctx, update) => AlertDialog(
        title: const Text('Add delivery address'),
        content: SingleChildScrollView(child: Column(mainAxisSize: MainAxisSize.min, children: [
          DropdownButtonFormField<String>(value: cityId, decoration: const InputDecoration(labelText: 'City'), items: cities.map((c) => DropdownMenuItem(value: c['id'] as String, child: Text('${c['name']}'))).toList(), onChanged: (v) => update(() => cityId = v!)),
          TextField(controller: label, decoration: const InputDecoration(labelText: 'Label (Home, Work…)')),
          TextField(controller: text, maxLines: 2, decoration: const InputDecoration(labelText: 'Full address')),
          TextField(controller: latitude, keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true), decoration: const InputDecoration(labelText: 'Latitude')),
          TextField(controller: longitude, keyboardType: const TextInputType.numberWithOptions(decimal: true, signed: true), decoration: const InputDecoration(labelText: 'Longitude')),
        ])),
        actions: [TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancel')), FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Save'))],
      )));
      if (saved == true) {
        await dio.post('/api/v1/addresses', data: {'city_id': cityId, 'label': label.text.trim(), 'address_text': text.text.trim(), 'latitude': latitude.text.trim(), 'longitude': longitude.text.trim()});
        if (context.mounted) _snack(context, 'Address saved. The backend will verify serviceability at checkout.');
        await _load();
      }
      label.dispose(); text.dispose(); latitude.dispose(); longitude.dispose();
    } catch (e) { if (context.mounted) _snack(context, _message(e)); }
  }
}

class SignInScreen extends ConsumerStatefulWidget {
  const SignInScreen({super.key});
  @override ConsumerState<SignInScreen> createState() => _SignInScreenState();
}
class _SignInScreenState extends ConsumerState<SignInScreen> {
  final formKey = GlobalKey<FormState>();
  final email = TextEditingController(), password = TextEditingController(); bool create = false, busy = false;
  @override void dispose() { email.dispose(); password.dispose(); super.dispose(); }
  Future<void> _submit() async {
    if (!(formKey.currentState?.validate() ?? false)) return;
    setState(() => busy = true);
    try {
      final dio = ref.read(transportProvider);
      if (create) {
        await dio.post('/api/v1/auth/register', data: {'email': email.text.trim(), 'password': password.text});
      }
      final response = await dio.post('/api/v1/auth/login', data: {'email': email.text.trim(), 'password': password.text});
      await tokenStore.saveTokens(response.data['access_token'] as String, response.data['refresh_token'] as String);
      if (mounted) { context.pop(); }
    } catch (e) { if (mounted) _snack(context, _message(e)); }
    finally { if (mounted) setState(() => busy = false); }
  }
  @override Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(22), children: [
    const SizedBox(height: 14), const Center(child: QbBrand()), const SizedBox(height: 24),
    Text(create ? 'Create your account' : 'Welcome back', style: const TextStyle(fontSize: 23, fontWeight: FontWeight.w800)),
    const SizedBox(height: 8), const Text('Sign in to save your address, cart and orders.', style: TextStyle(color: QuickbuddyColors.muted)),
    const SizedBox(height: 14), const QbPreviewNotice(message: 'Email/password is supported. Phone OTP registration and recovery are not implemented.'),
    const SizedBox(height: 12),
    Form(key: formKey, child: Column(children: [
      TextFormField(controller: email, keyboardType: TextInputType.emailAddress, autofillHints: const [AutofillHints.email], textInputAction: TextInputAction.next, validator: (v) => v == null || !RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$').hasMatch(v.trim()) ? 'Enter a valid email address.' : null, decoration: const InputDecoration(labelText: 'Email', prefixIcon: Icon(Icons.mail_outline))),
      const SizedBox(height: 10),
      TextFormField(controller: password, obscureText: true, autofillHints: [create ? AutofillHints.newPassword : AutofillHints.password], textInputAction: TextInputAction.done, onFieldSubmitted: (_) => _submit(), validator: (v) => v == null || (create ? v.length < 12 : v.isEmpty) ? (create ? 'Use at least 12 characters.' : 'Enter your password.') : null, decoration: InputDecoration(labelText: 'Password', helperText: create ? 'Use at least 12 characters.' : null, prefixIcon: const Icon(Icons.lock_outline))),
    ])),
    const SizedBox(height: 14), QbPrimaryButton(label: busy ? 'Please wait…' : create ? 'Create account' : 'Sign in', enabled: !busy, onPressed: busy ? null : _submit),
    TextButton(onPressed: busy ? null : () => setState(() { create = !create; formKey.currentState?.reset(); }), child: Text(create ? 'Already registered? Sign in' : 'New to Quickbuddy? Create account')),
  ]);
}

class OnboardingScreen extends StatelessWidget {
  const OnboardingScreen({super.key});
  @override Widget build(BuildContext context) => ListView(padding: const EdgeInsets.fromLTRB(20, 16, 20, 24), children: [
    Row(children: [const QbBrand(), const Spacer(), TextButton(onPressed: () => context.go('/'), child: const Text('Skip'))]),
    const SizedBox(height: 14),
    ClipRRect(borderRadius: BorderRadius.circular(21), child: Stack(alignment: Alignment.bottomLeft, children: [const QbPhoto('burger', width: double.infinity, height: 390, radius: 0), Container(height: 78, color: const Color(0xCC1B1747)), const Padding(padding: EdgeInsets.all(18), child: Text('Good food.\nBrighter days.', style: TextStyle(color: Colors.white, fontSize: 25, height: 1.1, fontWeight: FontWeight.w800)))])),
    const SizedBox(height: 18),
    const Text('Everything you need, delivered happier.', textAlign: TextAlign.center, style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: QuickbuddyColors.indigo)),
    const SizedBox(height: 7),
    const Text('Food, groceries, medicines and essentials — discover local merchants around you.', textAlign: TextAlign.center, style: TextStyle(color: QuickbuddyColors.muted, fontSize: 12, height: 1.5)),
    const SizedBox(height: 18),
    QbPrimaryButton(label: 'Get started', onPressed: () => context.go('/')),
    TextButton(onPressed: () => context.push('/sign-in'), child: const Text('Sign in or create account')),
  ]);
}

class _PageHeader extends StatelessWidget { const _PageHeader({required this.title, required this.subtitle}); final String title, subtitle; @override Widget build(BuildContext context) => Padding(padding: const EdgeInsets.only(bottom: 14), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(title, style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w800, color: QuickbuddyColors.ink)), const SizedBox(height: 4), Text(subtitle, style: const TextStyle(fontSize: 12, color: QuickbuddyColors.muted))])); }
class _InfoCard extends StatelessWidget { const _InfoCard({required this.text, this.action}); final String text; final Widget? action; @override Widget build(BuildContext context) => QbPanel(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [Text(text, style: const TextStyle(fontSize: 12, height: 1.45)), if (action != null) Align(alignment: Alignment.centerRight, child: action!)])); }
class _PriceLine extends StatelessWidget { const _PriceLine(this.label, this.value, {this.bold = false}); final String label, value; final bool bold; @override Widget build(BuildContext context) => Padding(padding: const EdgeInsets.symmetric(vertical: 8), child: Row(children: [Expanded(child: Text(label, style: TextStyle(fontWeight: bold ? FontWeight.w700 : FontWeight.normal))), Text(value, style: TextStyle(fontWeight: bold ? FontWeight.w800 : FontWeight.w600))])); }
