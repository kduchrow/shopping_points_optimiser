# Miles & More Scraper - User Guide

## Quick Start

### For Admins

1. **Start the Application**
   ```bash
   python setup_test_environment.py
   ```

2. **Run the Scraper**
   - Navigate to `http://127.0.0.1:5000/admin`
   - Click "▶ Run Miles & More Scraper"
   - Wait for completion (can take several minutes)
   - Check the "Scraper Logs" section at bottom for results

3. **Monitor Results**
   - View created proposals at `/proposals`
   - Filter by source to see only scraper proposals (🤖 badge)
   - Check logs for any errors or uncertain matches

### For Regular Users

1. **Review Scraper Proposals**
   - Navigate to `/proposals`
   - Look for proposals with 🤖 badge (scraper-created)
   - Click on a proposal to see details
   - Click "Review Proposal" button

2. **Edit & Confirm Data**
   - Review pre-filled form fields
   - Edit any fields that need correction
   - Add notes about your changes in "Your Note" field
   - Click "Confirm & Submit"

3. **Submission Complete**
   - Your review creates a new User Proposal
   - Original scraper proposal is marked as approved
   - Your proposal now appears in the community voting system
   - Other users can upvote it

## What Gets Scraped

The Miles & More scraper collects:
- **Shop Name**: Partner name
- **Points Rate**: How many Miles points per €1 spent
- **Cashback**: Any percentage cashback (if available)

## Error Handling

### ✓ Successfully Scraped
- Shop is added to database
- ShopProgramRate is created with points value
- Proposal is created as "approved" (automatic)

### ⚠️ Needs Review
- Points could not be extracted automatically
- A proposal is created marked for manual review
- First user to select this shop will see the popup
- User can provide the correct rate

### ❌ Error During Scrape
- Network error or page structure changed
- Error is logged in ScrapeLog
- Proposal is created for manual recovery
- Admin can check logs for details

## Proposal Types

After review, scraper proposals become one of:

### Rate Changes
- **New Points Rate**: Points per EUR spent
- **Cashback %**: Any bonus cash value
- **Shop**: Which shop to add the rate to
- **Program**: For Miles & More

### New Shop Additions
- **Shop Name**: Name of the partner
- **Location**: Where to find it (if available)

### New Coupon/Specials
- **Type**: Points multiplier (e.g., 2x) or discount (e.g., 10%)
- **Description**: What the offer is
- **Validity**: When it expires
- **Applicability**: Specific shop or all shops

## Voting System

After user creates a proposal from scraper data:
1. Community can upvote/downvote the proposal
2. Admin votes count 3x more than regular votes
3. 3+ weighted votes = auto-approval
4. Admin can also approve directly with ✓ button

## Common Issues

### Scraper Takes Too Long
- Miles & More website loads partners dynamically
- Scraper waits for page load before scrolling
- This is normal - let it complete

### Uncertain/Missing Data Warnings
- Some partners don't show points clearly
- Scraper marks these for manual review
- You can help by providing the correct data

### Already Exists
- If shop is in database, rate is updated (not duplicated)
- Old rate is marked valid_to with current timestamp
- New rate replaces it with valid_from = now

## Admin Dashboard Features

### Run Buttons
- Payback Scraper: 720+ shops
- Miles & More Scraper: 500+ partners

### Logs Section
- Shows last 200 scrape operations
- Timestamps show when each scraper ran
- Error messages if something failed
- Count of shops added/updated

### Programs & Shops Tables
- View all registered programs
- View all shops in database
- See point values and details

## Tips & Tricks

### ✨ Best Practices
1. **Review Carefully**: Check the source URL before confirming
2. **Add Context**: Use notes field to explain any corrections
3. **Current Rates**: Only update if rate has actually changed
4. **Check Errors**: Look at logs if unsure about data quality

### 🚀 Power User Features
- Admin can directly approve proposals with ✓ button
- Vote weight shown for admin votes (👍 Admin+3)
- Filter proposals by type, status, source
- Search proposals by shop name

### 📊 Data Quality
- Proposals from confirmed users get faster approval
- Contributor role needed to submit proposals
- Admin always has final say on acceptance
- All changes are tracked in audit logs

## Troubleshooting

### "Scraper Error: ..." in logs
1. Check internet connection
2. Miles & More website might be down
3. Wait a few minutes and retry
4. Check website manually to see if structure changed

### Form won't submit
1. Check all required fields are filled
2. Some fields show help text - read them
3. Points/cashback must be numeric
4. Try refresh page if stuck

### Proposal not appearing
1. Wait a moment for page to refresh
2. Check you're logged in as contributor+
3. Viewer accounts can only see proposals, not create
4. Contact admin if still not visible

## Need Help?

- Check the existing proposals for examples
- Look at proposal details before submitting
- Ask admin to review your first few proposals
- Report issues in admin dashboard
