#!/usr/bin/env python
"""
Test Environment Setup Script
Startet den Server einmal zur DB-Initialisierung, erstellt dann Test-User, Shops, Programme und Coupons
"""

import subprocess
import time
import sys
import os
from datetime import datetime, timedelta

# Step 3 onwards uses these imports
_app = None
_db = None
_Coupon = None
_Shop = None
_BonusProgram = None

print("=" * 60)
print("🚀 Shopping Points Optimiser - Test Environment Setup")
print("=" * 60)

# Step 1: Starte Flask kurz, um DB zu erstellen
print("\n[1/5] Starte Flask zum Erstellen der Datenbank...")
flask_process = subprocess.Popen(
    [sys.executable, 'app.py'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Warte kurz, bis Flask gestartet hat
time.sleep(3)

# Beende Flask
print("       Flask wird beendet...")
flask_process.terminate()
flask_process.wait(timeout=5)

# Step 2: Erstelle Test-Accounts
print("\n[2/5] Erstelle Test-Accounts...")
result = subprocess.run(
    [sys.executable, 'create_test_accounts.py'],
    capture_output=True,
    text=True
)
if result.returncode != 0:
    print("       ❌ create_test_accounts.py fehlgeschlagen")
    if result.stdout:
        print("       stdout:")
        print("       " + "\n       ".join(result.stdout.strip().split('\n')))
    if result.stderr:
        print("       stderr:")
        print("       " + "\n       ".join(result.stderr.strip().split('\n')))
    sys.exit(1)
else:
    print("       " + "\n       ".join([line for line in result.stdout.strip().split('\n') if line]))

# Verifiziere, dass der Admin-User existiert
from app import app as _app_verify  # noqa: E402
from models import User  # noqa: E402
_app_verify.app_context().push()
admin_user = User.query.filter_by(username='admin').first()
if not admin_user:
    print("       ❌ Admin-User wurde nicht angelegt. Bitte prüfen, ob das Script im richtigen Virtualenv lief (sys.executable = {})".format(sys.executable))
    sys.exit(1)
else:
    print("       ✓ Admin-User vorhanden ({} / admin123)".format(admin_user.username))

# Step 3: Erstelle Test-Einträge und Coupons
print("\n[3/5] Erstelle Test-Daten...")
from app import app, db  # noqa: E402
from models import Coupon, Shop, BonusProgram, ShopProgramRate  # noqa: E402

app.app_context().push()

# Finde Payback
payback = BonusProgram.query.filter_by(name='Payback').first()
if not payback:
    print("       ❌ Payback Programm nicht gefunden!")
    sys.exit(1)

print(f"       ✓ Found Payback Program (ID: {payback.id})")

# Finde einen Payback-Shop
payback_shop = Shop.query.join(ShopProgramRate).filter(
    ShopProgramRate.program_id == payback.id
).first()

if not payback_shop:
    print("       ❌ Kein Payback-Shop gefunden!")
    print("       Hinweis: Bitte erst Payback Scraper in Admin ausführen")
    sys.exit(1)

print(f"       ✓ Found Payback Shop: {payback_shop.name} (ID: {payback_shop.id})")

# Lösche alte Test-Coupons
old_coupons = Coupon.query.filter(
    Coupon.status == 'active'
).all()
for coupon in old_coupons:
    db.session.delete(coupon)
db.session.commit()
print("       ✓ Old test coupons removed")

# Finde alle Shops für verschiedene Coupons
all_shops = Shop.query.all()
if len(all_shops) < 2:
    print("       ⚠️  Warnung: Weniger als 2 Shops verfügbar, nutze erste Shop mehrfach")
    test_shops = all_shops * 3
else:
    test_shops = all_shops[:3]

# Erstelle Test-Coupons für verschiedene Shops
coupons_to_create = [
    {
        'shop_idx': 0,
        'type': 'multiplier',
        'name': '20x Punkte Multiplier',
        'description': '20-fach Punkte beim Einkauf',
        'value': 20.0,
        'combinable': True,
        'program': payback,
    },
    {
        'shop_idx': 1 if len(test_shops) > 1 else 0,
        'type': 'discount',
        'name': '10% Rabatt',
        'description': '10% Rabatt auf Einkauf',
        'value': 10.0,
        'combinable': False,
        'program': None,
    },
    {
        'shop_idx': 2 if len(test_shops) > 2 else 0,
        'type': 'multiplier',
        'name': '5x Punkte (kombinierbar)',
        'description': '5-fach Punkte - kombinierbar mit anderen Aktionen',
        'value': 5.0,
        'combinable': True,
        'program': None,
    },
    {
        'shop_idx': 0,
        'type': 'multiplier',
        'name': '3x Punkte Weekend',
        'description': '3-fach Punkte an Wochenenden',
        'value': 3.0,
        'combinable': False,
        'program': payback,
    },
]

for i, coupon_data in enumerate(coupons_to_create):
    shop = test_shops[coupon_data['shop_idx']]
    program = coupon_data['program']
    
    coupon = Coupon(
        coupon_type=coupon_data['type'],
        name=coupon_data['name'],
        description=coupon_data['description'],
        value=coupon_data['value'],
        combinable=coupon_data['combinable'],
        shop_id=shop.id,
        program_id=program.id if program else None,
        valid_from=datetime.utcnow(),
        valid_to=datetime.utcnow() + timedelta(days=30),
        status='active'
    )
    db.session.add(coupon)
    program_text = f" ({program.name})" if program else " (alle Programme)"
    print(f"       ✓ Created coupon: {coupon_data['name']} für {shop.name}{program_text}")

db.session.commit()

print("\n[4/5] Test-Daten Summary:")
print(f"       Payback Programm: {payback.name}")
print(f"       Shops mit Coupons: {', '.join([s.name for s in test_shops[:len(set([c['shop_idx'] for c in coupons_to_create]))]])}")
print(f"       Coupons insgesamt: {len(coupons_to_create)}")

# Step 5: Starte Flask im Hintergrund
print("\n[5/5] Starte Flask Server...")
print("\n" + "=" * 60)
print("✅ Test Environment Setup Abgeschlossen!")
print("=" * 60)
print("\n🔗 Server läuft auf: http://127.0.0.1:5000")
print("\n📝 Test-Accounts:")
print("   Admin:       admin / admin123")
print("   Contributor: contributor / contrib123")
print("   User:        testuser / user123")
print("   Viewer:      viewer / viewer123")
print("\n🎯 Test-Coupons nach Shop:")
for coupon_data in coupons_to_create:
    shop = test_shops[coupon_data['shop_idx']]
    coupon_type = 'x' if coupon_data['type'] == 'multiplier' else '%'
    print(f"   • {coupon_data['name']} ({coupon_data['value']}{coupon_type}) @ {shop.name}")
print("\n💡 Hinweis: Flask läuft im Hintergrund. Drücke CTRL+C zum Beenden.")
print("=" * 60 + "\n")

# Starte Flask im Vordergrund
os.execvp(sys.executable, [sys.executable, 'app.py'])
