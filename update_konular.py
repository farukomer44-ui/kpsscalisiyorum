# update_konular.py dosyası oluşturun:
import sqlite3
from datetime import datetime

conn = sqlite3.connect("database.db")
cur = conn.cursor()

print("Konular tablosu güncelleniyor...")

# 1. Önce konular tablosunu temizleyelim
cur.execute("DELETE FROM konular")
print("✓ konular tablosu temizlendi")

# 2. sorular tablosundaki TÜM verileri konular tablosuna aktaralım
# (10.01.2026'dan itibaren ve konu bilgisi olanlar)
cur.execute("""
    SELECT ders, konu, SUM(yanlis) as toplam_yanlis, tarih
    FROM sorular
    WHERE konu IS NOT NULL 
        AND konu != ''
        AND konu != 'Konu Bilgisi Yok'
        AND yanlis > 0
        AND tarih >= '2026-01-10'
    GROUP BY ders, konu, tarih
    ORDER BY tarih
""")

sorular = cur.fetchall()

toplam_eklenen = 0
for ders, konu, yanlis, tarih in sorular:
    try:
        cur.execute("""
            INSERT INTO konular (ders, konu_adi, yanlis_sayisi, tarih)
            VALUES (?, ?, ?, ?)
        """, (ders, konu, yanlis, tarih))
        toplam_eklenen += 1
    except:
        pass  # Hata olursa atla

conn.commit()
conn.close()

print(f"✓ {toplam_eklenen} kayıt konular tablosuna eklendi")
print("\n✅ Konular tablosu güncellemesi tamamlandı!")