import sqlite3
from datetime import date

conn = sqlite3.connect("database.db")
cur = conn.cursor()

print("Veritabanı düzeltiliyor...")

# 1. sorular tablosuna konu sütunu ekleyelim (eğer yoksa)
try:
    cur.execute("ALTER TABLE sorular ADD COLUMN konu TEXT")
    print("✓ sorular tablosuna 'konu' sütunu eklendi")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("✓ 'konu' sütunu zaten var")
    else:
        print(f"! konu sütunu eklenirken hata: {e}")

# 2. konular tablosunu oluşturalım (eğer yoksa)
try:
    cur.execute("""
        CREATE TABLE konular (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ders TEXT,
            konu_adi TEXT,
            yanlis_sayisi INTEGER DEFAULT 0,
            tarih TEXT
        )
    """)
    print("✓ konular tablosu oluşturuldu")
except sqlite3.OperationalError as e:
    if "already exists" in str(e):
        print("✓ konular tablosu zaten var")
    else:
        print(f"! konular tablosu oluşturulurken hata: {e}")

# 3. gunluk_hedef tablosunu oluşturalım (eğer yoksa)
try:
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
    print("✓ gunluk_hedef tablosu oluşturuldu")
    
    # Bugünün kaydını ekle
    bugun = date.today().isoformat()
    cur.execute("""
        INSERT OR IGNORE INTO gunluk_hedef (tarih, hedef_soru, cozulen_soru, acik_soru, tasinan_acik)
        VALUES (?, 100, 0, 0, 0)
    """, (bugun,))
    print("✓ Bugünün hedef kaydı eklendi")
    
except sqlite3.OperationalError as e:
    print(f"! gunluk_hedef tablosu oluşturulurken hata: {e}")

conn.commit()
conn.close()
print("\n✅ Veritabanı düzeltme tamamlandı!")