# Category configuration

Products use one typed category registry (`catalog.product_categories`), with category-specific attributes in the existing schema and zone/category activation rows. Admins may enable a non-regulated category per inactive city's zone. Customer category listing and product discovery omit regulated categories. Attempting to enable a regulated category fails closed until pharmacy compliance is implemented.

There is no versioned capability registry for tax, delivery limits, required documents, returns, payment eligibility or UI presentation. Category data is not an arbitrary EAV schema builder.
