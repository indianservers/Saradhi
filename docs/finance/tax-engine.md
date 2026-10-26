# Tax engine foundation

Typed tax code/rule, invoice, invoice line, and credit note records are present. The order quote does not yet resolve reviewed tax treatment by jurisdiction, merchant legal entity, category, supply date, inclusive/exclusive price, platform fees, or delivery charges. No universal GST rate is hardcoded.

Before invoicing or tax reports, obtain qualified India tax review, define supplier/e-commerce operator liability and invoice ownership, version effective rates, snapshot tax components at order time, and create credit-note/reversal behavior for refunds. Country-specific rules must remain explicit adapters.
