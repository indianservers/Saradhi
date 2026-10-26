import 'package:flutter/material.dart';

ThemeData quickbuddyTheme() => ThemeData(
  useMaterial3: true,
  scaffoldBackgroundColor: Colors.white,
  colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF17684B),
      surface: Colors.white, brightness: Brightness.light),
  appBarTheme: const AppBarTheme(backgroundColor: Colors.white, centerTitle: false),
  visualDensity: VisualDensity.compact,
);

class FoundationShell extends StatelessWidget {
  const FoundationShell({super.key, required this.title, required this.subtitle, required this.modules});
  final String title;
  final String subtitle;
  final List<String> modules;
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('quickbuddy.')),
    body: ListView(padding: const EdgeInsets.all(24), children: [
      const Icon(Icons.hub_outlined, size: 38, color: Color(0xFF17684B)),
      const SizedBox(height: 24),
      Text(title, style: Theme.of(context).textTheme.headlineMedium),
      const SizedBox(height: 12), Text(subtitle), const SizedBox(height: 24),
      ...modules.map((name) => Card(elevation: 0, color: const Color(0xFFF4F7F5),
        child: ListTile(leading: const Icon(Icons.layers_outlined), title: Text(name),
          subtitle: const Text('Planned capability'), enabled: false))),
      const SizedBox(height: 24),
      const Text('Phase 1 · Secure platform foundation', textAlign: TextAlign.center),
    ]),
  );
}
