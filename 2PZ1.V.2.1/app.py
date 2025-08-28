from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import random
import smtplib
from datetime import datetime, timedelta
import subprocess
from flask import Flask, jsonify

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Ganti dengan key yang lebih aman

# Fungsi untuk membuat database jika belum ada
def create_database():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Buat tabel users jika belum ada
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nik TEXT UNIQUE NOT NULL,
            nama TEXT NOT NULL,
            departemen TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)

    # Buat tabel otp untuk verifikasi
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS otp_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            kode TEXT NOT NULL,
            expiry TIMESTAMP NOT NULL
        )
    """)

    conn.commit()
    conn.close()

# Panggil fungsi untuk memastikan database dibuat
create_database()

# Fungsi untuk mengirim OTP ke email tertentu
def send_otp(email, kode):
    sender_email = "zidni.r.arifiyanto@sat.co.id"
    sender_password = "vcis owxj sxii scfw"
    receiver_email = "zidni.r.arifiyanto@sat.co.id"  # Hanya dikirim ke email ini
    
    subject = "Kode OTP Verifikasi"
    body = f"Kode OTP Anda adalah: {kode}\nKode ini berlaku selama 2 menit."

    message = f"Subject: {subject}\n\n{body}"

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message)
        print("OTP berhasil dikirim!")
    except Exception as e:
        print("Error saat mengirim OTP:", e)

@app.route('/')
def home():
    return redirect(url_for('login'))

# Route Halaman Register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nik = request.form["nik"]
        nama = request.form["nama"]
        departemen = request.form["departemen"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        try:
            cursor.execute("INSERT INTO users (nik, nama, departemen, email, password) VALUES (?, ?, ?, ?, ?)",
                           (nik, nama, departemen, email, password))
            conn.commit()
            flash("Registrasi berhasil! Periksa email untuk kode OTP.", "success")

            # Generate OTP dan Simpan di Database
            otp_code = str(random.randint(100000, 999999))
            expiry_time = datetime.now() + timedelta(minutes=2)
            cursor.execute("INSERT INTO otp_codes (email, kode, expiry) VALUES (?, ?, ?)",
                           (email, otp_code, expiry_time))
            conn.commit()

            # Kirim OTP ke Email
            send_otp(email, otp_code)

            session["email"] = email  # Simpan email untuk verifikasi
            return redirect(url_for("verifikasi"))

        except sqlite3.IntegrityError:
            flash("NIK atau email sudah terdaftar!", "danger")

        conn.close()

    return render_template("register.html")

# Route Halaman Verifikasi OTP
@app.route("/verifikasi", methods=["GET", "POST"])
def verifikasi():
    if "email" not in session:
        return redirect(url_for("register"))

    if request.method == "POST":
        otp_input = request.form["otp"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute("SELECT kode, expiry FROM otp_codes WHERE email = ?", (session["email"],))
        data = cursor.fetchone()

        if data:
            kode_terdaftar, expiry = data
            if datetime.now() < datetime.strptime(expiry, "%Y-%m-%d %H:%M:%S.%f"):
                if otp_input == kode_terdaftar:
                    flash("Verifikasi berhasil!", "success")
                    session.pop("email", None)  # Hapus session email setelah verifikasi
                    return redirect(url_for("login"))
                else:
                    flash("Kode OTP salah!", "danger")
            else:
                flash("Kode OTP telah kedaluwarsa. Minta ulang.", "warning")
        else:
            flash("Tidak ada kode OTP untuk email ini!", "danger")

        conn.close()

    return render_template("verifikasi.html")

# Route untuk meminta ulang OTP
@app.route("/resend_otp")
def resend_otp():
    if "email" not in session:
        return redirect(url_for("register"))

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Hapus OTP lama
    cursor.execute("DELETE FROM otp_codes WHERE email = ?", (session["email"],))

    # Buat OTP baru
    otp_code = str(random.randint(100000, 999999))
    expiry_time = datetime.now() + timedelta(minutes=2)
    cursor.execute("INSERT INTO otp_codes (email, kode, expiry) VALUES (?, ?, ?)",
                   (session["email"], otp_code, expiry_time))
    conn.commit()

    # Kirim OTP baru
    send_otp(session["email"], otp_code)

    flash("Kode OTP baru telah dikirim!", "info")
    conn.close()
    return redirect(url_for("verifikasi"))

# Route Halaman Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        nik = request.form["nik"]

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT nama, departemen FROM users WHERE nik = ?", (nik,))
        user = cursor.fetchone()
        conn.close()

        if user:
            nama, departemen = user
            session["nik"] = nik
            session["nama"] = nama
            session["departemen"] = departemen
            return redirect(url_for("dashboard"))
        else:
            flash("NIK tidak ditemukan!", "danger")

    return render_template("login.html")

# Route Dashboard
@app.route('/dashboard')
def dashboard():
    if 'nik' not in session:
        return redirect(url_for('login'))

    departemen = session.get('departemen')
    dashboard_templates = {
        "FINANCE": "dashboard_finance.html",
        "IT": "dashboard.html",
        "MARKETING": "dashboard_marketing.html",
        "LOGISTIC": "dashboard_logistic.html",
        "HUMAN CAPITAL": "dashboard_hc.html",
        "MERCHANDISING": "dashboard_merchandising.html",
        "OPERATION": "dashboard_operation.html",
        "PROPERTY & DEVELOPMENT": "dashboard_property.html",
        "FRANCHISE": "dashboard_franchise.html",
    }

    # Pilih template berdasarkan departemen atau fallback ke dashboard umum
    template = dashboard_templates.get(departemen, "dashboard_general.html")
    
    return render_template(template, nama=session.get('nama'))

# Route Logout
@app.route("/logout")
def logout():
    session.clear()
    flash("Anda telah logout!", "info")
    return redirect(url_for("login"))

@app.route('/run_app')
def run_app():
    try:
        subprocess.Popen(r'\\10.234.91.15\Application\Desktop\SAT_Applications.exe')  
        return jsonify({"message": "Aplikasi berhasil dijalankan!"})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(debug=True)
