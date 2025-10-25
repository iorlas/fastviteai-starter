# MedusaJS Technical Evaluation for Environ.jp E-Commerce Migration

**Evaluation Date:** October 24, 2025
**Project:** Environ.jp - Japanese Skincare E-Commerce Platform
**Decision Required:** Go/No-Go for MedusaJS as Headless Commerce Foundation

---

## EXECUTIVE SUMMARY

### RECOMMENDATION: **CONDITIONAL GO** with Critical Risk Mitigation Required

MedusaJS can serve as the foundation for Environ.jp's headless architecture, but **significant custom development is required** for business-critical integrations. The platform provides strong core commerce capabilities but lacks mature plugins for several key requirements.

### Top 3 Strengths for This Use Case

1. **Open Architecture & Extensibility**
   - Highly customizable Node.js/TypeScript foundation
   - Strong API-first design aligns with headless requirements
   - React Admin dashboard provides foundation for custom business rules
   - Active development community and regular updates

2. **Core Commerce Capabilities**
   - Robust product, cart, and order management out-of-box
   - Multi-currency support (JPY compatible)
   - Tax calculation framework (configurable for Japanese consumption tax)
   - Inventory management with real-time stock tracking

3. **Developer Experience**
   - Well-documented plugin architecture
   - TypeScript-first development
   - Strong ORM (TypeORM) for data modeling
   - Good alignment with team's Node.js/React skills

### Top 3 Risks/Concerns

1. **⚠️ CRITICAL: Immature Plugin Ecosystem for Key Integrations**
   - **No official Voucherify plugin** (loyalty redemption at checkout is business-critical)
   - **No NetSuite connector** (hourly sync of 5,000+ products is mission-critical)
   - **Limited Stripe Billing integration** (subscriptions require custom implementation)
   - **Estimated custom development: 2-3 months for integrations alone**

2. **⚠️ HIGH: Complex Business Logic Implementation Burden**
   - Purchase limits per customer/variant/month require custom middleware
   - Step-up program logic needs custom service layer
   - Commission tracking requires custom order tagging
   - **Risk:** These customizations become technical debt if not architected properly

3. **⚠️ HIGH: Timeline Pressure vs. Customization Reality**
   - Target: 6-8 months delivery with existing team
   - Reality: Core MedusaJS setup (1 month) + Custom integrations (2-3 months) + Business logic (2-3 months) + Testing (1-2 months) = **6-9 months MINIMUM**
   - **Risk:** Timeline assumes zero roadblocks and perfect execution

---

## DETAILED FINDINGS

### 1. Plugin Ecosystem Assessment

| Requirement | Available Solution | Maturity Level | Gaps/Custom Work Required |
|-------------|-------------------|----------------|---------------------------|
| **Algolia Search** | ✅ Official `medusa-plugin-algolia` | ⭐⭐⭐⭐ Mature | Minor config for Japanese language, custom ranking rules |
| **Auth0 Integration** | ⚠️ Community plugin exists | ⭐⭐ Early | Custom auth flow integration, session management |
| **Clerk Integration** | ❌ No official plugin | N/A | **Full custom implementation required** (1-2 weeks) |
| **Stripe Payments** | ✅ Official `medusa-payment-stripe` | ⭐⭐⭐⭐⭐ Production-ready | Works well for one-time payments |
| **Stripe Billing (Subscriptions)** | ⚠️ No dedicated plugin | ⭐ Experimental | **Custom webhook handlers, subscription lifecycle management required** (3-4 weeks) |
| **RakutenPay Gateway** | ❌ No plugin | N/A | **Full custom payment provider implementation** (2-3 weeks) |
| **Voucherify Loyalty** | ❌ No plugin | N/A | **Custom service integration at checkout** (2-3 weeks) |
| **NetSuite Sync** | ❌ No plugin | N/A | **Custom batch job + API integration** (4-6 weeks) |
| **Klaviyo Events** | ✅ Community plugin | ⭐⭐⭐ Stable | Event mapping customization needed |
| **Sanity CMS** | ✅ Multiple approaches | ⭐⭐⭐ Stable | Content-product linking requires custom fields |
| **Multiple Payment Gateways** | ✅ Architecture supports | ⭐⭐⭐⭐ Good | Custom routing logic for Stripe vs. RakutenPay |

