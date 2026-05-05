from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import date, timedelta
import math  # <--- BU SATIRI EKLEYİN

import os

database_url = os.environ.get("DATABASE_URL")

if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url

app = Flask(__name__)
app.secret_key = "kpss_2026_farukomer_guvenlik"

KULLANICI_ADI = "farukomer.44"
PAROLA = "15temmuz"
NOTLAR_SIFRE = "vicecity_44"
# Jinja2 filter'ı ekleyelim
def jinja2_filter_date_diff(date_str):
    """Tarih farkını gün olarak hesaplayan filter"""
    try:
        from datetime import date
        target_date = date.fromisoformat(date_str)
        today = date.today()
        return (today - target_date).days
    except:
        return 0

# App'e filter'ı ekleyelim
app.jinja_env.filters['date_diff'] = jinja2_filter_date_diff

# app.py'ye bu filter'ı ekleyin (diğer filter'ların yanına)
def format_date(date_str):
    """YYYY-MM-DD formatını DD.MM.YYYY'ye çevir"""
    try:
        from datetime import datetime
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%d.%m.%Y")
    except:
        return date_str

app.jinja_env.filters['format_date'] = format_date

# String'den date'e çevirme için
def to_date(date_str):
    from datetime import date
    return date.fromisoformat(date_str)

