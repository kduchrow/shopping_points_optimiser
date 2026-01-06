# Miles & More Scraper - Visual Workflow Guide

## Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MILES & MORE SCRAPER WORKFLOW                        │
└─────────────────────────────────────────────────────────────────────────┘

PHASE 1: SCRAPING (Admin Action)
═════════════════════════════════════════════════════════════════════════

    Admin Dashboard
         ↓
    Click Button: "▶ Run Miles & More Scraper"
         ↓
    MilesAndMoreScraper.scrape()
         ├─ Visit: miles-and-more.com/partners
         ├─ Scroll: Load all 500+ partners
         ├─ For each partner:
         │  ├─ Extract name & detail URL
         │  ├─ Visit detail page
         │  ├─ Parse points rate (e.g., 1.5 points/€)
         │  ├─ Create/Update Shop record
         │  ├─ Create/Update ShopProgramRate
         │  └─ On error/uncertainty → Create Proposal
         └─ Log results: +150 shops, ±50 updated, 8 uncertain

    Database Updates:
    ├─ shops table (NEW: 150 entries)
    ├─ shop_program_rates (NEW: 200 entries, OLD marked valid_to)
    └─ proposals (NEW: 8 entries, source='scraper')

    Admin Dashboard Shows:
    ├─ "Miles & More scraper finished"
    ├─ "Added 150 shops, updated 50, 8 errors"
    └─ Links to error details


PHASE 2: USER REVIEW (Community Action)
═════════════════════════════════════════════════════════════════════════

    User navigates to Results Page
         ↓
    System detects pending scraper proposals
         ↓
    POPUP ALERT:
    ┌────────────────────────────────────────┐
    │  🤖 Scraper-Vorschlag                  │
    │  ────────────────────────────────────  │
    │  Shop: Hotel Partner XYZ                │
    │  Reason: Could not auto-extract rate   │
    │  Source: [Link to partner page]        │
    │                                        │
    │  [✏️ Review Proposal] [✕ Close]       │
    └────────────────────────────────────────┘
         ↓
    User clicks "✏️ Review Proposal"
         ↓
    Form Opens with Pre-filled Data:
    ┌────────────────────────────────────────┐
    │  Scraper-Vorschlag reviewen            │
    │  ────────────────────────────────────  │
    │                                        │
    │  Shop: Hotel Partner XYZ [🤖 Scraper] │
    │  Program: MilesAndMore                 │
    │  Original Reason: Could not extract    │
    │                                        │
    │  ┌─ Edit Form                        ┐ │
    │  │                                    │ │
    │  │ Punkte pro EUR: [1.5]             │ │
    │  │ Cashback %:     [0]               │ │
    │  │ Ihre Notiz:     [optional text]   │ │
    │  │                                    │ │
    │  │ [✓ Bestätigen] [⬅ Zurück]       │ │
    │  └─────────────────────────────────┘ │
    │                                        │
    └────────────────────────────────────────┘
         ↓
    User reviews & edits data
         ↓
    User clicks "✓ Confirm & Submit"
         ↓
    System creates NEW User Proposal
    ├─ source='user' (✓ Important!)
    ├─ user_id=current_user.id
    ├─ Includes edited data
    ├─ Includes user notes
    └─ Status='pending'
         ↓
    System marks Original Scraper Proposal
    └─ status='approved' ✓


PHASE 3: COMMUNITY VOTING (Social Action)
═════════════════════════════════════════════════════════════════════════

    Proposals Page (/proposals)
         ↓
    Shows both proposal types:
    ┌─────────────────────────────────────────┐
    │ User Proposal (from Phase 2)          │ │ ← Only these show here
    │ ───────────────────────────────────── │ │
    │ Shop: Hotel Partner XYZ                │ │
    │ By: Username (Contributor)             │ │
    │ From Scraper Proposal: #42              │ │
    │                                         │ │
    │ [👍 Upvote] [👎 Downvote]             │ │
    │                                         │ │
    │ Votes: +2 / -0 = 2 weighted             │ │
    │ Status: pending                         │ │
    │ [✓ Genehmigen] (Admin only)            │ │
    └─────────────────────────────────────────┘
         ↓
    Community votes on proposal
    ├─ Regular user vote = 1x weight
    ├─ Admin vote = 3x weight
    └─ Auto-approval at 3+ weighted votes
         ↓
    Proposal Status Updates
    ├─ pending → approved (auto at 3+ votes)
    ├─ approved → applied to database
    └─ Shows in Results page


PHASE 4: FINAL STATE
═════════════════════════════════════════════════════════════════════════

    Database Final State:
    ├─ Shop created: ✓
    ├─ Rate stored: ✓
    ├─ Scraper Proposal: approved (phase 1)
    └─ User Proposal: approved (phase 3)

    Visibility:
    ├─ Scraper proposal: 🤖 Hidden after approval
    ├─ User proposal: ✓ In results with all data
    └─ Shop rate: ✓ Used in calculations


═══════════════════════════════════════════════════════════════════════════
DETAILED FLOW: WHAT CAN GO WRONG?
═══════════════════════════════════════════════════════════════════════════

SCENARIO 1: Perfect Scrape
────────────────────────────
✓ Data extracted successfully
✓ All fields populated
✓ Proposal auto-approved
✓ No user action needed
⚡ Result appears in calculations immediately