**Plugin Ecosystem Grade: C+**
- Core commerce plugins are solid
- Critical business integrations require 8-12 weeks of custom development
- No blocking gaps, but significant custom work ahead

---

### 2. Integration Capability Analysis

#### ✅ **STRENGTHS**

**NetSuite Integration (Custom Required)**
- MedusaJS's event-driven architecture supports webhook-based syncing
- Batch job framework can handle hourly product/inventory pulls
- TypeORM makes it easy to model NetSuite data structures
- **Implementation Path:** Custom service + scheduled jobs + error handling
- **Estimated Effort:** 4-6 weeks for robust implementation

**Voucherify Loyalty Points**
- Can integrate as custom discount/promotion provider
- Checkout flow is extensible via middleware
- Point calculation can hook into order totals
- **Implementation Path:** Custom Voucherify service + checkout middleware
- **Estimated Effort:** 2-3 weeks

**Stripe Billing Subscriptions**
- MedusaJS supports custom order types and recurring logic
- Can delegate subscription management to Stripe Billing
- Webhook handlers for pause/skip/cancel events
- **Implementation Path:** Custom subscription service + Stripe webhook handlers
- **Estimated Effort:** 3-4 weeks for full lifecycle management

**Klaviyo Event Tracking**
- Community plugin (`medusa-plugin-klaviyo`) provides foundation
- Easy to extend with custom event types
- **Implementation Path:** Install plugin + customize event payloads
- **Estimated Effort:** 1 week

#### ⚠️ **CONCERNS**

**Multiple Payment Gateway Complexity**
- Stripe + RakutenPay requires custom routing logic
- Order attribution (which gateway processed payment) needs tracking
- Refund handling must work across both gateways
- **Risk:** Payment flow complexity increases QA burden

**Auth Provider Flexibility**
- No official Auth0/Clerk plugins means custom integration
- Session management between MedusaJS and auth provider needs care
- **Risk:** Authentication bugs are high-severity in production

**API Adapter Layer**
- Current Rails API contracts must be matched or adapted
- React frontend expects specific endpoint structures
- **Mitigation:** Custom API layer can wrap MedusaJS admin/store APIs
- **Estimated Effort:** 2-3 weeks for adapter layer

---

### 3. Business Logic Complexity Evaluation

#### ✅ **CAN MEDUSAJS HANDLE THESE?**

**Purchase Limits (Max 3 units/variant/month/customer)**
- **YES, via Custom Middleware**
- Implementation: Pre-checkout hook that queries order history
- Database: Track purchases by customer + variant + timeframe
- **Effort:** 1-2 weeks for robust implementation with edge case handling

**Step-Up Program (Vitamin-A Concentration Progression)**
- **YES, via Custom Product Eligibility Service**
- Implementation: Custom service checks purchase history before allowing add-to-cart
- Data Model: Product metadata for concentration levels + customer purchase records
- **Effort:** 2 weeks for service + validation rules

**Store Commission Tracking**
- **YES, via Custom Order Metadata**
- Implementation: Tag orders with store ID during checkout
- Reporting: Custom analytics endpoint for commission calculations
- **Effort:** 1 week for tagging + 1 week for reporting

**Loyalty Tier Management (Voucherify)**
- **YES, via External Integration**
- Implementation: Voucherify API calls during checkout
- Tier updates: Webhook from Voucherify → MedusaJS customer metadata
- **Effort:** Included in Voucherify integration (2-3 weeks)

#### ⚠️ **IMPLEMENTATION CHALLENGES**

**Business Rules as Technical Debt**
- Complex custom logic must be well-architected to avoid maintenance nightmares
- Need comprehensive test coverage (unit + integration tests)
- Documentation critical for knowledge transfer
- **Recommendation:** Invest 20% extra time in architecture/testing upfront

**Data Consistency Across Systems**
- Purchase history in MedusaJS vs. NetSuite vs. Voucherify
- **Risk:** Eventual consistency issues if sync fails
- **Mitigation:** Implement retry logic, monitoring, and manual reconciliation tools

