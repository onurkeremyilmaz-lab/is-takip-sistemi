import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime
import os

# ============================================================
# SAYFA AYARLARI
# ============================================================

st.set_page_config(
    page_title="İşlerim",
    page_ticon="8914570C-3748-4E4A-BBC5-2AA43B821FD5.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# VERİTABANI
# ============================================================

DB = "isler.db"

def baglanti():
    return sqlite3.connect(DB)

def tablo_olustur():
    conn = baglanti()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS isler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            is_adi TEXT NOT NULL,
            kategori TEXT,
            oncelik TEXT,
            termin TEXT,
            durum TEXT,
            beklenen TEXT,
            notlar TEXT,
            olusturma TEXT,
            tamamlanma TEXT
        )
    """)

    conn.commit()
    conn.close()

tablo_olustur()

# ============================================================
# SABİT LİSTELER
# ============================================================

KATEGORILER = [
    "Saha / İSG",
    "Risk Değerlendirmesi",
    "Aksiyon Takibi",
    "Hastane Süreçleri",
    "Revir Süreçleri",
    "Satınalma Süreçleri",
    "Eğitim Süreçleri",
    "Toplantı",
    "Evrak / Doküman",
    "E-posta",
    "Diğer"
]

ONCELIKLER = [
    "🔴 Kritik",
    "🟠 Yüksek",
    "🟡 Normal",
    "🟢 Düşük"
]

DURUMLAR = [
    "⚪ Başlanmadı",
    "🔵 Devam Ediyor",
    "🟣 Beklemede",
    "🟢 Tamamlandı"
]

# ============================================================
# VERİTABANI İŞLEMLERİ
# ============================================================

def isleri_getir():
    conn = baglanti()

    df = pd.read_sql_query(
        "SELECT * FROM isler ORDER BY id DESC",
        conn
    )

    conn.close()

    return df


def is_ekle(
    is_adi,
    kategori,
    oncelik,
    termin,
    durum,
    beklenen,
    notlar
):

    conn = baglanti()
    c = conn.cursor()

    c.execute("""
        INSERT INTO isler
        (
            is_adi,
            kategori,
            oncelik,
            termin,
            durum,
            beklenen,
            notlar,
            olusturma,
            tamamlanma
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        is_adi,
        kategori,
        oncelik,
        str(termin) if termin else "",
        durum,
        beklenen,
        notlar,
        datetime.now().strftime("%d.%m.%Y %H:%M"),
        ""
    ))

    conn.commit()
    conn.close()


def is_guncelle(
    id,
    is_adi,
    kategori,
    oncelik,
    termin,
    durum,
    beklenen,
    notlar
):

    tamamlanma = ""

    if durum == "🟢 Tamamlandı":
        tamamlanma = datetime.now().strftime("%d.%m.%Y %H:%M")

    conn = baglanti()
    c = conn.cursor()

    c.execute("""
        UPDATE isler

        SET
            is_adi = ?,
            kategori = ?,
            oncelik = ?,
            termin = ?,
            durum = ?,
            beklenen = ?,
            notlar = ?,
            tamamlanma = ?

        WHERE id = ?
    """, (
        is_adi,
        kategori,
        oncelik,
        str(termin) if termin else "",
        durum,
        beklenen,
        notlar,
        tamamlanma,
        id
    ))

    conn.commit()
    conn.close()


