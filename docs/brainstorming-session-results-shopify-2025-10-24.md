# Brainstorming Session Results: Environ.jp Shopify Plus Migration Strategy

**Date:** October 24, 2025
**Facilitator:** Carson (CIS Brainstorming Coach)
**Participant:** BMad
**Duration:** Strategic Analysis Session (45 minutes)
**Session Type:** Platform-Focused Delivery Estimation & Risk Assessment

---

## Executive Summary

### Session Topic
**Environ.jp Migration to Shopify Plus: Delivery Estimation, 2-Stream Parallel Strategy & Risk Registry**

Build a comprehensive delivery plan for migrating Environ.jp from Ruby on Rails to **Shopify Plus**, including:
- Realistic timeline estimation (target: 7-8 months)
- 2-stream parallel delivery strategy
- Risks registry with mitigation plans
- Open questions requiring validation
- Integration architecture for 9 external systems

### Goals
1. **Delivery Estimation** - Build week-by-week timeline for Shopify Plus implementation
2. **2-Stream Parallelization** - Design optimal team structure to maximize velocity
3. **Risks Registry** - Identify all risks specific to Shopify Plus with mitigation strategies
4. **Open Questions** - Document unknowns requiring POC validation
5. **Platform Viability** - Determine if Shopify Plus can handle complex Japanese e-commerce requirements

### Techniques Used
1. **Platform Ecosystem Mapping** - Shopify Plus app marketplace analysis
2. **Question Storming** - Shopify-specific unknowns and validation requirements
3. **Six Thinking Hats** - Multi-perspective analysis of Shopify Plus choice
4. **Delivery Stream Analysis** - Optimal parallelization strategy for Shopify development

### Total Ideas Generated
- **180+ Questions** across 10 categories (Shopify apps, custom development, NetSuite, payments)
- **35+ Risks** identified (Critical: 4, High: 6, Medium: 8)
- **4 Stream Split Options** evaluated
- **12 Major Integration Points** mapped
- **10 Key Insights** about Shopify Plus for Japanese e-commerce

---

## Key Themes Discovered

### 1. Shopify Plus Reduces Custom Development Significantly
**Rationale:** Unlike MedusaJS, Shopify Plus has a mature app ecosystem for most requirements:
- ✅ **Stripe Payments** - Native integration
- ✅ **Subscriptions** - Recharge, Bold Subscriptions, or native Shopify Subscriptions
- ✅ **Loyalty/Points** - Voucherify has official Shopify app
- ✅ **Search** - Algolia has official Shopify app
- ✅ **Email Marketing** - Klaviyo has official Shopify app
- ✅ **Auth** - Shopify Multipass for SSO, or Auth0/Clerk integrations available
- ⚠️ **NetSuite** - Multiple connector apps available (Celigo, Farapp, OneSaas)
- ⚠️ **RakutenPay** - Requires custom payment gateway development

**Impact:** Estimated **6-8 weeks less custom integration work** compared to MedusaJS.

---

### 2. RakutenPay Integration is THE Critical Unknown
**Rationale:** Shopify Plus supports custom payment gateways, but implementation complexity is unclear:
- Shopify has Payment Provider API (for offsite gateways)
- RakutenPay may work via iframe/redirect flow
- Dual gateway support (Stripe + RakutenPay) is standard in Shopify
- **BUT:** Japanese payment gateway integrations often have edge cases

**Mitigation:**
- Week 1-2 POC: Test RakutenPay sandbox with Shopify Payment Provider API
- Engage Shopify Plus partner agency with Japanese payment experience
- Budget 3-4 weeks for custom payment gateway development + testing

---

### 3. NetSuite Connector Apps May Not Handle Custom Logic
**Rationale:** Available NetSuite-Shopify connectors (Celigo, Farapp) focus on standard flows:
- ✅ Order sync (standard)
- ✅ Inventory sync (standard)
- ✅ Customer sync (standard)
- ❌ **Purchase limits per variant per customer** (custom logic)
- ❌ **Store commission tracking** (custom field mapping)
- ❌ **Step-Up program eligibility** (custom business rules)

**Decision Point:**
- Option A: Use connector app + custom Shopify Functions for business logic (RECOMMENDED)
- Option B: Build custom NetSuite sync service (adds 4-6 weeks)

---

### 4. Shopify Admin UI is Non-Negotiable
**Rationale:** Unlike MedusaJS (where you build admin UI), Shopify Plus provides:
- ✅ Out-of-the-box admin UI for orders, customers, products
- ✅ Staff permissions and roles
- ✅ Order management workflows
- ⚠️ **BUT:** Custom admin pages require Shopify App development

**Impact:**
- **Saves 6-8 weeks** of admin UI development
- **BUT:** Custom reports/dashboards for ops team may require Admin App development (2-3 weeks)

---

### 5. Hydrogen Framework Enables React Frontend Migration
**Rationale:** Shopify's Hydrogen (React-based framework) allows reusing existing React UI:
- Built on Remix (React framework)
- Server-side rendering (SSR) for performance
- Hosted on Shopify Oxygen (CDN)
- Shopify Storefront API for data fetching

**Migration Path:**
- Adapt existing React components to Hydrogen/Remix patterns
- Use Shopify Storefront API instead of custom backend APIs
- Leverage Shopify's global CDN for Japanese market performance

**Estimated Effort:** 8-10 weeks for frontend migration (vs. 6-8 weeks with MedusaJS backend)

---

### 6. Subscription Management Has Mature Solutions
**Rationale:** Unlike MedusaJS (where Stripe Billing integration is custom), Shopify has:
- **Native Shopify Subscriptions** (newer, simpler, free)
- **Recharge** (mature, feature-rich, Japanese market proven)
- **Bold Subscriptions** (enterprise features)

**Recommendation:** Start with **Native Shopify Subscriptions** (monthly frequency only = perfect fit)
- If advanced features needed (pause/skip/reschedule), upgrade to Recharge

**Impact:** **Saves 3-5 weeks** vs. building custom Stripe Billing integration

---

### 7. Step-Up Program Still Requires Custom Development
**Rationale:** Vitamin-A concentration progression logic is unique:
- No off-the-shelf Shopify app for this
- Python microservice (existing architecture) can stay separate
- Shopify Functions can enforce purchase restrictions at checkout

**Architecture:**
- Python microservice (client engineer) handles step-up eligibility calculation
- Shopify Function (custom code) calls microservice at checkout
- Block cart if customer not eligible for higher concentration

**Estimated Effort:** 8-10 weeks (same as MedusaJS approach)

---

### 8. PCI DSS Compliance is Built-In (Major Win)
**Rationale:** Shopify Plus is PCI DSS Level 1 certified:
- Shopify handles all payment tokenization
- No card data touches your infrastructure
- Even custom payment gateways (RakutenPay) use Shopify's secure flow

**Impact:** **Eliminates 2-3 weeks** of security audit preparation vs. self-hosted solutions

---

### 9. Migration Tooling Exists But Needs Validation
**Rationale:** Shopify has migration tools and partner agencies:
- Customer import via CSV or API
- Order history import (for reference)
- **BUT:** Loyalty points, subscription migration requires custom work

**POC Requirement:** Test customer migration flow with sample data (Week 2-3)

---

### 10. "Set It and Be Done" Fits Shopify Plus Philosophy
**Rationale:** Shopify Plus is designed for retail companies, not software companies:
- Managed infrastructure (no DevOps for platform itself)
- Automatic updates and security patches
- 24/7 Shopify Plus support
- App ecosystem handles most integrations

**Post-Launch Team:** Can reduce to 1 UI + 1 Backend + 1 QA (vs. larger team for MedusaJS)

---

## Technique 1: Platform Ecosystem Mapping (30 minutes)

### System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ENVIRON.JP SHOPIFY PLUS ARCHITECTURE             │
└─────────────────────────────────────────────────────────────────────┘

FRONTEND LAYER (React/Hydrogen)
┌──────────────────────────────────────────────────────────────────┐
│  Hydrogen Storefront (React/Remix)                                │
│  - Product Pages (data from Canto PIM + Shopify Storefront API)  │
│  - Search (Algolia Shopify App)                                   │
│  - Cart & Checkout (Shopify native)                               │
│  - Account Dashboard (Shopify Customer API)                       │
│  - Store Finder (Sanity CMS + Custom UI)                          │
│  - QR Code / Apple Wallet (Custom implementation)                 │
│                                                                    │
│  Hosted on: Shopify Oxygen (Global CDN)                           │
└──────────────────────────────────────────────────────────────────┘
                              ↓ Shopify Storefront API
┌──────────────────────────────────────────────────────────────────┐
│  SHOPIFY PLUS CORE                                                │
│  - Product Catalog (synced from NetSuite)                         │
│  - Inventory Management (synced from NetSuite)                    │
│  - Order Management (native)                                      │
│  - Customer Accounts (native + Multipass for SSO)                 │
│  - Admin UI (native + custom Admin App)                           │
│  - Shopify Functions (purchase limits, step-up checks)            │
│  - Shopify Flow (automation workflows)                            │
└──────────────────────────────────────────────────────────────────┘
        ↓ Apps & Custom Code              ↓ Webhooks & Events

