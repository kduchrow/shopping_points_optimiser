# Landing Page Tutorial Draft

## Purpose & Overview Section

### What is Shopping Points Optimiser?

Shopping Points Optimiser helps you **maximize the value of your online purchases** by comparing cashback and loyalty programs across different retailers. Instead of wondering which loyalty program offers the best returns, this tool shows you exactly how much each program will reward you for shopping at a specific store.

### Why Should You Use It?

- **Compare instantly**: See all available bonus programs for a shop in one place
- **Make informed decisions**: Know the estimated value before you shop
- **Save money**: Earn more cashback and loyalty points by choosing the best programs
- **No commitments**: View rates without entering a purchase amount

---

## How to Use Guide

### Step 1: Select a Shop
- Use the shop dropdown to search for the retailer you want to shop at
- Type to quickly find the shop in our database
- All major online retailers are covered (Amazon, eBay, AirBnB, Hotels.com, etc.)

### Step 2: Enter an Amount (Optional)
- **Want to calculate earnings?** Enter your expected purchase amount in euros
- **Just want to see rates?** Leave the field empty - we'll show you the raw rates without calculations
- The button will change to guide you:
  - **Empty**: "Informationen ohne Wert anzeigen" (Show information without value)
  - **With amount**: "Bonus berechnen" (Calculate bonus)

### Step 3: View Your Results
- **Programs listed by value**: Top earning programs are shown first
- **For each program, you'll see:**
  - Base estimated value in euros
  - Money left after reward deduction
  - Category-specific rates if available
  - Special promotions or multipliers when active

### Understanding the Results

#### Without an Amount (Info-Only Mode)
When you leave the amount empty, you see:
- **Points/EUR**: How many loyalty points you earn per euro spent
- **Cashback %**: Percentage cashback offered
- **Absolute rewards**: Fixed bonuses for purchasing at this shop

#### With an Amount
When you enter an amount, you see:
- **Estimated Value**: How much that purchase is worth in rewards (in euros)
- **Amount Remaining**: Your purchase amount minus the reward value
- **Multiple programs**: Compare different loyalty schemes side-by-side
- **Multipliers/Discounts**: Additional bonuses when promotions are active

---

## Example Scenarios

### Scenario 1: Quick Rate Check
**User wants to know**: "What rates does Amazon offer?"

1. Select "Amazon" from the dropdown
2. Leave amount empty
3. Click "Informationen ohne Wert anzeigen"
4. View all available programs with their rates

**Result**: See Payback, Miles&More, Shoop, etc. with points/EUR and cashback %

### Scenario 2: Calculate Specific Purchase
**User wants to know**: "How much will I earn from a €150 Amazon purchase?"

1. Select "Amazon" from the dropdown
2. Enter "150" in the amount field
3. Button changes to "Bonus berechnen"
4. Click to calculate
5. See estimated returns in euros for each program

**Result**: "With Payback you'll earn approximately €4.50, with Miles&More approximately €6.00"

### Scenario 3: Find the Best Shop for a Purchase
**User wants to know**: "Where should I buy a printer to maximize rewards?"

1. Select printer retailer from dropdown
2. Enter purchase amount (€300)
3. Click "Bonus berechnen"
4. Compare which shop offers the best program value

**Result**: See which combination of shop + program gives the highest reward

---

## Tips & Tricks

### Maximize Your Rewards
1. **Check before you click**: Always compare rates before shopping
2. **Use cashback sites**: Shoop often offers multipliers on top of base rates
3. **Combine programs**: Some retailers work with multiple loyalty programs
4. **Watch for campaigns**: Special promotions can significantly boost rewards

### Understanding Special Symbols
- 🎉 **Special promotions**: Active multipliers or discounts available
- 📍 **Shop-specific rates**: Category-based rewards for this retailer
- ℹ️ **Info-only mode**: See raw rates without doing calculations

---

## FAQ

**Q: Is my data saved?**
A: No. We don't store your search history or purchase data. Every search is independent.

**Q: Why do different programs have different rates?**
A: Each loyalty program negotiates rates directly with retailers. Some specialize in cashback, others in points.

**Q: Can I use multiple programs at once?**
A: It depends on the retailer. Some allow stacking multipliers and discounts. See the special promotions section for details.

**Q: How often are rates updated?**
A: Rates are updated regularly by our automated scrapers to reflect the latest offers from retailers and loyalty programs.

**Q: Why isn't my favorite shop listed?**
A: We're constantly adding new shops. You can submit a suggestion on the "Vorschlag einreichen" (Submit Suggestion) page to request a new shop.

---

## HTML/Template Version (for index.html)

```html
<!-- Info Section - Could be added above or below the form -->
<div class="info-section" style="margin-bottom: 32px; background: #f8fafc; border-radius: 12px; padding: 24px;">
  <h2 style="margin-top: 0;">🤔 Wie funktioniert's?</h2>

  <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-top: 16px;">
    <!-- Step 1 -->
    <div style="background: white; padding: 16px; border-radius: 8px; border-left: 4px solid #3b82f6;">
      <h3 style="margin-top: 0; color: #1f2937;">1. Shop wählen</h3>
      <p style="color: #666; margin: 0;">Wähle den Online-Shop aus, bei dem du kaufen möchtest</p>
    </div>

    <!-- Step 2 -->
    <div style="background: white; padding: 16px; border-radius: 8px; border-left: 4px solid #8b5cf6;">
      <h3 style="margin-top: 0; color: #1f2937;">2. Betrag eingeben (optional)</h3>
      <p style="color: #666; margin: 0;">Gib einen Betrag ein oder lass das Feld leer um nur die Raten zu sehen</p>
    </div>

    <!-- Step 3 -->
    <div style="background: white; padding: 16px; border-radius: 8px; border-left: 4px solid #ec4899;">
      <h3 style="margin-top: 0; color: #1f2937;">3. Ergebnisse vergleichen</h3>
      <p style="color: #666; margin: 0;">Sehe alle verfügbaren Bonusprogramme und deren Wert</p>
    </div>
  </div>

  <div style="margin-top: 20px; padding: 16px; background: #ecf0ff; border-radius: 8px; border-left: 4px solid #3b82f6;">
    <strong>💡 Tipp:</strong> Du brauchst keinen Betrag einzugeben um die Raten zu sehen. Lass das Feld einfach leer!
  </div>
</div>
```