def is_sil(id):

    conn = baglanti()
    c = conn.cursor()

    c.execute(
        "DELETE FROM isler WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()


# ============================================================
# TERMİN HESAPLAMA
# ============================================================

def termin_durumu(row):

    if row["durum"] == "🟢 Tamamlandı":
        return "✅ Tamamlandı"

    if not row["termin"]:
        return "⚪ Termin yok"

    try:
        t = datetime.strptime(
            row["termin"],
            "%Y-%m-%d"
        ).date()
    except:
        return ""

    bugun = date.today()

    fark = (t - bugun).days

    if fark < 0:
        return f"🔴 {abs(fark)} gün gecikti"

    if fark == 0:
        return "🟠 Bugün"

    if fark == 1:
        return "🟡 Yarın"

    return f"🟢 {fark} gün kaldı"


# ============================================================
# TASARIM
# ============================================================

st.markdown("""
<style>

.block-container {
    padding-top: 1.2rem;
    padding-bottom: 5rem;
    max-width: 1100px;
}

h1 {
    font-size: 2rem !important;
}

div[data-testid="stMetric"] {
    background: rgba(128,128,128,0.08);
    border-radius: 14px;
    padding: 12px;
}

.stButton button {
    border-radius: 10px;
    min-height: 42px;
}

div[data-testid="stExpander"] {
    border-radius: 12px;
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# BAŞLIK
# ============================================================

st.title("📋 İşlerim")

st.caption(
    "Kişisel iş takip ve süreç yönetim sistemi"
)

df = isleri_getir()

# ============================================================
# DASHBOARD
# ============================================================

if not df.empty:

    df["termin_durumu"] = df.apply(
        termin_durumu,
        axis=1
    )

    toplam = len(df)

    tamamlanan = len(
        df[df["durum"] == "🟢 Tamamlandı"]
    )

    acik = toplam - tamamlanan

    geciken = len(
        df[
            df["termin_durumu"]
            .str.contains("gecikti", na=False)
        ]
    )

    bugun_sayisi = len(
        df[
            df["termin_durumu"] == "🟠 Bugün"
        ]
    )

else:

    toplam = 0
    tamamlanan = 0
    acik = 0
    geciken = 0
    bugun_sayisi = 0


c1, c2, c3, c4 = st.columns(4)

c1.metric("⚠️ Açık", acik)

c2.metric("🔴 Geciken", geciken)

c3.metric("🟠 Bugün", bugun_sayisi)

c4.metric("✅ Tamamlanan", tamamlanan)

st.divider()

# ============================================================
# MENÜ
# ============================================================

sekme1, sekme2, sekme3 = st.tabs([
    "📋 İşlerim",
    "➕ Yeni İş",
    "⚙️ Yönet"
])

# ============================================================
# İŞLERİM
# ============================================================

with sekme1:

    if df.empty:

        st.info(
            "Henüz iş eklenmedi."
        )

    else:

        arama = st.text_input(
            "🔎 İşlerde ara",
            placeholder="Kelime yaz..."
        )

        filtre1, filtre2 = st.columns(2)

        with filtre1:

            kategori_filtre = st.selectbox(
                "Kategori",
                ["Tümü"] + KATEGORILER
            )

        with filtre2:

            gorunum = st.selectbox(
                "Görünüm",
                [
                    "Açık İşler",
                    "Bugün",
                    "Gecikenler",
                    "Beklemede",
                    "Tamamlananlar",
                    "Tüm İşler"
                ]
            )

        goster = df.copy()

        if kategori_filtre != "Tümü":

            goster = goster[
                goster["kategori"] == kategori_filtre
            ]

        if gorunum == "Açık İşler":

            goster = goster[
                goster["durum"] != "🟢 Tamamlandı"
            ]

        elif gorunum == "Bugün":

            goster = goster[
                goster["termin_durumu"] == "🟠 Bugün"
            ]

        elif gorunum == "Gecikenler":

            goster = goster[
                goster["termin_durumu"]
                .str.contains("gecikti", na=False)
            ]

        elif gorunum == "Beklemede":

            goster = goster[
                goster["durum"] == "🟣 Beklemede"
            ]

        elif gorunum == "Tamamlananlar":

            goster = goster[
                goster["durum"] == "🟢 Tamamlandı"
            ]

        if arama:

            arama_kucuk = arama.lower()

            goster = goster[
                goster.apply(
                    lambda row:
                    arama_kucuk in
                    " ".join(
                        row.astype(str)
                    ).lower(),
                    axis=1
                )
            ]

        if goster.empty:

            st.info(
                "Bu filtreye uygun iş bulunamadı."
            )

        else:

            for _, row in goster.iterrows():

                baslik = (
                    f'{row["oncelik"]}  '
                    f'{row["is_adi"]}'
                )

                with st.expander(baslik):

                    st.write(
                        f'**Kategori:** {row["kategori"]}'
                    )

                    st.write(
                        f'**Durum:** {row["durum"]}'
                    )

                    st.write(
                        f'**Termin:** '
                        f'{row["termin"] if row["termin"] else "Yok"}'
                    )

                    st.write(
                        f'**Termin Durumu:** '
                        f'{row["termin_durumu"]}'
                    )

                    if row["beklenen"]:

                        st.write(
                            f'**Beklenen kişi/bölüm:** '
                            f'{row["beklenen"]}'
                        )

                    if row["notlar"]:

                        st.write(
                            f'**Not:** {row["notlar"]}'
                        )

                    st.caption(
                        f'Kayıt No: #{row["id"]} | '
                        f'Oluşturma: {row["olusturma"]}'
                    )

# ============================================================
# YENİ İŞ
# ============================================================

with sekme2:

    st.subheader("➕ Yeni İş Ekle")

    with st.form(
        "yeni_is_formu",
        clear_on_submit=True
    ):

        yeni_is = st.text_input(
            "İş *",
            placeholder="Yapılacak işi yaz..."
        )

        yeni_kategori = st.selectbox(
            "Kategori",
            KATEGORILER
        )

        yeni_oncelik = st.selectbox(
            "Öncelik",
            ONCELIKLER,
            index=2
        )

        termin_var = st.checkbox(
            "Termin tarihi var",
            value=True
        )

        if termin_var:

            yeni_termin = st.date_input(
                "Termin",
                value=date.today()
            )

        else:

            yeni_termin = None

        yeni_durum = st.selectbox(
            "Durum",
            DURUMLAR
        )

        yeni_beklenen = st.text_input(
            "Beklenen kişi / bölüm",
            placeholder="Varsa..."
        )

        yeni_not = st.text_area(
            "Not / Sonraki Aksiyon",
            placeholder="Kısa açıklama..."
        )

        kaydet = st.form_submit_button(
            "💾 İŞİ KAYDET",
            use_container_width=True
        )

        if kaydet:

            if not yeni_is.strip():

                st.error(
                    "İş adı boş bırakılamaz."
                )

            else:

                is_ekle(
                    yeni_is.strip(),
                    yeni_kategori,
                    yeni_oncelik,
                    yeni_termin,
                    yeni_durum,
                    yeni_beklenen,
                    yeni_not
                )

                st.success(
                    "✅ İş kaydedildi."
                )

                st.rerun()

# ============================================================
# İŞ YÖNETİMİ
# ============================================================

with sekme3:

    st.subheader("⚙️ İş Düzenle / Tamamla / Sil")

    df_yonet = isleri_getir()

    if df_yonet.empty:

        st.info(
            "Düzenlenecek iş bulunmuyor."
        )

    else:

        secenekler = {
            f'#{row["id"]} - {row["is_adi"]}':
            row["id"]

            for _, row in df_yonet.iterrows()
        }

        secilen_yazi = st.selectbox(
            "İş Seç",
            list(secenekler.keys())
        )

        secilen_id = secenekler[
            secilen_yazi
        ]

        row = df_yonet[
            df_yonet["id"] == secilen_id
        ].iloc[0]

        with st.form("duzenleme_formu"):

            duz_is = st.text_input(
                "İş",
                value=row["is_adi"]
            )

            kategori_index = (
                KATEGORILER.index(row["kategori"])
                if row["kategori"] in KATEGORILER
                else 0
            )

            duz_kategori = st.selectbox(
                "Kategori",
                KATEGORILER,
                index=kategori_index
            )

            oncelik_index = (
                ONCELIKLER.index(row["oncelik"])
                if row["oncelik"] in ONCELIKLER
                else 2
            )

            duz_oncelik = st.selectbox(
                "Öncelik",
                ONCELIKLER,
                index=oncelik_index
            )

            if row["termin"]:

                mevcut_termin = datetime.strptime(
                    row["termin"],
                    "%Y-%m-%d"
                ).date()

            else:

                mevcut_termin = date.today()

            duz_termin_var = st.checkbox(
                "Termin tarihi var",
                value=bool(row["termin"])
            )

            if duz_termin_var:

                duz_termin = st.date_input(
                    "Termin",
                    value=mevcut_termin
                )

            else:

                duz_termin = None

            durum_index = (
                DURUMLAR.index(row["durum"])
                if row["durum"] in DURUMLAR
                else 0
            )

            duz_durum = st.selectbox(
                "Durum",
                DURUMLAR,
                index=durum_index
            )

            duz_beklenen = st.text_input(
                "Beklenen kişi / bölüm",
                value=row["beklenen"] or ""
            )

            duz_not = st.text_area(
                "Not / Sonraki Aksiyon",
                value=row["notlar"] or ""
            )

            guncelle = st.form_submit_button(
                "💾 DEĞİŞİKLİKLERİ KAYDET",
                use_container_width=True
            )

            if guncelle:

                is_guncelle(
                    secilen_id,
                    duz_is,
                    duz_kategori,
                    duz_oncelik,
                    duz_termin,
                    duz_durum,
                    duz_beklenen,
                    duz_not
                )

                st.success(
                    "✅ İş güncellendi."
                )

                st.rerun()

        st.divider()

        if row["durum"] != "🟢 Tamamlandı":

            if st.button(
                "✅ İŞİ TAMAMLANDI YAP",
                use_container_width=True
            ):

                is_guncelle(
                    secilen_id,
                    row["is_adi"],
                    row["kategori"],
                    row["oncelik"],
                    (
                        datetime.strptime(
                            row["termin"],
                            "%Y-%m-%d"
                        ).date()
                        if row["termin"]
                        else None
                    ),
                    "🟢 Tamamlandı",
                    row["beklenen"],
                    row["notlar"]
                )

                st.rerun()

        st.warning(
            "Silinen kayıt geri alınamaz."
        )

        sil_onay = st.checkbox(
            "Bu işi silmek istediğimi onaylıyorum."
        )

        if st.button(
            "🗑️ İŞİ SİL",
            disabled=not sil_onay,
            use_container_width=True
        ):

            is_sil(secilen_id)

            st.success(
                "İş silindi."
            )

            st.rerun()

# ============================================================
# ALT BİLGİ
# ============================================================

st.divider()

st.caption(
    f"📅 Bugün: {date.today().strftime('%d.%m.%Y')}"
)
