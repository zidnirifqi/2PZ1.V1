import sqlite3

# Koneksi ke database (akan membuat file baru jika tidak ada)
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Buat ulang tabel users
cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nik TEXT UNIQUE NOT NULL,
        nama TEXT NOT NULL,
        departemen TEXT NOT NULL,
        email TEXT NOT NULL
    )
''')

# Buat ulang tabel otps untuk menyimpan kode OTP
cursor.execute('''
    CREATE TABLE otps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nik TEXT NOT NULL,
        otp_code TEXT NOT NULL,
        created_at TIMESTAMP NOT NULL
    )
''')

# Simpan perubahan dan tutup koneksi
conn.commit()
conn.close()

print("Database berhasil dibuat ulang.")
