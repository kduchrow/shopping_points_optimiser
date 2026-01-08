# Platform Research & Integration Feasibility Analysis

**Last Updated:** January 2026
**Market Focus:** German/European Cashback & Loyalty Platforms

---

## Executive Summary

Analyzed 12 major platforms across 3 categories (Cashback, Coupons/Deals, Loyalty Programs).

**Key Findings:**
- ✅ **4 platforms RECOMMENDED** for implementation (high ROI, low friction)
- ⚠️ **3 platforms MEDIUM EFFORT** (feasible but complex)
- ❌ **5 platforms NOT RECOMMENDED** (ToS restrictions, anti-scraping, poor data access)
- 📊 **3 already partially implemented** (Payback, Shoop, Miles & More)

---

## 🟢 TIER 1: RECOMMENDED FOR IMPLEMENTATION (Easy → Medium)

### 1. **TopCashback.de** — ⭐⭐ (EASIEST)

| Property | Value |
|----------|-------|
| **Category** | Cashback Platform (German) |
| **Shops** | ~1,200+ partner merchants |
| **API Available** | ❌ No public API |
| **Data Access** | 🟢 Static HTML + Minimal JS |
| **Data Source** | Shop directory + rate pages |
| **Implementation Difficulty** | ⭐⭐ (2/5 stars) |
| **Authentication Required** | ❌ No (partner list public) |
| **robots.txt** | ✅ Allows scraping `/partner/` paths |
| **ToS** | ✅ No explicit scraping prohibition |
| **Affiliate Program** | ✅ Yes - TopCashback Affiliate Network |
| **Current Status** | 🔴 Not implemented |
| **Estimated Effort** | **1-2 days** |

**Feasibility Details:**
- Clean, structured HTML on partner directory
- Minimal JavaScript rendering needed
- Straightforward rate extraction patterns
- Large active user base in Germany
- Good metadata (shop category, description, rate history)

**Implementation Path:**
1. Create `scrapers/topcashback_scraper.py` extending `BaseScraper`
2. Fetch partner list from `https://www.topcashback.de/partner/`
3. Extract shop names, URLs, cashback %
4. Register to DB via `get_or_create_shop_main()`
5. Schedule daily/weekly updates via APScheduler

**Recommendation:** 🟢 **START HERE** — Quickest ROI, proven marketplace

---

### 2. **Shoop.de** — ⭐⭐⭐ (COMPLETE EXISTING)

| Property | Value |
|----------|-------|
| **Category** | Cashback Platform (German) |
| **Shops** | ~2,200+ partner merchants |
| **API Available** | ❌ No public API |
| **Data Access** | 🟡 HTML + JavaScript rendering |
| **Data Source** | Dynamic shop directory |
| **Implementation Difficulty** | ⭐⭐⭐ (3/5 stars) |
| **Authentication Required** | ❌ No (partner list public) |
| **robots.txt** | ✅ Allows crawling `/shops/` |
| **ToS** | ✅ No explicit scraping block |
| **Affiliate Program** | ✅ Yes - Shoop Affiliate Programme |
| **Current Status** | 🟡 Partial (bonus_programs/shoop.py exists, no scraper) |
| **Estimated Effort** | **2-3 days** |

**Feasibility Details:**
- Partner list rendered via JavaScript (React/Vue likely)
- Requires Playwright for full shop data
- More shops than TopCashback
- Dynamic rate updates
- Categories and filtering available

**Implementation Path:**
1. Create `scrapers/shoop_scraper.py` extending `BaseScraper`
2. Use Playwright to load `https://www.shoop.de/shops/`
3. Scroll/paginate to load all shops
4. Extract shop name, URL, cashback % + bonus info
5. Handle dynamic content (wait for DOM elements)
6. Register via existing `bonus_programs/shoop.py` integration

**Recommendation:** 🟢 **PRIORITY #2** — Already partially integrated, largest shop coverage

---

### 3. **Payback.de** (Improve Existing) — ⭐⭐⭐

| Property | Value |
|----------|-------|
| **Category** | Points Program (German) |
| **Shops** | ~700+ partners |
| **API Available** | ❌ No public API; B2B partnership available |
| **Data Access** | 🟢 HTML + JavaScript pages |
| **Data Source** | Shop directory + rate pages |
| **Implementation Difficulty** | ⭐⭐⭐ (3/5 stars) |
| **Authentication Required** | ❌ No |
| **robots.txt** | ✅ Allows `/shopping/` crawling |
| **ToS** | ⚠️ Standard ToS; no explicit block |
| **Affiliate Program** | ✅ Yes - B2B PAYBACK.GROUP partnership |
| **Current Status** | 🟢 Implemented (payback_scraper.py + payback_scraper_js.py) |
| **Estimated Effort** | **1-2 days** (optimization only) |

