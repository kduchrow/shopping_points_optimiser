# Miles & More Scraper - Technical Reference

## Class: MilesAndMoreScraper

Main scraper class for collecting Miles & More partner data.

### Initialization
```python
scraper = MilesAndMoreScraper()
```

**Attributes:**
- `base_url` (str): "https://www.miles-and-more.com/de/de/program/partners.html"
- `program_name` (str): "MilesAndMore" (matches database)
- `system_user` (User): Auto-created system user for scraper proposals

### Methods

#### `get_or_create_system_user()`
```python
user = scraper.get_or_create_system_user()
```
Returns or creates a special system user `_scraper_system` used for all scraper-generated proposals.

**Returns:**
- `User`: SQLAlchemy User object with role='contributor'

**Note:** User cannot login (password_hash='locked')

#### `scrape()`
```python
added, updated, errors = scraper.scrape()
```

Main scraping function. Automates:
1. Page loading with Playwright
2. Dynamic scrolling to load all partners
3. Partner link extraction
4. Detail page parsing for rates
5. Database updates
6. Error recovery proposal creation

**Returns:**
```python
(
    shops_added: int,     # Number of new shops created
    shops_updated: int,   # Number of existing shops with rate updates
    errors: list[str]     # Error messages encountered
)
```

**Database Operations:**
- Creates/updates Shop records
- Creates/updates ShopProgramRate records
- Creates Proposal records for uncertain data
- Logs all activity

**Error Handling:**
- Network errors → Logged + Proposal created
- Missing data → Marked for review + Proposal created
- Page structure changes → Graceful fallback
- All errors collected and returned

### Private Methods

#### `_extract_points_rate(html)`
```python
points_per_eur = scraper._extract_points_rate(html)
```

Extracts points rate from partner detail page HTML using regex patterns.

**Parameters:**
- `html` (str): HTML content of partner page

**Returns:**
- `float`: Points per EUR (e.g., 1.5)
- `None`: If extraction fails (proposal created for review)

**Regex Patterns:**
1. "X Meilen pro Y EUR" format
2. "X Points per EUR" format
3. "X per Y€" format
4. Fallback patterns for variations

#### `_create_scraper_proposal(user, shop, program, reason, source_url)`
```python
proposal_id = scraper._create_scraper_proposal(
    user=system_user,
    shop=shop_object,
    program=program_object,
    reason="Could not extract rate",
    source_url="https://..."
)
```

Creates a pending Proposal for uncertain/error cases.

**Parameters:**
- `user` (User): User who created proposal (usually system user)
- `shop` (Shop): Shop object
- `program` (BonusProgram): Program object
- `reason` (str): Why the proposal needs review
- `source_url` (str): Link to source page

**Returns:**
- `int`: Proposal ID if successful
- `None`: If creation fails

**Proposal Details:**
- Type: 'rate_change'
- Status: 'pending'
- Source: 'scraper' (marked automatically)
- User: _scraper_system
- Reason: Provided text
- source_url: Provided URL

## Usage Example

### Run Standalone
```python
from app import app, db
from scrapers.miles_and_more_scraper import MilesAndMoreScraper

with app.app_context():
    scraper = MilesAndMoreScraper()
    added, updated, errors = scraper.scrape()

    print(f"Added: {added}")
    print(f"Updated: {updated}")
    print(f"Errors: {len(errors)}")

    for error in errors:
        print(f"  - {error}")
```

### Run from App Route (Already Implemented)
```python
@app.route('/admin/run_miles_and_more', methods=['POST'])
@login_required
def admin_run_miles_and_more():
    from scrapers.miles_and_more_scraper import MilesAndMoreScraper

    scraper = MilesAndMoreScraper()
    added, updated, errors = scraper.scrape()

    # Log results
    db.session.add(ScrapeLog(
        message=f'M&M: +{added}, updated {updated}, {len(errors)} errors'
    ))
    db.session.commit()
```

## Database Integration

### Created Entities

#### Shop
```python
shop = Shop(
    name="Lufthansa Lounge",  # From scraper
    # ... other fields
)
db.session.add(shop)
```

#### ShopProgramRate
```python
rate = ShopProgramRate(
    shop_id=shop.id,
    program_id=program.id,
    points_per_eur=1.5,  # Extracted from page
    cashback_pct=0.0,
    valid_from=datetime.utcnow(),
    valid_to=None
)
db.session.add(rate)
```

#### Proposal (for uncertain data)
```python
proposal = Proposal(
    proposal_type='rate_change',
    status='pending',
    source='scraper',  # Important: marks as scraper-created
    user_id=system_user.id,
    shop_id=shop.id,
    program_id=program.id,
    proposed_points_per_eur=None,  # Unknown - needs review
    reason="Could not automatically extract points rate",
    source_url="https://miles-and-more.com/partners/..."
)
db.session.add(proposal)
```

## API Routes

### `/admin/run_miles_and_more` (POST)
Trigger scraper execution from admin panel.

**Requirements:**
- Admin role
- Authenticated session

**Returns:**
- Redirects to `/admin` dashboard
- Displays results in scraper logs

**Example:**
```html
<form method="post" action="/admin/run_miles_and_more">
  <button type="submit">▶ Run Miles & More Scraper</button>
</form>
```

