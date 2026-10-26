# Merchant menu management

The branch-scoped menu endpoint returns every organization product variant, whether active, priced, or stocked, and only returns it for a branch the caller may manage. Current active branch price and stock are joined when present. The customer catalogue remains separate and filters to currently sellable items.

The app can create a product, variant/SKU and branch-specific INR price using the existing write endpoints. It reads category options from the shared category API. Creating the three records is a sequence of API calls without a transaction spanning all calls; if a later call fails, the app reloads and warns that an earlier step may have succeeded. Inspect before retrying to avoid duplicate records.

Editing, product images, addon/modifier groups, dietary/allergen metadata, tax configuration, schedule windows, branch visibility, duplication and customer product preview are not yet wired. The category management endpoint currently requires broader `geo.write`, so the app does not expose category creation to merchants.
