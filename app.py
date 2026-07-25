import streamlit as st
import pandas as pd
import os
from datetime import datetime
import cv2
from pyzbar.pyzbar import decode
import numpy as np
import qrcode
from io import BytesIO
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
import json
import glob
import zipfile
import base64

# ============================================
# PATH FILE
# ============================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SISWA_FILE = os.path.join(BASE_DIR, "database", "siswa.csv")
ABSENSI_FILE = os.path.join(BASE_DIR, "database", "absensi.csv")
CONFIG_FILE = os.path.join(BASE_DIR, "database", "config.json")
LOGO_PATH = os.path.join(BASE_DIR, "assets", "logo.png")
LOGO_JPG = os.path.join(BASE_DIR, "assets", "logo.jpg")
BG_LOGIN = os.path.join(BASE_DIR, "assets", "bg_login.png")
BG_LOGIN_JPG = os.path.join(BASE_DIR, "assets", "bg_login.jpg")
BG_DASHBOARD = os.path.join(BASE_DIR, "assets", "bg_dashboard.png")
BG_DASHBOARD_JPG = os.path.join(BASE_DIR, "assets", "bg_dashboard.jpg")

# ============================================
# KONFIGURASI & TEMA
# ============================================
def load_config():
	if os.path.exists(CONFIG_FILE):
		with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
			return json.load(f)
	return {
		"nama_sekolah": "MA Plus Sunan Giri Salatiga",
		"slogan": "Smart Attendance for Modern Islamic Schools",
		"warna_utama": "#2d8a5e",
		"warna_aksen": "#f4d03f",
		"logo_emoji": "📷"
	}

def save_config(config):
	with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
		json.dump(config, f, indent=2, ensure_ascii=False)

CONFIG = load_config()

# Cek file yang tersedia
def get_logo_path():
	if os.path.exists(LOGO_PATH):
		return LOGO_PATH
	if os.path.exists(LOGO_JPG):
		return LOGO_JPG
	return None

def get_bg_login_path():
	if os.path.exists(BG_LOGIN):
		return BG_LOGIN
	if os.path.exists(BG_LOGIN_JPG):
		return BG_LOGIN_JPG
	return None

def get_bg_dashboard_path():
	if os.path.exists(BG_DASHBOARD):
		return BG_DASHBOARD
	if os.path.exists(BG_DASHBOARD_JPG):
		return BG_DASHBOARD_JPG
	return None

def get_image_base64(image_path):
	"""Konversi gambar ke base64 untuk CSS background"""
	if image_path and os.path.exists(image_path):
		with open(image_path, "rb") as img_file:
			return base64.b64encode(img_file.read()).decode()
	return None

# ============================================
# USER (2 USER: ADMIN & GURU)
# ============================================
USERS = {
	"admin": {
		"password": "admin123",
		"nama": "Anggas WJ",
		"role": "admin"
	},
	"guru": {
		"password": "guru123",
		"nama": "Guru Mapel",
		"role": "guru"
	}
}

def cek_login(username, password):
	if username in USERS:
		if USERS[username]["password"] == password:
			return True, USERS[username]
	return False, None

def logout():
	for key in ["logged_in", "user", "role", "nama"]:
		if key in st.session_state:
			del st.session_state[key]
	st.rerun()

