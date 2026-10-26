import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

export 'package:flutter_riverpod/flutter_riverpod.dart';
final localeProvider = NotifierProvider<LocaleState, Locale>(LocaleState.new);

// One locale state boundary; add generated ARB translations before business screens.
class LocaleState extends Notifier<Locale> {
  @override
  Locale build() => const Locale('en');
  void select(Locale locale) { state = locale; }
}

class QuickbuddyApp extends ConsumerWidget {
  const QuickbuddyApp({super.key, required this.title, required this.theme, required this.router});
  final String title;
  final ThemeData theme;
  final GoRouter router;
  @override
  Widget build(BuildContext context, WidgetRef ref) => MaterialApp.router(
    title: title, theme: theme, routerConfig: router,
    locale: ref.watch(localeProvider), supportedLocales: const [Locale('en'), Locale('hi')],
    localizationsDelegates: GlobalMaterialLocalizations.delegates,
  );
}