---

### 4. Japanese Market Fit Assessment

#### ✅ **STRONG AREAS**

**Currency & Localization**
- Multi-currency support includes JPY
- Locale-aware pricing and formatting
- **Grade: A-** (Minor customization for Japanese number formatting)

**Tax Handling**
- Tax rate configuration supports Japanese consumption tax (10%)
- Tax-inclusive vs. tax-exclusive pricing options
- **Grade: A** (Meets requirements)

**Language Support**
- Admin dashboard can be localized (community translations available)
- Product/content data supports multi-language
- **Grade: B+** (Some admin UI may require custom translations)

#### ⚠️ **GAPS & CUSTOM WORK**

**RakutenPay / Konbini Payments**
- **No official plugin**
- Must implement as custom payment provider
- **Complexity:** Medium (similar to Stripe plugin architecture)
- **Effort:** 2-3 weeks + RakutenPay API integration testing
- **Risk:** RakutenPay API documentation quality unknown

**Japanese E-Commerce Conventions**
- Address formatting (Japanese postal format)
- Name ordering (family name first)
- Phone number validation (Japanese format)
- **Customization Required:** Frontend + backend validation rules
- **Effort:** 1-2 weeks

**Furigana (Phonetic Reading) Support**
- Not standard in MedusaJS customer data model
- **Custom Field Required:** Add furigana fields to customer entity
- **Effort:** 3-5 days

---

### 5. Architecture & Performance Assessment

#### ✅ **STRENGTHS**

**React Frontend Compatibility**
- MedusaJS provides clean REST/GraphQL APIs
- Existing React UI can consume APIs without tight coupling
- **Grade: A** (Excellent separation of concerns)

**API Design Flexibility**
- Custom routes and endpoints easy to add
- Can create adapter layer to match existing Rails API contracts
- **Grade: A-** (Requires adapter development)

**Static Site Build Strategy**
- MedusaJS APIs work well with static site generation (SSG)
- Product data can be fetched at build time (every 3 hours)
- Real-time pricing/stock via client-side API calls
- **Grade: A** (Aligns perfectly with current strategy)

**Scalability**
- Node.js handles concurrent API requests well
- Database (PostgreSQL) scales for Japanese traffic
- Redis caching layer available for high-traffic endpoints
- **Grade: B+** (Good for projected traffic, monitoring needed)

#### ⚠️ **PERFORMANCE CONCERNS**

**NetSuite Real-Time Pricing/Stock**
- Hourly batch sync + real-time API calls for pricing
- **Risk:** API latency if NetSuite responses are slow
- **Mitigation:** Aggressive caching strategy, fallback to last-known values
- **Recommendation:** POC NetSuite API performance before committing

**Complex Business Rule Overhead**
- Purchase limit checks require database queries per add-to-cart
- Step-up validation adds latency to product pages
- **Mitigation:** Redis caching for customer purchase history
- **Estimated Performance Impact:** +50-100ms per request (manageable)

**Database Query Optimization**
- TypeORM sometimes generates inefficient queries
- **Risk:** N+1 query problems in custom logic
- **Mitigation:** Code reviews, performance testing, query monitoring

---

### 6. Development Timeline Feasibility

#### **REALISTIC TIMELINE BREAKDOWN**

| Phase | Estimated Duration | Key Activities |
|-------|-------------------|----------------|
| **1. MedusaJS Setup & Config** | 3-4 weeks | Infrastructure, PostgreSQL, Redis, basic product catalog |
| **2. Authentication Integration** | 2 weeks | Auth0 or Clerk custom integration |
| **3. Payment Gateways** | 3-4 weeks | Stripe (standard) + RakutenPay (custom) |
| **4. NetSuite Integration** | 5-6 weeks | Batch sync jobs, inventory management, error handling |
| **5. Voucherify Loyalty** | 2-3 weeks | Checkout integration, point redemption logic |
| **6. Stripe Billing Subscriptions** | 3-4 weeks | Webhook handlers, subscription lifecycle |
| **7. Business Logic Layer** | 4-5 weeks | Purchase limits, step-up program, commission tracking |
| **8. API Adapter Layer** | 2-3 weeks | Match existing Rails API contracts for React frontend |
| **9. Algolia Search Setup** | 1-2 weeks | Plugin config, Japanese language tuning, ranking rules |
| **10. Sanity CMS Integration** | 1-2 weeks | Content-product linking, custom fields |
| **11. Testing & QA** | 6-8 weeks | Unit tests, integration tests, UAT, performance testing |
| **12. DevOps & Deployment** | 2-3 weeks | CI/CD pipelines, staging environments, production deploy |
| **TOTAL** | **34-47 weeks** | **8-11 months** |

