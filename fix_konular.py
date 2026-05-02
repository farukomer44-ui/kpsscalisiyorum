# fix_konular.py dosyası oluşturun:
import sqlite3
from datetime import datetime

conn = sqlite3.connect("database.db")
cur = conn.cursor()

print("Zayıf konular veritabanı düzeltiliyor...")

# 1. Önce konular tablosunu tamamen temizleyelim
cur.execute("DELETE FROM konular")
print("✓ konular tablosu temizlendi")

# 2. sorular tablosundan DOĞRU şekilde konu istatistiklerini oluşturalım
# Grup by ile aynı gün aynı konu için TEK kayıt oluşturalım
cur.execute("""
    SELECT 
        ders,
        konu,
        tarih,
        SUM(yanlis) as gunluk_yanlis,
        SUM(dogru + yanlis) as gunluk_toplam_soru
    FROM sorular
    WHERE konu IS NOT NULL 
        AND konu != ''
        AND konu != 'Konu Bilgisi Yok'
    GROUP BY ders, konu, tarih
    HAVING SUM(yanlis) > 0
    ORDER BY tarih, ders, konu
""")

gruplanmis_sorular = cur.fetchall()
print(f"✓ {len(gruplanmis_sorular)} grup kayıt bulundu")

# 3. Doğru şekilde konular tablosuna ekleyelim
toplam_eklenen = 0
for ders, konu, tarih, gunluk_yanlis, gunluk_toplam in gruplanmis_sorular:
    try:
        cur.execute("""
            INSERT INTO konular (ders, konu_adi, yanlis_sayisi, tarih)
            VALUES (?, ?, ?, ?)
        """, (ders, konu, gunluk_yanlis, tarih))
        toplam_eklenen += 1
    except Exception as e:
        print(f"Kayıt eklenirken hata: {e}")

conn.commit()

# 4. Kontrol: Toplam yanlış sayılarını karşılaştıralım
print("\n📊 KONTROL:")
print("-" * 50)

# sorular tablosundan toplam
cur.execute("""
    SELECT ders, konu, SUM(yanlis) as gercek_toplam_yanlis
    FROM sorular
    WHERE konu IS NOT NULL AND konu != ''
    GROUP BY ders, konu
    HAVING SUM(yanlis) > 0
    ORDER BY SUM(yanlis) DESC
    LIMIT 10
""")
soru_toplamlari = cur.fetchall()

print("sorular tablosu - Top 10 Yanlış Konu:")
for ders, konu, toplam in soru_toplamlari:
    print(f"  {ders} - {konu}: {toplam} yanlış")

# konular tablosundan toplam
cur.execute("""
    SELECT ders, konu_adi, SUM(yanlis_sayisi) as konu_tablo_toplam
    FROM konular
    GROUP BY ders, konu_adi
    ORDER BY SUM(yanlis_sayisi) DESC
    LIMIT 10
""")
konu_toplamlari = cur.fetchall()

print("\nkonular tablosu - Top 10 Yanlış Konu:")
for ders, konu, toplam in konu_toplamlari:
    print(f"  {ders} - {konu}: {toplam} yanlış")

# 5. Yanlış olan kayıtları bulalım (fark > %10)
print("\n🔍 PROBLEMLİ KAYITLAR (Fark > %10):")
print("-" * 50)

for soru_kaydi in soru_toplamlari:
    ders, konu, gercek_toplam = soru_kaydi
    
    cur.execute("""
        SELECT SUM(yanlis_sayisi) 
        FROM konular 
        WHERE ders = ? AND konu_adi = ?
    """, (ders, konu))
    
    konu_tablo_toplam = cur.fetchone()[0] or 0
    
    if gercek_toplam > 0:
        fark = abs(konu_tablo_toplam - gercek_toplam)
        fark_yuzdesi = (fark / gercek_toplam) * 100
        
        if fark_yuzdesi > 10:  # %10'dan fazla fark varsa
            print(f"  ⚠️ {ders} - {konu}:")
            print(f"     sorular tablosu: {gercek_toplam}")
            print(f"     konular tablosu: {konu_tablo_toplam}")
            print(f"     Fark: {fark} (%{fark_yuzdesi:.1f})")

conn.close()
print(f"\n✅ Toplam {toplam_eklenen} kayıt eklendi.")
print("✅ Zayıf konular veritabanı düzeltildi.")