# ============================================
# CSS DINAMIS - VERSI TERANG + BACKGROUND
# ============================================
def apply_theme():
	primary = CONFIG.get("warna_utama", "#2d8a5e")
	accent = CONFIG.get("warna_aksen", "#f4d03f")
    
	# Cek background dashboard
	bg_dashboard = get_bg_dashboard_path()
	bg_dashboard_css = ""
	if bg_dashboard:
		bg_b64 = get_image_base64(bg_dashboard)
		if bg_b64:
			ext = "png" if bg_dashboard.endswith(".png") else "jpg"
			bg_dashboard_css = f"""
			.stApp {{
				background-image: url("data:image/{ext};base64,{bg_b64}");
				background-size: cover;
				background-attachment: fixed;
				background-position: center;
			}}
			.stApp::before {{
				content: "";
				position: fixed;
				top: 0;
				left: 0;
				width: 100%;
				height: 100%;
				background: rgba(255, 255, 255, 0.85);
				z-index: -1;
			}}
			"""
    
	st.markdown(f"""
	<style>
		{bg_dashboard_css}
        
		/* ===== SIDEBAR TERANG ===== */
		[data-testid="stSidebar"] {{
			background: linear-gradient(180deg, {primary} 0%, #1e6b4a 100%);
		}}
		[data-testid="stSidebar"] h1, 
		[data-testid="stSidebar"] h2,
		[data-testid="stSidebar"] p,
		[data-testid="stSidebar"] label {{
			color: white !important;
			text-shadow: 1px 1px 2px rgba(0,0,0,0.5) !important;
		}}
        
		/* ===== TOMBOL ===== */
		.stButton>button {{
			background: linear-gradient(90deg, {primary} 0%, #4ecda4 100%);
			color: white;
			border-radius: 8px;
			font-weight: bold;
			border: none;
			text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
		}}
		.stButton>button:hover {{
			transform: translateY(-2px);
			box-shadow: 0 4px 12px rgba(0,0,0,0.2);
		}}
        
		/* ===== METRIC CARDS ===== */
		[data-testid="stMetric"] {{
			background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
			border-radius: 12px;
			padding: 15px;
			border-left: 5px solid {primary};
			box-shadow: 0 2px 8px rgba(0,0,0,0.08);
		}}
		[data-testid="stMetricLabel"] {{
			color: #166534 !important;
			font-weight: 600 !important;
		}}
		[data-testid="stMetricValue"] {{
			color: {primary} !important;
			font-weight: 700 !important;
		}}
        
		/* ===== FORM LOGIN ===== */
		.stTextInput input {{
			border-radius: 8px;
		}}
        
		/* ===== GLASSMORPHISM UNTUK KONTEN ===== */
		.glass {{
			background: rgba(255, 255, 255, 0.9);
			backdrop-filter: blur(10px);
			border-radius: 15px;
			padding: 20px;
			box-shadow: 0 4px 15px rgba(0,0,0,0.1);
		}}
	</style>
	""", unsafe_allow_html=True)

def apply_login_background():
	"""CSS khusus untuk background halaman login"""
	bg_login = get_bg_login_path()
	if bg_login:
		bg_b64 = get_image_base64(bg_login)
		if bg_b64:
			ext = "png" if bg_login.endswith(".png") else "jpg"
			st.markdown(f"""
			<style>
				.stApp {{
					background-image: url("data:image/{ext};base64,{bg_b64}");
					background-size: cover;
					background-position: center;
					background-attachment: fixed;
				}}
				.stApp::before {{
					content: "";
					position: fixed;
					top: 0;
					left: 0;
					width: 100%;
					height: 100%;
					background: rgba(0, 0, 0, 0.4);
					z-index: -1;
				}}
			</style>
			""", unsafe_allow_html=True)
			return True
	return False

# ============================================
# FUNGSI DATABASE SISWA
# ============================================
def load_siswa():
	if os.path.exists(SISWA_FILE):
		df = pd.read_csv(SISWA_FILE, dtype={"nisn": str, "id": str})
		df = df.dropna(subset=["nisn"])
		df = df[df["nisn"] != "nan"]
		return df
	return pd.DataFrame(columns=["id", "nama", "kelas", "jenis_kelamin", "nisn"])

def save_siswa(df):
	df.to_csv(SISWA_FILE, index=False)

def tambah_siswa(nama, kelas, jenis_kelamin, nisn):
	df = load_siswa()
	new_id = 1 if len(df) == 0 else int(df["id"].astype(int).max()) + 1
	data_baru = pd.DataFrame([{
		"id": str(new_id), "nama": nama, "kelas": kelas,
		"jenis_kelamin": jenis_kelamin, "nisn": str(nisn)
	}])
	df = pd.concat([df, data_baru], ignore_index=True)
	save_siswa(df)
	return True

def hapus_siswa(id_siswa):
	df = load_siswa()
	df = df[df["id"] != str(id_siswa)]
	save_siswa(df)
	return True

# ============================================
# FUNGSI ABSENSI
# ============================================
def load_absensi():
	if os.path.exists(ABSENSI_FILE):
		df = pd.read_csv(ABSENSI_FILE, dtype={"nisn": str, "id": str})
		return df
	return pd.DataFrame(columns=["id", "tanggal", "jam", "nisn", "nama", "kelas", "status"])

