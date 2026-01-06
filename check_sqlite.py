import sqlite3

conn = sqlite3.connect("instance/shopping_points.db")
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall() if not r[0].startswith("sqlite_")]

print(f"\n{'='*70}")
print(f"SQLite Database: {len(tables)} Tabellen")
print("=" * 70)

for t in tables:
    c.execute(f"SELECT COUNT(*) FROM {t}")
    count = c.fetchone()[0]
    print(f"  • {t}: {count} rows")

conn.close()
