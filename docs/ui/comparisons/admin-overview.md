# Admin overview visual review

Date: 2026-10-26

- Target crop: [`../reference-crops/admin-01.png`](../reference-crops/admin-01.png) (Platform Overview Dashboard).
- Running page: `http://127.0.0.1:3000/` (development mode; backend unavailable).
- Captured browser viewport: 1265 × 720 CSS pixels in the available in-app browser. The target panel is approximately 500 × 385 pixels inside the 1448 × 1086 board; the viewports are not directly pixel-comparable.
- Review type: visual inspection of the live browser screenshot, not a pixel-diff. Screenshot bytes were not saved as a repository image in this run.

## Matches

- Snow-white and pale neutral surfaces, indigo headings/selected navigation, orange chart/action accents, narrow persistent sidebar, search and city controls.
- Four top KPIs, dual-series trend panel, city performance list, and four lower metrics follow the target's hierarchy and density.
- `All Cities` is the default selection, matching the board; the preview city table now includes Bengaluru, Hyderabad, Chennai, Mumbai and Delhi NCR.
- Preview-data notice makes fixture status clear.

## Differences and fixes

- The app viewport is wider/taller than the target panel, so the live page continues vertically and the footer sits below the first viewport. The layout remains responsive instead of fixing to the montage's panel dimensions.
- The target uses small city-specific portraits/markers; current city rows use colored dots. Live map/location provider is not connected.
- The target's period selector is not backed by analytics data. The current control is labeled `Refresh data` and reloads the page; it does not claim to filter a live period.
- Live order/GMV aggregates, notification events and city metrics are not available from the development backend. Preview dashboard numbers are labeled as illustrative and are never shown as production data.
- A runtime bug found during this review (Lucide `Map` shadowing JavaScript `Map`) was fixed by renaming the icon import. The app then rendered and all sidebar views were checked.

## Follow-up

Run a screenshot capture at a board-matched desktop viewport and compare all ten admin crops. Add a configured map provider and aggregate metrics endpoints before claiming visual/data parity for map and analytics sections.