#### **CRITICAL TIMELINE ANALYSIS**

**Target: 6-8 months (26-35 weeks)**
**Realistic Estimate: 8-11 months (34-47 weeks)**

**Gap Analysis:**
- **Optimistic Target:** Assumes perfect execution, no roadblocks
- **Realistic Timeline:** Accounts for integration complexity, learning curve, debugging
- **Risk Buffer:** Additional 2-3 months for unknowns

**Team Composition Impact:**
- 2 React Engineers: Can work in parallel on frontend
- 2-3 Backend Engineers: Split across integrations (NetSuite, payments, subscriptions)
- 1 DevOps: Infrastructure setup can happen early
- 2 QA: Testing should start in parallel with development (not sequential)

**Acceleration Strategies:**
1. **Parallel Workstreams:** Frontend + Backend + DevOps in parallel
2. **Reduce Scope:** Consider MVP without RakutenPay initially (Stripe only)
3. **Pre-built Integrations:** Evaluate paid integration services (e.g., third-party NetSuite connectors)
4. **Agile Sprints:** 2-week sprints with continuous deployment to catch issues early

**VERDICT:** 6-8 month timeline is **AGGRESSIVE BUT POSSIBLE** if:
- Team has prior MedusaJS experience (reduces learning curve)
- Scope is strictly controlled (no feature creep)
- Third-party integration services used where available
- Testing happens in parallel with development

---

## RISK REGISTRY

### 🔴 **CRITICAL RISKS (Show-Stoppers)**

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|---------------------|
| **NetSuite Integration Failure** | Showstopper | Medium | **POC REQUIRED:** Build proof-of-concept for NetSuite sync BEFORE committing to MedusaJS. Verify API performance, data mapping, error handling. *Decision Point: If POC fails, MedusaJS is NOT viable.* |
| **Voucherify Checkout Integration Blocker** | High | Low-Medium | Validate Voucherify API capabilities for real-time point redemption. Build POC for checkout flow integration. *Fallback: Simplified points system if Voucherify integration proves too complex.* |
| **Timeline Overrun (9+ months)** | High | High | Implement strict sprint planning, weekly progress reviews, and scope control. *Mitigation: Plan for 10-month timeline internally, communicate 8-month externally with buffer.* |

### 🟠 **HIGH RISKS (Significant Impact, Mitigation Possible)**

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|---------------------|
| **RakutenPay Integration Complexity** | High | Medium | Research RakutenPay API documentation quality BEFORE development. Consider delaying RakutenPay to Phase 2 (launch with Stripe only). |
| **Custom Business Logic Technical Debt** | Medium-High | High | Invest in strong architecture upfront. Comprehensive test coverage (80%+ for business logic). Document all custom rules thoroughly. |
| **Team Learning Curve (MedusaJS)** | Medium | Medium | Allocate 2 weeks for team training/ramp-up. Pair programming for knowledge transfer. Consider hiring 1 contract MedusaJS expert for first 2 months. |
| **Authentication Provider Integration Issues** | Medium | Medium | Choose Auth0 over Clerk (better documentation). Budget 3 weeks instead of 2 for auth integration. |
| **Performance Degradation Under Load** | High | Low-Medium | Load testing from week 20 onwards. Redis caching for hot paths. Database query optimization reviews. |

