# Pencatat Keuangan Multi-User

Web app catat pemasukan & pengeluaran dengan sistem akun (login/daftar),
pakai Streamlit + **PostgreSQL** (permanen, hosted gratis lewat Neon).
Setiap user punya data transaksi sendiri-sendiri, tidak bisa saling
lihat/hapus punya orang lain.

## Struktur Project

```
expense_tracker/
├── app.py                          # Tampilan & logika utama (Streamlit) + halaman login
├── auth.py                         # Hashing & verifikasi password (PBKDF2)
├── database.py                     # Koneksi & operasi Postgres (users + transaksi, per user_id)
├── requirements.txt                # Dependency Python
└── .streamlit/
    └── secrets.toml.example        # Contoh format connection string (salin & isi)
```

## Setup Database Permanen (Neon — sekali saja)

1. Buka **https://neon.tech**, daftar akun gratis (bisa pakai GitHub/Google).
2. Setelah masuk dashboard, klik **"Create a project"** (atau langsung dikasih
   satu project default). Kasih nama bebas, misal `expense-tracker`.
3. Di halaman project, cari bagian **"Connection string"** — copy string yang
   formatnya kira-kira:
   ```
   postgresql://neondb_owner:xxxxx@ep-xxxxx.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
   ```
4. Di folder project kamu, masuk ke folder `.streamlit/`, **copy** file
   `secrets.toml.example` jadi file baru bernama **`secrets.toml`** (buang
   `.example`-nya).
5. Buka `secrets.toml`, ganti isi `DATABASE_URL` dengan connection string
   yang tadi kamu copy dari Neon.

Selesai — database permanennya udah siap dipakai. Kamu **tidak perlu** bikin
tabel manual, `init_db()` di `app.py` otomatis bikinin tabel `users` dan
`transaksi` pas pertama kali app dijalankan.

## Cara Menjalankan (Lokal)

```
pip install -r requirements.txt
python -m streamlit run app.py
```

Browser otomatis kebuka di `http://localhost:8501`.

## Deploy ke Streamlit Community Cloud

1. Push project ini ke GitHub — **JANGAN** ikut push file `.streamlit/secrets.toml`
   (isinya kredensial database). Tambahkan `.streamlit/secrets.toml` ke
   `.gitignore`.
2. Buka **share.streamlit.io**, connect ke repo GitHub kamu, deploy.
3. Di dashboard app kamu di Streamlit Cloud, buka **Settings → Secrets**,
   paste isi yang sama seperti di `secrets.toml` lokal kamu:
   ```
   DATABASE_URL = "postgresql://...connection string dari Neon..."
   ```
4. Save — app otomatis pakai database Neon yang sama, datanya permanen dan
   sama antara versi lokal & yang online.

## Fitur
- Daftar akun & login (password di-hash, tidak disimpan plain text)
- Data transaksi terpisah per user, tersimpan permanen di Postgres
- Input transaksi dengan format Rupiah otomatis
- Ringkasan total pemasukan, pengeluaran, saldo
- Daftar transaksi dikelompokkan per bulan (rata tengah, mobile-friendly)
- Grafik pengeluaran per kategori
- Logout

## Ide Pengembangan Selanjutnya
- Auto-kategorisasi dari teks catatan
- Filter berdasarkan rentang tanggal
- Export ke CSV/Excel
- Budget alert per kategori
- Reset password / lupa password