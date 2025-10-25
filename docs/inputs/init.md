We need to take https://environ.jp/ and rewrite it's backend. We used to have a Ruby on Rails backend, which was rich, yet it was integrated with Netsuite. I had many functions. Now, we want to ditch many functions to rely on services: Stripe, RakutenPay, Klavyo, Algolia, Vouncherify. We will use PIM system - Canto PIM. All of the orders should go to the Netsuite (we will need to write a syncronization logic).




## Project Overview

Environ.jp is a Japanese skincare e‑commerce site with a React front‑end. The current back‑end is a feature‑rich Ruby on Rails monolith that integrates tightly with NetSuite for order management and inventory. Will integrate with a set of SaaS platforms to replace custom functionality:

- **NetSuite** – remains the system of record for orders, inventory and product restrictions. Orders will be synchronised to NetSuite on an hourly schedule and status updates/inventory changes will be pulled back. NetSuite controls purchase limits per product variant (e.g., maximum 3 units per customer per month).
    
- **Canto PIM** – holds cold product data (names, descriptions, images). Prices and stock availability stay in NetSuite. Product data will be pulled during static site builds (~every 3 hours) and through API calls for real‑time details.
    
- **Stripe & RakutenPay** – handle payments. Stripe Billing is used for subscriptions; RakutenPay is accessed via Stripe’s third‑party payment integration for konbini purchases. Refunds are initiated in Stripe and then reflected in our system and NetSuite.
    
- **Voucherify** – provides loyalty points, promotions, referral codes, samples, campaigns and tier statuses (Bronze/Silver/Gold). The goal is to delegate as much loyalty logic as possible to Voucherify and avoid custom code.
    
- **Klaviyo** – used for marketing and transactional emails. A separate team configures campaigns; our system must send the relevant events (sign‑up, purchase, subscription changes) to Klaviyo.
    
- **Algolia** – powers product search. Only products are indexed; no synonyms or multi‑language support is needed.
    
- **Auth0/Clerk** – identity provider for user accounts with social login (Facebook, Google, Line, Twitter). A “reset password” flow will be implemented to migrate existing users. No multi‑tenant or region‑specific rules.
    
- **Sanity CMS** – stores static page content and texts for the UI. Store details may be migrated here from the current database.

## Project Agreements & Expectations

- **User experience** – The existing React UI will remain, so new APIs must either match current endpoints or provide adapters. Screens and flows should stay intact.
    
- **Integrations first** – Wherever a SaaS can provide functionality (payments, loyalty, promotions, identity), use it rather than re‑implementing logic. This reduces custom code but may impose API or rate‑limit constraints.
    
- **Phase‑based delivery** – Work will be organised into modules (Essentials, Catalog, Step‑Up & Status, Search, Authentication, Cart & Marketing, Recommendations, Checkout & Payments, Subscriptions, Store Finder & NAVI, Netsuite integration, Stabilisation). Each module should be deliverable within ~two months.
    
- **Team composition** – Two React engineers for UI integration, one team lead, one DevOps, 2–3 back‑end engineers (including one from the client), and two manual QA testers. Automated tests should focus on integration and critical unit tests.
    
- **Timeline** – A total of about six months with progressive releases. Legacy subscriptions may need to operate in parallel until users migrate.
    
## Constraints and Assumptions

- **Language and Currency** – Japanese only; pricing and tax rules reflect Japanese consumption tax. Shipping is a flat fee nationwide with no surcharges.
    
- **Static vs. Dynamic data** – Product descriptions come from Canto PIM; prices and stock come from NetSuite. The site will be statically built every ~3 hours and will fetch fresh data from the back‑end for dynamic information.
    
- **Purchase Limits** – NetSuite enforces product restrictions such as maximum three units of the same variant per month. The back‑end must respect these limits and block add‑to‑cart actions accordingly.
    
- **Step‑Up (A‑Level Program)** – Customers must progress through vitamin‑A concentrations by purchasing lower‑level variants before higher concentrations. Detailed rules (concentration thresholds, purchase count or time requirements) are not yet finalised and will require a contingency buffer.
    
- **Status and Points** – Voucherify manages loyalty tiers (Bronze/Silver/Gold), A‑points and referral rewards. Point expiry rules are unclear; the system must be flexible to accommodate different expiry or rollover policies.
    
- **Subscriptions** – Only monthly frequency is supported. Subscription management (pause, skip, cancel, change payment method) relies on Stripe Billing; our back‑end should not re‑implement subscription logic unless Stripe lacks a needed feature.
    
- **Store Finder & Commission** – Customers choose a store during sign‑up or checkout; orders are tagged with the store ID and commission flows through NetSuite. Store data (name, address, coordinates) may be stored in Sanity CMS with IDs retained in the back‑end.
    
- **QR Code & Apple Wallet** – Each user has a QR code that encodes only their customer ID. A pass can be added to Apple Wallet; it does not update dynamically when status/points change. Android support is not required.


## Goal

1. What are we brainstorming about? We need to build an estimation of delivery of the project described in @docs/inputs/init.md and @docs/inputs/implementation.md . We need to parallel the delivery into 2 streams. Build a risks registry for the project, open questions. We need a risks-aware delivery strategy of such project
2. Are there any constraints or parameters we should keep in mind?(Time limits, budget, existing systems, must-haves, deal-breakers, etc.) See the @docs/inputs/init.md 
3. Is the goal broad exploration or focused ideation on specific aspects?(Are we casting a wide net or diving deep into something particular?) Dive deep to avoid any gaps. We need a risks-aware delivery strategy of such project.