def save_absensi(df):
	df.to_csv(ABSENSI_FILE, index=False)

def cek_sudah_absen(nisn, tanggal):
	df = load_absensi()
	if len(df) > 0:
		sudah = df[(df["nisn"] == str(nisn)) & (df["tanggal"] == tanggal)]
		return len(sudah) > 0
	return False

def tambah_absensi(nisn, nama, kelas, status="Hadir"):
	df = load_absensi()
	tanggal = datetime.now().strftime("%Y-%m-%d")
	jam = datetime.now().strftime("%H:%M:%S")
	new_id = 1 if len(df) == 0 else int(df["id"].astype(int).max()) + 1
	data_baru = pd.DataFrame([{
		"id": str(new_id), "tanggal": tanggal, "jam": jam,
		"nisn": str(nisn), "nama": nama, "kelas": kelas, "status": status
	}])
	df = pd.concat([df, data_baru], ignore_index=True)
	save_absensi(df)
	return True

# ============================================
# FUNGSI BACKUP & RESTORE
# ============================================
def backup_to_json():
	try:
		backup_dir = os.path.join(BASE_DIR, "backups")
		os.makedirs(backup_dir, exist_ok=True)
		df_siswa = load_siswa()
		df_absensi = load_absensi()
		backup_data = {
			"tanggal_backup": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
			"versi": "MAGIScan v1.0",
			"total_siswa": len(df_siswa),
			"total_absensi": len(df_absensi),
			"siswa": df_siswa.to_dict('records') if len(df_siswa) > 0 else [],
			"absensi": df_absensi.to_dict('records') if len(df_absensi) > 0 else []
		}
		filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
		filepath = os.path.join(backup_dir, filename)
		with open(filepath, 'w', encoding='utf-8') as f:
			json.dump(backup_data, f, indent=2, ensure_ascii=False)
		return True, filename
	except Exception as e:
		return False, str(e)

def list_backups():
	backup_dir = os.path.join(BASE_DIR, "backups")
	if not os.path.exists(backup_dir):
		return []
	files = glob.glob(os.path.join(backup_dir, "backup_*.json"))
	files.sort(reverse=True)
	return files

def restore_from_json(filepath):
	try:
		with open(filepath, 'r', encoding='utf-8') as f:
			data = json.load(f)
		if data.get('siswa') and len(data['siswa']) > 0:
			save_siswa(pd.DataFrame(data['siswa']))
		else:
			save_siswa(pd.DataFrame(columns=["id", "nama", "kelas", "jenis_kelamin", "nisn"]))
		if data.get('absensi') and len(data['absensi']) > 0:
			save_absensi(pd.DataFrame(data['absensi']))
		else:
			save_absensi(pd.DataFrame(columns=["id", "tanggal", "jam", "nisn", "nama", "kelas", "status"]))
		return True
	except Exception as e:
		st.error(f"❌ Error restore: {str(e)}")
		return False

# ============================================
# FUNGSI QR CODE & PDF
# ============================================
def generate_qr(nisn):
	qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=4)
	qr.add_data(str(nisn))
	qr.make(fit=True)
	return qr.make_image(fill_color="black", back_color="white")

def scan_qr_code(image):
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	qr_codes = decode(gray)
	for qr in qr_codes:
		return qr.data.decode('utf-8')
	return None

