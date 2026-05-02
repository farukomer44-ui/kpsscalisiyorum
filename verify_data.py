# verify_data.py dosyası oluşturun:
import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

print("Veri Doğrulama Kontrolü")
print("=" * 60)

# Temel Hukuk Kavramları konusunu kontrol et
konu_adi = "Temel Hukuk Kavramları"  # Konu adını tam olarak yazın

print(f"🔍 '{konu_adi}' konusu analizi:")
print("-" * 60)

# 1. sorular tablosundan gerçek veriler
cur.execute("""
    SELECT 
        SUM(dogru) as toplam_dogru,
        SUM(yanlis) as toplam_yanlis,
        SUM(dogru + yanlis) as toplam_soru,
        COUNT(DISTINCT tarih) as calisilan_gun,
        MIN(tarih) as ilk_tarih,
        MAX(tarih) as son_tarih
    FROM sorular
    WHERE konu = ?
""", (konu_adi,))

sonuc = cur.fetchone()
if sonuc:
    toplam_dogru, toplam_yanlis, toplam_soru, calisilan_gun, ilk_tarih, son_tarih = sonuc
    
    print("📊 sorular tablosu:")
    print(f"   Toplam Doğru: {toplam_dogru or 0}")
    print(f"   Toplam Yanlış: {toplam_yanlis or 0}")
    print(f"   Toplam Soru: {toplam_soru or 0}")
    print(f"   Çalışılan Gün: {calisilan_gun or 0}")
    print(f"   İlk Tarih: {ilk_tarih or '-'}")
    print(f"   Son Tarih: {son_tarih or '-'}")
    
    if toplam_soru and toplam_soru > 0:
        yanlis_orani = (toplam_yanlis / toplam_soru) * 100
        print(f"   Yanlış Oranı: %{yanlis_orani:.1f}")

# 2. konular tablosundaki veriler
cur.execute("""
    SELECT 
        SUM(yanlis_sayisi) as konu_tablo_yanlis,
        COUNT(*) as kayit_sayisi
    FROM konular
    WHERE konu_adi = ?
""", (konu_adi,))

konu_sonuc = cur.fetchone()
if konu_sonuc:
    konu_tablo_yanlis, kayit_sayisi = konu_sonuc
    
    print(f"\n📋 konular tablosu:")
    print(f"   Toplam Yanlış: {konu_tablo_yanlis or 0}")
    print(f"   Kayıt Sayısı: {kayit_sayisi or 0}")
    
    if toplam_yanlis and konu_tablo_yanlis:
        fark = konu_tablo_yanlis - toplam_yanlis
        print(f"   Fark: {fark}")
        
        if toplam_yanlis > 0:
            fark_yuzdesi = (fark / toplam_yanlis) * 100
            print(f"   Fark Yüzdesi: %{fark_yuzdesi:.1f}")

# 3. Tüm kayıtları listele
print(f"\n📅 Tüm Kayıtlar:")
print("-" * 60)

cur.execute("""
    SELECT tarih, yanlis, dogru, (dogru + yanlis) as toplam_soru
    FROM sorular
    WHERE konu = ?
    ORDER BY tarih
""", (konu_adi,))

kayitlar = cur.fetchall()
print("   Tarih       | Yanlış | Doğru | Toplam")
print("   " + "-" * 35)

for tarih, yanlis, dogru, toplam in kayitlar:
    print(f"   {tarih} | {yanlis:6d} | {dogru:5d} | {toplam:6d}")

conn.close()
print("\n✅ Kontrol tamamlandı.")