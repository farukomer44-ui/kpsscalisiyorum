# db_add_history.py dosyası oluşturun:
import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

# Çalışma geçmişi tablosu
cur.execute("""
CREATE TABLE IF NOT EXISTS gunluk_calisma (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tarih DATE UNIQUE,
    toplam_sayfa INTEGER DEFAULT 0,
    toplam_soru INTEGER DEFAULT 0
)
""")

print("gunluk_calisma tablosu oluşturuldu.")
conn.commit()
conn.close()