def generate_pdf(tanggal, df_absensi):
	buffer = BytesIO()
	doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
	elements = []
	styles = getSampleStyleSheet()
	primary = CONFIG.get("warna_utama", "#2d8a5e")
	title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18,
								  textColor=colors.HexColor(primary), spaceAfter=20, alignment=1)
	elements.append(Paragraph("MAGIScan", title_style))
	elements.append(Paragraph(f"{CONFIG['nama_sekolah']}", styles['Normal']))
	elements.append(Paragraph(f"Laporan Absensi - {tanggal}", styles['Normal']))
	elements.append(Spacer(1, 20))
	elements.append(Paragraph(f"<b>Total Hadir:</b> {len(df_absensi)} siswa", styles['Normal']))
	elements.append(Paragraph(f"<b>Total Siswa:</b> {len(load_siswa())} siswa", styles['Normal']))
	elements.append(Spacer(1, 20))
	if len(df_absensi) > 0:
		data = [['No', 'NISN', 'Nama', 'Kelas', 'Jam', 'Status']]
		for idx, row in df_absensi.iterrows():
			data.append([str(idx + 1), str(row['nisn']), str(row['nama']), str(row['kelas']), str(row['jam']), str(row['status'])])
		table = Table(data, colWidths=[1*cm, 3*cm, 4*cm, 2*cm, 2.5*cm, 2*cm])
		table.setStyle(TableStyle([
			('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(primary)),
			('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
			('ALIGN', (0, 0), (-1, -1), 'CENTER'),
			('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
			('FONTSIZE', (0, 0), (-1, 0), 11),
			('GRID', (0, 0), (-1, -1), 1, colors.black),
			('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#e8f5e9')])
		]))
		elements.append(table)
	elements.append(Spacer(1, 30))
	elements.append(Paragraph(f"<i>Dicetak: {datetime.now().strftime('%Y-%m-%d %H:%M')}</i>", styles['Normal']))
	doc.build(elements)
	buffer.seek(0)
	return buffer.getvalue()

# ============================================
# SESSION STATE
# ============================================
if "logged_in" not in st.session_state:
	st.session_state.logged_in = False

# ============================================
# HALAMAN LOGIN
# ============================================
if not st.session_state.logged_in:
	apply_theme()
	apply_login_background()
    
	col1, col2, col3 = st.columns([1, 2, 1])
	with col2:
		logo_path = get_logo_path()
		nama_sekolah = CONFIG.get("nama_sekolah", "MA Plus Sunan Giri Salatiga")
		slogan = CONFIG.get("slogan", "Smart Attendance for Modern Islamic Schools")
		primary = CONFIG.get("warna_utama", "#2d8a5e")
		accent = CONFIG.get("warna_aksen", "#f4d03f")
        
		# Container login dengan glass effect
		st.markdown(f"""
		<div style="text-align: center; padding: 40px; 
					background: rgba(255, 255, 255, 0.95); 
					border-radius: 20px; 
					box-shadow: 0 20px 60px rgba(0,0,0,0.3);
					margin-top: 20px;">
		""", unsafe_allow_html=True)
        
		# Tampilkan logo
		if logo_path:
			st.image(logo_path, width=120)
		else:
			st.markdown(f"<div style='font-size: 60px; text-align: center;'>📷</div>", unsafe_allow_html=True)
        
		st.markdown(f"""
			<h1 style="color: {primary}; margin: 10px 0 0 0; font-size: 32px;">MAGIScan</h1>
			<p style="color: {accent}; font-size: 14px; margin-top: 5px;">
				✦ {slogan} ✦
			</p>
			<h3 style="color: #333; margin-top: 15px;">{nama_sekolah}</h3>
		</div>
		""", unsafe_allow_html=True)
        
		st.markdown("<br>", unsafe_allow_html=True)
        
		# Form login dalam container putih
		with st.container():
			with st.form("login_form"):
				st.markdown(f"<h3 style='text-align: center; color: {primary}'>🔐 Login</h3>", unsafe_allow_html=True)
				username = st.text_input("👤 Username", placeholder="admin atau guru")
				password = st.text_input("🔑 Password", type="password", placeholder="Password")
				submit = st.form_submit_button("Masuk", use_container_width=True)
            
			if submit:
				if username and password:
					success, user_data = cek_login(username, password)
					if success:
						st.session_state.logged_in = True
						st.session_state.nama = user_data["nama"]
						st.session_state.user = username
						st.session_state.role = user_data["role"]
						st.success(f"Selamat datang, {user_data['nama']}! 🎉")
						st.rerun()
					else:
						st.error("❌ Username atau password salah!")
				else:
					st.warning("⚠️ Harap isi username dan password!")
        
		st.caption("🔒 Sistem Absensi Internal - Hubungi admin untuk bantuan login.")

# ============================================
# HALAMAN UTAMA
# ============================================
else:
	apply_theme()
    
	# ============================================
	# SIDEBAR DENGAN LOGO
	# ============================================
	with st.sidebar:
		logo_path = get_logo_path()
		primary = CONFIG.get("warna_utama", "#2d8a5e")
		accent = CONFIG.get("warna_aksen", "#f4d03f")
        
		# LOGO SEKOLAH DI ATAS SIDEBAR
		if logo_path:
			st.image(logo_path, width=140, use_container_width=False)
		else:
			st.markdown(f"<div style='font-size: 50px; text-align: center;'>📷</div>", unsafe_allow_html=True)
        
		st.markdown(f"""
		<div style="text-align: center; padding: 10px 0;">
			<h2 style="color: {accent}; margin: 5px 0; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">MAGIScan</h2>
			<p style="color: #e0ffe0; font-size: 11px;">{CONFIG.get('nama_sekolah', 'MA Plus Sunan Giri')}</p>
		</div>
		""", unsafe_allow_html=True)
        
		st.divider()
        
		st.markdown(f"""
		<div style="background: rgba(255,255,255,0.15); padding: 15px; border-radius: 10px; margin: 10px 0;">
			<p style="color: white; margin: 0; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);"><b>👤 {st.session_state.nama}</b></p>
			<p style="color: {accent}; margin: 5px 0 0 0; font-size: 12px; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">
				🏷️ {st.session_state.role.upper()}
			</p>
		</div>
		""", unsafe_allow_html=True)
        
		st.divider()
        
		role = st.session_state.role
		if role == "admin":
			menu_items = ["🏠 Dashboard", "👨‍🎓 Data Siswa", "📷 Scan QR", "📄 Laporan", "🏷️ Generate QR", "💾 Backup & Restore", "⚙️ Pengaturan"]
		else:
			menu_items = ["🏠 Dashboard", "📷 Scan QR", "📄 Laporan"]
		menu = st.radio("Menu", menu_items)
        
		st.divider()
		if st.button("🚪 Logout", use_container_width=True):
			logout()

	# ============================================
	# MENU DASHBOARD
	# ============================================
	if menu == "🏠 Dashboard":
		primary = CONFIG.get("warna_utama", "#2d8a5e")
		accent = CONFIG.get("warna_aksen", "#f4d03f")
        
		# Header dengan glass effect
		st.markdown(f"""
		<div style="text-align: center; padding: 25px; 
					background: linear-gradient(90deg, {primary} 0%, #4ecda4 100%); 
					color: white; border-radius: 15px; margin-bottom: 20px;
					box-shadow: 0 4px 15px rgba(0,0,0,0.15);">
			<h1 style="margin: 0; text-shadow: 2px 2px 4px rgba(0,0,0,0.4);">🏠 Dashboard</h1>
			<p style="margin: 8px 0 0 0; font-size: 16px; text-shadow: 1px 1px 2px rgba(0,0,0,0.4);">
				Selamat Datang di MAGIScan
			</p>
		</div>
		""", unsafe_allow_html=True)
        
		st.write(f"### Assalamu'alaikum, {st.session_state.nama}! 👋")
		st.markdown("---")
        
		df_siswa = load_siswa()
		df_absensi = load_absensi()
		tanggal_hari_ini = datetime.now().strftime("%Y-%m-%d")
		absensi_hari_ini = df_absensi[df_absensi["tanggal"] == tanggal_hari_ini]
        
		col1, col2, col3, col4 = st.columns(4)
		with col1:
			st.metric("👨‍🎓 Total Siswa", len(df_siswa))
		with col2:
			st.metric("✅ Hadir Hari Ini", len(absensi_hari_ini))
		with col3:
			persen = (len(absensi_hari_ini)/len(df_siswa)*100) if len(df_siswa) > 0 else 0
			st.metric("📊 Persentase", f"{persen:.1f}%")
		with col4:
			st.metric("📅 Tanggal", tanggal_hari_ini)
        
		st.markdown("---")
        
		if len(df_absensi) > 0:
			st.write("### 📈 Kehadiran 7 Hari Terakhir")
			df_absensi['tanggal'] = pd.to_datetime(df_absensi['tanggal'])
			last_7 = df_absensi[df_absensi['tanggal'] >= (pd.Timestamp.now() - pd.Timedelta(days=7))]
			daily = last_7.groupby('tanggal').size().reset_index(name='jumlah')
			if len(daily) > 0:
				st.bar_chart(daily.set_index('tanggal'))
        
		col1, col2 = st.columns(2)
		with col1:
			if len(absensi_hari_ini) > 0:
				st.write("### 📋 Absensi Hari Ini")
				st.dataframe(absensi_hari_ini[["jam", "nisn", "nama", "kelas"]], use_container_width=True)
			else:
				st.info("Belum ada absensi hari ini.")
		with col2:
			if len(df_siswa) > 0:
				st.write("### 👨‍🎓 Siswa Terbaru")
				st.dataframe(df_siswa.tail(5), use_container_width=True)
			else:
				st.info("Belum ada data siswa.")

	# ============================================
	# MENU DATA SISWA (ADMIN ONLY)
	# ============================================
	elif menu == "👨‍🎓 Data Siswa":
		st.title("👨‍🎓 Data Siswa")
		tab1, tab2 = st.tabs(["📋 Lihat Data", "➕ Tambah Siswa"])
		with tab1:
			df_siswa = load_siswa()
			if len(df_siswa) > 0:
				kelas_filter = st.selectbox("Filter Kelas", ["Semua"] + sorted(df_siswa["kelas"].unique().tolist()))
				if kelas_filter != "Semua":
					df_siswa = df_siswa[df_siswa["kelas"] == kelas_filter]
				st.dataframe(df_siswa, use_container_width=True)
				st.divider()
				st.write("### 🗑️ Hapus Siswa")
				col1, col2 = st.columns([2, 1])
				with col1:
					id_hapus = st.number_input("ID Siswa", min_value=1, step=1)
				with col2:
					st.write("")
					st.write("")
					if st.button("Hapus", use_container_width=True, type="primary"):
						if str(id_hapus) in df_siswa["id"].values:
							hapus_siswa(id_hapus)
							st.success("Berhasil dihapus!")
							st.rerun()
						else:
							st.error("ID tidak ditemukan!")
			else:
				st.info("Belum ada data siswa.")
		with tab2:
			st.write("### ➕ Tambah Siswa Baru")
			with st.form("tambah_siswa_form"):
				nama = st.text_input("Nama Lengkap")
				nisn = st.text_input("NISN")
				col1, col2 = st.columns(2)
				with col1:
					kelas = st.selectbox("Kelas", ["X", "XI", "XII"])
				with col2:
					jenis_kelamin = st.selectbox("Jenis Kelamin", ["Laki-laki", "Perempuan"])
				submit = st.form_submit_button("Simpan", use_container_width=True)
			if submit:
				if nama and nisn:
					tambah_siswa(nama, kelas, jenis_kelamin, nisn)
					st.success(f"Siswa **{nama}** berhasil ditambahkan!")
					st.balloons()
				else:
					st.warning("Nama dan NISN wajib diisi!")

	# ============================================
	# MENU SCAN QR
	# ============================================
	elif menu == "📷 Scan QR":
		st.title("📷 Scan QR Code")
		tab1, tab2 = st.tabs(["📷 Scan Kamera", "⌨️ Input Manual"])
		with tab1:
			st.write("Arahkan QR Code ke kamera")
			camera_image = st.camera_input("📷 Ambil Foto")
			if camera_image is not None:
				bytes_data = camera_image.getvalue()
				nparr = np.frombuffer(bytes_data, np.uint8)
				image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
				hasil_scan = scan_qr_code(image)
				if hasil_scan:
					st.success(f"✅ Terdeteksi: **{hasil_scan}**")
					df_siswa = load_siswa()
					siswa = df_siswa[df_siswa["nisn"] == str(hasil_scan)]
					if len(siswa) > 0:
						nama = siswa.iloc[0]["nama"]
						kelas = siswa.iloc[0]["kelas"]
						st.write(f"**Nama:** {nama} | **Kelas:** {kelas}")
						tanggal_hari_ini = datetime.now().strftime("%Y-%m-%d")
						if cek_sudah_absen(hasil_scan, tanggal_hari_ini):
							st.warning("⚠️ Sudah absen hari ini!")
						else:
							if st.button("✅ Konfirmasi Absensi", use_container_width=True):
								tambah_absensi(hasil_scan, nama, kelas)
								st.success(f"✅ {nama} berhasil absen!")
								st.balloons()
					else:
						st.error("❌ NISN tidak ditemukan!")
				else:
					st.error("❌ QR tidak terdeteksi!")
		with tab2:
			st.write("Input NISN Manual")
			with st.form("manual_absensi"):
				nisn_manual = st.text_input("NISN")
				submit_manual = st.form_submit_button("Cek & Absen", use_container_width=True)
			if submit_manual:
				if nisn_manual:
					df_siswa = load_siswa()
					siswa = df_siswa[df_siswa["nisn"] == str(nisn_manual)]
					if len(siswa) > 0:
						nama = siswa.iloc[0]["nama"]
						kelas = siswa.iloc[0]["kelas"]
						tanggal_hari_ini = datetime.now().strftime("%Y-%m-%d")
						if cek_sudah_absen(nisn_manual, tanggal_hari_ini):
							st.warning("⚠️ Sudah absen hari ini!")
						else:
							tambah_absensi(nisn_manual, nama, kelas)
							st.success(f"✅ {nama} berhasil absen!")
							st.balloons()
					else:
						st.error("❌ NISN tidak ditemukan!")
				else:
					st.warning("NISN wajib diisi!")

	# ============================================
	# MENU LAPORAN
	# ============================================
	elif menu == "📄 Laporan":
		st.title("📄 Laporan Absensi")
		df_absensi = load_absensi()
		if len(df_absensi) > 0:
			tanggal_list = sorted(df_absensi["tanggal"].unique().tolist(), reverse=True)
			tanggal_pilih = st.selectbox("Pilih Tanggal", tanggal_list)
			df_filter = df_absensi[df_absensi["tanggal"] == tanggal_pilih]
			st.write(f"### 📋 Absensi {tanggal_pilih}")
			st.dataframe(df_filter, use_container_width=True)
			col1, col2 = st.columns(2)
			with col1:
				st.metric("Total Hadir", len(df_filter))
			with col2:
				st.metric("Total Siswa", len(load_siswa()))
			if st.button("📄 Generate PDF", use_container_width=True):
				pdf_data = generate_pdf(tanggal_pilih, df_filter)
				st.download_button("⬇️ Download PDF", data=pdf_data, 
								 file_name=f"Laporan_{tanggal_pilih}.pdf", mime="application/pdf")
		else:
			st.info("Belum ada data absensi.")

	# ============================================
	# MENU GENERATE QR (ADMIN ONLY)
	# ============================================
	elif menu == "🏷️ Generate QR":
		st.title("🏷️ Generate QR Code")
		df_siswa = load_siswa()
		if len(df_siswa) > 0:
			siswa_list = df_siswa.apply(lambda x: f"{x['nama']} - {x['nisn']}", axis=1).tolist()
			pilihan = st.selectbox("Pilih Siswa", siswa_list)
			nisn_terpilih = str(pilihan.split(" - ")[-1]).strip()
			siswa_filter = df_siswa[df_siswa["nisn"] == nisn_terpilih]
			if len(siswa_filter) > 0:
				siswa_terpilih = siswa_filter.iloc[0]
				col1, col2 = st.columns(2)
				with col1:
					st.write("**Data Siswa**")
					st.write(f"Nama: {siswa_terpilih['nama']}")
					st.write(f"NISN: {siswa_terpilih['nisn']}")
					st.write(f"Kelas: {siswa_terpilih['kelas']}")
				with col2:
					qr_image = generate_qr(nisn_terpilih)
					buf = BytesIO()
					qr_image.save(buf, format="PNG")
					st.image(buf.getvalue(), caption=f"QR - {siswa_terpilih['nama']}")
					st.download_button("⬇️ Download", data=buf.getvalue(),
									 file_name=f"QR_{siswa_terpilih['nama']}.png", mime="image/png")
			st.divider()
			if st.button("🖨️ Download Semua QR (ZIP)", use_container_width=True):
				zip_buf = BytesIO()
				with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
					for _, row in df_siswa.iterrows():
						qr_img = generate_qr(row['nisn'])
						img_buf = BytesIO()
						qr_img.save(img_buf, format="PNG")
						filename = f"QR_{row['nama'].replace(' ', '_')}_{row['nisn']}.png"
						zf.writestr(filename, img_buf.getvalue())
				st.download_button("⬇️ Download ZIP", data=zip_buf.getvalue(),
								 file_name="QR_Semua_Siswa.zip", mime="application/zip")
		else:
			st.info("Belum ada siswa.")

	# ============================================
	# MENU BACKUP & RESTORE (ADMIN ONLY)
	# ============================================
	elif menu == "💾 Backup & Restore":
		st.title("💾 Backup & Restore")
		tab1, tab2 = st.tabs(["💾 Backup", "🔄 Restore"])
		with tab1:
			if st.button("💾 Backup Sekarang", use_container_width=True, type="primary"):
				success, result = backup_to_json()
				if success:
					st.success(f"✅ Backup: `{result}`")
					backup_dir = os.path.join(BASE_DIR, "backups")
					latest = max(glob.glob(os.path.join(backup_dir, "backup_*.json")), key=os.path.getctime)
					with open(latest, 'rb') as f:
						st.download_button("⬇️ Download", data=f, 
										 file_name=os.path.basename(latest), mime="application/json")
				else:
					st.error(f"❌ Gagal: {result}")
			backups = list_backups()
			if backups:
				st.write("### 📁 Backup Tersedia")
				for i, b in enumerate(backups[:5]):
					st.write(f"{i+1}. `{os.path.basename(b)}` ({os.path.getsize(b)/1024:.1f} KB)")
		with tab2:
			backups = list_backups()
			if backups:
				pilihan = st.selectbox("Pilih Backup", [os.path.basename(b) for b in backups])
				if st.button("🔄 Restore", use_container_width=True, type="primary"):
					filepath = os.path.join(BASE_DIR, "backups", pilihan)
					if restore_from_json(filepath):
						st.success("✅ Restore berhasil!")
						st.balloons()
					else:
						st.error("❌ Restore gagal!")
			else:
				st.info("Tidak ada backup.")

	# ============================================
	# MENU PENGATURAN (ADMIN ONLY)
	# ============================================
	elif menu == "⚙️ Pengaturan":
		st.title("⚙️ Pengaturan Aplikasi")
		st.write("### Edit Tampilan MAGIScan")
		st.info("Ubah nama sekolah, warna, dan logo di bawah ini. Klik **Simpan** untuk menerapkan.")
		with st.form("pengaturan_form"):
			nama_sekolah = st.text_input("Nama Sekolah", value=CONFIG.get("nama_sekolah", "MA Plus Sunan Giri Salatiga"))
			slogan = st.text_input("Slogan", value=CONFIG.get("slogan", "Smart Attendance for Modern Islamic Schools"))
			logo_emoji = st.text_input("Logo (Emoji)", value=CONFIG.get("logo_emoji", "📷"))
			col1, col2 = st.columns(2)
			with col1:
				warna_utama = st.color_picker("Warna Utama", value=CONFIG.get("warna_utama", "#2d8a5e"))
			with col2:
				warna_aksen = st.color_picker("Warna Aksen", value=CONFIG.get("warna_aksen", "#f4d03f"))
			submit = st.form_submit_button("💾 Simpan Pengaturan", use_container_width=True)
		if submit:
			new_config = {
				"nama_sekolah": nama_sekolah,
				"slogan": slogan,
				"warna_utama": warna_utama,
				"warna_aksen": warna_aksen,
				"logo_emoji": logo_emoji
			}
			save_config(new_config)
			st.success("✅ Pengaturan berhasil disimpan! Refresh halaman untuk melihat perubahan.")
			st.balloons()
		st.divider()
		st.write("### 🎨 Preview Warna")
		col1, col2 = st.columns(2)
		with col1:
			st.markdown(f"""
			<div style="background: {warna_utama}; color: white; padding: 20px; border-radius: 10px; text-align: center; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">
				<b>Warna Utama</b><br>{warna_utama}
			</div>
			""", unsafe_allow_html=True)
		with col2:
			st.markdown(f"""
			<div style="background: {warna_aksen}; color: white; padding: 20px; border-radius: 10px; text-align: center; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">
				<b>Warna Aksen</b><br>{warna_aksen}
			</div>
			""", unsafe_allow_html=True)
		st.divider()
		st.write("### 📊 Info Database")
		col1, col2 = st.columns(2)
		with col1:
			st.metric("Total Siswa", len(load_siswa()))
		with col2:
			st.metric("Total Absensi", len(load_absensi()))