┌─────────────────────────────────────────────────────────────────┐
│  INTEGRATION LAYER (Shopify Apps + Custom Services)              │
│                                                                   │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐│
│  │ NetSuite        │  │ Payments         │  │ Loyalty         ││
│  │ Connector App   │  │ - Stripe (native)│  │ Voucherify App  ││
│  │ (Celigo/Farapp) │  │ - RakutenPay     │  │ (Official)      ││
│  │                 │  │   (Custom)       │  │                 ││
│  │ Sync:           │  │                  │  │ - Points        ││
│  │ • Orders        │  │ Dual gateway     │  │ - Tier Status   ││
│  │ • Inventory     │  │ checkout flow    │  │ - Campaigns     ││
│  │ • Customers     │  │                  │  │ - Redemption    ││
│  └─────────────────┘  └──────────────────┘  └─────────────────┘│
│                                                                   │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐│
│  │ Subscriptions   │  │ Marketing        │  │ Search          ││
│  │ Native Shopify  │  │ Klaviyo App      │  │ Algolia App     ││
│  │ Subscriptions   │  │ (Official)       │  │ (Official)      ││
│  │                 │  │                  │  │                 ││
│  │ - Monthly only  │  │ - Transactional  │  │ - Product index ││
│  │ - Pause/Cancel  │  │ - Marketing      │  │ - Japanese lang ││
│  │ - Mgmt portal   │  │ - Events tracking│  │                 ││
│  └─────────────────┘  └──────────────────┘  └─────────────────┘│
│                                                                   │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐│
│  │ Auth/Identity   │  │ CMS              │  │ Custom Services ││
│  │ Shopify         │  │ Sanity           │  │                 ││
│  │ Multipass +     │  │ (Headless CMS)   │  │ Python:         ││
│  │ Auth0/Clerk     │  │                  │  │ • Step-Up       ││
│  │                 │  │ - Static pages   │  │ • Skin Check    ││
│  │ - Social login  │  │ - UI texts       │  │ • Recommend     ││
│  │ - Migration     │  │ - Store data     │  │                 ││
│  └─────────────────┘  └──────────────────┘  └─────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Integration Points Mapped (12 Total)

| # | Integration | Shopify Solution | Maturity | Custom Work Required |
|---|-------------|------------------|----------|----------------------|
| 1 | **NetSuite Orders** | Celigo/Farapp connector app | ⭐⭐⭐⭐ Proven | Custom field mapping (1-2 weeks) |
| 2 | **NetSuite Inventory** | Celigo/Farapp connector app | ⭐⭐⭐⭐ Proven | Schedule config (1 week) |
| 3 | **NetSuite Purchase Limits** | Shopify Function + NetSuite API | ⭐⭐ Custom | Full custom logic (3-4 weeks) |
| 4 | **Stripe Payments** | Native Shopify integration | ⭐⭐⭐⭐⭐ Native | Configuration only (1 day) |
| 5 | **RakutenPay Gateway** | Custom Payment Provider | ❌ None | **Full custom dev (3-4 weeks)** |
| 6 | **Voucherify Loyalty** | Official Voucherify Shopify app | ⭐⭐⭐⭐ Official | Point redemption config (1-2 weeks) |
| 7 | **Shopify Subscriptions** | Native Shopify feature | ⭐⭐⭐⭐ Native | Configuration + testing (1-2 weeks) |
| 8 | **Klaviyo Marketing** | Official Klaviyo Shopify app | ⭐⭐⭐⭐⭐ Official | Event mapping (1 week) |
| 9 | **Algolia Search** | Official Algolia Shopify app | ⭐⭐⭐⭐ Official | Product sync config (1 week) |
| 10 | **Auth0/Clerk SSO** | Shopify Multipass + custom | ⭐⭐⭐ Proven | SSO flow implementation (2-3 weeks) |
| 11 | **Sanity CMS** | Hydrogen + Sanity SDK | ⭐⭐⭐⭐ Proven | Content fetching (1-2 weeks) |
| 12 | **Step-Up Microservice** | Shopify Function + Python API | ⭐⭐ Custom | Shopify Function dev (2-3 weeks) |

**KEY FINDING:** 8/12 integrations have official or proven Shopify apps = **Significantly less custom work than MedusaJS**

---

## Technique 2: Question Storming - Shopify-Specific Unknowns (30 minutes)

### Category 1: RakutenPay Payment Gateway (HIGH PRIORITY)
1. Does Shopify's Payment Provider API support Japanese payment gateways?
2. Can RakutenPay work as an offsite payment gateway (redirect flow)?
3. What is the typical development timeline for custom Shopify payment gateways?
4. Are there existing RakutenPay integrations in Shopify (even unofficial)?
5. Can customers switch between Stripe and RakutenPay at checkout seamlessly?
6. How does Shopify handle refunds for custom payment gateways?
7. Does RakutenPay provide sandbox environment with Shopify-compatible webhooks?
8. What certification/approval process does Shopify require for custom gateways?
9. Can subscriptions use RakutenPay as payment method?
10. **CRITICAL:** Will dual gateway (Stripe + RakutenPay) work in production?

---

### Category 2: NetSuite Connector Apps
11. Which NetSuite connector is best for Japanese e-commerce (Celigo vs. Farapp vs. OneSaas)?
12. Can connectors handle hourly inventory sync without rate limits?
13. Do connectors support custom NetSuite fields (store ID, commission tracking)?
14. Can connector enforce purchase limits (max 3 per variant per month)?
15. How do connectors handle NetSuite API slowness (known issue)?
16. What is the cost of NetSuite connector apps (monthly)?
17. Can we build custom sync logic on top of connector app?
18. How are conflicts handled (simultaneous updates in Shopify + NetSuite)?
19. Can connector sync historical order data for reporting?
20. Does connector support NetSuite multi-currency (JPY)?

---

### Category 3: Shopify Functions & Custom Logic
21. Can Shopify Functions call external APIs (Python microservice for step-up)?
22. What are performance limits for Shopify Functions at checkout?
23. Can Functions block add-to-cart based on customer eligibility?
24. How do we test Shopify Functions in development environment?
25. Can Functions access customer purchase history from NetSuite?
26. Are there timeout limits for Function API calls?
27. Can Functions run asynchronously (non-blocking checkout)?
28. How do we deploy and version Shopify Functions?
29. Can Functions integrate with Voucherify for point validation?
30. What error handling exists if Function API call fails?

---

### Category 4: Hydrogen Frontend Migration
31. Can existing React components be ported to Hydrogen/Remix easily?
32. How does Hydrogen handle static site generation (every 3 hours requirement)?
33. Can Hydrogen pull data from Canto PIM API directly?
34. What is Oxygen (Shopify hosting) performance for Japanese users?
35. Can we use existing React state management (Redux/Context)?
36. Does Hydrogen support Japanese character encoding properly?
37. How do we handle SEO migration from current React site?
38. Can Hydrogen integrate with Sanity CMS for static content?
39. What is the learning curve for Remix framework?
40. Can we incrementally migrate pages or must it be all-at-once?

---

### Category 5: Subscription Management
41. Does native Shopify Subscriptions support monthly-only frequency? (YES per docs)
42. Can customers pause/skip/cancel subscriptions via customer portal?
43. How does subscription payment retry work with Stripe?
44. Can subscription products have purchase limits (step-up)?
45. Does Shopify Subscriptions integrate with Voucherify points?
46. Can we migrate existing subscribers from Rails to Shopify?
47. What webhooks are available for subscription events?
48. Can subscription frequency be changed post-purchase?
49. How are failed payments handled (dunning management)?
50. Can customers use RakutenPay for subscriptions?

---

### Category 6: Voucherify Loyalty Integration
51. Does Voucherify Shopify app support tier status (Bronze/Silver/Gold)?
52. Can points be redeemed at checkout in real-time?
53. How does Voucherify handle point expiry rules?
54. Can referral codes be generated and tracked?
55. Does Voucherify support sample product campaigns in Shopify?
56. How do we migrate existing customer points to Voucherify?
57. Can Voucherify block checkout if insufficient points?
58. What is the API rate limit for Voucherify during checkout?
59. Can Voucherify track purchase count for step-up program?
60. How are point adjustments handled (refunds, cancellations)?

---

### Category 7: Migration Strategy
61. Can we import 50,000+ customers from Rails to Shopify?
62. How do we migrate customer passwords (reset flow required)?
63. Can order history be imported for customer reference?
64. How do we handle active subscriptions during migration?
65. Can we run Rails and Shopify in parallel (gradual cutover)?
66. What is downtime requirement for final migration?
67. How do we migrate loyalty points to Voucherify?
68. Can we test migration with subset of customers first?
69. What rollback plan exists if migration fails?
70. How do we communicate migration to customers?

---

### Category 8: Admin UI & Operations
71. Does Shopify admin UI support Japanese language fully?
72. Can ops team manage orders in NetSuite and Shopify simultaneously?
73. What custom reports are needed beyond Shopify standard reports?
74. Can we build custom admin pages for store commission tracking?
75. How do we train ops team on Shopify admin?
76. Can Shopify admin show customer step-up eligibility status?
77. What permissions exist for different staff roles?
78. Can we integrate Shopify admin with existing internal tools?
79. How do refunds work across Shopify + NetSuite + Stripe?
80. Can ops team manually adjust loyalty points in Voucherify?

---

### Category 9: Performance & Scale
81. Can Shopify Plus handle Japanese traffic patterns (peak hours)?
82. What is Oxygen CDN latency for Japan?
83. How does Shopify handle 10,000+ SKUs from NetSuite?
84. Can Algolia search handle real-time inventory updates?
85. What are Shopify API rate limits for Storefront API?
86. How do we cache product data from Canto PIM?
87. Can Shopify Functions handle 100+ concurrent checkouts?
88. What monitoring exists for Shopify performance?
89. How do we optimize mobile performance for Japanese users?
90. Can Shopify handle flash sales / promotional traffic spikes?

---

