import os
from flask import Flask, render_template, request, redirect, url_for, abort
import pyrebase
from datetime import datetime, timedelta

# --- Konfigurasi Firebase ---
# PASTIKAN INI MASIH KONFIGURASI ANDA
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
# ------------------------------

firebase = pyrebase.initialize_app(config)
db = firebase.database()
# ------------------------------

app = Flask(__name__)

def hitung_interval_hari(tipe_rambut):
    """
    Helper function untuk menentukan interval hari berdasarkan tipe rambut.
    """
    if tipe_rambut == 'berminyak':
        return 2  # Setiap 2 hari
    elif tipe_rambut == 'kering_keriting':
        return 4  # Setiap 4 hari
    else:
        return 3  # Normal, setiap 3 hari

def hitung_jadwal_berikutnya(tipe_rambut, tanggal_terakhir):
    """
    Menghitung jadwal keramas berikutnya (hanya 1 kali)
    """
    hari_tambah = hitung_interval_hari(tipe_rambut)
    jadwal_berikutnya = tanggal_terakhir + timedelta(days=hari_tambah)
    return jadwal_berikutnya

@app.route('/', methods=['GET', 'POST'])
def index():
    saran_terbaru = ""
    histori_jadwal = []
    calendar_events = [] # List baru untuk kalender

    if request.method == 'POST':
        # --- LOGIKA UNTUK MENYIMPAN DATA BARU (TIDAK BERUBAH) ---
        tipe_rambut = request.form['tipe_rambut']
        tanggal_terakhir_str = request.form['tanggal_terakhir']
        tanggal_terakhir_obj = datetime.strptime(tanggal_terakhir_str, '%Y-%m-%d')

        jadwal_berikutnya_obj = hitung_jadwal_berikutnya(tipe_rambut, tanggal_terakhir_obj)
        jadwal_berikutnya_str = jadwal_berikutnya_obj.strftime('%Y-%m-%d')

        data = {
            "tipe_rambut": tipe_rambut,
            "terakhir_keramas": tanggal_terakhir_str,
            "jadwal_berikutnya": jadwal_berikutnya_str
        }
        db.child("jadwal_keramas").push(data)
        return redirect(url_for('index'))

    # --- LOGIKA BARU UNTUK MENAMPILKAN HALAMAN (GET) ---
    semua_jadwal = db.child("jadwal_keramas").get().val()

    if semua_jadwal:
        # 1. Ubah data dari Firebase menjadi list, SERTAKAN ID-NYA
        for key, value in semua_jadwal.items():
            value['id'] = key  # <-- INI PENTING UNTUK FITUR HAPUS
            histori_jadwal.append(value)
            
            # Tambahkan event "Sudah Keramas" ke kalender
            calendar_events.append({
                'title': 'Sudah Keramas',
                'start': value['terakhir_keramas'],
                'backgroundColor': '#198754', # Hijau
                'borderColor': '#198754'
            })

        # 2. Urutkan histori (terbaru di atas)
        histori_jadwal.sort(key=lambda x: x['terakhir_keramas'], reverse=True)
        
        # 3. Buat saran & PROYEKSI JADWAL BERULANG
        if histori_jadwal:
            data_terbaru = histori_jadwal[0]
            saran_terbaru = f"Terakhir keramas {data_terbaru['terakhir_keramas']} (Tipe: {data_terbaru['tipe_rambut']}). Jadwal Anda berikutnya adalah **{data_terbaru['jadwal_berikutnya']}**."
            
            # --- Logika Proyeksi ---
            interval = hitung_interval_hari(data_terbaru['tipe_rambut'])
            tanggal_awal_proyeksi = datetime.strptime(data_terbaru['jadwal_berikutnya'], '%Y-%m-%d')
            
            # Buat 12 proyeksi jadwal ke depan (sekitar 3 bulan)
            for i in range(12): 
                tanggal_proyeksi = tanggal_awal_proyeksi + timedelta(days=interval * i)
                calendar_events.append({
                    'title': 'Proyeksi Keramas',
                    'start': tanggal_proyeksi.strftime('%Y-%m-%d'),
                    'backgroundColor': '#fd7e14', # Orange
                    'borderColor': '#fd7e14'
                })

    return render_template(
        'index.html', 
        saran=saran_terbaru, 
        histori=histori_jadwal, 
        calendar_events=calendar_events  # Kirim data kalender yang sudah diolah
    )


# --- ROUTE BARU UNTUK MENGHAPUS ITEM ---
@app.route('/delete/<string:item_id>', methods=['POST'])
def delete_item(item_id):
    try:
        # Hapus item dari Firebase menggunakan ID-nya
        db.child("jadwal_keramas").child(item_id).remove()
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Error deleting item: {e}")
        return abort(500) # Kasih error jika gagal


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)