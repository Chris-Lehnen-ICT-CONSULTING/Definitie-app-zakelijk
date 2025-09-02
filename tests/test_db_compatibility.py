"""
Test database compatibility met legacy velden.
"""
import sqlite3
from datetime import datetime, timezone
import json

print("Testing database compatibility...")

# Test 1: Check schema
conn = sqlite3.connect("definities.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(definities)")
columns = {row[1] for row in cursor.fetchall()}

print("\n✅ Legacy velden aanwezig:")
print(f"  - datum_voorstel: {'✓' if 'datum_voorstel' in columns else '✗'}")
print(f"  - ketenpartners: {'✓' if 'ketenpartners' in columns else '✗'}")

# Test 2: Insert met legacy velden
try:
    test_ketenpartners = json.dumps(["OM", "DJI", "KMAR"])

    cursor.execute("""
        INSERT INTO definities (
            begrip, definitie, categorie, organisatorische_context,
            created_by, datum_voorstel, ketenpartners
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        "test_legacy",
        "Test definitie met legacy velden",
        "proces",
        "Test organisatie",
        "test_user",
        datetime.now(timezone.utc),
        test_ketenpartners
    ))
    conn.commit()

    print("\n✅ Insert met legacy velden succesvol")

    # Test 3: Query legacy velden
    cursor.execute("""
        SELECT begrip, datum_voorstel, ketenpartners
        FROM definities
        WHERE begrip = 'test_legacy'
    """)

    row = cursor.fetchone()
    if row:
        print(f"\n✅ Legacy velden opgehaald:")
        print(f"  - begrip: {row[0]}")
        print(f"  - datum_voorstel: {row[1]}")
        print(f"  - ketenpartners: {row[2]}")

        # Parse ketenpartners
        partners = json.loads(row[2])
        print(f"  - Parsed partners: {partners}")

    # Cleanup
    cursor.execute("DELETE FROM definities WHERE begrip = 'test_legacy'")
    conn.commit()

except Exception as e:
    print(f"\n❌ Database test mislukt: {e}")
finally:
    conn.close()

print("\n🎉 Database compatibility test compleet!")