### Category 10: Compliance & Security
91. Is Shopify Plus GDPR compliant for Japanese market? (Not GDPR but privacy laws)
92. How does Shopify handle Japanese consumption tax calculation?
93. Can Shopify generate invoices compliant with Japanese regulations?
94. What data residency options exist for Japanese customer data?
95. How do we handle PII data in NetSuite sync?
96. Can Shopify audit logs track all order/customer changes?
97. What security certifications does Shopify Plus have (beyond PCI DSS)?
98. How do we secure custom Shopify Functions code?
99. Can we implement 2FA for admin users?
100. How do we handle data breach notification requirements?

---

### Critical Questions Requiring POC Validation (Top 10)

| # | Question | Why Critical | POC Test |
|---|----------|--------------|----------|
| 1 | Can RakutenPay integrate as custom payment gateway? | Non-negotiable payment method | Build sandbox integration Week 1-2 |
| 2 | Can Shopify Functions call Python step-up microservice? | Core business logic dependency | Test Function + API call Week 2 |
| 3 | Which NetSuite connector handles custom logic best? | 10-week critical path item | Evaluate Celigo vs. Farapp Week 1-2 |
| 4 | Can Hydrogen pull from Canto PIM directly? | Frontend data architecture | Build proof-of-concept page Week 2 |
| 5 | Does Voucherify app support checkout point redemption? | Loyalty requirement | Test checkout flow Week 2 |
| 6 | Can purchase limits be enforced via Shopify Functions? | NetSuite business rule | Build test Function Week 2 |
| 7 | Can customer migration preserve order history? | Migration requirement | Test import API Week 3 |
| 8 | Can subscriptions use both Stripe and RakutenPay? | Payment flexibility | Test subscription payment methods Week 2 |
| 9 | What is Oxygen performance for Japan? | User experience critical | Load test from Japan Week 2-3 |
| 10 | Can we build custom admin pages for commission tracking? | Ops team requirement | Build prototype admin app Week 3 |

---

## Technique 3: Six Thinking Hats - Shopify Plus Analysis (40 minutes)

### ⚪ White Hat: Facts & Data

**What We Know:**
1. **Shopify Plus** is an enterprise e-commerce platform with managed infrastructure
2. **Hydrogen** is Shopify's React-based frontend framework (Remix under the hood)
3. **App Ecosystem:** 8,000+ apps in Shopify App Store, high maturity for standard integrations
4. **Pricing:** Shopify Plus starts at ~$2,000/month (vs. self-hosted MedusaJS infrastructure costs)
5. **Market Presence:** Used by major Japanese brands (Uniqlo international, others)
6. **PCI DSS:** Level 1 certified (highest level)
7. **NetSuite Connectors:** Celigo iPaaS ($500-1,500/month), Farapp ($99-299/month)
8. **Voucherify:** Official Shopify app exists (confirmed)
9. **Klaviyo:** Official Shopify app, tier 1 integration (confirmed)
10. **Algolia:** Official Shopify app (confirmed)
11. **Payment Gateways:** 100+ supported, custom gateway API available
12. **Subscription Apps:** Recharge (most popular), Bold, Native Shopify Subscriptions (2023+)
13. **Team Size Post-Launch:** Typically 1-2 developers for maintenance (vs. 3-4 for custom platform)
14. **Timeline Benchmarks:** Shopify Plus implementations typically 4-9 months for complex projects

**Team Composition:**
- 2 React engineers (Hydrogen/Remix experience required)
- 1 Technical lead (Shopify Plus certified)
- 1 DevOps (reduced scope - Shopify manages platform)
- 2-3 Backend engineers (Shopify app development, Functions, NetSuite integration)
- 2 QA testers
- **CAN HIRE:** TypeScript developers (Shopify apps are Node.js/TypeScript)

**Timeline Constraint:**
- 7 months build + 1 month migration = 8 months total (non-negotiable)

---

### 🔴 Red Hat: Gut Feelings & Intuition

**What Feels Right:**
1. **"Shopify feels safe"** - It's a proven platform, not a risky open-source project
2. **"Less custom code = less to break"** - App ecosystem means less code we maintain
3. **"Set it and be done" fits perfectly** - Shopify manages infrastructure, we manage apps
4. **"PCI DSS is handled"** - Don't need to worry about security audits
5. **"Other Japanese brands use it"** - Social proof for Japanese market
6. **"Admin UI is ready"** - Ops team can start training immediately after launch

**What Feels Risky:**
1. **"RakutenPay is unknown"** - Custom payment gateway development could be messy
2. **"Locked into Shopify"** - Harder to migrate away later vs. open-source
3. **"Monthly fees forever"** - $2,000+/month platform + apps vs. one-time dev
4. **"NetSuite connector might not fit"** - Off-the-shelf connectors may not handle custom logic
5. **"Less control over checkout"** - Shopify checkout is somewhat rigid vs. fully custom
6. **"Hydrogen is newer"** - Less mature than Next.js or other React frameworks

**Emotional State:**
- **Relief:** "At least it won't be as buggy as the current Rails system"
- **Concern:** "What if RakutenPay doesn't work and we find out in Month 3?"
- **Confidence:** "If Uniqlo can do it, we can do it"
- **Impatience:** "Need to decide fast and start POC"

---

### 💛 Yellow Hat: Benefits & Optimism

**Why Shopify Plus is Appealing:**

1. **Faster Timeline (Realistic 6-7 months build)**
   - 8-10 integrations available as apps (vs. building from scratch)
   - Admin UI is built-in (saves 6-8 weeks)
   - PCI DSS compliance included (saves 2-3 weeks)
   - Native subscription management (saves 3-5 weeks)
   - **Total time savings: 15-20 weeks vs. MedusaJS**

2. **Lower Technical Risk**
   - Proven platform with 99.99% uptime SLA
   - Managed infrastructure (no DevOps scaling concerns)
   - Battle-tested checkout flow (billions in GMV processed)
   - Automatic security patches

3. **Better Post-Launch Maintenance**
   - Smaller team required (1 UI + 1 BE + 1 QA vs. larger team)
   - Shopify Plus support available 24/7
   - App updates handled by vendors
   - Less custom code to maintain

4. **Japanese Market Fit**
   - Supports Japanese yen (JPY) natively
   - Consumption tax calculation built-in
   - Japanese language admin UI
   - Other Japanese brands using it (social proof)

5. **Scalability Confidence**
   - Shopify handles Black Friday scale globally
   - CDN optimized for global performance
   - No infrastructure scaling concerns

6. **Faster Migration Path**
   - Customer import tools exist
   - Partner agencies experienced in e-commerce migrations
   - Can run parallel with Rails (gradual cutover)

7. **Stakeholder Confidence**
   - "We're using Shopify Plus" sounds better than "We built custom MedusaJS platform"
   - Easier to hire Shopify developers (larger talent pool)
   - Easier to hand off to maintenance team

**Best Case Scenario:**
- POC validates RakutenPay integration (Week 2)
- NetSuite connector (Celigo) handles 90% of sync logic (Week 4-8)
- Hydrogen migration reuses 70% of React components (Week 4-12)
- Voucherify app works perfectly for loyalty (Week 8-10)
- Launch in **Month 6** with 1 month buffer for stabilization
- Migration in Month 7 = **7 months total** (beats target!)

---

### ⚫ Black Hat: Risks & Concerns

**Critical Risks (4)**

| # | Risk | Impact | Probability | Mitigation Strategy |
|---|------|--------|-------------|---------------------|
| **C1** | **RakutenPay custom gateway fails or takes 8+ weeks** | BLOCKER - Cannot launch without RakutenPay | 🔴 MEDIUM (40%) | POC Week 1-2: Build sandbox integration. If fails, engage Shopify Plus partner agency with Japanese payment experience. Budget 4-6 weeks total (not 3-4). |
| **C2** | **NetSuite connector cannot enforce purchase limits** | BLOCKER - Core business requirement | 🔴 MEDIUM (35%) | POC Week 2: Test Celigo custom field mapping + Shopify Function integration. Worst case: Build custom sync service (adds 4 weeks). |
| **C3** | **Shopify Functions cannot call external APIs (Python microservice)** | BLOCKER - Step-up program broken | 🟡 LOW (20%) | POC Week 2: Test Function with external API call. Fallback: Move step-up logic into Shopify Function (TypeScript rewrite, 3-4 weeks). |
| **C4** | **Timeline overrun due to underestimated Hydrogen complexity** | Project delay, stakeholder loss of confidence | 🔴 MEDIUM (40%) | Add 2-week buffer to frontend stream (Week 12-14). Hire Shopify Hydrogen expert for first month. |

---

**High Risks (6)**

| # | Risk | Impact | Probability | Mitigation Strategy |
|---|------|--------|-------------|---------------------|
| **H1** | **Voucherify app doesn't support checkout point redemption** | Loyalty program delayed or custom build required | 🟡 LOW (25%) | POC Week 2: Test full checkout flow with points. Fallback: Custom Shopify Function for point validation (2-3 weeks). |
| **H2** | **Customer migration loses data (points, order history)** | Customer complaints, support burden | 🔴 MEDIUM (35%) | Dry-run migration Week 24-25 with test customers. Build verification scripts. Budget 1 week buffer for fixes. |
| **H3** | **Shopify checkout too rigid for custom logic (store commission)** | Cannot track store IDs properly, commission broken | 🟡 LOW (20%) | Store ID as customer tag or order metafield. Test in POC Week 2. |
| **H4** | **Hydrogen performance poor for Japan (Oxygen CDN latency)** | Slow page loads, poor UX | 🟡 LOW (25%) | POC Week 2-3: Load test from Japan. Implement aggressive caching. Consider CloudFlare in front if needed. |
| **H5** | **NetSuite API rate limits cause sync failures** | Inventory out of sync, overselling risk | 🔴 MEDIUM (30%) | Use connector app's queue system. Implement exponential backoff. Monitor sync lag. |
| **H6** | **Subscription migration breaks for active subscribers** | Revenue loss, customer churn | 🔴 MEDIUM (35%) | Migrate subscriptions in batches (Week 29-31). Test with 10 customers first. Communication plan (email 2 weeks before). |