**Feasibility Details:**
- Two scrapers already exist (HTTP + Playwright versions)
- Point rate extraction patterns established
- Complex point schemes (fixed points, bonus multipliers, tiered rates)
- Large established user base
- **Consider contacting PAYBACK.GROUP for official B2B data feed** — may get CSV/XML

**Implementation Path:**
1. Contact PAYBACK.GROUP for B2B partnership + data feed
2. Or: Optimize existing `payback_scraper_js.py` for better coverage
3. Improve rate pattern matching (handle edge cases)
4. Add bonus/multiplier tracking

**Recommendation:** 🟡 **ENHANCE EXISTING** — Already working; focus on official partnership

---

### 4. **Miles & More** (Maintain Existing) — ⭐⭐⭐

| Property | Value |
|----------|-------|
| **Category** | Airline Miles/Points Program (Lufthansa) |
| **Shops** | ~150+ partners |
| **API Available** | ❌ No public API |
| **Data Access** | 🟡 Heavy JavaScript (complex SPA) |
| **Data Source** | Dynamic partner directory |
| **Implementation Difficulty** | ⭐⭐⭐⭐ (4/5 stars) |
| **Authentication Required** | ❌ No |
| **robots.txt** | ✅ Partner list crawlable |
| **ToS** | ✅ No explicit prohibition |
| **Affiliate Program** | ❌ B2B only (Lufthansa Group) |
| **Current Status** | 🟢 Implemented (miles_and_more_scraper.py) |
| **Estimated Effort** | **Maintenance only** |

**Feasibility Details:**
- Complex JavaScript app with anti-bot protections
- Smaller shop base than cashback platforms
- Specialized audience (Lufthansa members)
- Already working well in production

**Recommendation:** 🟢 **MAINTAIN** — Works well, lower priority for expansion

---

## 🟡 TIER 2: MEDIUM EFFORT (Feasible but Complex)

### 5. **iGraal.de** — ⭐⭐⭐⭐

| Property | Value |
|----------|-------|
| **Category** | Cashback Platform (French/German) |
| **Shops** | ~1,500+ partners |
| **API Available** | ❌ No public API |
| **Data Access** | 🔴 Heavy JavaScript (modern SPA) |
| **Implementation Difficulty** | ⭐⭐⭐⭐ (4/5 stars) |
| **Authentication Required** | ❌ No |
| **robots.txt** | ✅ Allows crawling |
| **ToS** | ✅ No explicit scraping block |
| **Affiliate Program** | ✅ Yes - iGraal Affiliate Programme |
| **Current Status** | 🔴 Not implemented |
| **Estimated Effort** | **3-4 days** |

**Feasibility Details:**
- Modern JavaScript framework (likely Vue/React)
- Requires Playwright with scrolling + dynamic loading
- Strong alternative to TopCashback in German market
- Good shop coverage + user ratings

**Implementation Path:**
1. Create `scrapers/igraal_scraper.py`
2. Use Playwright to load `https://www.igraal.de/shops`
3. Implement infinite scroll handling
4. Extract rates + bonus offers
5. Register via `get_or_create_shop_main()`

**Recommendation:** 🟡 **SECONDARY PRIORITY** — Good coverage, more complex than TopCashback

---

### 6. **Kaufda.de** — ⭐⭐⭐⭐

| Property | Value |
|----------|-------|
| **Category** | Weekly Circular/Prospekt Aggregator |
| **Shops** | ~1,000+ retailers (grocery, electronics, pharma) |
| **API Available** | ❌ No public API |
| **Data Access** | 🟡 HTML + Modern JS |
| **Implementation Difficulty** | ⭐⭐⭐⭐ (4/5 stars) |
| **Authentication Required** | ❌ No |
| **robots.txt** | ⚠️ Restricts aggressive crawling |
| **ToS** | ⚠️ Standard ToS; unclear on scraping |
| **Affiliate Program** | ❌ No (owned by Blackstone/Groupe Casino) |
| **Current Status** | 🔴 Not implemented |
| **Estimated Effort** | **2-3 days** |

**Feasibility Details:**
- Mobile-first platform (responsive design)
- Good for grocery/supermarket integration
- Weekly prospekt updates (historical pricing data)
- Location-based data (store addresses, opening hours)
- Contact for bulk data access recommended

