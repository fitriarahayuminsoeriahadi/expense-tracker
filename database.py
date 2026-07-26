"""
database.py
Modul untuk koneksi ke database PostgreSQL (hosted, permanen — misal Neon)
dan operasi CRUD untuk tabel users & transaksi (multi-user).
"""

import streamlit as st
import psycopg2
import psycopg2.extras
import psycopg2.errors


def get_connection():
    """Buka koneksi ke Postgres pakai connection string dari st.secrets."""
    db_url = st.secrets["DATABASE_URL"]
    conn = psycopg2.connect(db_url, cursor_factory=psycopg2.extras.RealDictCursor)
    return conn


def init_db():
    """Bikin tabel users & transaksi kalau belum ada. Panggil sekali di awal app."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            password_salt TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transaksi (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            tanggal DATE NOT NULL,
            tipe TEXT NOT NULL CHECK (tipe IN ('Masuk', 'Keluar')),
            jumlah NUMERIC NOT NULL,
            kategori TEXT NOT NULL,
            catatan TEXT
        )
        """
    )
    conn.commit()
    cur.close()
    conn.close()


# ---------------------------------------------------------------------------
# USERS
# ---------------------------------------------------------------------------

def buat_user(username: str, password_hash: str, password_salt: str) -> bool:
    """Daftarin user baru. Return False kalau username udah dipakai."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password_hash, password_salt) VALUES (%s, %s, %s)",
            (username, password_hash, password_salt),
        )
        conn.commit()
        return True
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def ambil_user(username: str):
    """Ambil data satu user berdasarkan username. None kalau nggak ketemu."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row


# ---------------------------------------------------------------------------
# TRANSAKSI (semua di-scope ke user_id)
# ---------------------------------------------------------------------------

def tambah_transaksi(user_id: int, tanggal: str, tipe: str, jumlah: float, kategori: str, catatan: str = ""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO transaksi (user_id, tanggal, tipe, jumlah, kategori, catatan)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (user_id, tanggal, tipe, jumlah, kategori, catatan),
    )
    conn.commit()
    cur.close()
    conn.close()


def ambil_semua_transaksi(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM transaksi WHERE user_id = %s ORDER BY tanggal DESC, id DESC",
        (user_id,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def hapus_transaksi(user_id: int, transaksi_id: int):
    """Hapus transaksi, dengan cek kepemilikan (user_id) biar orang lain nggak bisa hapus punya orang lain."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM transaksi WHERE id = %s AND user_id = %s",
        (transaksi_id, user_id),
    )
    conn.commit()
    cur.close()
    conn.close()


def ambil_ringkasan(user_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT COALESCE(SUM(jumlah), 0) AS total FROM transaksi WHERE tipe = 'Masuk' AND user_id = %s",
        (user_id,),
    )
    total_masuk = float(cur.fetchone()["total"])
    cur.execute(
        "SELECT COALESCE(SUM(jumlah), 0) AS total FROM transaksi WHERE tipe = 'Keluar' AND user_id = %s",
        (user_id,),
    )
    total_keluar = float(cur.fetchone()["total"])
    cur.close()
    conn.close()
    return {
        "total_masuk": total_masuk,
        "total_keluar": total_keluar,
        "saldo": total_masuk - total_keluar,
    }