import 'package:flutter/material.dart';
import 'package:flutter_core/flutter_core.dart';
import 'package:flutter_design_system/flutter_design_system.dart';
import 'package:flutter_networking/flutter_networking.dart';
import 'package:go_router/go_router.dart';

final transportProvider = Provider((ref) => createTransport(SecureTokenStore()));
final router = GoRouter(routes: [GoRoute(path: '/', builder: (context, state) =>
  const FoundationShell(title: 'Your business, connected', subtitle: 'A connected Quickbuddy workspace.',
    modules: ["Branches", "Orders & preparation", "Catalog & inventory", "Settlements", "Staff"]))]);

void main() => runApp(ProviderScope(child: QuickbuddyApp(
  title: 'Quickbuddy Merchant App', theme: quickbuddyTheme(), router: router)));