app.jinja_env.filters['to_date'] = to_date

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if (
            request.form["username"] == KULLANICI_ADI and
            request.form["password"] == PAROLA
        ):
            session["login"] = True
            return redirect("/dashboard")
    return render_template("login.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if not session.get("login"):
        return redirect("/")

    basvuru_tarihi = date(2026, 7, 1)
    sinav_tarihi = date(2026, 9, 6)
    bugun = date.today()
    bugun_str = bugun.isoformat()

    # 4 AYLIK HEDEF BİTİŞ TARİHİ: 15.05.2026
    hedef_bitis_tarihi = date(2026, 5, 15)

    # Sınava kalan gün
    kalan_gun = max((sinav_tarihi - bugun).days, 0)

    # 4 aylık hedef için kalan gün (15.05.2026'ya kadar)
    hedef_kalan_gun = max((hedef_bitis_tarihi - bugun).days, 0)

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # -------- DERS / SAYFA BİLGİLERİ --------
    cur.execute("SELECT ders, toplam_sayfa, calisilan_sayfa FROM dersler")
    ders_listesi = cur.fetchall()

    toplam_sayfa = sum(d[1] for d in ders_listesi)
    calisilan_sayfa = sum(d[2] for d in ders_listesi)
    kalan_sayfa = toplam_sayfa - calisilan_sayfa

    # -------- SON 7 GÜNLÜK ORTALAMA ÇALIŞMA TEMPOSU --------
    try:
        cur.execute("""
            SELECT AVG(toplam_sayfa)
            FROM gunluk_calisma
            WHERE tarih >= date('now', '-7 days')
        """)
        sonuc = cur.fetchone()
        son_7_gun_ortalama = round(sonuc[0] if sonuc and sonuc[0] else 0, 2)
    except:
        son_7_gun_ortalama = 0

    # Eğer son 7 gün verisi yoksa, genel ortalamayı hesapla
    if son_7_gun_ortalama <= 0:
        # Toplam çalışılan gün sayısını bul (sorular tablosundan farklı tarihler)
        cur.execute("SELECT COUNT(DISTINCT tarih) FROM sorular WHERE tarih <= ?", (bugun_str,))
        calisilan_gun_sayisi = cur.fetchone()[0] or 1

        if calisilan_gun_sayisi > 0:
            son_7_gun_ortalama = round(calisilan_sayfa / calisilan_gun_sayisi, 2)
        else:
            son_7_gun_ortalama = 0

    # -------- TAHMİNİ BİTİŞ TARİHİ HESAPLAMA (GENEL ORTALAMA İLE) --------
    # Başlangıçtan itibaren geçen gün sayısı
    calisma_baslangic = date(2026, 1, 15)
    gecen_gun = max((bugun - calisma_baslangic).days, 1)

    # Genel ortalama tempo: toplam çalışılan sayfa / geçen gün sayısı
    genel_ortalama_tempo = calisilan_sayfa / gecen_gun if gecen_gun > 0 else 0

    if genel_ortalama_tempo > 0:
        # Tahmini kalan gün = kalan sayfa / genel ortalama tempo
        tahmini_kalan_gun = int(kalan_sayfa / genel_ortalama_tempo)

        # Kalan sayfa tam bölünmüyorsa 1 gün ekle
        if kalan_sayfa % genel_ortalama_tempo > 0:
            tahmini_kalan_gun += 1

        # Tahmini bitiş tarihi
        tahmini_bitis_tarihi = bugun + timedelta(days=tahmini_kalan_gun)
        tahmini_bitis_tarihi_str = tahmini_bitis_tarihi.strftime("%d.%m.%Y")

        # Hedef bitiş tarihi (15.05.2026) ile fark
        gun_farki = (tahmini_bitis_tarihi - hedef_bitis_tarihi).days
    else:
        tahmini_kalan_gun = 0
        tahmini_bitis_tarihi_str = "Hesaplanamadı"
        gun_farki = 0

    # -------- DİNAMİK SAYFA HEDEFİ --------
    toplam_calisilacak_gun = 120

    # Bugüne kadar geçen gün sayısı (15.01.2026'dan itibaren)
    calisma_baslangic = date(2026, 1, 15)
    gecen_gun = max((bugun - calisma_baslangic).days, 0)

    # Bugüne kadar çalışılması gereken sayfa
    bugune_kadar_gereken = round((toplam_sayfa / toplam_calisilacak_gun) * gecen_gun, 2)

    # Açık: Bugüne kadar çalışılması gereken - şu ana kadar çalışılan
    acik_sayfa = round(bugune_kadar_gereken - calisilan_sayfa, 2)
    telafi_gerekiyor_sayfa = acik_sayfa > 0

    # 15.05.2026'ya kalan gün
    kalan_hedef_gunu = max(hedef_kalan_gun, 1)

    # İdeal günlük hedef (açık yoksa)
    ideal_gunluk_hedef = round(kalan_sayfa / kalan_hedef_gunu, 2) if kalan_hedef_gunu > 0 else 0

    # Telafi ile birlikte günlük hedef
    if telafi_gerekiyor_sayfa and kalan_hedef_gunu > 0:
        telafi_gunluk = round(acik_sayfa / kalan_hedef_gunu, 2)
        final_gunluk_hedef_sayfa = round(ideal_gunluk_hedef + telafi_gunluk, 2)
    else:
        final_gunluk_hedef_sayfa = ideal_gunluk_hedef

    # Realist hedef (%10 fazlası)
    realist_gunluk_hedef = round(final_gunluk_hedef_sayfa * 1.1, 2)

    # İlerleme yüzdesi
    ilerleme_yuzdesi = round((calisilan_sayfa / toplam_sayfa) * 100, 1) if toplam_sayfa > 0 else 0

    # Planlanan ilerleme
    planlanan_ilerleme = round((gecen_gun / toplam_calisilacak_gun) * 100, 1) if toplam_calisilacak_gun > 0 else 0

    # Fark: Gerçek ilerleme - Planlanan ilerleme
    ilerleme_farki = round(ilerleme_yuzdesi - planlanan_ilerleme, 1)

    # -------- ÇALIŞMA DURUMUNA GÖRE ANALİZ --------
    if son_7_gun_ortalama > 0:
        tempo_orani = round((son_7_gun_ortalama / final_gunluk_hedef_sayfa) * 100, 1) if final_gunluk_hedef_sayfa > 0 else 0
    else:
        tempo_orani = 0

    # Durum belirleme
    if ilerleme_farki >= 5 and tempo_orani >= 100:
        sayfa_durum = "iyi"
    elif ilerleme_farki >= -5 and tempo_orani >= 80:
        sayfa_durum = "orta"
    else:
        sayfa_durum = "risk"

    # -------- DİNAMİK SORU HEDEFİ --------
    # Bugün çözülen soru sayısını al
    cur.execute("""
        SELECT SUM(dogru + yanlis)
        FROM sorular
        WHERE tarih = ?
    """, (bugun_str,))
    result = cur.fetchone()
    bugun_cozulen_soru = result[0] if result and result[0] else 0

    # Toplam çözülen soru
    cur.execute("SELECT SUM(dogru + yanlis) FROM sorular")
    result = cur.fetchone()
    toplam_cozulen_soru = result[0] if result and result[0] else 0

    # -------- UZUN VADELİ SORU HEDEFLERİ (10.000 ve 20.000) --------
    hedef_10000 = 10000
    hedef_20000 = 20000

    kalan_10000 = max(hedef_10000 - toplam_cozulen_soru, 0)
    kalan_20000 = max(hedef_20000 - toplam_cozulen_soru, 0)

    # İlerleme yüzdeleri
    ilerleme_10000 = round((toplam_cozulen_soru / hedef_10000) * 100, 1) if hedef_10000 > 0 else 0
    ilerleme_20000 = round((toplam_cozulen_soru / hedef_20000) * 100, 1) if hedef_20000 > 0 else 0

    # GENEL ORTALAMA HESAPLAMA (başlangıçtan bugüne)
    baslangic_tarihi = date(2026, 1, 15)
    gecen_gun_sayisi = max((bugun - baslangic_tarihi).days, 1)

    # Toplam çözülen soru / geçen gün sayısı = genel günlük ortalama
    genel_gunluk_ortalama = round(toplam_cozulen_soru / gecen_gun_sayisi, 1) if toplam_cozulen_soru > 0 else 0

    # Uzun vadeli hedefler için tahmini bitiş tarihleri (GENEL ORTALAMA ile)
    if genel_gunluk_ortalama > 0:
        # 10.000 soru için
        tahmini_gun_10000 = int(kalan_10000 / genel_gunluk_ortalama)
        if kalan_10000 % genel_gunluk_ortalama > 0:
            tahmini_gun_10000 += 1
        tahmini_bitis_10000 = bugun + timedelta(days=tahmini_gun_10000)
        tahmini_bitis_10000_str = tahmini_bitis_10000.strftime("%d.%m.%Y")

        # 20.000 soru için
        tahmini_gun_20000 = int(kalan_20000 / genel_gunluk_ortalama)
        if kalan_20000 % genel_gunluk_ortalama > 0:
            tahmini_gun_20000 += 1
        tahmini_bitis_20000 = bugun + timedelta(days=tahmini_gun_20000)
        tahmini_bitis_20000_str = tahmini_bitis_20000.strftime("%d.%m.%Y")

        # Gereken ortalama hesaplamaları
        gereken_ortalama_10000 = round(kalan_10000 / tahmini_gun_10000, 1) if tahmini_gun_10000 > 0 else 0
        gereken_ortalama_20000 = round(kalan_20000 / tahmini_gun_20000, 1) if tahmini_gun_20000 > 0 else 0
    else:
        tahmini_gun_10000 = 0
        tahmini_bitis_10000_str = "Hesaplanamadı"
        tahmini_gun_20000 = 0
        tahmini_bitis_20000_str = "Hesaplanamadı"
        gereken_ortalama_10000 = 0
        gereken_ortalama_20000 = 0

    # Son 7 günlük ortalama (bilgi amaçlı)
    cur.execute("""
        SELECT SUM(dogru + yanlis)
        FROM sorular
        WHERE tarih >= date('now', '-7 days')
    """)
    result = cur.fetchone()
    haftalik_soru = result[0] if result and result[0] else 0
    son_7_gun_ortalama_soru = round(haftalik_soru / 7, 1) if haftalik_soru > 0 else 0

    # Günlük hedef tablosundan verileri al
    gunluk_hedef_sayi = 100
    acik_soru = 0
    tasinan_acik = 0
    yarin_hedefi = 100

    try:
        cur.execute("""
            SELECT hedef_soru, cozulen_soru, acik_soru, tasinan_acik
            FROM gunluk_hedef
            WHERE tarih = ?
        """, (bugun_str,))
        hedef_kaydi = cur.fetchone()

        if hedef_kaydi:
            gunluk_hedef_sayi, kayitli_cozulen, acik_soru, tasinan_acik = hedef_kaydi

            if bugun_cozulen_soru != kayitli_cozulen:
                yeni_acik = max(gunluk_hedef_sayi - bugun_cozulen_soru, 0)
                cur.execute("""
                    UPDATE gunluk_hedef
                    SET cozulen_soru = ?, acik_soru = ?
                    WHERE tarih = ?
                """, (bugun_cozulen_soru, yeni_acik, bugun_str))
                conn.commit()
                acik_soru = yeni_acik
        else:
            acik_soru = max(100 - bugun_cozulen_soru, 0)
            cur.execute("""
                INSERT INTO gunluk_hedef (tarih, hedef_soru, cozulen_soru, acik_soru)
                VALUES (?, ?, ?, ?)
            """, (bugun_str, 100, bugun_cozulen_soru, acik_soru))
            conn.commit()

    except Exception as e:
        print(f"Günlük hedef hatası: {e}")
        acik_soru = max(100 - bugun_cozulen_soru, 0)

    # Yarına taşınacak açık
    yarina_tasinan = acik_soru
    yarin_hedefi = 100 + yarina_tasinan

    # Geçmiş açıklar (son 7 gün)
    try:
        cur.execute("""
            SELECT SUM(acik_soru)
            FROM gunluk_hedef
            WHERE tarih >= date('now', '-7 days')
        """)
        result = cur.fetchone()
        toplam_acik_7gun = result[0] if result and result[0] else 0
    except:
        toplam_acik_7gun = 0

    # Soru durumu
    tamamlanma_yuzdesi = 0
    if gunluk_hedef_sayi > 0:
        tamamlanma_yuzdesi = min(int((bugun_cozulen_soru / gunluk_hedef_sayi) * 100), 100)

    if tamamlanma_yuzdesi >= 100:
        soru_durum = "iyi"
    elif tamamlanma_yuzdesi >= 70:
        soru_durum = "orta"
    else:
        soru_durum = "risk"

    conn.close()

    # -------- TEMPO ORANI HESAPLAMALARI --------
    tempo_orani_genel = round((genel_gunluk_ortalama / final_gunluk_hedef_sayfa) * 100, 1) if final_gunluk_hedef_sayfa > 0 else 0

    return render_template(
        "dashboard.html",
        basvuru_tarihi=basvuru_tarihi.strftime("%d.%m.%Y"),
        sinav_tarihi=sinav_tarihi.strftime("%d.%m.%Y"),
        kalan_gun=kalan_gun,
        hedef_bitis_tarihi=hedef_bitis_tarihi.strftime("%d.%m.%Y"),
        hedef_kalan_gun=hedef_kalan_gun,
        toplam_calisilacak_gun=toplam_calisilacak_gun,
        gecen_gun=gecen_gun,
        dersler=ders_listesi,
        toplam_sayfa=toplam_sayfa,
        calisilan_sayfa=calisilan_sayfa,
        kalan_sayfa=kalan_sayfa,
        gunluk_sayfa_hedef=final_gunluk_hedef_sayfa,
        ideal_gunluk_hedef=ideal_gunluk_hedef,
        realist_gunluk_hedef=realist_gunluk_hedef,
        acik=acik_sayfa,
        telafi_gerekiyor=telafi_gerekiyor_sayfa,
        ilerleme_yuzdesi=ilerleme_yuzdesi,
        planlanan_ilerleme=planlanan_ilerleme,
        ilerleme_farki=ilerleme_farki,
        son_7_gun_ortalama=son_7_gun_ortalama,
        tahmini_bitis_tarihi=tahmini_bitis_tarihi_str,
        tahmini_kalan_gun=tahmini_kalan_gun,
        gun_farki=gun_farki,
        tempo_orani=tempo_orani,
        tempo_orani_genel=tempo_orani_genel,
        genel_ortalama_tempo=genel_ortalama_tempo,  # <--- BURASI ÇOK ÖNEMLİ
        bugun_soru=bugun_cozulen_soru,
        toplam_soru=toplam_cozulen_soru,
        gunluk_hedef=gunluk_hedef_sayi,
        acik_soru=acik_soru,
        yarin_hedefi=yarin_hedefi,
        tasinan_acik=yarina_tasinan,
        toplam_acik_7gun=toplam_acik_7gun,
        soru_yuzde=tamamlanma_yuzdesi,
        soru_durum=soru_durum,
        hedef_10000=hedef_10000,
        hedef_20000=hedef_20000,
        kalan_10000=kalan_10000,
        kalan_20000=kalan_20000,
        ilerleme_10000=ilerleme_10000,
        ilerleme_20000=ilerleme_20000,
        tahmini_bitis_10000=tahmini_bitis_10000_str,
        tahmini_bitis_20000=tahmini_bitis_20000_str,
        tahmini_gun_10000=tahmini_gun_10000,
        tahmini_gun_20000=tahmini_gun_20000,
        genel_gunluk_ortalama=genel_gunluk_ortalama,
        son_7_gun_ortalama_soru=son_7_gun_ortalama_soru,
        gereken_ortalama_10000=gereken_ortalama_10000,
        gereken_ortalama_20000=gereken_ortalama_20000,
        gecen_gun_sayisi=gecen_gun_sayisi,
        gunluk_gerekli=final_gunluk_hedef_sayfa,
        konu_durum=sayfa_durum,
        motivasyon=sayfa_durum,
        motivasyon_mesaj="KPSS 2026'ya hazırlanıyorum!",
    )
# <--- BURADA FONKSİYON BİTMELİ, EKSTRA KOD OLMAMALI

# ---------------- SAYFA EKLE ----------------
@app.route("/sayfa_ekle", methods=["POST"])
def sayfa_ekle():
    if not session.get("login"):
        return redirect("/")

    ders = request.form["ders"]
    eklenen = int(request.form["sayfa"])
    bugun = date.today().isoformat()

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # Mevcut değerleri al
    cur.execute(
        "SELECT calisilan_sayfa, toplam_sayfa FROM dersler WHERE ders = ?",
        (ders,)
    )
    mevcut, toplam = cur.fetchone()

    # Toplamı geçmemek için kontrol
    yeni = min(mevcut + eklenen, toplam)

    # Dersi güncelle
    cur.execute(
        "UPDATE dersler SET calisilan_sayfa = ? WHERE ders = ?",
        (yeni, ders)
    )

    # Günlük çalışma geçmişini güncelle
    try:
        # Bugün için kayıt var mı kontrol et
        cur.execute(
            "SELECT toplam_sayfa FROM gunluk_calisma WHERE tarih = ?",
            (bugun,)
        )
        kayit = cur.fetchone()

        if kayit:
            # Kayıt varsa güncelle
            yeni_toplam = kayit[0] + eklenen
            cur.execute(
                "UPDATE gunluk_calisma SET toplam_sayfa = ? WHERE tarih = ?",
                (yeni_toplam, bugun)
            )
        else:
            # Kayıt yoksa oluştur
            cur.execute(
                "INSERT INTO gunluk_calisma (tarih, toplam_sayfa) VALUES (?, ?)",
                (bugun, eklenen)
            )
    except Exception as e:
        print(f"Günlük çalışma kaydı hatası: {e}")
        # Tablo yoksa oluştur
        try:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS gunluk_calisma (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tarih DATE UNIQUE,
                    toplam_sayfa INTEGER DEFAULT 0
                )
            """)
            cur.execute(
                "INSERT INTO gunluk_calisma (tarih, toplam_sayfa) VALUES (?, ?)",
                (bugun, eklenen)
            )
        except:
            pass  # Hata olursa devam et

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ---------------- SORU TAKİBİ ----------------
@app.route("/soru", methods=["GET", "POST"])
def soru():
    if not session.get("login"):
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # EKLEME
    if request.method == "POST":
        ders = request.form["ders"]
        konu = request.form.get("konu", "").strip()
        dogru = int(request.form["dogru"])
        yanlis = int(request.form["yanlis"])
        net = dogru - (yanlis * 0.25)
        tarih = date.today().isoformat()

        # SADECE sorular tablosuna ekle
        # konular tablosuna EKLEME - artık zayıf_konular() sorular tablosundan okuyor
        cur.execute("""
            INSERT INTO sorular (ders, konu, dogru, yanlis, net, tarih)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (ders, konu, dogru, yanlis, net, tarih))

        conn.commit()

    # ... (diğer kodlar aynı) ...

    # LİSTE - Tüm soruları al
    cur.execute("""
        SELECT id, ders, konu, dogru, yanlis, net, tarih
        FROM sorular
        ORDER BY tarih DESC, id DESC
    """)
    sorular = cur.fetchall()

    # ZAYIF KONULAR İÇİN ÖNİZLEME (soru sayfasında da gösterelim)
    cur.execute("""
        SELECT ders, konu, SUM(yanlis) as toplam_yanlis
        FROM sorular
        WHERE konu IS NOT NULL AND konu != '' AND yanlis > 0
        GROUP BY ders, konu
        ORDER BY SUM(yanlis) DESC
        LIMIT 5
    """)
    zayif_konular_onizleme = cur.fetchall()

    # Grafik için veriler
    cur.execute("""
        SELECT ders, SUM(net) as toplam_net
        FROM sorular
        WHERE net IS NOT NULL
        GROUP BY ders
        HAVING SUM(net) IS NOT NULL
    """)
    ders_netleri = cur.fetchall()

    dersler_grafik = []
    netler_grafik = []

    for d in ders_netleri:
        if d[0] and d[1] is not None:
            dersler_grafik.append(d[0])
            netler_grafik.append(float(d[1]))

    conn.close()

    return render_template(
        "soru.html",
        sorular=sorular,
        dersler=dersler_grafik,
        netler=netler_grafik,
        zayif_konular=zayif_konular_onizleme
    )

