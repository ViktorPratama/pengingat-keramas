import os
from datetime import datetime, timedelta
import requests  # Library untuk mengirim request HTTP
import pyrebase

# --- 1. KONFIGURASI FIREBASE ANDA ---
# (Salin dari app.py)
config = {
  "apiKey": "AIzaSyBUECKqv35xEWzfJPSsH_U0xQghB9Cn4fo",
  "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN"),
  "databaseURL": os.environ.get("FIREBASE_DB_URL"),
  "projectId": os.environ.get("FIREBASE_PROJECT_ID"),
  "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET"),
  "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID"),
  "appId": os.environ.get("FIREBASE_APP_ID"),
  "measurementId": os.environ.get("FIREBASE_MEASUREMENT_ID")
}

# --- 2. KONFIGURASI TELEGRAM ANDA ---
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# --- 3. FUNGSI KIRIM PESAN ---
def send_telegram_message(message):
    """Mengirim pesan ke Telegram."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        print(f"Telegram response: {response.json()}")
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

# --- 4. FUNGSI LOGIKA (Salin dari app.py) ---
def hitung_interval_hari(tipe_rambut):
    if tipe_rambut == 'berminyak':
        return 2
    elif tipe_rambut == 'kering_keriting':
        return 4
    else:
        return 3

# --- 5. FUNGSI UTAMA PENGECEK ---
def check_schedule():
    print("Mulai mengecek jadwal...")
    try:
        # Inisialisasi Firebase
        firebase = pyrebase.initialize_app(config)
        db = firebase.database()

        # Dapatkan tanggal hari ini
        today_str = datetime.now().strftime('%Y-%m-%d')
        print(f"Mengecek untuk tanggal: {today_str}")

        # Ambil semua data
        semua_jadwal = db.child("jadwal_keramas").get().val()
        if not semua_jadwal:
            print("Tidak ada data di database.")
            return

        # Urutkan untuk menemukan yang terbaru
        histori_jadwal = []
        for key, value in semua_jadwal.items():
            histori_jadwal.append(value)
        
        histori_jadwal.sort(key=lambda x: x['terakhir_keramas'], reverse=True)
        
        if not histori_jadwal:
            print("Histori kosong.")
            return

        # Ambil data paling baru
        data_terbaru = histori_jadwal[0]
        
        # Buat proyeksi dari data terbaru
        interval = hitung_interval_hari(data_terbaru['tipe_rambut'])
        tanggal_awal = datetime.strptime(data_terbaru['jadwal_berikutnya'], '%Y-%m-%d')
        interval_obj = timedelta(days=interval)

        # Cek 12 proyeksi ke depan
        for i in range(12):
            tanggal_proyeksi = tanggal_awal + (interval_obj * i)
            tanggal_proyeksi_str = tanggal_proyeksi.strftime('%Y-%m-%d')
            
            # JIKA JADWAL PROYEKSI = HARI INI
            if tanggal_proyeksi_str == today_str:
                print(f"Menemukan jadwal hari ini! Mengirim notifikasi...")
                send_telegram_message(f"🔔 *Pengingat Keramas!* \nHai, berdasarkan jadwalmu (tipe rambut: {data_terbaru['tipe_rambut']}), hari ini adalah waktunya keramas!")
                break # Cukup kirim satu notifikasi
        
        print("Pengecekan selesai.")

    except Exception as e:
        print(f"Terjadi error besar di checker: {e}")
        # Kirim notifikasi error jika gagal
        send_telegram_message(f"⚠️ Bot keramas Anda error: {e}")

# --- Jalankan fungsi utama ---
if __name__ == "__main__":
    check_schedule()