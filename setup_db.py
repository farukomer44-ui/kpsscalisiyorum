# setup_db.py'ye ekleyin veya ayrı bir dosya oluşturun
import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

# KONULAR tablosunu oluştur (eğer yoksa)
cur.execute("""
CREATE TABLE IF NOT EXISTS konular (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ders TEXT,
    konu_adi TEXT,
    yanlis_sayisi INTEGER DEFAULT 0,
    tarih TEXT
)
""")

# Örnek veriler ekleyelim (isteğe bağlı)
ornek_konular = [
    ("Matematik", "Problemler", 15),
    ("Matematik", "Sayısal Mantık", 12),
    ("Türkçe", "Paragraf", 8),
    ("Türkçe", "Dil Bilgisi", 10),
    ("Coğrafya", "İklim Tipleri", 6),
    ("Tarih", "İnkılap Tarihi", 14),
    ("Vatandaşlık", "Anayasa", 9),
]

for ders, konu, yanlis in ornek_konular:
    cur.execute("""
        INSERT INTO konular (ders, konu_adi, yanlis_sayisi, tarih)
        VALUES (?, ?, ?, date('now'))
    """, (ders, konu, yanlis))

conn.commit()
conn.close()
print("Konular tablosu oluşturuldu ve örnek veriler eklendi.")