**Recommendation:** 🟡 **SECONDARY PRIORITY** — Good for supermarket/location data; consider partnership

---

### 7. **Marktguru.de** — ⭐⭐⭐⭐⭐

| Property | Value |
|----------|-------|
| **Category** | Coupon/Deal Aggregator (Grocery + Stores) |
| **Shops** | ~500+ retailers + brands |
| **API Available** | ❌ No public API |
| **Data Access** | 🔴 Heavy JavaScript SPA |
| **Implementation Difficulty** | ⭐⭐⭐⭐⭐ (5/5 stars) |
| **Authentication Required** | ❌ No (but may trigger bot detection) |
| **robots.txt** | ⚠️ Restrictive crawling policies |
| **ToS** | ❌ **Explicit scraping prohibition** |
| **Affiliate Program** | ❌ No |
| **Current Status** | 🔴 Not implemented |
| **Estimated Effort** | **NOT RECOMMENDED** |

**Feasibility Details:**
- Heavy bot protection (Cloudflare/similar)
- Terms of Service explicitly forbid scraping
- Dynamically loaded coupon data
- User-curated content model (less reliable)

**Recommendation:** ❌ **NOT RECOMMENDED** — ToS violation risk, strong bot detection

---

### 8. **Amazon Prime** — ⭐⭐⭐⭐⭐

| Property | Value |
|----------|-------|
| **Category** | E-commerce Loyalty Program |
| **Shops** | N/A (Amazon marketplace partners) |
| **API Available** | ✅ **Yes — Product Advertising API + SP-API** |
| **Data Access** | 🟢 Official REST API |
| **Implementation Difficulty** | ⭐⭐⭐⭐ (4/5 stars - API complexity) |
| **Authentication Required** | ✅ Yes (AWS IAM + API keys) |
| **robots.txt** | ✅ Amazon-friendly crawling allowed |
| **ToS** | ✅ API usage permitted under agreement |
| **Affiliate Program** | ✅ Yes - Amazon Associates |
| **Current Status** | 🔴 Not implemented |
| **Estimated Effort** | **4-5 days** (API integration) |

**Feasibility Details:**
- Official REST APIs available (Product Advertising API, SP-API)
- Requires AWS account + credential setup
- Good for product discounts + Prime deals
- **Note:** Prime membership points cannot be scraped (account-specific, behind login)
- Good for integration with product/deal recommendations

**Recommendation:** 🟡 **SECONDARY** — Has APIs, but loyalty points not scrape-able; useful for deal integration

---

## 🔴 TIER 3: NOT RECOMMENDED

### ❌ **MyDeals.de** (aka MyDealz)

**Issue:** User-generated content platform (crowdsourced deals)
- ❌ No official data feed or API
- ❌ Heavy JavaScript with infinite scroll
- ❌ Strong bot detection (Cloudflare)
- ❌ ToS explicitly forbids scraping
- **Recommendation:** Skip — not suitable for reliable cashback/loyalty data

---

### ❌ **DealDoktor.de**

**Issue:** Community deal voting platform
- ❌ No API or structured data export
- ❌ User-curated content (unreliable for product data)
- ❌ Strong bot protection
- ❌ ToS restricts automated access
- **Recommendation:** Skip — better as user community source

---

### ❌ **Saturn.de / MediaMarkt.de**

**Issue:** Large electronics retailers with anti-scraping measures
- ❌ No public APIs
- ❌ Heavy JavaScript rendering + dynamic pricing
- ❌ Strong anti-scraping protections (WAF)
- ❌ Loyalty program locked behind login (points account-specific)
- ❌ ToS explicitly forbids scraping
- **Recommendation:** Contact for official B2B partnership instead

---

### ❌ **DM.de / Rossmann.de**

**Issue:** Pharmacy/drug store chains with strong IP restrictions
- ❌ No public APIs
- ❌ Loyalty points (dm-drogerie Markt card) = login-only account data
- ❌ Aggressive bot detection
- ❌ ToS prohibits scraping
- ❌ Complex regional pricing structures
- **Recommendation:** Not feasible via scraping; official partnerships needed

---

### ❌ **Uber Eats / Restaurant Loyalty**