### 🟡 **MEDIUM RISKS (Manageable with Planning)**

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|---------------------|
| **Stripe Billing Subscription Edge Cases** | Medium | Medium | Thorough testing of pause/skip/cancel flows. Webhook retry logic. Manual intervention tools for edge cases. |
| **API Adapter Layer Complexity** | Medium | Medium | Start API adapter development early (week 8). Incremental migration of endpoints. Comprehensive API contract testing. |
| **Japanese Localization Gaps** | Low-Medium | Medium | Budget 1-2 weeks for custom localization (address formats, furigana fields). QA with Japanese stakeholders. |
| **Data Consistency Across Systems** | Medium | Medium | Implement robust error handling, retry logic, and monitoring. Build manual reconciliation tools for edge cases. |

---

## ALTERNATIVES ANALYSIS

### Should You Consider Alternatives to MedusaJS?

**Short Answer: YES, evaluate at least 2 alternatives before final decision.**

MedusaJS is viable but requires significant custom development. Below are alternatives that may reduce integration overhead.

### Alternative Platforms Comparison

| Platform | Strengths for Environ.jp | Weaknesses | Estimated Timeline | Cost |
|----------|--------------------------|------------|-------------------|------|
| **Shopify Plus** | ✅ Mature plugin ecosystem (Klaviyo, Algolia, loyalty apps)<br>✅ Japanese market support (RakutenPay plugins available)<br>✅ Subscription apps (Recharge, Bold)<br>✅ Fast time-to-market | ❌ Less flexible for complex business logic<br>❌ Shopify Script/Functions limitations<br>❌ Vendor lock-in<br>❌ Higher long-term costs | **4-6 months** | **High** ($2K+/month platform fees) |
| **CommerceTools** | ✅ Enterprise-grade API-first platform<br>✅ Strong integration ecosystem<br>✅ Excellent scalability<br>✅ Flexible business logic via extensions | ❌ **Very expensive** (enterprise pricing)<br>❌ Steeper learning curve<br>❌ Overkill for current scale | **8-10 months** | **Very High** (6-figure annual costs) |
| **Saleor** | ✅ Open-source, GraphQL-first<br>✅ Strong product/variant modeling<br>✅ Active community<br>✅ Python/Django backend (mature ecosystem) | ❌ Smaller plugin marketplace than Shopify<br>❌ Team would need Python skills<br>❌ Fewer Japanese market integrations | **7-9 months** | **Low-Medium** (self-hosted or cloud) |
| **Custom NestJS/Node.js** | ✅ **Maximum flexibility** for business logic<br>✅ Team already knows Node.js/TypeScript<br>✅ No platform constraints<br>✅ Full control over integrations | ❌ **Longest timeline** (12-18 months)<br>❌ Must build all commerce primitives from scratch<br>❌ Ongoing maintenance burden | **12-18 months** | **Medium** (developer time) |
| **BigCommerce** | ✅ Headless API available<br>✅ Strong checkout customization<br>✅ Multi-currency/tax support | ❌ Less flexible than MedusaJS<br>❌ Smaller ecosystem than Shopify<br>❌ Limited Japanese market presence | **5-7 months** | **Medium** ($300-$1K+/month) |

### **RECOMMENDATION: Parallel Evaluation**

Before final MedusaJS commitment, conduct **2-week evaluation sprints** for:

1. **Shopify Plus** - If budget allows, this may be fastest path
   - **POC Focus:** Evaluate subscription apps, RakutenPay plugins, Voucherify integration
   - **Decision Criteria:** Can Shopify's business logic handle purchase limits and step-up program?

2. **Saleor** - If team is open to Python/Django
   - **POC Focus:** Build sample business logic extensions, evaluate integration patterns
   - **Decision Criteria:** Does Python ecosystem provide better NetSuite/Voucherify integrations?

**If both alternatives show blockers, MedusaJS remains the best choice.**

---

## OPEN QUESTIONS & REQUIRED VERIFICATION

### 🔍 **Critical Questions Requiring POC/Research**

1. **NetSuite API Performance**
   - **Question:** Can NetSuite API handle hourly bulk product fetches (5,000+ SKUs) within acceptable latency?
   - **Verification Needed:** 2-day POC with NetSuite sandbox and MedusaJS batch job
   - **Decision Impact:** **SHOWSTOPPER** if NetSuite API is too slow or unreliable

