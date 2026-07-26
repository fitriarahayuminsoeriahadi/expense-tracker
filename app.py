"""
app.py
Bot/aplikasi pencatat pengeluaran & pemasukan pribadi.
Jalankan dengan: python -m streamlit run app.py
"""

import re
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

    .main { background-color: #0e1117; }

    /* Header banner */
    .hero {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        padding: 28px 32px;
        border-radius: 16px;
        margin-bottom: 28px;
        box-shadow: 0 8px 24px rgba(16, 185, 129, 0.25);
    }
    .hero h1 { color: white; margin: 0; font-size: 28px; font-weight: 700; }
    .hero p { color: rgba(255,255,255,0.85); margin: 4px 0 0 0; font-size: 14px; }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background-color: #1a1f2b;
        border: 1px solid #2a3040;
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.2);
    }
    div[data-testid="stMetricLabel"] { font-weight: 500; color: #9ca3af !important; }
    div[data-testid="stMetricValue"] { font-weight: 700; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #12161f;
        border-right: 1px solid #2a3040;
    }
    section[data-testid="stSidebar"] h2 { color: #10b981; font-weight: 600; }

    /* Buttons */
    div.stButton > button {
        background-color: #10b981;
        color: white;
        border-radius: 10px;
        border: none;
        font-weight: 600;
        padding: 8px 16px;
        transition: background-color 0.2s ease;
        width: 100%;
    }
    div.stButton > button:hover { background-color: #059669; color: white; }

    button[data-baseweb="tab"] { font-weight: 600; }

    /* Custom transaction table, centered + per-month */
    .table-wrap {
        overflow-x: auto;
        border: 1px solid #2a3040;
        border-radius: 12px;
        margin-bottom: 6px;
    }
    table.custom-table {
        width: 100%;
        min-width: 480px;
        border-collapse: collapse;
        background-color: #1a1f2b;
    }
    table.custom-table th, table.custom-table td {
        text-align: center;
        padding: 10px 14px;
        border-bottom: 1px solid #2a3040;
        white-space: nowrap;
        font-size: 14px;
    }
    table.custom-table th {
        color: #9ca3af;
        font-weight: 600;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.03em;
        background-color: #161a24;
    }
    table.custom-table tr:last-child td { border-bottom: none; }
    table.custom-table tr:hover td { background-color: #20263380; }
    .badge-masuk { color: #34d399; font-weight: 600; }
    .badge-keluar { color: #f87171; font-weight: 600; }
    .bulan-summary { color: #9ca3af; font-size: 13px; margin: -4px 0 10px 2px; }

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
# RINGKASAN
# ---------------------------------------------------------------------------
ringkasan = ambil_ringkasan(user_id)

col1, col2, col3 = st.columns(3)
col1.metric("💵 Total Pemasukan", format_rupiah(ringkasan["total_masuk"]))
col2.metric("💸 Total Pengeluaran", format_rupiah(ringkasan["total_keluar"]))
col3.metric("🏦 Saldo", format_rupiah(ringkasan["saldo"]))

st.write("")

# ---------------------------------------------------------------------------
# TABEL & GRAFIK
# ---------------------------------------------------------------------------
rows = ambil_semua_transaksi(user_id)

if not rows:
    st.info("Belum ada transaksi. Yuk tambahkan lewat form di sidebar. 👈")
else:
    df = pd.DataFrame([dict(r) for r in rows])
    df["tanggal_dt"] = pd.to_datetime(df["tanggal"])
    df["bulan_key"] = df["tanggal_dt"].dt.strftime("%Y-%m")

    tab1, tab2 = st.tabs(["📋 Daftar Transaksi", "📊 Grafik per Kategori"])

    with tab1:
        bulan_keys = sorted(df["bulan_key"].unique(), reverse=True)

        for i, bkey in enumerate(bulan_keys):
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