# Quickbuddy visual design specification

Source: visual inspection of the four 1448 × 1086 target boards. Coordinates below are visual estimates because the boards are rasterized composites, not design tokens exported from a source design file.

## Brand and color

| Token | Intended use | Approximate source value |
|---|---|---|
| `brand.orange` | Primary customer/pilot/merchant CTA, alerts, logo | `#FF5A00` to `#FF6A00` |
| `brand.violet` | Quickbuddy secondary accent, selected categories, admin active navigation | `#6528E8` |
| `brand.indigo` | Admin headings, navigation and chart series | `#211B73` |
| `ink.strong` | Titles and important values | `#151936` |
| `ink.muted` | Descriptions, timestamps and labels | `#62677A` |
| `surface.page` | Main background | `#F7F8FC` |
| `surface.card` | Cards and sheets | `#FFFFFF` |
| `line.subtle` | Card borders and dividers | `#E7EAF2` |
| `status.success` | Online, delivered, settled | `#20B978` |
| `status.warning` | Preparing, delayed, low stock | `#F3A51D` |
| `status.danger` | Exceptions, rejection, out of stock | `#E54A4A` |
| `status.info` | On-way, navigation and neutral information | `#2877E8` |

## Type, layout and elevation

- Use a clean geometric sans (Inter or a native system sans fallback); the supplied board resembles a rounded modern sans with heavy display/logo weights. Do not rasterize body text.
- Mobile top bars are compact (roughly 48–56 dp), content gutters 16–20 dp, dense table rows 34–42 px and body text usually 12–15 px at reference scale. Keep mobile touch targets at least 44 dp despite the dense source screenshot.
- Web admin uses a persistent sidebar around 210–225 px, 8–16 px table/control gaps, a compact top filter bar, 4–5 KPI cards per row on desktop, and chart/table cards with consistent alignment.
- Spacing scale: 4, 8, 12, 16, 20, 24, 32. Card radius 12–16 px; pill radius 999 px; primary buttons 12–16 px. Borders are thin and pale. Shadows are subtle, low-opacity, and reserved for floating sheets/highlight cards.
- Use orange primary actions on consumer/operations mobile screens and violet on admin selection/secondary emphasis as shown. Avoid arbitrary gradients; the boards include limited violet/orange promo treatments only.

## Reusable primitives

Provide shared tokens/components for app bars, desktop shell/sidebar, search/filter controls, cards, compact metric cards, data tables, status badges, category and product tiles, primary/secondary/destructive actions, bottom navigation, order progress, empty/loading/error states, confirmation sheets, and AI insight cards. Customer, pilot, and merchant apps may share primitives while retaining app-specific task flows and navigation.

## Imagery and iconography

- Use consistent outline icons (Lucide on web; Material Symbols/Icons with mapped equivalents in Flutter) rather than emoji.
- Customer and merchant screens need food/product imagery with a consistent photographic crop; source imagery is not embedded as a licensed asset in the boards. Record attribution/licensing in an asset manifest before adding production photos.
- Keep map panels visually legible with route/zone overlays and legend. If no map provider is configured, render a clearly labeled unavailable map state; never present a fabricated live map as connected.

## Responsive behavior and accessibility

- At narrow widths, preserve readable cards and primary controls, use bottom navigation on mobile, and allow horizontal chip scrollers only where the design shows them. Admin data tables may become row cards or horizontally scroll inside their own bounded container.
- Respect safe areas, keyboard insets, text scaling and reduced motion. Status must include text/icon, never color alone. Add focus indicators and semantic labels. Do not hide payment consent or price components to match a dense crop.

## Integration display policy

Backend data must be labeled by connection state. Unconfigured or unauthenticated APIs render loading/empty/error/unavailable states. Preview-only visual content must carry an explicit demo label and remain isolated from production. AI cards must distinguish deterministic rule output from a trained model and expose fallback/unavailable status.
