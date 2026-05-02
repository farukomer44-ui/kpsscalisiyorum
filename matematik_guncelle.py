# matematik_guncelle.py dosyası oluşturun:
import sqlite3

conn = sqlite3.connect("database.db")
cur = conn.cursor()

# Yeni değeri burada değiştirin
YENI_TOPLAM_SAYFA = 406  # İstediğiniz sayıyı girin

# Kontrol: Çalışılan sayfadan küçük olmamalı
cur.execute("SELECT calisilan_sayfa FROM dersler WHERE ders = 'Matematik'")
calisilan = cur.fetchone()[0]

if YENI_TOPLAM_SAYFA < calisilan:
    print(f"HATA: Yeni toplam ({YENI_TOPLAM_SAYFA}) çalışılandan ({calisilan}) küçük!")
    print("Çalışılan sayfayı da güncellemek için 1, iptal için 2 seçin.")

    secim = input("Seçiminiz (1/2): ")

    if secim == "1":
        cur.execute("""
            UPDATE dersler
            SET toplam_sayfa = ?, calisilan_sayfa = ?
            WHERE ders = 'Matematik'
        """, (YENI_TOPLAM_SAYFA, YENI_TOPLAM_SAYFA))
        print("✓ Hem toplam hem çalışılan sayfa güncellendi.")
    else:
        print("İşlem iptal edildi.")
        conn.close()
        exit()
else:
    # Normal güncelleme
    cur.execute("UPDATE dersler SET toplam_sayfa = ? WHERE ders = 'Matematik'", (YENI_TOPLAM_SAYFA,))
    print("✓ Matematik toplam sayfası güncellendi.")

conn.commit()

# Sonucu göster
cur.execute("SELECT * FROM dersler WHERE ders = 'Matematik'")
print("\nGüncel Matematik Bilgileri:")
print("-" * 40)
ders = cur.fetchone()
print(f"Ders: {ders[0]}")
print(f"Toplam Sayfa: {ders[1]}")
print(f"Çalışılan Sayfa: {ders[2]}")
print(f"Kalan Sayfa: {ders[1] - ders[2]}")

conn.close()