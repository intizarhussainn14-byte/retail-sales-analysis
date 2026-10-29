# Reviewed stock-code decisions

The actual workbook was grouped by unusual StockCode and Description before these decisions. Every cleaning run exports the full code/description profile to stock_code_review.csv. These are analytical inclusion decisions, not invented product categories.

- Exclude POST (POSTAGE), DOT (DOTCOM POSTAGE), C2 (CARRIAGE), BANK CHARGES, AMAZONFEE, CRUK (Commission), D (Discount), B (Adjust bad debt), M and m (Manual), and S (SAMPLES). They are charges, adjustments, samples or ambiguous manual entries rather than identifiable merchandise sales.
- Exclude gift_0001_10/20/30/40/50: descriptions identify gift vouchers. Keep them in audit, separate from merchandise revenue; no redemption assumptions are made.
- Retain PADS: actual description is PADS TO MATCH ALL CUSHIONS, a product despite its alphabetic code.
- Retain DCGS0003 (BOXED GLASS ASHTRAY), DCGS0004 (HAYNES CAMPER SHOULDER BAG), DCGS0069 (OOH LA LA DOGS COLLAR), DCGS0070 (CAMOUFLAGE DOG COLLAR), DCGS0076 (SUNJAR LED NIGHT NIGHT LIGHT), DCGSSBOY and DCGSSGIRL (party bags). Some occurrences say ebay; the product description elsewhere provides supporting evidence for code-level inclusion. All other sales rules still apply.
- Quarantine remaining unusual DCGS codes: descriptions are blank or only ebay, so merchandise status is not established. New unexpected code formats are also quarantined for review.
- Retain ordinary five-digit codes with optional alphabetic suffixes, such as 85123A. Letters alone do not make a code invalid. This format policy is a documented heuristic; later catalog evidence may justify revisions.

No source descriptions or codes are rewritten. Missing descriptions alone do not invalidate a recognized product line. The financial effect of these decisions is measured in the sequential cleaning report.
