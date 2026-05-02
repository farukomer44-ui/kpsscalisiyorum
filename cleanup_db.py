# cleanup_db.py dosyası oluşturun:
import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

print("Veritabanı temizleniyor...")

# konular tablosundaki TÜM verileri sil
cur.execute("DELETE FROM konular")
print("✓ konular tablosu temizlendi")

# gunluk_hedef tablosunu temizle (isteğe bağlı)
cur.execute("DELETE FROM gunluk_hedef")
print("✓ gunluk_hedef tablosu temizlendi")

conn.commit()
conn.close()
print("\n✅ Veritabanı temizlendi!")