import json
import bcrypt
import streamlit as st
import os

# Dapatkan folder MAGIScan (folder induk dari modules/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USERS_FILE = os.path.join(BASE_DIR, "database", "users.json")

def load_users():
	"""Memuat data users dari JSON"""
	if os.path.exists(USERS_FILE):
		with open(USERS_FILE, "r") as f:
			return json.load(f)
	return {}

def verify_password(password_input, password_hash):
	"""Cek apakah password cocok dengan hash"""
	return bcrypt.checkpw(password_input.encode(), password_hash.encode())

def login(username, password):
	"""Proses login"""
	users = load_users()
	if username in users:
		stored_hash = users[username]["password"]
		if verify_password(password, stored_hash):
			return True, users[username]
	return False, None

def init_session():
	"""Inisialisasi session state"""
	if "logged_in" not in st.session_state:
		st.session_state.logged_in = False
		st.session_state.user = None
		st.session_state.role = None

def logout():
	"""Proses logout"""
	st.session_state.logged_in = False
	st.session_state.user = None
	st.session_state.role = None
	st.rerun()