### `/review-scraper-proposal/<int:proposal_id>` (GET/POST)
Review and confirm a scraper-created proposal.

**GET Parameters:**
- `proposal_id`: ID of scraper proposal to review

**GET Returns:**
- Renders `review_scraper_proposal.html` with pre-filled form

**POST Parameters:**
- `points_per_eur` (float): Points per EUR (for rate changes)
- `cashback_pct` (float): Cashback percentage
- `name` (str): Shop/program name
- `coupon_type` (str): 'multiplier' or 'discount'
- `coupon_value` (float): Multiplier value or discount percent
- `reason` (str): User's additional notes

**POST Returns:**
- Creates new User Proposal
- Marks original proposal as 'approved'
- Redirects to `/proposals`

## Proposal Workflow

### Scraper Creates Proposal
```
Miles & More Website
        ↓
MilesAndMoreScraper.scrape()
        ↓
Extract Data or Error
        ↓
Create Proposal (source='scraper')
        ↓
Database (Pending)
```

### User Reviews Proposal
```
/proposals (shows 🤖 scraper badge)
        ↓
User clicks "Review Proposal"
        ↓
/review-scraper-proposal/<id>
        ↓
Form with pre-filled data
        ↓
User submits (creates new User Proposal)
        ↓
Original marked 'approved'
        ↓
Community voting begins
```

## Configuration

### Playwright Settings
```python
browser = p.chromium.launch(headless=True)  # Run without GUI
page.goto(url, wait_until='networkidle', timeout=30000)  # Wait for load
page.wait_for_selector(selector, timeout=10000)  # Wait for elements
```

### Scroll Settings
```python
max_scrolls = 20  # Maximum scroll iterations
scroll_delay = time.sleep(1)  # Delay between scrolls
```

### Regex Patterns
Patterns tried in order for points extraction:
1. German format: "X Meilen/Punkte pro Y€"
2. English format: "X Miles per EUR"
3. Simple format: "X per Y€"
4. Fallback: "X" after "pro €"

## Performance Notes

### Execution Time
- ~2-5 minutes depending on:
  - Number of partners (500+)
  - Website response time
  - Network latency
  - Server load

### Database Impact
- Creates minimal new shops (most reuse existing)
- Updates rates efficiently (old marked expired)
- Creates proposals only for uncertain data
- All operations wrapped in transactions

### Error Recovery
- Failed network requests → Skip partner, continue
- Extraction fails → Create proposal, continue
- Database errors → Log error, continue
- Robust - designed to complete despite partial failures

## Security Considerations

### User Elevation
- System user cannot login (`password_hash='locked'`)
- Only used for proposal attribution
- All scraped data is "pending" until human review

### Data Validation
- No direct rate insertion without proposal review
- All values validated before database insertion
- Numeric fields checked (points, cashback)
- URLs validated before storing

### Admin Access
- Scraper run requires admin role
- Proposal review available to all contributors+
- Voting system applies community consensus
- Admin can override with direct approval

## Logging

### ScrapeLog Entries
```python
ScrapeLog(
    message=f'Miles & More scraper started at {start}',
    timestamp=datetime.utcnow()
)

ScrapeLog(
    message=f'Added 150 shops, updated 42, 8 errors'
)

ScrapeLog(
    message='Error: Could not extract rate from Hotel Partner'
)
```

## Monitoring

### Check Logs
```
SELECT * FROM scrape_log
WHERE message LIKE 'Miles & More%'
ORDER BY timestamp DESC LIMIT 50;
```

### Check Proposals
```
SELECT * FROM proposals
WHERE source = 'scraper'
ORDER BY created_at DESC;
```

### Check Uncertain Proposals
```
SELECT * FROM proposals
WHERE source = 'scraper'
  AND status = 'pending'
  AND proposed_points_per_eur IS NULL
ORDER BY created_at DESC;
```

## Troubleshooting

### Playwright Not Found
```bash
pip install playwright
playwright install chromium
```

### Program Not Found
Make sure MilesAndMore program exists:
```python
prog = BonusProgram.query.filter_by(name='MilesAndMore').first()
if not prog:
    prog = BonusProgram(name='MilesAndMore', point_value_eur=0.01)
    db.session.add(prog)
    db.session.commit()
```

### Scraper Hangs
- Check if Miles & More website is up
- Try timeout adjustment in code
- Check network connectivity
- Try again in a few minutes

### No Data Extracted
- Website structure might have changed
- Check HTML content manually
- Update regex patterns if needed
- Create issue with sample HTML for debugging

## Future Enhancements

1. **Scheduled Execution**
   - Use Celery or APScheduler
   - Run nightly or weekly
   - Email admin with results

2. **Rate Change Detection**
   - Compare new vs old rates
   - Alert if significant changes
   - Track rate history

3. **Additional Scrapers**
   - Shoop integration
   - Other programs
   - Unified dashboard

4. **AI Assistance**
   - Machine learning for extraction
   - Learn from manual corrections
   - Improve accuracy over time

5. **Batch Operations**
   - Approve multiple proposals at once
   - Bulk rate updates
   - Export to CSV
