import 'package:flutter/material.dart';
import 'package:flutter_core/flutter_core.dart';
import 'package:flutter_design_system/flutter_design_system.dart';
import 'package:flutter_networking/flutter_networking.dart';
import 'package:go_router/go_router.dart';

final transportProvider = Provider((ref) => createTransport(SecureTokenStore()));
final router = GoRouter(routes: [GoRoute(path: '/', builder: (context, state) =>
  const FoundationShell(title: 'Ready for your next route', subtitle: 'A connected Quickbuddy workspace.',
    modules: ["Availability", "Assignments", "Pickup & delivery", "Earnings", "Notifications"]))]);

void main() => runApp(ProviderScope(child: QuickbuddyApp(
  title: 'Quickbuddy Pilot App', theme: quickbuddyTheme(), router: router)));