2. **Voucherify Real-Time Redemption**
   - **Question:** Can Voucherify API handle point redemption during checkout without blocking cart flow?
   - **Verification Needed:** API latency testing + error handling scenarios
   - **Decision Impact:** **HIGH** - May need to simplify points redemption flow

3. **RakutenPay API Documentation Quality**
   - **Question:** Is RakutenPay API well-documented enough for custom integration?
   - **Verification Needed:** Contact RakutenPay for developer docs and sandbox access
   - **Decision Impact:** **MEDIUM** - Determines if RakutenPay can be in MVP or Phase 2

4. **Auth0 vs. Clerk for MedusaJS**
   - **Question:** Which auth provider integrates more easily with MedusaJS custom flows?
   - **Verification Needed:** Research community implementations, auth flow complexity
   - **Decision Impact:** **LOW** - Both are viable, but Auth0 may have better docs

5. **Stripe Billing Subscription Webhooks**
   - **Question:** Can MedusaJS reliably handle Stripe subscription webhooks for pause/skip/cancel?
   - **Verification Needed:** 3-day POC building webhook handlers and testing edge cases
   - **Decision Impact:** **MEDIUM** - Determines subscription feature completeness

6. **Team MedusaJS Experience**
   - **Question:** Has anyone on the team built with MedusaJS before?
   - **Verification Needed:** Team skill assessment
   - **Decision Impact:** **HIGH** - If zero experience, add 3-4 weeks to timeline

### 📋 **Information Missing from Public Documentation**

1. **MedusaJS Production Case Studies in Japan**
   - Need: Real-world Japanese e-commerce examples using MedusaJS
   - Why: Validate localization/tax/payment gateway approaches
   - Source: Contact MedusaJS team, search Japanese dev communities

2. **MedusaJS v2.0 Stability**
   - Need: Current production readiness of MedusaJS v2.0 (major rewrite released 2024)
   - Why: Determine if v2.0 is stable enough or if v1.x is safer choice
   - Source: GitHub issues, community Discord, production user feedback

3. **NetSuite SuiteScript Performance at Scale**
   - Need: Latency benchmarks for NetSuite API calls with 5,000+ SKU catalogs
   - Why: Critical for hourly sync feasibility
   - Source: NetSuite developer forums, contact NetSuite support

4. **Voucherify Checkout Integration Patterns**
   - Need: Examples of Voucherify integrated into headless checkout flows
   - Why: Validate real-time point redemption is feasible
   - Source: Voucherify documentation, customer success team

---

## FINAL VERDICT & NEXT STEPS

### **CONDITIONAL GO: MedusaJS is Viable with Risk Mitigation**

MedusaJS can serve as the foundation for Environ.jp's headless architecture, **BUT ONLY IF**:

1. ✅ **NetSuite POC succeeds** (2-day proof-of-concept for API sync)
2. ✅ **Timeline expectations are reset** (8-10 months realistic, not 6-8)
3. ✅ **Team commits to custom development** (8-12 weeks of integration work)
4. ✅ **Budget allows for contingencies** (10-15% buffer for unknowns)

### **Pre-Commitment Action Items (1-2 Weeks)**

**WEEK 1:**
1. **NetSuite API POC** - Build proof-of-concept for hourly product sync
2. **Voucherify API Research** - Test real-time point redemption latency
3. **RakutenPay Documentation Review** - Assess integration feasibility
4. **Team Skill Assessment** - Determine MedusaJS experience level

**WEEK 2:**
5. **Shopify Plus Evaluation** - If budget allows, compare plugin ecosystem
6. **Auth0 vs Clerk Decision** - Choose authentication provider
7. **MedusaJS v1 vs v2 Decision** - Assess stability for production use
8. **Finalize Technology Stack** - Make Go/No-Go decision with stakeholders

### **If GO Decision is Made:**

