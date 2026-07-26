# Public storefront discovery

Use this process during first-time setup after the merchant supplies the public storefront URL, and refresh it when the configured discovery snapshot is stale. This discovery supplements authenticated merchant connectors; it never replaces order, customer, payment, inventory, or admin access.

## Run discovery

Initialize the runtime first, then run from the Skill directory:

```bash
python3 scripts/configure.py init
python3 scripts/discover_store.py --url https://store.example
python3 scripts/configure.py path store-discovery
python3 scripts/configure.py status
```

The command writes `store-discovery.json` under the private runtime directory and records its path and retrieval time in `config.json`. The merchant only needs to provide the public storefront URL. Do not ask for storefront admin credentials for this step.

After showing the findings and receiving merchant confirmation, record it with:

```bash
python3 scripts/configure.py storefront confirmed
```

The discovery process:

1. accepts only public HTTP or HTTPS destinations;
2. rejects credentials in URLs, private or local network addresses, and cross-host redirects;
3. reads `robots.txt`, follows its crawl rules, and considers declared sitemaps;
4. limits response size, page count, request time, and request rate;
5. extracts structured public product data, likely policy pages, and public campaign evidence;
6. records source URLs, retrieval time, warnings, and limitations;
7. never logs in, submits forms, accepts customer input, or reads customer, order, payment, admin, unpublished, or personalized data.

## Review the result

Show the merchant a short summary containing:

- detected platform and confidence;
- product count and a few sample product names;
- policy types and source URLs;
- campaign evidence and source URLs;
- blocked, unavailable, or ambiguous pages;
- explicit confirmation that only public pages were read.

Ask the merchant to confirm the primary domain and identify any missing regional store, help center, policy subdomain, or campaign source. Because cross-host discovery is intentionally blocked, each additional approved host must be run separately and retained as a separate source snapshot.

## Use in customer service

- Public product pages may support product descriptions, compatibility clues, published instructions, and public price displays. They do not prove what a customer purchased, the order variant, historical price, current stock, or entitlement.
- Public policy pages are candidate sources. Before using a term in a reply, check the relevant market, channel, product, effective date, version, exceptions, and any platform-level rules.
- Public banners and campaign copy are candidate evidence only. Do not promise eligibility until an authenticated campaign source or a human confirms the customer, product, region, channel, and order-time conditions.
- If public content conflicts with an authenticated commerce connector, versioned policy source, platform rule, or applicable law, do not resolve the conflict by guessing. Escalate or obtain the authoritative source.
- Complete order matching always requires an authorized commerce, marketplace, ERP, or OMS connector.

## Refresh and failure handling

Use `storefront.refresh_interval_hours` from `config.json`; the default is 24 hours. Refresh before processing when the snapshot is missing or older than that interval. Preserve the latest successful snapshot if a refresh fails, but mark it stale and do not use time-sensitive promotions, stock labels, prices, or policy terms without verification.

After first-time setup, refresh with the saved URL and configured limits:

```bash
python3 scripts/discover_store.py
```

Discovery failure must not block Gmail setup. It does block claims that depend on missing storefront evidence. Continue in `draft_only`, request the minimum missing information, or route the case to a human.
