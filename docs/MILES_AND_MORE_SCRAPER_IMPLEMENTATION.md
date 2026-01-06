# Miles & More Scraper Implementation - Summary

## What Was Implemented

### 1. **Miles & More Scraper** (`scrapers/miles_and_more_scraper.py`)

A Playwright-based web scraper that:
- Visits `https://www.miles-and-more.com/de/de/program/partners.html`
- Scrolls to load all partner shops dynamically
- Extracts partner names and detail page URLs
- Scrapes points rates from individual partner pages
- Handles uncertainty gracefully:
  - If points rate cannot be extracted → creates a Proposal marked `source='scraper'`
  - If an error occurs → logs error and creates a recovery Proposal

Features:
- Auto-creates/updates Shop and ShopProgramRate records in database
- Creates a system user `_scraper_system` for scraper-generated proposals
- Marks all proposals with source field: 'scraper'
- Includes source_url field pointing to the partner page
- Returns statistics: (shops_added, shops_updated, errors)

### 2. **Admin Route** (`app.py` - `/admin/run_miles_and_more`)

New POST route that:
- Requires admin authentication
- Executes the Miles & More scraper
- Logs results to ScrapeLog table
- Displays results on admin dashboard
- Handles errors gracefully

### 3. **Admin UI Update** (`templates/admin.html`)

Added button to scraper section:
```html
<button type="submit">▶ Run Miles & More Scraper</button>
```

### 4. **Scraper Proposal Modal** (`templates/result.html`)

New modal component that:
- Displays when a scraper-created proposal exists for a selected shop
- Shows proposal details and source information
- Provides "Review Proposal" button
- Includes modal styling and animations

Functions added:
- `openProposalModal()` - Open modal with proposal details
- `closeProposalModal()` - Close modal
- Click-to-close on background

### 5. **Scraper Proposal Review Route** (`app.py` - `/review-scraper-proposal/<id>`)

GET/POST route that:
- **GET**: Shows review form with:
  - Original scraper proposal details
  - Pre-filled form fields based on proposal type
  - Edit capability for all fields
  - Scraper badge indicator

- **POST**:
  - Creates new User Proposal from reviewed data
  - Sets `source='user'` on new proposal
  - Marks original scraper proposal as 'approved'
  - User can add additional notes
  - Redirects to proposals list

### 6. **Scraper Proposal Review Template** (`templates/review_scraper_proposal.html`)

New template supporting all proposal types:
- **Rate Change**: Points per EUR, Cashback %
- **Shop Add**: Shop name
- **Program Add**: Program name, point value
- **Coupon Add**: Type, value, description, combinability, valid_to

Features:
- Pre-populated from scraper proposal data
- User can edit any field
- Optional additional notes
- Visual scraper badge indicator
- Clean form styling with help text

## Database Schema Updates

The Proposal model already had these fields:
- `source` - tracks 'user' or 'scraper' origin
- `source_url` - link to source page for scraper proposals

## Workflow

### For Users:
1. **Run Scraper**: Admin clicks button to run Miles & More scraper
2. **Auto-Create Proposals**: Scraper creates proposals for:
   - Successfully scraped partners (marked as scraped)
   - Partners with missing data (marked for manual review)
3. **User Interaction**:
   - User selects a shop that has a scraper proposal
   - Modal popup shows the proposal
   - User clicks "Review Proposal" button
   - Form opens with pre-filled scraper data
   - User can edit/confirm the data
   - Submitting creates a User Proposal (source='user')
   - Original scraper proposal marked as 'approved'

### For Admins:
1. Check admin panel
2. Click "Run Miles & More Scraper" button
3. Monitor logs for results
4. View created proposals in `/proposals` page

## Error Handling

The scraper handles:
- Network errors → Log to ScrapeLog, create recovery proposal
- Missing data → Create proposal with "needs review" flag
- Page structure changes → Regex fallback patterns for points extraction
- Invalid proposals → Exception handling with detailed error logging

## Key Design Decisions

1. **Soft Errors**: Instead of failing completely, scraper creates proposals for uncertain cases
2. **User Validation**: All scraper data can be reviewed/edited by users before final approval
3. **Tracking**: `source` field distinguishes scraper vs user proposals in community system
4. **Modularity**: Scraper is independent, can be run on demand or scheduled
5. **Visibility**: All scraper activity logged and accessible to admins

## Files Modified/Created

**Created:**
- `scrapers/miles_and_more_scraper.py` - Scraper implementation
- `templates/review_scraper_proposal.html` - Proposal review UI

**Modified:**
- `app.py` - Added `/admin/run_miles_and_more` and `/review-scraper-proposal/<id>` routes
- `templates/admin.html` - Added Miles & More scraper button
- `templates/result.html` - Added proposal modal component

## Testing the Implementation

1. **Setup Database**:
   ```bash
   python setup_test_environment.py
   ```

2. **Run Scraper**:
   - Login as admin
   - Go to `/admin`
   - Click "Run Miles & More Scraper" button

3. **Review Results**:
   - Check ScrapeLog at `/admin`
   - View created proposals at `/proposals`

4. **Review Individual Proposal**:
   - Click on scraper proposal (shows source badge)
   - Click "Review" button
   - Edit pre-filled data
   - Submit to create user proposal

## Future Enhancements

- Schedule scraper to run periodically (Celery/APScheduler)
- Add more scrapers (Shoop, other programs)
- Batch import from CSV/API
- Proposal auto-approval based on user trust level
- Notification system when proposals need review