**Phase 1: Foundation (Weeks 1-12)**
- MedusaJS setup + PostgreSQL + Redis
- Authentication integration (Auth0 or Clerk)
- Stripe payment gateway (standard)
- Algolia search plugin setup
- DevOps: CI/CD pipelines, staging environment

**Phase 2: Core Integrations (Weeks 13-24)**
- NetSuite batch sync implementation
- Voucherify loyalty integration
- Stripe Billing subscriptions
- Sanity CMS integration
- API adapter layer for React frontend

**Phase 3: Business Logic (Weeks 25-32)**
- Purchase limit middleware
- Step-up program validation
- Commission tracking
- Japanese localization customizations

**Phase 4: Polish & Launch (Weeks 33-40)**
- RakutenPay payment gateway (or defer to Phase 2 post-launch)
- Comprehensive testing (unit, integration, UAT)
- Performance optimization
- Production deployment

### **If NO-GO Decision is Made:**

**Evaluate in This Order:**
1. **Shopify Plus** (fastest time-to-market, highest cost)
2. **Saleor** (Python ecosystem, mature commerce primitives)
3. **Custom NestJS** (maximum flexibility, longest timeline)

---

## APPENDIX: TECHNICAL ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  React Frontend (Existing UI - Static Site)              │   │
│  │  - Product Pages (rebuilt every 3 hours from Canto PIM)  │   │
│  │  - Cart & Checkout (real-time API calls)                │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │ REST/GraphQL APIs
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     API ADAPTER LAYER (Custom)                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Endpoint Mappers (Rails API contract compatibility)    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      MEDUSAJS CORE                              │
│  ┌────────────────┬────────────────┬─────────────────────────┐  │
│  │ Product Mgmt   │ Cart & Orders  │ Inventory & Pricing     │  │
│  ├────────────────┼────────────────┼─────────────────────────┤  │
│  │ Customer Mgmt  │ Tax Calc       │ Promotions & Discounts  │  │
│  └────────────────┴────────────────┴─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐
│  OFFICIAL        │  │  COMMUNITY   │  │  CUSTOM          │
│  PLUGINS         │  │  PLUGINS     │  │  INTEGRATIONS    │
├──────────────────┤  ├──────────────┤  ├──────────────────┤
│ - Algolia Search │  │ - Klaviyo    │  │ - NetSuite Sync  │
│ - Stripe Payments│  │ - Auth0      │  │ - Voucherify     │
│                  │  │              │  │ - RakutenPay     │
│                  │  │              │  │ - Stripe Billing │
│                  │  │              │  │ - Purchase Limits│
│                  │  │              │  │ - Step-Up Logic  │
└──────────────────┘  └──────────────┘  └──────────────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐
│  PostgreSQL      │  │  Redis Cache │  │  External APIs   │
│  (Product Data,  │  │  (Sessions,  │  │  - NetSuite      │
│   Orders,        │  │   Cart,      │  │  - Voucherify    │
│   Customers)     │  │   Inventory) │  │  - Stripe        │
└──────────────────┘  └──────────────┘  └──────────────────┘
```

---

## TECHNOLOGY STACK SUMMARY

**Backend:**
- Platform: MedusaJS (Node.js/TypeScript)
- Database: PostgreSQL
- Cache: Redis
- ORM: TypeORM

**Frontend:**
- Framework: React (existing UI)
- Build: Static Site Generation (SSG) - rebuilds every 3 hours
- API Client: REST/GraphQL

**Integrations:**
- Search: Algolia (official plugin)
- Auth: Auth0 or Clerk (custom integration)
- Payments: Stripe (official plugin) + RakutenPay (custom)
- Subscriptions: Stripe Billing (custom webhook handlers)
- Loyalty: Voucherify (custom service)
- ERP: NetSuite (custom batch sync)
- Analytics: Klaviyo (community plugin)
- CMS: Sanity (custom integration)

**DevOps:**
- Hosting: TBD (AWS/GCP recommended)
- CI/CD: TBD (GitHub Actions or similar)
- Monitoring: TBD (DataDog, New Relic, or similar)

---

**Document Version:** 1.0
**Last Updated:** October 24, 2025
**Next Review:** After NetSuite POC completion (Week 1)