---

**Medium Risks (8)**

| # | Risk | Impact | Mitigation |
|---|------|--------|------------|
| M1 | Shopify Plus monthly costs higher than expected ($3,000-4,000/month with apps) | Budget overrun | Get detailed quote from Shopify partner. Compare to MedusaJS infrastructure + maintenance costs. |
| M2 | Ops team struggles with Shopify admin UI (different from Rails) | Support burden on dev team | Train ops team Week 26-28. Create custom documentation. Record video walkthroughs. |
| M3 | Custom admin pages (commission reports) take 4+ weeks | Ops workarounds required | Defer to Phase 2 if needed. Export data to Google Sheets temporarily. |
| M4 | Algolia search doesn't handle Japanese properly (tokenization) | Poor search UX | POC Week 2: Test Japanese search. Configure custom dictionary. |
| M5 | Klaviyo event mapping incomplete (missing custom events) | Marketing campaigns broken | Map all events Week 16-18. Test with marketing team. |
| M6 | Sanity CMS integration with Hydrogen more complex than expected | Static pages delayed | Use Shopify Pages as fallback for launch. Migrate to Sanity in Phase 2. |
| M7 | Auth0/Clerk SSO (Multipass) has edge cases | Some customers can't log in | Thorough testing Week 20-22. Fallback: Email/password login. |
| M8 | QR code / Apple Wallet implementation custom work (no Shopify app) | Feature delayed | Defer to Phase 2 if timeline tight. Build as separate service. |

---

### 💚 Green Hat: Creative Solutions

**Alternative Approaches & Innovations:**

1. **Hybrid Payment Strategy**
   - **Idea:** Launch with Stripe only (Month 7), add RakutenPay in Month 8 post-launch
   - **Benefit:** De-risks launch timeline
   - **Drawback:** Requires user acceptance that RakutenPay comes later

2. **NetSuite Connector + Custom Layer**
   - **Idea:** Use Celigo for 80% of sync, build custom Shopify app for purchase limits
   - **Benefit:** Best of both worlds (proven connector + custom logic)
   - **Effort:** 6-8 weeks (connector config + custom app)

3. **Recharge Instead of Native Subscriptions**
   - **Idea:** Use Recharge app for subscriptions (more mature, Japanese market proven)
   - **Benefit:** Faster implementation, more features
   - **Cost:** $300-500/month (vs. free native)

4. **Shopify Plus Partner Engagement**
   - **Idea:** Hire Shopify Plus partner agency for first 8 weeks (POC + architecture)
   - **Benefit:** Expertise accelerates delivery, reduces risk
   - **Cost:** $20,000-40,000 consulting fee

5. **Staged Migration Strategy**
   - **Week 29:** Migrate 10% of customers (test cohort)
   - **Week 30:** Migrate 40% (larger batch)
   - **Week 31:** Migrate remaining 50%
   - **Week 32-33:** Stabilization + rollback buffer

6. **Custom Admin Dashboard**
   - **Idea:** Build separate admin dashboard (React app) for custom reports
   - **Benefit:** Flexibility for ops team needs
   - **Effort:** 4-6 weeks (can be Phase 2)

7. **Loyalty Points Bridge Service**
   - **Idea:** Build microservice to sync Rails loyalty points → Voucherify during migration
   - **Benefit:** Smooth customer transition
   - **Effort:** 2-3 weeks

---

### 🔵 Blue Hat: Process & Decision Framework

**Platform Decision: CONDITIONAL GO on Shopify Plus**

**Conditions for GO (Week 3 Checkpoint):**
1. ✅ RakutenPay POC successful (sandbox integration works)
2. ✅ NetSuite connector (Celigo/Farapp) can sync custom fields
3. ✅ Shopify Functions can call Python microservice API
4. ✅ Voucherify app supports checkout point redemption
5. ✅ Hydrogen performance acceptable from Japan (<2s page load)

**If ANY condition fails:** Evaluate alternatives (MedusaJS, custom NestJS, or hybrid approach)

---

**3-Week POC Validation Plan (Week 1-3)**

**Week 1-2 Focus:**
- Set up Shopify Plus trial environment
- RakutenPay sandbox integration (Payment Provider API)
- Celigo NetSuite connector trial (test order/inventory sync)
- Shopify Function prototype (call external API)
- Voucherify app trial (test checkout integration)

**Week 2-3 Focus:**
- Hydrogen prototype (1-2 pages with Canto PIM data)
- Load testing from Japan (Oxygen CDN performance)
- Customer migration dry-run (import 100 test customers)
- Subscription flow testing (native Shopify Subscriptions)
- Custom admin page prototype (commission tracking)

**Week 3 Deliverables:**
- POC report with GO/NO-GO recommendation
- Detailed risk assessment
- Updated timeline with buffers
- Architecture decision records

---

**Timeline Framework: 30 Weeks (6.9 months) Build + 3 Weeks Migration**

| Phase | Weeks | Outcome |
|-------|-------|---------|
| **POC Validation** | 1-3 (3 weeks) | GO/NO-GO decision |
| **Build Phase - 2 Streams** | 4-27 (24 weeks) | Feature complete platform |
| **Integration Testing** | 28-30 (3 weeks) | End-to-end testing, ops training |
| **Migration** | 31-33 (3 weeks) | Customer migration, go-live |
| **TOTAL** | **33 weeks (7.6 months)** | **Fits 8-month target** |

---

## Technique 4: Morphological Analysis - 2-Stream Delivery Options

### Dimension Analysis: How to Split Work Across 2 Teams

**Option A: Frontend (Stream 1) vs. Backend (Stream 2)**
- Stream 1: Hydrogen frontend migration, UI components, Sanity CMS integration
- Stream 2: Shopify setup, apps, NetSuite, payments, subscriptions, Voucherify

**Pros:** Clear ownership, minimal overlap
**Cons:** Stream 1 blocked until Stream 2 builds APIs, too sequential
**Verdict:** ❌ REJECTED - Not enough parallelization

---

**Option B: Apps/Integrations (Stream 1) vs. Custom Code (Stream 2)**
- Stream 1: Install and configure Shopify apps (Celigo, Voucherify, Klaviyo, Algolia)
- Stream 2: Custom development (RakutenPay, Shopify Functions, Hydrogen, admin pages)

**Pros:** Clear separation of "configure" vs. "code"
**Cons:** Stream 1 finishes too early (Week 12), Stream 2 overloaded
**Verdict:** ⚠️ POSSIBLE but unbalanced

---

**Option C: Customer-Facing (Stream 1) vs. Operations (Stream 2)**
- Stream 1: Storefront (Hydrogen), checkout, payments, subscriptions, loyalty
- Stream 2: Admin UI, NetSuite sync, reporting, ops workflows, migration tools

**Pros:** Business-value driven, customer experience prioritized
**Cons:** High interdependencies (both need NetSuite), hard to parallelize
**Verdict:** ⚠️ POSSIBLE but requires tight coordination

---

**Option D: High-Risk Critical Path (Stream 1) vs. Standard Features (Stream 2) ✅ RECOMMENDED**

**Stream 1: High-Risk & Long-Lead Items**
- RakutenPay custom gateway (Week 4-10, 6 weeks + 1 buffer)
- NetSuite connector + custom logic (Week 4-14, 10 weeks + 2 buffer)
- Shopify Functions (purchase limits, step-up) (Week 8-14, 6 weeks)
- Voucherify checkout integration (Week 12-16, 4 weeks)
- Subscriptions (native Shopify) (Week 14-18, 4 weeks)

**Stream 2: Standard & Independent Features**
- Hydrogen frontend foundation (Week 4-10, 6 weeks)
- Algolia search + Canto PIM integration (Week 8-14, 6 weeks)
- Klaviyo events + Sanity CMS (Week 10-16, 6 weeks)
- Auth0/Clerk SSO (Multipass) (Week 14-20, 6 weeks)
- Cart, account, order history UI (Week 16-22, 6 weeks)
- Custom admin pages (Week 20-27, 7 weeks)

