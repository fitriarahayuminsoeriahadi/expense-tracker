"""
app.py
Bot/aplikasi pencatat pengeluaran & pemasukan pribadi.
Jalankan dengan: python -m streamlit run app.py
"""

import re
import os
import base64
from datetime import date

import pandas as pd
import streamlit as st

import auth
from database import (
    init_db,
    buat_user,
    ambil_user,
    tambah_transaksi,
    ambil_semua_transaksi,
    hapus_transaksi,
    ambil_ringkasan,
)

KATEGORI_MASUK = ["Gaji", "Uang Saku", "Bonus", "Lain-lain"]
KATEGORI_KELUAR = ["Makanan", "Transportasi", "Belanja", "Hiburan", "Tagihan", "Lain-lain"]

BULAN_ID = {
    1: "Januari", 2: "Februari", 3: "Maret", 4: "April",
    5: "Mei", 6: "Juni", 7: "Juli", 8: "Agustus",
    9: "September", 10: "Oktober", 11: "November", 12: "Desember",
}

st.set_page_config(page_title="Pencatat Keuangan", page_icon="💰", layout="wide")
init_db()

# ---------------------------------------------------------------------------
# STYLING
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }

    /* ============================================================
       TEMA: krem/ivory + hijau + charcoal + coral pink
       ============================================================ */
    .main { background-color: #F3EEDC; }

    h1, h2, h3, h4, h5, h6, p, label, span, div {
        color: #262622;
    }

    /* Header banner */
    .hero {
        background: linear-gradient(135deg, #6FBE68 0%, #3E7A46 100%);
        padding: 28px 32px;
        border-radius: 16px;
        margin-bottom: 28px;
        box-shadow: 0 8px 24px rgba(62, 122, 70, 0.3);
        text-align: center;
    }
    .hero h1 { color: #FFFFFF !important; margin: 0; font-size: 28px; font-weight: 700; }
    .hero p { color: #FFFFFF !important; margin: 4px 0 0 0; font-size: 14px; }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background-color: #FCFBF3;
        border: 1px solid #D9D2B8;
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 2px 8px rgba(38, 38, 34, 0.08);
    }
    div[data-testid="stMetricLabel"] { font-weight: 500; color: #6B7A63 !important; }
    div[data-testid="stMetricValue"] { font-weight: 700; color: #262622 !important; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #E9E2C6;
        border-right: 1px solid #D9D2B8;
    }
    section[data-testid="stSidebar"] h2 { color: #3E7A46 !important; font-weight: 600; }
    section[data-testid="stSidebar"] label { color: #262622 !important; }

    /* Buttons */
    div.stButton > button {
        background-color: #3E7A46;
        color: #FCFBF3;
        border-radius: 10px;
        border: none;
        font-weight: 600;
        padding: 8px 16px;
        transition: background-color 0.2s ease;
        width: 100%;
    }
    div.stButton > button:hover { background-color: #2F5F37; color: #FCFBF3; }
    div.stButton > button p { color: #FCFBF3 !important; }

    button[data-baseweb="tab"] { font-weight: 600; }
    button[data-baseweb="tab"] p { color: #262622 !important; }

    /* Input & selectbox fields */
    div[data-baseweb="input"], div[data-baseweb="select"] > div {
        background-color: #FCFBF3 !important;
        border-color: #D9D2B8 !important;
    }

    /* Expander (kotak per bulan) */
    div[data-testid="stExpander"] {
        background-color: #FCFBF3;
        border: 1px solid #D9D2B8;
        border-radius: 12px;
    }

    /* Custom transaction table, centered + per-month */
    .table-wrap {
        overflow-x: auto;
        border: 1px solid #D9D2B8;
        border-radius: 12px;
        margin-bottom: 6px;
    }
    table.custom-table {
        width: 100%;
        min-width: 480px;
        border-collapse: collapse;
        background-color: #FCFBF3;
    }
    table.custom-table th, table.custom-table td {
        text-align: center;
        padding: 10px 14px;
        border-bottom: 1px solid #E9E2C6;
        white-space: nowrap;
        font-size: 14px;
        color: #262622;
    }
    table.custom-table th {
        color: #000000;
        font-weight: 600;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        background-color: #E9E2C6;
    }
    table.custom-table tr:last-child td { border-bottom: none; }
    table.custom-table tr:hover td { background-color: #EFEAD5; }
    .badge-masuk { color: #3E7A46; font-weight: 600; }
    .badge-keluar { color: #E0526B; font-weight: 600; }
    .bulan-summary { color: #6B7A63; font-size: 13px; margin: -4px 0 10px 2px; }

    /* Mobile tweaks */
    @media (max-width: 640px) {
        .hero { padding: 20px 18px; }
        .hero h1 { font-size: 21px; }
        .hero p { font-size: 12px; }
        table.custom-table th, table.custom-table td {
            padding: 8px 10px;
            font-size: 12.5px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _get_base64_gambar(nama_file: str) -> str | None:
    """Baca file gambar di folder assets/ dan encode jadi base64 buat CSS background."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", nama_file)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


_bg_base64 = _get_base64_gambar("background.jpg")
if _bg_base64:
    st.markdown(
        f"""
        <style>
        .stApp {{
            background:
                linear-gradient(rgba(243, 238, 220, 0.55), rgba(243, 238, 220, 0.55)),
                url("data:image/jpeg;base64,{_bg_base64}") center center / cover no-repeat fixed !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def format_rupiah(angka: float) -> str:
    """Ubah angka jadi format 'Rp 1.234.567'."""
    return "Rp " + f"{int(angka):,}".replace(",", ".")


def reformat_input_jumlah():
    """Callback: bersihin karakter non-digit lalu format ulang jadi 'ribuan.ribuan'."""
    raw = st.session_state.get("jumlah_raw", "")
    digits = re.sub(r"[^\d]", "", raw)
    st.session_state.jumlah_raw = f"{int(digits):,}".replace(",", ".") if digits else ""


def render_tabel_bulan(group: pd.DataFrame) -> str:
    """Bikin HTML tabel rata-tengah untuk satu grup bulan.

    Catatan: semua baris HTML digabung TANPA indentasi/newline berlebih,
    karena st.markdown() menganggap baris yang diawali banyak spasi
    sebagai code block markdown, bukan HTML.
    """
    sel_baris = []
    for row in group.itertuples():
        badge_class = "badge-masuk" if row.tipe == "Masuk" else "badge-keluar"
        catatan = row.catatan if row.catatan else "-"
        sel_baris.append(
            "<tr>"
            f"<td>{row.tanggal_dt.strftime('%d %b %Y')}</td>"
            f"<td><span class='{badge_class}'>{row.tipe}</span></td>"
            f"<td>{row.kategori}</td>"
            f"<td>{format_rupiah(row.jumlah)}</td>"
            f"<td>{catatan}</td>"
            "</tr>"
        )
    baris_html = "".join(sel_baris)

    return (
        "<div class='table-wrap'>"
        "<table class='custom-table'>"
        "<thead><tr>"
        "<th>Tanggal</th><th>Tipe</th><th>Kategori</th><th>Jumlah</th><th>Catatan</th>"
        "</tr></thead>"
        f"<tbody>{baris_html}</tbody>"
        "</table>"
        "</div>"
    )


# ---------------------------------------------------------------------------
# AUTENTIKASI: harus login dulu sebelum bisa akses app
# ---------------------------------------------------------------------------
if "user_id" not in st.session_state:
    st.session_state.user_id = None
    st.session_state.username = None

if st.session_state.user_id is None:
    st.markdown(
        """
        <div class="hero">
            <h1>💰 Pencatat Keuangan Pribadi</h1>
            <p>Login atau daftar dulu buat mulai catat transaksimu.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_login, tab_daftar = st.tabs(["🔑 Login", "📝 Daftar Akun"])

    with tab_login:
        with st.form("form_login"):
            username_l = st.text_input("Username", key="login_username")
            password_l = st.text_input("Password", type="password", key="login_password")
            submit_login = st.form_submit_button("Login", use_container_width=True)

            if submit_login:
                user = ambil_user(username_l.strip())
                if user and auth.verify_password(password_l, user["password_hash"], user["password_salt"]):
                    st.session_state.user_id = user["id"]
                    st.session_state.username = user["username"]
                    st.rerun()
                else:
                    st.error("Username atau password salah.")

    with tab_daftar:
        with st.form("form_daftar"):
            username_d = st.text_input("Username baru", key="daftar_username")
            password_d = st.text_input("Password baru", type="password", key="daftar_password")
            password_d2 = st.text_input("Ulangi password", type="password", key="daftar_password2")
            submit_daftar = st.form_submit_button("Daftar", use_container_width=True)

            if submit_daftar:
                username_clean = username_d.strip()
                if not username_clean or not password_d:
                    st.warning("Username dan password wajib diisi.")
                elif password_d != password_d2:
                    st.warning("Password dan ulangi password tidak sama.")
                elif len(password_d) < 6:
                    st.warning("Password minimal 6 karakter.")
                else:
                    hash_hex, salt_hex = auth.hash_password(password_d)
                    berhasil = buat_user(username_clean, hash_hex, salt_hex)
                    if berhasil:
                        st.success("Akun berhasil dibuat! Silakan login lewat tab Login.")
                    else:
                        st.error("Username sudah dipakai, coba yang lain.")

    st.stop()  # jangan render apa pun di bawah ini kalau belum login

user_id = st.session_state.user_id

# ---------------------------------------------------------------------------
# HERO HEADER
# ---------------------------------------------------------------------------
hero_col, logout_col = st.columns([5, 1])
with hero_col:
    st.markdown(
        f"""
        <div class="hero">
            <h1>💰 Pencatat Keuangan Pribadi</h1>
            <p>Halo, {st.session_state.username}! Catat pemasukan & pengeluaranmu, pantau saldo secara real-time.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
with logout_col:
    st.write("")
    st.write("")
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.user_id = None
        st.session_state.username = None
        st.rerun()

# ---------------------------------------------------------------------------
# SIDEBAR: FORM INPUT
# ---------------------------------------------------------------------------

# Reset nilai "jumlah_raw" HARUS dilakukan sebelum widget-nya dibuat,
# karena Streamlit melarang mengubah session_state punya widget
# setelah widget itu diinstansiasi di run yang sama.
if st.session_state.get("reset_jumlah", False):
    st.session_state.jumlah_raw = ""
    st.session_state.reset_jumlah = False

with st.sidebar:
    st.header("➕ Tambah Transaksi")

    tipe = st.radio("Tipe", ["Keluar", "Masuk"], horizontal=True)
    tanggal = st.date_input("Tanggal", value=date.today())

    st.text_input(
        "Jumlah (Rp)",
        key="jumlah_raw",
        placeholder="0",
        on_change=reformat_input_jumlah,
    )

    daftar_kategori = KATEGORI_KELUAR if tipe == "Keluar" else KATEGORI_MASUK
    kategori = st.selectbox("Kategori", daftar_kategori)
    catatan = st.text_input("Catatan (opsional)")

    if st.button("Simpan Transaksi", use_container_width=True):
        digits = re.sub(r"[^\d]", "", st.session_state.get("jumlah_raw", ""))
        jumlah = int(digits) if digits else 0

        if jumlah <= 0:
            st.warning("Jumlah harus lebih dari 0.")
        else:
            tambah_transaksi(
                user_id=user_id,
                tanggal=tanggal.isoformat(),
                tipe=tipe,
                jumlah=jumlah,
                kategori=kategori,
                catatan=catatan,
            )
            st.session_state.reset_jumlah = True
            st.success("Transaksi tersimpan!")
            st.rerun()

# ---------------------------------------------------------------------------
# AMBIL DATA TRANSAKSI (dipakai bareng buat ringkasan & tabel)
# ---------------------------------------------------------------------------
rows = ambil_semua_transaksi(user_id)

if rows:
    df = pd.DataFrame([dict(r) for r in rows])
    df["tanggal_dt"] = pd.to_datetime(df["tanggal"])
    df["bulan_key"] = df["tanggal_dt"].dt.strftime("%Y-%m")
    bulan_keys_tersedia = sorted(df["bulan_key"].unique(), reverse=True)
else:
    df = pd.DataFrame()
    bulan_keys_tersedia = []


def _label_bulan(bkey: str) -> str:
    if bkey == "semua":
        return "Semua Bulan"
    tahun, bulan = bkey.split("-")
    return f"{BULAN_ID[int(bulan)]} {tahun}"


# ---------------------------------------------------------------------------
# RINGKASAN (bisa difilter per bulan)
# ---------------------------------------------------------------------------
opsi_bulan = ["semua"] + bulan_keys_tersedia
bulan_dipilih = st.selectbox(
    "📅 Tampilkan ringkasan untuk",
    options=opsi_bulan,
    format_func=_label_bulan,
)

if bulan_dipilih == "semua" or df.empty:
    df_ringkasan = df
else:
    df_ringkasan = df[df["bulan_key"] == bulan_dipilih]

total_masuk = df_ringkasan.loc[df_ringkasan["tipe"] == "Masuk", "jumlah"].sum() if not df_ringkasan.empty else 0
total_keluar = df_ringkasan.loc[df_ringkasan["tipe"] == "Keluar", "jumlah"].sum() if not df_ringkasan.empty else 0

col1, col2, col3 = st.columns(3)
col1.metric("💵 Total Pemasukan", format_rupiah(total_masuk))
col2.metric("💸 Total Pengeluaran", format_rupiah(total_keluar))
col3.metric("🏦 Saldo", format_rupiah(total_masuk - total_keluar))

st.write("")

# ---------------------------------------------------------------------------
# TABEL & GRAFIK (tetap tampilkan semua bulan, dikelompokkan per bulan)
# ---------------------------------------------------------------------------
if not rows:
    st.info("Belum ada transaksi. Yuk tambahkan lewat form di sidebar. 👈")
else:
    tab1, tab2 = st.tabs(["📋 Daftar Transaksi", "📊 Grafik per Kategori"])

    with tab1:
        for i, bkey in enumerate(bulan_keys_tersedia):
            group = df[df["bulan_key"] == bkey].sort_values("tanggal_dt", ascending=False)
            contoh_tanggal = group["tanggal_dt"].iloc[0]
            label_bulan = f"{BULAN_ID[contoh_tanggal.month]} {contoh_tanggal.year}"

            total_masuk_bulan = group.loc[group["tipe"] == "Masuk", "jumlah"].sum()
            total_keluar_bulan = group.loc[group["tipe"] == "Keluar", "jumlah"].sum()

            with st.expander(f"🗓️ {label_bulan} · {len(group)} transaksi", expanded=(i == 0)):
                st.markdown(
                    f"<div class='bulan-summary'>Masuk: {format_rupiah(total_masuk_bulan)}"
                    f" &nbsp;|&nbsp; Keluar: {format_rupiah(total_keluar_bulan)}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(render_tabel_bulan(group), unsafe_allow_html=True)


        st.write("")
        st.subheader("🗑️ Hapus Transaksi")
        label_map = {
            row["id"]: f"#{row['id']} — {row['tanggal']} — {row['kategori']} — {format_rupiah(row['jumlah'])}"
            for row in df.to_dict("records")
        }
        id_hapus = st.selectbox(
            "Pilih transaksi yang mau dihapus",
            options=list(label_map.keys()),
            format_func=lambda x: label_map[x],
        )
        if st.button("Hapus Transaksi Terpilih"):
            hapus_transaksi(user_id, int(id_hapus))
            st.success(f"Transaksi #{id_hapus} dihapus.")
            st.rerun()

    with tab2:
        df_keluar = df[df["tipe"] == "Keluar"]
        if df_keluar.empty:
            st.info("Belum ada data pengeluaran untuk ditampilkan.")
        else:
            rekap_kategori = df_keluar.groupby("kategori")["jumlah"].sum().reset_index()
            rekap_kategori = rekap_kategori.sort_values("jumlah", ascending=False)
            st.bar_chart(rekap_kategori.set_index("kategori"), color="#10b981")