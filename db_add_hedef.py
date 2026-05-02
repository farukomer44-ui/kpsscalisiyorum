# db_add_hedef.py dosyası oluşturun:
import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

# Günlük hedef tablosu
cur.execute("""
CREATE TABLE IF NOT EXISTS gunluk_hedef (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tarih DATE UNIQUE,
    hedef_soru INTEGER DEFAULT 100,
    cozulen_soru INTEGER DEFAULT 0,
    acik_soru INTEGER DEFAULT 0,
    tasinan_acik INTEGER DEFAULT 0
)
""")

print("gunluk_hedef tablosu oluşturuldu.")

# Bugünün kaydını oluştur (eğer yoksa)
from datetime import date
bugun = date.today().isoformat()

cur.execute("""
    INSERT OR IGNORE INTO gunluk_hedef (tarih, hedef_soru, cozulen_soru, acik_soru, tasinan_acik)
    VALUES (?, 100, 0, 0, 0)
""", (bugun,))

conn.commit()
conn.close()