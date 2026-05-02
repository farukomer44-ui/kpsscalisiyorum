# create_gunluk_calisma.py dosyası oluşturun:
import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

# gunluk_calisma tablosunu oluştur
cur.execute("""
CREATE TABLE IF NOT EXISTS gunluk_calisma (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tarih DATE UNIQUE,
    toplam_sayfa INTEGER DEFAULT 0
)
""")

print("✓ gunluk_calisma tablosu oluşturuldu/doğrulandı")

# Mevcut çalışma verilerinden geçmiş veri oluştur (isteğe bağlı)
cur.execute("SELECT DISTINCT tarih FROM sorular WHERE tarih IS NOT NULL")
tarihler = cur.fetchall()

for tarih in tarihler:
    tarih_str = tarih[0]
    # O gün çalışılan toplam sayfa (sorulardan tahmin)
    cur.execute("""
        SELECT SUM(dogru + yanlis) / 10  -- Tahmini: 10 soru = 1 sayfa
        FROM sorular 
        WHERE tarih = ?
    """, (tarih_str,))
    tahmini_sayfa = cur.fetchone()[0] or 0
    
    if tahmini_sayfa > 0:
        cur.execute("""
            INSERT OR REPLACE INTO gunluk_calisma (tarih, toplam_sayfa)
            VALUES (?, ?)
        """, (tarih_str, int(tahmini_sayfa)))

conn.commit()
conn.close()
print("✓ Geçmiş veriler işlendi")