**Issue:** Account-specific loyalty points + complex API
- ❌ Loyalty points tied to user accounts (can't scrape aggregate data)
- ❌ Complex marketplace with vendor-specific programs
- ❌ Requires authentication
- **Recommendation:** Skip for now; consider in later phase if restaurant integration desired

---

## 📊 Quick Comparison Table

| Platform | Difficulty | Shops | Feasibility | Status | Priority |
|----------|-----------|-------|------------|--------|----------|
| **TopCashback** | ⭐⭐ | 1,200+ | 🟢 Easy | ❌ Not implemented | 🎯 START HERE |
| **Shoop** | ⭐⭐⭐ | 2,200+ | 🟢 Medium | 🟡 Partial | 🎯 #2 |
| **Payback** | ⭐⭐⭐ | 700+ | 🟢 Medium | ✅ Implemented | 🔧 Enhance |
| **Miles & More** | ⭐⭐⭐⭐ | 150+ | 🟡 Complex | ✅ Implemented | 🔧 Maintain |
| **iGraal** | ⭐⭐⭐⭐ | 1,500+ | 🟡 Medium | ❌ Not implemented | 📌 Secondary |
| **Kaufda** | ⭐⭐⭐⭐ | 1,000+ | 🟡 Medium | ❌ Not implemented | 📌 Secondary |
| **Marktguru** | ⭐⭐⭐⭐⭐ | 500+ | ❌ Hard (ToS) | ❌ Not implemented | ❌ SKIP |
| **Amazon** | ⭐⭐⭐⭐ | N/A | 🟡 API | ❌ Not implemented | 📌 Secondary |
| **MyDeals** | ⭐⭐⭐⭐⭐ | N/A | ❌ Hard (ToS) | ❌ Not implemented | ❌ SKIP |
| **DealDoktor** | ⭐⭐⭐⭐⭐ | N/A | ❌ Hard (ToS) | ❌ Not implemented | ❌ SKIP |
| **Saturn/MM** | ⭐⭐⭐⭐⭐ | N/A | ❌ Hard (ToS) | ❌ Not implemented | ❌ SKIP |
| **DM/Rossmann** | ⭐⭐⭐⭐⭐ | N/A | ❌ Hard (ToS) | ❌ Not implemented | ❌ SKIP |

---

## 🎯 Recommended Implementation Roadmap

### **Phase 1: Quick Wins (Weeks 1-2)**
1. ✅ **TopCashback scraper** (1-2 days) — Easiest, quick ROI
2. ✅ **Complete Shoop scraper** (2-3 days) — Largest shop base
3. ✅ **Payback optimization** (1-2 days) — Improve existing

**Expected Result:** 4,000+ shops, 3 active cashback platforms

### **Phase 2: Secondary Platforms (Weeks 3-4)**
4. 📌 **iGraal scraper** (3-4 days) — Alternative cashback platform
5. 📌 **Kaufda integration** (2-3 days) — Supermarket/prospekt data

**Expected Result:** 6,500+ shops, regional pricing/prospekt history

### **Phase 3: Future (Months 2-3)**
6. 🔄 **Amazon API integration** (4-5 days) — Product deal recommendations
7. 🔄 **Coupon feature layer** — Building on Phase 1-2 data
8. 🔄 **Official partnerships** — Contact PAYBACK, Shoop, TopCashback for B2B feeds

---

## 💡 Key Recommendations

### **1. Prioritize Official Partnerships**
- Contact **PAYBACK.GROUP**, **TopCashback**, **Shoop** for B2B CSV/XML data feeds
- Often faster, more reliable, and legally safer than scraping
- May provide historical data + future rate updates

### **2. Use Browser Automation for JS-Heavy Sites**
- Playwright (already in your Docker setup) for sites like Shoop, iGraal
- Implement proper delays + user-agent rotation
- Respect robots.txt crawl-delay directives

### **3. Avoid ToS Violations**
- **Skip:** MyDeals, DealDoktor, Marktguru, Saturn, DM, Rossmann (explicit scraping blocks)
- **Proceed carefully:** Amazon (use official APIs only)
- **Safe to scrape:** TopCashback, Shoop, Payback, iGraal (permissive or unclear ToS)

### **4. Data Quality Over Coverage**
- 4,000 shops with accurate rates > 10,000 shops with unreliable data
- Focus on Tier-1 platforms (TopCashback, Shoop, Payback) first
- Validate rate data regularly (daily/weekly updates)

### **5. User Privacy**
- Scrape shop/rate data only (public information)
- Never scrape user accounts, transactions, or loyalty balances
- All loyalty points are account-specific (can't aggregate across users)

---

## 📞 Next Steps

1. **Approve Phase 1 priorities** (TopCashback, Shoop, Payback)
2. **Decide:** Build scrapers or pursue B2B partnerships first?
3. **Start with TopCashback** (lowest technical risk, quick implementation)
4. **Validate shop coverage** — ensure 100+ shops from each platform in first week

---

**Questions?** Let me know which platform to start with!