SCENARIO 2: Uncertain Data (⚠️ Common)
─────────────────────────────────────
⚠️ Scraper can't find points rate
⚠️ Creates Proposal with source='scraper'
⚠️ Sets proposed_points_per_eur=NULL
⏳ Waits for user review
👤 User opens review form
✏️ User enters correct rate (e.g., 1.5)
✓ User submits → New proposal created
⏳ Community votes
✓ When approved → Rate applied


SCENARIO 3: Network Error (❌ Rare)
────────────────────────────────────
❌ Website down or timeout
❌ Scraper catches exception
❌ Creates error Proposal
❌ Logs error message
⏳ Admin checks logs
⚠️ Decides: retry or manual data?
📝 Creates proposal manually or reruns


SCENARIO 4: Page Structure Changed (❌ Rare)
──────────────────────────────────────────────
❌ Website updated HTML structure
❌ Regex patterns don't match
❌ Fallback patterns don't work
❌ Creates "needs review" proposal
⏳ Waits for user/admin action
📝 Admin updates scraper code
🔄 Reruns scraper with new patterns


═══════════════════════════════════════════════════════════════════════════
BADGE SYSTEM & VISUAL INDICATORS
═══════════════════════════════════════════════════════════════════════════

In Proposals List:
┌──────────────────────────────────────┐
│ 🤖 Scraper Proposal                  │ ← Special styling
│    By: _scraper_system                │
│    Source: miles-and-more.com         │
│    Status: approved                   │
│    [Under review - don't vote]        │
└──────────────────────────────────────┘

│                                       │

┌──────────────────────────────────────┐
│ 👤 User Proposal                      │ ← Normal styling
│    By: john_doe                       │
│    From Scraper: #42 ✓                │ ← Shows it was reviewed
│    Status: pending                    │
│    [👍+2] [👎-0] → Vote!            │
└──────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════
SUCCESS CRITERIA CHECKLIST
═══════════════════════════════════════════════════════════════════════════

Scraper Phase:
  [✓] Connects to miles-and-more.com
  [✓] Loads 500+ partners
  [✓] Extracts shop names
  [✓] Parses points rates
  [✓] Creates Shop records
  [✓] Creates ShopProgramRate records
  [✓] Creates Proposals for uncertain data
  [✓] Logs all activity

User Review Phase:
  [✓] Modal shows pending proposals
  [✓] Form pre-fills scraped data
  [✓] User can edit all fields
  [✓] Validation works
  [✓] Submit creates User Proposal
  [✓] Original marked approved

Community Phase:
  [✓] Proposals appear in list
  [✓] Users can vote
  [✓] Admin can approve directly
  [✓] 3+ votes triggers auto-approval
  [✓] Approved proposals applied to database

Result:
  [✓] Shop data available in system
  [✓] Rates used in calculations
  [✓] Community validated data
  [✓] Full audit trail maintained


═══════════════════════════════════════════════════════════════════════════
QUICK START FOR USERS
═══════════════════════════════════════════════════════════════════════════

AS ADMIN:
  1. Go to /admin
  2. Click "Run Miles & More Scraper"
  3. Wait for completion
  4. Check logs for results

AS USER:
  1. Go to /evaluate (select shop)
  2. If popup appears: Click "Review Proposal"
  3. Edit fields as needed
  4. Click "Confirm & Submit"
  5. Go to /proposals to vote

RESULT:
  ✓ Your data appears in calculations!
  ✓ Community voted on your contribution!
  ✓ Shopping points optimizer improved!


═══════════════════════════════════════════════════════════════════════════
```

## Phase Summary Table

| Phase | Who | Action | Input | Output | Time |
|-------|-----|--------|-------|--------|------|
| 1: Scrape | Admin | Click button | Website | Proposals + DB | 2-5 min |
| 2: Review | User | Edit form | Scraped data | User Proposal | 1-5 min |
| 3: Vote | Community | Upvote/down | User Proposal | Approved/Rejected | Hours-days |
| 4: Apply | System | Auto-apply | Approved proposal | Database update | Instant |

## Data Flow Visualization

```
Internet                                    Database
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Miles-and-More Website                      shops
  └─ [Partner Data]                         shop_program_rates
       ↓                                    proposals (scraped)
  MilesAndMoreScraper                       ↓
       ↓                                    User Review
  [Partial/Error/Success]                   (edit form)
       ↓                                    ↓
  Proposals Created                         proposals (user)
  (source='scraper')                        ↓
       ↓                                    Community Voting
  User Opens Modal                          ↓
       ↓                                    Approved Proposals
  Review Form (pre-filled)                  ↓
       ↓                                    Applied to Database
  User Submits                              ↓
       ↓                                    ✓ Complete
  New Proposal Created
  (source='user')
```

## Time Estimate

```
Total Time to Get Results in System
═══════════════════════════════════════════════

Scraping Time:           2-5 minutes
  ├─ Load page           30 sec
  ├─ Scroll partners     1 min
  ├─ Scrape details      2-4 min
  └─ Database write      30 sec

User Review Time:        1-5 minutes (or skip if auto-approved)
  ├─ Open proposal       30 sec
  ├─ Review data         1-2 min
  ├─ Edit if needed      1-3 min
  └─ Submit              30 sec

Community Voting:        Hours to days (depends on users)
  └─ Accumulate votes    varies

───────────────────────────────────────────
Total for Full Approval: 3-15 minutes*

*Shorter if data is good, longer if edits needed
*Community voting adds hours/days for approval
```
