# Shopping Points Optimiser - Admin System Documentation

## 📋 Übersicht

Das Admin-System wurde komplett überarbeitet mit folgenden Features:
- ✅ Shop-Deduplication (automatisches Zusammenführen)
- ✅ Shop Merge Approval Workflow
- ✅ Rate Review System
- ✅ Notification System
- ✅ Moderne Tab-basierte UI

---

## 🎯 Features

### 1. Shop Deduplication System

**Automatische Duplikate-Erkennung:**
- `≥98%` Ähnlichkeit → **Automatisches Merge**
- `70-98%` Ähnlichkeit → **Community-Review nötig**
- `<70%` Ähnlichkeit → **Neuer separater Shop**

**Beispiel:**
```
"Amazon" (Miles & More) + "amazon" (Payback) = 100% → AUTO-MERGED ✓
"Amazone" (Manual) = 92.3% → NEEDS REVIEW ⚠️
```

**Datenstruktur:**
- `ShopMain`: Kanonischer Shop (UUID, unveränderlich)
- `ShopVariant`: Quellenspezifische Varianten
- `Shop`: Legacy-Tabelle (Backward-Kompatibilität)

---

### 2. Shop Merge Proposal System

**Workflow:**
1. User/System schlägt Shop-Merge vor
2. Admin sieht Proposal in UI (Tab: Shop Merges)
3. Admin approved oder rejected mit Reason
4. User erhält Notification über Entscheidung

**API Endpoints:**
- `GET /admin/shops/merge_proposals` - Liste aller Proposals
- `POST /admin/shops/merge_proposal` - Neues Proposal erstellen
- `POST /admin/shops/merge_proposal/<id>/approve` - Approve & Execute
- `POST /admin/shops/merge_proposal/<id>/reject` - Reject mit Reason

---

### 3. Rate Review System

**Features:**
- Reviewer können Kommentare zu Rates hinterlassen
- Kommentar-Typen: `FEEDBACK`, `REJECTION_REASON`, `SUGGESTION`
- Notifications bei neuen Kommentaren

**API Endpoints:**
- `POST /admin/rate/<id>/comment` - Kommentar hinzufügen
- `GET /admin/rate/<id>/comments` - Alle Kommentare abrufen

---

### 4. Notification System

**Notification-Typen:**
- `PROPOSAL_REJECTED` - Proposal wurde abgelehnt
- `PROPOSAL_APPROVED` - Proposal wurde approved
- `RATE_COMMENT` - Neuer Kommentar auf Rate
- `MERGE_REJECTED` - Shop-Merge abgelehnt
- `MERGE_APPROVED` - Shop-Merge approved

**API Endpoints:**
- `GET /api/notifications` - Alle Notifications (max 50)
- `GET /api/notifications/unread_count` - Anzahl ungelesener
- `POST /api/notifications/<id>/read` - Als gelesen markieren
- `POST /api/notifications/read_all` - Alle als gelesen markieren

**Features:**
- Unread-Badge im Header
- Real-time Updates (alle 30 Sekunden)
- Click-to-mark-read

---

## 🎨 UI - Admin Panel

### Tab-Navigation

**1. 🤖 Scrapers**
- Miles & More Scraper starten
- Payback Scraper starten
- Live Job Progress mit Echtzeitanzeige
- Progress Bar & Message Feed

**2. 🔗 Shop Merges**
- Liste aller pending Merge Proposals
- Approve/Reject mit einem Klick
- Automatische Notification an Proposer

**3. ⭐ Rate Review**
- Rates mit niedriger Confidence
- Kommentar-Funktion
- Status-Management (Coming Soon)

**4. 🔔 Notifications**
- Alle Notifications chronologisch
- Unread-Highlighting
- Mark as Read / Mark All as Read
- Unread-Badge im Header

---

## 🚀 Verwendung

### Admin-Panel starten:

```bash
python app.py
# Öffne: http://127.0.0.1:5000/admin
# Login: admin / admin123
```

### Tests ausführen:

```bash
# Shop Deduplication testen
python demo_dedup.py

# Notification System testen
python test_notifications.py

# Shop Dedup Unit Tests
python test_shop_dedup.py
```

---

## 📊 Datenbank-Schema

### Neue Tabellen:

**shop_main**
- `id` (UUID, Primary Key)
- `canonical_name` (Normalisierter Name)
- `canonical_name_lower` (Für Fuzzy Matching)
- `website`, `logo_url`
- `status` (active, merged, inactive)
- `merged_into_id` (Bei Merge)

**shop_variants**
- `id` (Primary Key)
- `shop_main_id` (Foreign Key → shop_main)
- `source` (miles_and_more, payback, manual)
- `source_name` (Original-Name aus Quelle)
- `source_id` (Externe ID)
- `confidence_score` (0-100)

**shop_merge_proposals**
- `id` (Primary Key)
- `variant_a_id`, `variant_b_id`
- `proposed_by_user_id`
- `status` (PENDING, APPROVED, REJECTED)
- `reason`, `decided_reason`
- `decided_at`, `decided_by_user_id`

**rate_comments**
- `id` (Primary Key)
- `rate_id` (Foreign Key → shop_program_rates)
- `reviewer_id` (Foreign Key → users)
- `comment_type` (FEEDBACK, REJECTION_REASON, SUGGESTION)
- `comment_text`

**notifications**
- `id` (Primary Key)
- `user_id` (Foreign Key → users)
- `notification_type`
- `title`, `message`
- `link_type`, `link_id`
- `is_read` (Boolean)
- `created_at`

---

## 🔧 API Integration

### Notification Helper:

```python
from notifications import (
    notify_proposal_rejected,
    notify_merge_approved,
    notify_rate_comment
)

# Beispiel: Proposal reject
notify_proposal_rejected(proposal, "Reason: Duplicate entry")

# Beispiel: Merge approved
notify_merge_approved(merge_proposal)
```

### Shop Dedup Helper:

```python
from shop_dedup import (
    get_or_create_shop_main,
    fuzzy_match_score,
    merge_shops
)

# Auto-dedup beim Scrapen
shop_main, is_new, confidence = get_or_create_shop_main(
    shop_name="Amazon",
    source="miles_and_more",
    source_id="12345"
)

# Manuelles Merge
merge_shops(
    main_from_id="uuid-a",
    main_to_id="uuid-b",
    user_id=current_user.id
)
```

---

## ✅ Testing Checklist

- [x] Shop Deduplication funktioniert (Amazon/amazon → merged)
- [x] Notification System funktioniert
- [x] Admin UI lädt korrekt
- [x] API Endpoints erreichbar
- [x] Datenbank-Tabellen erstellt

---

## 🎯 Next Steps (Optional)

1. **Rate Approval Workflow** - Status-Management für Rates
2. **Email Notifications** - Optional: Benachrichtigung per Email
3. **Advanced Fuzzy Matching** - ML-basierte Shop-Erkennung
4. **User Dashboard** - Eigene Proposals/Notifications anzeigen
5. **API Documentation** - Swagger/OpenAPI Docs

---

## 🐛 Troubleshooting

**Problem: Notification Badge zeigt nicht an**
- Solution: Browser-Cache löschen, Seite neu laden

**Problem: Merge Proposal schlägt fehl**
- Check: Beide Variants existieren in DB
- Check: User ist Admin

**Problem: Scraper erstellt Duplikate**
- Check: `get_or_create_shop_main()` wird verwendet
- Check: `confidence_score` in ShopVariant

---

## 📝 License

MIT License - Shopping Points Optimiser 2026