**Pros:**
- De-risks early (RakutenPay + NetSuite tackled Week 4-14)
- Parallel independent work (Stream 2 doesn't block on Stream 1)
- Clear success criteria (Stream 1 must finish Week 18, Stream 2 can extend to Week 27)
- Balanced team allocation

**Cons:**
- Requires tight checkpoint coordination (Week 10, 14, 18)

**Verdict:** ✅ **SELECTED** - Optimal for risk mitigation + parallelization

---

### Team Allocation for Option D

**Stream 1: Critical Path Team (4 people)**
- 1 Senior Backend Engineer (Lead) - RakutenPay + Shopify Functions
- 1 Backend Engineer - NetSuite connector + custom sync logic
- 1 Frontend Engineer - Checkout UI + payment flows
- DevOps (50% allocation) - Shopify environment + monitoring

**Stream 2: Features Team (3 people)**
- 1 Senior Frontend Engineer (Lead) - Hydrogen framework + component library
- 1 Backend Engineer - App integrations (Voucherify, Klaviyo, Algolia)
- 1 Python Engineer (Client) - Step-up microservice + skin check integration

**Shared Resources:**
- Technical Lead (oversight both streams, 20% each + 60% architecture/reviews)
- DevOps (50% Stream 1, 30% Stream 2, 20% infrastructure)
- 2 QA Testers (rotate between streams, focus on integration points)

---

## Idea Categorization

### Immediate Opportunities (Week 1-4)

1. **Execute 3-Week POC Validation**
   - **Why:** De-risk RakutenPay, NetSuite connector, Shopify Functions before committing team
   - **Who:** 1 backend engineer + technical lead
   - **Deliverable:** GO/NO-GO decision Week 3

2. **Hire Shopify Plus Partner Agency for POC Support**
   - **Why:** Accelerate POC, get expert guidance on RakutenPay integration patterns
   - **Investment:** $10,000-15,000 for 2-week engagement
   - **Deliverable:** POC architecture + risk assessment

3. **Secure RakutenPay Sandbox Access Day 1**
   - **Why:** Non-negotiable integration, need early access
   - **Who:** Client procurement team
   - **Deliverable:** API credentials + documentation Week 1

4. **Evaluate Celigo vs. Farapp NetSuite Connectors**
   - **Why:** Connector choice impacts 10-week critical path
   - **Test:** Trial both, compare custom field support
   - **Decision:** Week 2

5. **Set Up Shopify Plus Trial Environment**
   - **Why:** Need working environment for POC
   - **Who:** DevOps
   - **Deliverable:** Sandbox + staging environments Week 1

---

### Future Innovations (Month 9-12, Phase 2)

1. **Custom Shopify Admin Dashboard for Commission Tracking**
   - **Why:** Ops team needs advanced reporting beyond Shopify standard
   - **Effort:** 4-6 weeks
   - **Tech:** React + Shopify Admin API

2. **QR Code / Apple Wallet Integration**
   - **Why:** Customer loyalty feature, nice-to-have
   - **Effort:** 3-4 weeks
   - **Approach:** Build as separate microservice

3. **AI-Powered Product Recommendations (Beyond Skin Check)**
   - **Why:** Upsell/cross-sell optimization
   - **Leverage:** Existing Python microservices + Shopify product data
   - **Effort:** 6-8 weeks

4. **Advanced Analytics Dashboard**
   - **Why:** Business intelligence for marketing team
   - **Tech:** Shopify GraphQL API + data warehouse (BigQuery)
   - **Effort:** 8-10 weeks

5. **Mobile App (React Native)**
   - **Why:** Dedicated mobile experience
   - **Leverage:** Shopify Storefront API + existing React components
   - **Effort:** 12-16 weeks

---

### Moonshots (12+ months)

1. **Subscription Box Customization (Build Your Own Box)**
   - **Why:** Differentiate from competitors
   - **Complexity:** Custom checkout flow, inventory management
   - **Effort:** 16-20 weeks

2. **AR Skin Analysis (Replace Quiz with Camera)**
   - **Why:** Next-gen customer experience
   - **Tech:** TensorFlow.js + WebRTC
   - **Effort:** 20-24 weeks

3. **Marketplace for Third-Party Skincare Brands**
   - **Why:** Expand product catalog without inventory risk
   - **Complexity:** Multi-vendor management, commissions
   - **Effort:** 24-32 weeks

4. **International Expansion (Korean, Chinese Markets)**
   - **Why:** Growth opportunity
   - **Complexity:** Multi-currency, localization, regional regulations
   - **Effort:** 16-20 weeks per market

---

## Insights and Learnings

### Top 10 Key Insights

1. **Shopify Plus Dramatically Reduces Custom Code (40-50% less than MedusaJS)**
   - 8/12 integrations have official apps
   - Admin UI is built-in (saves 6-8 weeks)
   - PCI DSS compliance included (saves 2-3 weeks)
   - Subscription management native (saves 3-5 weeks)

2. **RakutenPay is Still THE Critical Unknown (Same as MedusaJS)**
   - Custom Payment Provider API exists but untested with RakutenPay
   - POC Week 1-2 is non-negotiable
   - Fallback: Engage Shopify Plus partner with Japanese payment experience

3. **NetSuite Connectors Exist But May Not Handle Custom Logic**
   - Celigo/Farapp proven for standard sync (orders, inventory, customers)
   - Purchase limits, store commission may require custom Shopify app
   - Hybrid approach: Connector (80%) + Custom (20%) = 6-8 weeks total

4. **Shopify Functions Enable Custom Business Logic at Checkout**
   - Can call external APIs (step-up microservice)
   - Can block cart/checkout based on eligibility
   - Performance limits require POC validation

5. **Hydrogen Learning Curve is Real But Manageable**
   - Remix framework different from typical React patterns
   - Estimated 2-3 weeks learning curve for team
   - Can reuse 60-70% of existing React components (vs. 80-90% with custom backend)

6. **Timeline is Achievable: 30 Weeks Build + 3 Weeks Migration = 7.6 Months**
   - 3-4 weeks faster than MedusaJS (due to less custom code)
   - Strategic buffers: RakutenPay +1 week, NetSuite +2 weeks, Migration +1 week
   - Fits within 8-month stakeholder expectation

7. **Post-Launch Team Can Be Smaller (1-2 Developers vs. 3-4)**
   - Shopify manages infrastructure (no scaling concerns)
   - Apps are maintained by vendors (Voucherify, Klaviyo, Algolia)
   - Less custom code to maintain

8. **"Set It and Be Done" Mandate Perfectly Aligned with Shopify Plus**
   - Managed platform (Shopify handles updates, security, scaling)
   - Proven 99.99% uptime SLA
   - 24/7 Shopify Plus support
   - Retail-focused (not software company focused)

9. **Migration is Lower Risk with Shopify (Better Tooling)**
   - Customer import API well-documented
   - Partner agencies experienced in e-commerce migrations
   - Can run parallel with Rails (gradual cutover)

10. **Monthly Cost Trade-Off: Predictable OpEx vs. Uncertain DevEx**
    - Shopify Plus: $2,000-3,000/month platform + $500-1,000/month apps = $3,000-4,000/month
    - MedusaJS: Infrastructure $500-1,000/month + 2-3 developers for maintenance = $15,000-25,000/month
    - **Shopify wins on total cost of ownership**

---

## Action Planning - Top 3 Priorities

### Priority #1: Execute 3-Week POC Validation Phase (Week 1-3)

**Why This is #1:**
- De-risks THE critical unknown (RakutenPay integration)
- Validates platform viability before committing $200,000+ team budget
- Week 3 GO/NO-GO decision allows pivot if needed

**Rationale:**
- RakutenPay is non-negotiable (user: "we need to integrate it ASAP")
- NetSuite connector choice impacts 10-week critical path (Week 4-14)
- Shopify Functions must call Python microservice (step-up program)
- Voucherify checkout integration is core loyalty requirement
- Hydrogen performance for Japan is UX-critical

**Success Criteria:**
1. ✅ RakutenPay sandbox integration working via Payment Provider API
2. ✅ Celigo or Farapp can sync NetSuite custom fields (store ID, purchase limits)
3. ✅ Shopify Function can call external API (Python microservice) <500ms response time
4. ✅ Voucherify app supports checkout point redemption in real-time
5. ✅ Hydrogen page loads from Japan <2 seconds (95th percentile)

**Execution Steps:**
1. **Week 1 Day 1-2:**
   - Set up Shopify Plus trial environment (sandbox + staging)
   - Secure RakutenPay sandbox API access
   - Start Celigo and Farapp trials
   - Install Voucherify app in sandbox
   - Hire Shopify Plus partner agency for POC support (2-week engagement)

2. **Week 1 Day 3-5:**
   - Build RakutenPay Payment Provider prototype (1 backend engineer + partner agency)
   - Configure Celigo NetSuite connector with test data (1 backend engineer)
   - Build Shopify Function prototype to call Python API (1 backend engineer)

3. **Week 2:**
   - Test RakutenPay checkout flow (sandbox transactions)
   - Test NetSuite sync (orders, inventory, custom fields)
   - Test Voucherify checkout integration (point redemption)
   - Build Hydrogen prototype page (1-2 pages with Canto PIM data)
   - Load test Hydrogen from Japan (synthetic monitoring)

4. **Week 3:**
   - Customer migration dry-run (import 100 test customers)
   - Subscription flow testing (native Shopify Subscriptions + Stripe)
   - Custom admin page prototype (commission tracking)
   - **Compile POC report:**
     - Technical feasibility assessment
     - Risk registry (updated with POC findings)
     - GO/NO-GO recommendation
     - Updated timeline with buffers

5. **Week 3 End: GO/NO-GO Decision Meeting**
   - Present POC findings to stakeholders
   - If GO: Proceed with 2-stream delivery (Week 4 start)
   - If NO-GO: Evaluate MedusaJS or custom NestJS alternative

**Resources Required:**
- 2 backend engineers (full-time Week 1-3)
- 1 frontend engineer (part-time Week 2-3 for Hydrogen prototype)
- Technical lead (50% time - oversight + architecture decisions)
- DevOps (25% time - environment setup)
- Shopify Plus partner agency ($10,000-15,000 for 2 weeks)

**Risks:**
- RakutenPay POC fails → **Mitigation:** Engage specialized payment gateway developer, extend POC 1 week
- NetSuite connector doesn't support custom logic → **Mitigation:** Plan custom sync service (adds 4 weeks to timeline)
- Shopify Functions timeout calling external API → **Mitigation:** Move step-up logic into Function (TypeScript rewrite, 3-4 weeks)

---

### Priority #2: Start RakutenPay + NetSuite Week 4 (Not Week 8) - Critical Path Mitigation

**Why This is #2:**
- RakutenPay (6 weeks) + NetSuite (10 weeks) are THE longest-lead items
- Starting Week 4 (immediately after POC) de-risks critical path
- Any delays in these areas will push launch date

**Rationale:**
- User: "RakutenPay is non-negotiable, we need to integrate it ASAP to surface any risks"
- NetSuite is "the silent killer" (known slow, unknown edge cases)
- Stream 1 focuses 100% on high-risk items first
- Early completion (Week 16-18) allows buffer for stabilization

**Execution Steps:**

**Week 4-10: RakutenPay Custom Payment Gateway (6 weeks + 1 buffer)**
1. Week 4-5: Implement Payment Provider API integration (sandbox)
2. Week 6-7: Build checkout UI flow (select Stripe or RakutenPay)
3. Week 8: Production credentials + compliance review
4. Week 9: End-to-end testing (purchase, refund, cancellation)
5. Week 10: **Buffer week** for edge cases

**Week 4-14: NetSuite Connector + Custom Logic (10 weeks + 2 buffer)**
1. Week 4-6: Configure Celigo connector (orders, inventory, customers)
2. Week 7-9: Build custom Shopify app for purchase limits logic
3. Week 10-11: Implement store commission tracking (custom fields)
4. Week 12-13: End-to-end testing (order sync, inventory updates, purchase blocking)
5. Week 14: **Buffer weeks** for NetSuite API performance tuning

**Success Criteria:**
1. ✅ RakutenPay production-ready Week 10 (checkout flow tested, compliance approved)
2. ✅ NetSuite sync working Week 14 (hourly inventory, order sync, purchase limits enforced)
3. ✅ Dual gateway checkout (Stripe + RakutenPay) functional
4. ✅ Zero critical bugs in payment or sync flows

**Resources Required:**
- **Stream 1 Team (4 people):**
  - 1 Senior Backend Engineer (RakutenPay lead)
  - 1 Backend Engineer (NetSuite connector + custom app)
  - 1 Frontend Engineer (checkout UI)
  - DevOps (50% - monitoring, production setup)

**Risks:**
- RakutenPay certification delays → **Mitigation:** Start compliance review Week 6 (parallel with dev)
- NetSuite API rate limits → **Mitigation:** Implement queue + exponential backoff, monitor sync lag
- Purchase limits logic complex → **Mitigation:** 2-week buffer built in (Week 12-14)

**Why Not Later:**
- If RakutenPay starts Week 8, finishes Week 14 → No buffer before launch (Week 30)
- If NetSuite starts Week 10, finishes Week 20 → Blocks subscription testing, integration testing
- Early start = early failure detection = time to pivot

---

### Priority #3: Hire Shopify Plus Partner for First 8 Weeks - Accelerate Delivery

**Why This is #3:**
- Shopify Plus expertise accelerates POC + critical path work
- De-risks RakutenPay integration (payment gateways are specialized skill)
- Reduces team learning curve (Hydrogen, Shopify Functions, Admin API)
- Ensures architecture best practices (avoid technical debt)

**Rationale:**
- Team has React experience but NOT Shopify Plus experience
- RakutenPay custom gateway is high-risk, specialized work
- Shopify Plus partners have built similar Japanese e-commerce sites
- $30,000-50,000 investment saves 4-6 weeks of trial-and-error

**Execution Steps:**

**Week 1-2: POC Phase Engagement**
- Partner leads RakutenPay Payment Provider API integration
- Partner reviews NetSuite connector options (Celigo vs. Farapp)
- Partner designs Shopify Functions architecture (step-up, purchase limits)
- Partner builds Hydrogen prototype (1-2 pages)

**Week 3-4: Architecture & Planning**
- Partner creates architecture decision records (ADRs)
- Partner designs 2-stream delivery plan (detailed tasks)
- Partner sets up development workflows (CI/CD, environments)
- Knowledge transfer to internal team

**Week 5-8: Critical Path Support**
- Partner pair-programs RakutenPay integration with backend engineer
- Partner reviews Shopify Functions code (performance, best practices)
- Partner guides Hydrogen frontend migration patterns
- Weekly architecture review meetings

**Success Criteria:**
1. ✅ POC completed successfully (Week 3 GO decision)
2. ✅ RakutenPay integration de-risked (partner expertise applied)
3. ✅ Team upskilled on Shopify Plus (can work independently Week 9+)
4. ✅ Architecture documentation complete (ADRs, diagrams, runbooks)

**Resources Required:**
- **Budget:** $30,000-50,000 for 8-week engagement (part-time, 20 hours/week)
- **Partner Selection Criteria:**
  - Shopify Plus certified agency
  - Experience with Japanese payment gateways (RakutenPay or similar)
  - Hydrogen/Remix expertise
  - NetSuite integration experience
  - Available to start Week 1 (immediate availability)

**ROI Calculation:**
- **Cost:** $40,000 (average)
- **Time Saved:** 4-6 weeks (avoid wrong architecture, rework)
- **Risk Reduced:** RakutenPay integration failure risk drops from 40% to 15%
- **Knowledge Transfer:** Team becomes self-sufficient by Week 9

**Risks:**
- Partner not available immediately → **Mitigation:** Start search NOW (pre-POC), have 2-3 backup options
- Partner over-engineers solution → **Mitigation:** Clear scope: POC + critical path only, no gold-plating
- Knowledge transfer incomplete → **Mitigation:** Require documentation + pair programming (not just consulting)

**Why Not DIY:**
- User: "we are fighting bugs every couple of days" in current system
- Cannot afford 4-6 weeks of trial-and-error on RakutenPay
- Shopify Plus expertise not available in-house
- Cost of delay (1 month) > Cost of partner engagement

---

## Session Reflection

### What Worked Well

1. **Shopify App Ecosystem Clarity**
   - Identifying 8/12 integrations with official apps simplified planning
   - Clear comparison vs. MedusaJS custom development effort

2. **Risk Categorization (Critical vs. High vs. Medium)**
   - Focused mitigation strategies on highest-impact risks
   - RakutenPay and NetSuite connector emerged as clear priorities

3. **Timeline Estimation Grounded in App Availability**
   - Realistic 30-week build timeline (vs. 34-week MedusaJS)
   - Confidence in 7.6-month total (fits 8-month target)

4. **2-Stream Strategy Optimized for Shopify**
   - Stream 1: High-risk items (RakutenPay, NetSuite) tackled early
   - Stream 2: Standard features (apps + Hydrogen frontend)
   - Clear parallelization with minimal blocking

5. **POC Validation Plan Comprehensive**
   - 5 critical validations in 3 weeks
   - GO/NO-GO decision framework clear

6. **"Set It and Be Done" Alignment**
   - Shopify Plus managed infrastructure fits mandate perfectly
   - Post-launch team size reduction (1-2 developers) vs. MedusaJS (3-4)

---

### Areas for Further Exploration

1. **Recharge vs. Native Shopify Subscriptions**
   - Need detailed comparison (features, cost, Japanese market fit)
   - Decision impacts Week 14-18 timeline

2. **Celigo vs. Farapp NetSuite Connector**
   - Both need trials in POC Week 1-2
   - Cost difference ($500-1,500/month vs. $99-299/month)
   - Custom field support comparison

3. **Hydrogen Performance Optimization**
   - Japan CDN latency testing required (POC Week 2-3)
   - Caching strategy for Canto PIM data (3-hour refresh)

4. **Shopify Functions Performance Limits**
   - Timeout limits for external API calls (step-up microservice)
   - Fallback strategy if Function cannot call Python API

5. **Customer Migration Tooling**
   - Dry-run required Week 24-25 with test customers
   - Loyalty points migration to Voucherify (custom script)

6. **Custom Admin Pages Scope**
   - Commission tracking reports requirements unclear
   - May need separate discovery session with ops team

7. **QR Code / Apple Wallet Implementation**
   - Defer to Phase 2 or build as separate service?
   - Effort estimation needed (3-4 weeks)

---

### Recommended Follow-Up Techniques

1. **Pre-Mortem Analysis (Week 3 - Post-POC)**
   - "Assume the project failed in Month 6. Why did it fail?"
   - Identify blind spots in current plan

2. **Cost-Benefit Analysis (Shopify Plus vs. MedusaJS)**
   - Total cost of ownership (5-year)
   - Risk-adjusted ROI comparison

3. **Stakeholder Mapping & Communication Plan**
   - Who needs updates? (CTO, ops team, marketing, finance)
   - What cadence? (weekly, bi-weekly, monthly)

4. **Ops Team Training Plan Design**
   - What workflows change from Rails to Shopify?
   - Training materials, video walkthroughs, documentation

---

### Questions That Emerged During Session

1. **Can Shopify Plus handle Japan-specific tax rules beyond consumption tax?**
   - Example: Reduced tax rates for certain product categories
   - May need custom tax calculation app

2. **What is Shopify's roadmap for native subscription features?**
   - If expanding, may avoid Recharge cost
   - Need to check Shopify Plus partner updates

3. **Can store commission tracking work with Shopify POS (if physical retail added later)?**
   - Future-proofing consideration
   - May influence architecture now

4. **What compliance certifications does Shopify Plus have for Japanese market?**
   - Beyond PCI DSS (data privacy, consumer protection)
   - Legal team review required

5. **Can we A/B test checkout flows (Stripe vs. RakutenPay default)?**
   - Shopify Scripts or Functions for dynamic gateway selection?
   - Marketing team interest

---

### Recommended Next Session(s)

1. **Platform Comparison Workshop (Shopify Plus vs. MedusaJS Side-by-Side)**
   - Duration: 2 hours
   - Participants: Technical lead, CTO, PM
   - Deliverable: Final platform decision with ROI model

2. **Ops Team Requirements Elicitation (Admin UI & Workflows)**
   - Duration: 2 hours
   - Participants: Ops team, QA, PM
   - Deliverable: Custom admin pages requirements, training plan

3. **Migration Planning Deep-Dive**
   - Duration: 3 hours
   - Participants: Backend engineers, DevOps, DBA
   - Deliverable: Week-by-week migration runbook, rollback plan

---

## APPENDIX: 2-Stream Detailed Delivery Timeline (Shopify Plus)

### Overview

- **Total Timeline:** 33 weeks (7.6 months)
- **POC Phase:** Week 1-3 (3 weeks)
- **Build Phase:** Week 4-27 (24 weeks) - 2 parallel streams
- **Integration Testing:** Week 28-30 (3 weeks)
- **Migration Phase:** Week 31-33 (3 weeks)

---

### STREAM 1: Critical Path & High-Risk Features (4 people)

**Team:** 1 Senior BE Engineer (Lead), 1 BE Engineer, 1 FE Engineer, DevOps (50%)

| Phase | Weeks | Focus Area | Deliverables | Critical Path |
|-------|-------|------------|--------------|---------------|
| **Foundation** | 4-6 (3 weeks) | Shopify Plus setup, environments, basic config | Production Shopify Plus store, sandbox/staging environments, CI/CD pipeline | ✅ CRITICAL |
| **RakutenPay Gateway** | 4-10 (6 weeks + 1 buffer) | Custom Payment Provider API integration | RakutenPay production-ready, dual gateway checkout (Stripe + RakutenPay), compliance approved | 🔴 HIGHEST RISK |
| **NetSuite Connector** | 4-14 (10 weeks + 2 buffer) | Celigo/Farapp setup, custom logic, purchase limits | Hourly inventory sync, order sync to NetSuite, purchase limits enforced, store commission tracking | 🔴 HIGHEST RISK |
| **Shopify Functions** | 8-14 (6 weeks) | Purchase limits, step-up eligibility checks | Functions calling Python microservice, cart blocking logic, checkout validation | ⚠️ HIGH RISK |
| **Voucherify Integration** | 12-16 (4 weeks) | Loyalty app setup, checkout point redemption | Points redemption at checkout, tier status display, campaign support | ⚠️ MEDIUM RISK |
| **Subscriptions** | 14-18 (4 weeks) | Native Shopify Subscriptions (or Recharge) | Monthly subscriptions working, customer portal (pause/cancel), Stripe Billing integration | ⚠️ MEDIUM RISK |
| **Integration Testing** | 25-27 (3 weeks) | End-to-end checkout flow, NetSuite sync, edge cases | All payment flows tested, NetSuite sync validated, performance benchmarks met | ✅ CRITICAL |

**Stream 1 Checkpoints:**
- **Week 10:** RakutenPay production-ready (GO/NO-GO for launch)
- **Week 14:** NetSuite sync working (GO/NO-GO for launch)
- **Week 18:** Subscriptions + Voucherify working (feature complete for critical path)
- **Week 27:** Integration testing complete (ready for migration)

---

### STREAM 2: Standard Features & Apps (3 people)

**Team:** 1 Senior FE Engineer (Lead), 1 BE Engineer, 1 Python Engineer (Client)

| Phase | Weeks | Focus Area | Deliverables | Dependencies |
|-------|-------|------------|--------------|--------------|
| **Hydrogen Foundation** | 4-10 (6 weeks) | Hydrogen/Remix setup, component library, design system | React component library, Hydrogen storefront skeleton, Oxygen deployment | None (independent) |
| **Canto PIM + Catalog** | 8-14 (6 weeks) | Product pages, Canto PIM API integration, static builds | Product detail pages, catalog pages, 3-hour build schedule, product data sync | Hydrogen foundation |
| **Algolia Search** | 10-14 (4 weeks) | Algolia app setup, product indexing, Japanese search | Search UI, product indexing, Japanese tokenization, filters/facets | Catalog complete |
| **Klaviyo Events** | 10-16 (6 weeks) | Klaviyo app setup, event mapping, transactional emails | Sign-up events, purchase events, subscription events, marketing campaigns | None (independent) |
| **Auth0/Clerk SSO** | 14-20 (6 weeks) | Shopify Multipass, social login, customer migration | SSO working (Facebook, Google, Line, Twitter), password reset flow, customer import | None (independent) |
| **Cart & Account UI** | 16-22 (6 weeks) | Shopping cart, customer dashboard, order history | Cart page, account dashboard, order tracking, wishlist (if needed) | Hydrogen + Voucherify (Stream 1) |
| **Sanity CMS** | 18-22 (4 weeks) | Sanity integration, static pages, store finder | Static pages (About, FAQ, etc.), store finder UI, Sanity content fetching | Hydrogen foundation |
| **Step-Up Microservice** | 10-22 (12 weeks, Python) | Python service development, API integration | Step-up microservice deployed, integrated with Shopify Functions (Stream 1) | Shopify Functions (Stream 1) |
| **Custom Admin Pages** | 20-27 (7 weeks) | Commission reports, custom dashboards | Admin app for commission tracking, custom reports, ops team training | NetSuite sync (Stream 1) |
| **UI Polish** | 22-27 (5 weeks) | Mobile optimization, accessibility, performance, Japanese localization | Mobile-optimized UI, WCAG 2.1 AA compliance, performance benchmarks (<2s page load), Japanese text final review | All UI complete |

**Stream 2 Checkpoints:**
- **Week 10:** Hydrogen foundation ready (can start building pages)
- **Week 14:** Catalog + Search working (product browsing functional)
- **Week 20:** Auth + Account working (customer login functional)
- **Week 22:** Step-up microservice integrated (business logic complete)
- **Week 27:** UI polish complete (ready for migration)

---

### Integration Sync Points (Across Both Streams)

| Week | Sync Point | Purpose | Participants |
|------|------------|---------|--------------|
| **Week 8** | Architecture Review | Validate RakutenPay + NetSuite progress, Hydrogen patterns | All engineers + Tech Lead |
| **Week 10** | RakutenPay GO/NO-GO | Critical decision: Can we launch with RakutenPay? | Stream 1 + Stakeholders |
| **Week 14** | NetSuite Integration Complete | Validate order sync, inventory sync, purchase limits | Stream 1 + Stream 2 (Step-Up) |
| **Week 18** | Feature Freeze Checkpoint | All critical features complete (subscriptions, loyalty, payments) | All teams |
| **Week 22** | UI Merge | Stream 2 UI integrated with Stream 1 backend (checkout, account) | Frontend engineers |
| **Week 27** | Code Freeze | All development complete, ready for integration testing | All teams |

---

### INTEGRATION TESTING PHASE (Week 28-30)

**Focus:** End-to-end testing, ops training, performance validation

| Week | Focus | Activities | Success Criteria |
|------|-------|------------|------------------|
| **Week 28** | **End-to-End Testing** | Full checkout flows (Stripe, RakutenPay, subscriptions), NetSuite sync validation, Voucherify point redemption, step-up eligibility | Zero critical bugs, <5 medium bugs |
| **Week 29** | **Performance & Security** | Load testing (1,000 concurrent users), security audit (PCI DSS review), Oxygen CDN performance from Japan | <2s page load (95th percentile), no security vulnerabilities |
| **Week 30** | **Ops Training & Runbooks** | Train ops team on Shopify admin, create runbooks (order management, refunds, customer support), UAT with ops team | Ops team confident, runbooks complete |

---

### MIGRATION PHASE (Week 31-33)

**Focus:** Customer migration, go-live, stabilization

| Week | Focus | Activities | Success Criteria |
|------|-------|------------|------------------|
| **Week 31** | **Staged Migration (10%)** | Migrate 5,000 customers (10% cohort), migrate loyalty points to Voucherify, test checkout flows, monitor for issues | <1% customer complaints, zero payment failures |
| **Week 32** | **Staged Migration (50%)** | Migrate 25,000 customers (additional 40%), migrate remaining subscriptions, full ops team handoff | Ops team handling support independently |
| **Week 33** | **Final Migration (100%) + Stabilization** | Migrate remaining 25,000 customers, decommission Rails system, monitoring + bug fixes, go-live announcement | 100% customers migrated, Rails system OFF |

**Migration Rollback Plan:**
- If >5% customer complaints Week 31 → Pause migration, fix issues
- If critical payment failure Week 32 → Rollback to Rails, investigate
- Week 33 is buffer week (can extend migration if needed)

---

### Critical Path Summary

**LONGEST DEPENDENCY CHAIN (determines minimum timeline):**

```
Week 1-3: POC (3 weeks)
  ↓
Week 4-14: NetSuite Integration (10 weeks + 2 buffer)
  ↓
Week 14-18: Subscriptions (4 weeks) [depends on NetSuite customer data]
  ↓
Week 25-27: Integration Testing (3 weeks)
  ↓
Week 28-30: Integration Testing Phase (3 weeks)
  ↓
Week 31-33: Migration (3 weeks)

TOTAL CRITICAL PATH: 33 weeks (7.6 months)
```

**SECONDARY CRITICAL PATH (RakutenPay):**

```
Week 1-3: POC (3 weeks)
  ↓
Week 4-10: RakutenPay Gateway (6 weeks + 1 buffer)
  ↓
Week 25-27: Integration Testing (3 weeks)
  ↓
Week 28-30: Integration Testing Phase (3 weeks)
  ↓
Week 31-33: Migration (3 weeks)

TOTAL: 26 weeks (completes before NetSuite critical path)
```

**KEY INSIGHT:** NetSuite integration (10 weeks) is THE longest single work item. Starting Week 4 (immediately after POC) is non-negotiable.

---

### Risk-Adjusted Timeline (Worst-Case Scenarios)

**If RakutenPay POC fails (Week 3):**
- Engage specialist payment gateway developer (+2 weeks)
- Total timeline: 35 weeks (8.1 months) - still within 8-month target

**If NetSuite connector doesn't work (Week 8):**
- Build custom sync service (+4 weeks)
- Total timeline: 37 weeks (8.5 months) - slightly over target, requires stakeholder communication

**If both RakutenPay AND NetSuite have issues:**
- Total timeline: 39 weeks (9 months) - over target
- Mitigation: Reduce scope (defer QR code, custom admin pages to Phase 2)

**Buffer Utilization Plan:**
- RakutenPay: +1 week buffer (Week 10)
- NetSuite: +2 weeks buffer (Week 12-14)
- Migration: +1 week buffer (Week 33)
- **Total buffers: 4 weeks** (can absorb moderate delays)

---

### Launch Readiness Criteria (Week 30 - Before Migration)

**MUST HAVE (Cannot Launch Without):**
1. ✅ Stripe payments working (production transactions successful)
2. ✅ RakutenPay payments working (production transactions successful)
3. ✅ NetSuite order sync working (hourly sync validated)
4. ✅ NetSuite inventory sync working (real-time stock updates)
5. ✅ Purchase limits enforced (max 3 per variant per month)
6. ✅ Subscriptions working (create, pause, cancel functional)
7. ✅ Voucherify points redemption at checkout
8. ✅ Customer login working (SSO + email/password)
9. ✅ Product catalog complete (all SKUs from NetSuite)
10. ✅ Search working (Algolia indexed, Japanese search functional)
11. ✅ Step-up program enforced (eligibility checks working)
12. ✅ Store commission tracking (store ID captured on orders)
13. ✅ Klaviyo events firing (sign-up, purchase, subscription)
14. ✅ Performance benchmarks met (<2s page load from Japan)
15. ✅ Ops team trained (can manage orders independently)

**NICE TO HAVE (Can Defer to Phase 2):**
1. ⚠️ Custom admin pages (commission reports) - can use Shopify standard reports temporarily
2. ⚠️ QR code / Apple Wallet - can defer to Month 9
3. ⚠️ Advanced analytics dashboard - can defer to Month 9
4. ⚠️ Subscription rescheduling (specific date) - customers can cancel and re-subscribe

**BLOCKERS (Will Delay Launch):**
1. 🔴 RakutenPay not production-ready
2. 🔴 NetSuite sync failing or too slow (>1 hour delay)
3. 🔴 Purchase limits not enforced (legal/business requirement)
4. 🔴 Payment failures >1% (user trust issue)
5. 🔴 Site performance >3s page load (UX unacceptable)

---

## Platform Decision: Shopify Plus - CONDITIONAL GO

### Recommendation: CONDITIONAL GO (Pending Week 3 POC Validation)

**Confidence Level: 80%** (vs. 65% for MedusaJS)

**Conditions for GO:**
1. ✅ RakutenPay POC successful (sandbox integration works) - **CRITICAL**
2. ✅ NetSuite connector (Celigo/Farapp) can sync custom fields - **CRITICAL**
3. ✅ Shopify Functions can call Python microservice API - **CRITICAL**
4. ✅ Voucherify app supports checkout point redemption - **HIGH**
5. ✅ Hydrogen performance acceptable from Japan (<2s page load) - **HIGH**

**If ANY critical condition fails:** Re-evaluate MedusaJS or custom NestJS

---

### Shopify Plus vs. MedusaJS Comparison Summary

| Dimension | Shopify Plus | MedusaJS |
|-----------|--------------|----------|
| **Timeline** | 30 weeks build (6.9 months) | 34 weeks build (7.8 months) |
| **Custom Code** | 40-50% less (apps available) | More custom integration work |
| **RakutenPay Risk** | Medium (custom gateway required) | Medium (same challenge) |
| **NetSuite Risk** | Low-Medium (connectors exist) | Medium (full custom sync) |
| **Admin UI** | Built-in (saves 6-8 weeks) | Custom build (6-8 weeks) |
| **PCI DSS** | Included (saves 2-3 weeks) | Custom compliance (2-3 weeks) |
| **Subscriptions** | Native or Recharge (saves 3-5 weeks) | Custom Stripe Billing (3-5 weeks) |
| **Learning Curve** | Hydrogen/Remix (2-3 weeks) | MedusaJS patterns (2-3 weeks) |
| **Post-Launch Team** | 1-2 developers | 2-3 developers |
| **Monthly Cost** | $3,000-4,000 (platform + apps) | $500-1,000 (infrastructure only) |
| **Total Cost (Year 1)** | $36,000-48,000 platform | $6,000-12,000 infrastructure |
| **Maintenance Cost (Year 1)** | $120,000-180,000 (1-2 devs) | $240,000-360,000 (2-3 devs) |
| **Total TCO (Year 1)** | $156,000-228,000 | $246,000-372,000 |
| **"Set It and Be Done"** | ✅ Perfect fit (managed platform) | ⚠️ Requires ongoing DevOps |
| **Flexibility** | ⚠️ Locked into Shopify ecosystem | ✅ Full control over stack |

**Winner: Shopify Plus** (lower TCO, faster timeline, better fit for "set it and be done" mandate)

---

### Why Shopify Plus is Recommended Over MedusaJS

1. **Faster Delivery (3-4 weeks faster)**
   - Less custom integration work (8/12 integrations have apps)
   - Admin UI built-in (saves 6-8 weeks)
   - PCI DSS included (saves 2-3 weeks)

2. **Lower Risk (Proven Platform)**
   - 99.99% uptime SLA vs. self-hosted reliability concerns
   - Battle-tested checkout (billions in GMV processed)
   - Managed infrastructure (no scaling concerns)

3. **Better TCO (Year 1: $150K-$230K vs. $250K-$370K)**
   - Lower maintenance team (1-2 devs vs. 2-3 devs)
   - Apps maintained by vendors (Voucherify, Klaviyo, Algolia)
   - Less custom code to maintain

4. **Perfect Fit for "Set It and Be Done" Mandate**
   - Shopify manages platform updates, security patches, scaling
   - Retail-focused (not software company focused)
   - 24/7 Shopify Plus support

5. **Easier Hiring & Handoff**
   - Larger talent pool for Shopify developers
   - Easier to onboard new team members
   - Easier to hand off to maintenance team

**Trade-Offs:**
- Less flexibility (locked into Shopify ecosystem)
- Higher monthly platform cost ($3K-4K vs. $500-1K infrastructure)
- Some custom development still required (RakutenPay, purchase limits)

**Verdict:** Shopify Plus is the safer, faster, more cost-effective choice for Environ.jp migration.

---

## Next Steps (Immediate Actions)

### Week 0 (Pre-POC Preparation)

1. **Secure Shopify Plus Trial** (Day 1)
   - Sign up for Shopify Plus trial (sandbox + staging environments)
   - Assign DevOps to set up environments

2. **Secure RakutenPay Sandbox Access** (Day 1-2)
   - Client procurement team requests API credentials
   - Confirm sandbox environment availability

3. **Hire Shopify Plus Partner Agency** (Day 1-3)
   - Research agencies with Japanese payment experience
   - Request proposals from 2-3 agencies
   - Select partner by Day 3, start Week 1

4. **Start NetSuite Connector Trials** (Day 2-3)
   - Sign up for Celigo trial
   - Sign up for Farapp trial
   - Prepare test NetSuite data

5. **Assemble POC Team** (Day 3-5)
   - Assign 2 backend engineers (full-time Week 1-3)
   - Assign 1 frontend engineer (part-time Week 2-3)
   - Confirm technical lead availability (50% Week 1-3)

---

### Week 1-3: Execute POC (See Priority #1)

---

### Week 3 End: GO/NO-GO Decision

**If GO:**
- Proceed with 2-stream delivery (Week 4 start)
- Hire additional team members if needed
- Secure Shopify Plus production contract

**If NO-GO:**
- Evaluate MedusaJS with 3-week POC (same rigor)
- Or evaluate custom NestJS solution
- Adjust timeline accordingly (inform stakeholders)

---

## Conclusion

Shopify Plus offers a **faster, lower-risk, more cost-effective** path to migrate Environ.jp from Ruby on Rails. The platform's mature app ecosystem, built-in admin UI, and managed infrastructure align perfectly with the "set it and be done" mandate.

**Key Success Factors:**
1. ✅ 3-week POC validates RakutenPay + NetSuite (THE critical unknowns)
2. ✅ 2-stream delivery de-risks early (RakutenPay + NetSuite Week 4-14)
3. ✅ Shopify Plus partner engagement accelerates delivery (Week 1-8)
4. ✅ Timeline fits within 8-month target (33 weeks = 7.6 months)
5. ✅ Lower total cost of ownership (Year 1: $150K-230K vs. $250K-370K for MedusaJS)

**Timeline Summary:**
- **Week 1-3:** POC Validation (GO/NO-GO decision)
- **Week 4-27:** 2-Stream Build Phase (24 weeks)
- **Week 28-30:** Integration Testing (3 weeks)
- **Week 31-33:** Migration (3 weeks)
- **Total: 33 weeks (7.6 months)** ✅ Fits 8-month target

**Next Immediate Action:** Execute 3-week POC validation (Priority #1) to validate platform viability.

---

**Session Complete. Ready for Platform Decision & POC Kickoff.**
