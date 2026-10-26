import 'package:flutter/material.dart';

abstract final class QuickbuddyColors {
  static const orange = Color(0xFFFF6208);
  static const orangeDark = Color(0xFFE94F00);
  static const violet = Color(0xFF6A31E8);
  static const indigo = Color(0xFF211B72);
  static const ink = Color(0xFF191A2D);
  static const muted = Color(0xFF727486);
  static const line = Color(0xFFE9EAF1);
  static const page = Color(0xFFF7F8FC);
  static const green = Color(0xFF20AE70);
  static const red = Color(0xFFE34F55);
  static const blue = Color(0xFF3377E8);
  static const amber = Color(0xFFF0A928);
}

ThemeData quickbuddyTheme() => ThemeData(
  useMaterial3: true,
  scaffoldBackgroundColor: QuickbuddyColors.page,
  colorScheme: ColorScheme.fromSeed(
    seedColor: QuickbuddyColors.orange,
    primary: QuickbuddyColors.orange,
    secondary: QuickbuddyColors.violet,
    surface: Colors.white,
    brightness: Brightness.light,
  ),
  appBarTheme: const AppBarTheme(
    backgroundColor: QuickbuddyColors.page,
    foregroundColor: QuickbuddyColors.ink,
    centerTitle: false,
    elevation: 0,
  ),
  cardTheme: CardThemeData(
    color: Colors.white,
    surfaceTintColor: Colors.transparent,
    elevation: 0,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(15),
      side: const BorderSide(color: QuickbuddyColors.line),
    ),
    margin: EdgeInsets.zero,
  ),
  inputDecorationTheme: InputDecorationTheme(
    filled: true,
    fillColor: Colors.white,
    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: const BorderSide(color: QuickbuddyColors.line),
    ),
    enabledBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: const BorderSide(color: QuickbuddyColors.line),
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: const BorderSide(color: QuickbuddyColors.violet, width: 1.5),
    ),
  ),
  visualDensity: VisualDensity.compact,
);

class QbBrand extends StatelessWidget {
  const QbBrand({super.key, this.pilot = false});
  final bool pilot;

  @override
  Widget build(BuildContext context) => Row(mainAxisSize: MainAxisSize.min, children: [
    Icon(pilot ? Icons.location_on_rounded : Icons.delivery_dining_rounded,
        color: QuickbuddyColors.orange, size: 27),
    const SizedBox(width: 4),
    const Text('Quick', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800,
        letterSpacing: -1, color: QuickbuddyColors.orange)),
    const Text('buddy', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w800,
        letterSpacing: -1, color: QuickbuddyColors.indigo)),
  ]);
}

class QbPreviewNotice extends StatelessWidget {
  const QbPreviewNotice({super.key, this.message = 'Preview only · sample records are not live business data'});
  final String message;
  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
    decoration: BoxDecoration(color: const Color(0xFFFFF7EB),
      border: Border.all(color: const Color(0xFFF5DFBF)), borderRadius: BorderRadius.circular(9)),
    child: Row(children: [const Icon(Icons.info_outline, size: 15, color: Color(0xFFB97720)),
      const SizedBox(width: 7), Expanded(child: Text(message, style: const TextStyle(
        color: Color(0xFF8B6532), fontSize: 10, height: 1.35)))]),
  );
}

class QbPrimaryButton extends StatelessWidget {
  const QbPrimaryButton({super.key, required this.label, this.icon, this.onPressed, this.enabled = true});
  final String label;
  final IconData? icon;
  final VoidCallback? onPressed;
  final bool enabled;
  @override
  Widget build(BuildContext context) => SizedBox(height: 48, child: FilledButton.icon(
    onPressed: enabled ? onPressed : null,
    style: FilledButton.styleFrom(backgroundColor: QuickbuddyColors.orange,
      disabledBackgroundColor: const Color(0xFFE7E7EB), disabledForegroundColor: QuickbuddyColors.muted,
      foregroundColor: Colors.white, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(13))),
    icon: Icon(icon ?? Icons.arrow_forward_rounded, size: 18),
    label: Text(label, style: const TextStyle(fontWeight: FontWeight.w700)),
  ));
}

class QbStatusChip extends StatelessWidget {
  const QbStatusChip(this.label, {super.key, this.tone = 'neutral'});
  final String label;
  final String tone;
  @override
  Widget build(BuildContext context) {
    final color = switch (tone) {
      'success' => QuickbuddyColors.green,
      'warning' => QuickbuddyColors.amber,
      'danger' => QuickbuddyColors.red,
      'info' => QuickbuddyColors.blue,
      'brand' => QuickbuddyColors.violet,
      _ => QuickbuddyColors.muted,
    };
    return Container(padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
      decoration: BoxDecoration(color: color.withValues(alpha: .10), borderRadius: BorderRadius.circular(20)),
      child: Text(label, style: TextStyle(color: color, fontWeight: FontWeight.w700, fontSize: 10)));
  }
}

class QbPhoto extends StatelessWidget {
  const QbPhoto(this.asset, {super.key, this.height = 108, this.width, this.radius = 12, this.fit = BoxFit.cover});
  final String asset;
  final double height;
  final double? width;
  final double radius;
  final BoxFit fit;
  @override
  Widget build(BuildContext context) => ClipRRect(
    borderRadius: BorderRadius.circular(radius),
    child: Image.asset('packages/flutter_design_system/assets/images/$asset.webp',
      height: height, width: width, fit: fit,
      errorBuilder: (context, error, stack) => Container(height: height, width: width,
        color: const Color(0xFFF1F2F7), child: const Icon(Icons.image_not_supported_outlined,
          color: QuickbuddyColors.muted))),
  );
}

class QbSectionTitle extends StatelessWidget {
  const QbSectionTitle(this.title, {super.key, this.action, this.onAction});
  final String title;
  final String? action;
  final VoidCallback? onAction;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 10),
    child: Row(children: [Expanded(child: Text(title, style: const TextStyle(
      color: QuickbuddyColors.ink, fontSize: 15, fontWeight: FontWeight.w700))),
      if (action != null) TextButton(onPressed: onAction, child: Text(action!,
        style: const TextStyle(color: QuickbuddyColors.violet, fontSize: 11))) ]),
  );
}

class QbPanel extends StatelessWidget {
  const QbPanel({super.key, required this.child, this.padding = const EdgeInsets.all(13)});
  final Widget child;
  final EdgeInsetsGeometry padding;
  @override
  Widget build(BuildContext context) => Card(child: Padding(padding: padding, child: child));
}

class FoundationShell extends StatelessWidget {
  const FoundationShell({super.key, required this.title, required this.subtitle, required this.modules});
  final String title;
  final String subtitle;
  final List<String> modules;
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const QbBrand()),
    body: ListView(padding: const EdgeInsets.all(24), children: [
      const Icon(Icons.hub_outlined, size: 38, color: QuickbuddyColors.violet),
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