# ---------------- SORU SİL ----------------
@app.route("/soru_sil/<int:id>")
def soru_sil(id):
    if not session.get("login"):
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("DELETE FROM sorular WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect("/soru")

# ---------------- GRAFİKLER ----------------
@app.route("/grafikler")
def grafikler():
    if not session.get("login"):
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # Tüm dersleri ve ilerlemelerini al
    cur.execute("SELECT ders, toplam_sayfa, calisilan_sayfa FROM dersler")
    dersler = cur.fetchall()

    # Grafikler için verileri hazırla
    ders_adlari = []
    yuzdeler = []

    for ders in dersler:
        ders_ad = ders[0]
        toplam = ders[1]
        calisilan = ders[2]

        # İlerleme yüzdesini hesapla (0'dan küçük olmamalı)
        yuzde = 0
        if toplam > 0:
            yuzde = round((calisilan / toplam) * 100, 1)

        ders_adlari.append(ders_ad)
        yuzdeler.append(yuzde)

    conn.close()

    return render_template(
        "grafikler.html",
        dersler=dersler,  # Tek tek grafikler için
        ders_adlari=ders_adlari,  # Tüm dersler grafiği için
        yuzdeler=yuzdeler  # Tüm dersler grafiği için
    )

# ---------------- ZAYIF KONULAR ----------------
@app.route("/zayif_konular")
def zayif_konular():
    if not session.get("login"):
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    konular = []
    ders_bazli_istatistikler = []  # YENİ: Ders bazlı istatistikler

    try:
        # KONU BAZLI SORGULAMA (mevcut)
        cur.execute("""
            SELECT
                ders,
                konu,
                SUM(yanlis) as toplam_yanlis,
                SUM(dogru + yanlis) as toplam_soru,
                ROUND(AVG(net), 2) as ortalama_net,
                COUNT(DISTINCT tarih) as calisilan_gun,
                ROUND(
                    CAST(SUM(yanlis) AS FLOAT) /
                    NULLIF(SUM(dogru + yanlis), 0) * 100,
                    1
                ) as yanlis_orani
            FROM sorular
            WHERE konu IS NOT NULL
                AND konu != ''
                AND konu != 'Konu Bilgisi Yok'
                AND tarih >= '2026-01-10'
            GROUP BY ders, konu
            HAVING SUM(dogru + yanlis) >= 20
                AND SUM(yanlis) > 0
                AND CAST(SUM(yanlis) AS FLOAT) / NULLIF(SUM(dogru + yanlis), 0) > 0.10
            ORDER BY
                yanlis_orani DESC,
                SUM(yanlis) DESC,
                AVG(net) ASC
            LIMIT 25
        """)

        sonuclar = cur.fetchall()

        for sonuc in sonuclar:
            ders, konu, toplam_yanlis, toplam_soru, ortalama_net, calisilan_gun, yanlis_orani = sonuc

            cur.execute("SELECT MAX(tarih) FROM sorular WHERE ders = ? AND konu = ?", (ders, konu))
            son_tarih = cur.fetchone()[0] or "Bilinmiyor"

            ortalama_gunluk_yanlis = round(toplam_yanlis / calisilan_gun, 1) if calisilan_gun > 0 else 0
            toplam_dogru = toplam_soru - toplam_yanlis
            basari_orani = round((toplam_dogru / toplam_soru) * 100, 1) if toplam_soru > 0 else 0

            konular.append((
                ders, konu, toplam_yanlis, toplam_soru, ortalama_net, yanlis_orani,
                son_tarih, calisilan_gun, ortalama_gunluk_yanlis, toplam_dogru, basari_orani
            ))

        # YENİ: DERS BAZLI İSTATİSTİKLER
        cur.execute("""
            SELECT
                ders,
                SUM(yanlis) as toplam_yanlis,
                SUM(dogru + yanlis) as toplam_soru,
                SUM(dogru) as toplam_dogru,
                ROUND(AVG(net), 2) as ortalama_net,
                COUNT(DISTINCT konu) as farkli_konu_sayisi,
                COUNT(DISTINCT tarih) as calisilan_gun,
                ROUND(
                    CAST(SUM(yanlis) AS FLOAT) /
                    NULLIF(SUM(dogru + yanlis), 0) * 100,
                    1
                ) as yanlis_orani,
                ROUND(
                    CAST(SUM(dogru) AS FLOAT) /
                    NULLIF(SUM(dogru + yanlis), 0) * 100,
                    1
                ) as basari_orani
            FROM sorular
            WHERE tarih >= '2026-01-10'
            GROUP BY ders
            HAVING SUM(dogru + yanlis) >= 50  -- Ders bazlı en az 50 soru
            ORDER BY
                CAST(SUM(yanlis) AS FLOAT) / NULLIF(SUM(dogru + yanlis), 0) DESC
        """)

        ders_sonuclari = cur.fetchall()

        for ders_sonuc in ders_sonuclari:
            (ders, toplam_yanlis, toplam_soru, toplam_dogru, ortalama_net,
             farkli_konu, calisilan_gun, yanlis_orani, basari_orani) = ders_sonuc

            # Bu derse ait en zayıf 3 konuyu bul
            cur.execute("""
                SELECT konu,
                       SUM(yanlis) as konu_yanlis,
                       SUM(dogru + yanlis) as konu_soru,
                       ROUND(
                           CAST(SUM(yanlis) AS FLOAT) /
                           NULLIF(SUM(dogru + yanlis), 0) * 100,
                           1
                       ) as konu_yanlis_orani
                FROM sorular
                WHERE ders = ?
                    AND konu IS NOT NULL
                    AND konu != ''
                    AND tarih >= '2026-01-10'
                GROUP BY konu
                HAVING SUM(dogru + yanlis) >= 10
                ORDER BY
                    CAST(SUM(yanlis) AS FLOAT) / NULLIF(SUM(dogru + yanlis), 0) DESC
                LIMIT 3
            """, (ders,))

            zayif_konular = cur.fetchall()

            ders_bazli_istatistikler.append((
                ders, toplam_yanlis, toplam_soru, toplam_dogru, ortalama_net,
                farkli_konu, calisilan_gun, yanlis_orani, basari_orani,
                zayif_konular  # Bu dersin en zayıf 3 konusu
            ))

    except Exception as e:
        print(f"Zayıf konular hatası: {e}")
        konular = []
        ders_bazli_istatistikler = []

    conn.close()

    if not konular:
        konular = [
            ("Henüz veri yok", "10.01.2026'dan itibaren", 0, 0, 0, 0, "-", 0, 0, 0, 0, 0),
        ]

    return render_template(
        "zayif_konular.html",
        konular=konular,
        ders_bazli=ders_bazli_istatistikler  # YENİ: Template'e gönder
    )

@app.route("/notlar", methods=["GET", "POST"])
def notlar_giris():
    if request.method == "POST":
        if request.form.get("sifre") == NOTLAR_SIFRE:
            session["notlar_giris"] = True
            return redirect("/notlar_liste")
        else:
            return render_template("notlar_giris.html", hata="Şifre yanlış")

    if session.get("notlar_giris"):
        return redirect("/notlar_liste")

    return render_template("notlar_giris.html")

@app.route("/notlar_tablo_olustur")
def notlar_tablo_olustur():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS notlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih DATE NOT NULL,
            not_metni TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    return "Notlar tablosu oluşturuldu"

@app.route("/notlar_liste", methods=["GET", "POST"])
def notlar_liste():
    if not session.get("notlar_giris"):
        return redirect("/notlar")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    if request.method == "POST":
        tarih = request.form["tarih"]
        not_metni = request.form["not_metni"].strip()
        if tarih and not_metni:
            cur.execute(
                "INSERT INTO notlar (tarih, not_metni) VALUES (?, ?)",
                (tarih, not_metni)
            )
            conn.commit()

    cur.execute("""
        SELECT id, tarih, not_metni
        FROM notlar
        ORDER BY tarih DESC, id DESC
    """)
    notlar = cur.fetchall()

    conn.close()
    return render_template("notlar.html", notlar=notlar)

@app.route("/not_duzenle/<int:id>", methods=["GET", "POST"])
def not_duzenle(id):
    if not session.get("notlar_giris"):
        return redirect("/notlar")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    if request.method == "POST":
        yeni_not = request.form["not_metni"]
        cur.execute("UPDATE notlar SET not_metni = ? WHERE id = ?", (yeni_not, id))
        conn.commit()
        conn.close()
        return redirect("/notlar_liste")

    cur.execute("SELECT id, tarih, not_metni FROM notlar WHERE id = ?", (id,))
    not_bilgisi = cur.fetchone()
    conn.close()

    return render_template("not_duzenle.html", not_bilgisi=not_bilgisi)

@app.route("/not_sil/<int:id>")
def not_sil(id):
    if not session.get("notlar_giris"):
        return redirect("/notlar")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM notlar WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect("/notlar_liste")

@app.route("/notlar_cikis")
def notlar_cikis():
    session.pop("notlar_giris", None)
    return redirect("/dashboard")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
