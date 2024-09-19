import streamlit as st
from correlation_module import correlation_page
from normality_module import normality_page
from regression_module import regression_page
from forecasting_module import forecasting_mev_page
from scalingarima_module import scaling_arima_page
import os

# Fungsi untuk menampilkan halaman yang sesuai
def display_page(page_name):
    if page_name == 'Korelasi':
        correlation_page()
    elif page_name == 'Normalitas':
        normality_page()
    elif page_name == 'Regresi':
        regression_page()
    elif page_name == 'Forecasting MEV':
        forecasting_mev_page()
    elif page_name == 'Scaling ARIMA':
        scaling_arima_page()
    else:
        st.title("Selamat datang di Aplikasi Data Analysis!")
        st.write("Pilih salah satu opsi dari menu di sebelah kiri.")

# Cek path gambar logo
logo_path = "D:/python/Psak_web/logo/logo_app.png"  # Gantilah dengan path ke logo aplikasi Anda

# Menampilkan logo aplikasi dengan penanganan kesalahan
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, width=150)
else:
    st.sidebar.write("Logo aplikasi tidak ditemukan!")

# Judul menu sidebar
st.sidebar.title("Menu Navigasi")

# Menambahkan Font Awesome untuk ikon
st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">', unsafe_allow_html=True)

# Fungsi untuk membuat menu dengan logo dan tombol
def render_sidebar():
    menu_items = {
        "Home": "fa-home",
        "Korelasi": "fa-chart-line",
        "Normalitas": "fa-chart-pie",
        "Regresi": "fa-chart-bar",
        "Forecasting MEV": "fa-calendar-alt",
        "Scaling ARIMA": "fa-expand-arrows-alt"
    }

    # Render menu di sidebar
    for page, icon in menu_items.items():
        icon_html = f"<i class='fa {icon}'></i>"
        button_html = f"""
            <a class="menu-item" href="?page={page}" style="text-decoration: none; color: inherit; display: flex; align-items: center; gap: 10px; padding: 10px;">
                {icon_html} {page}
            </a>
        """
        st.sidebar.markdown(button_html, unsafe_allow_html=True)

# Mengambil parameter query dari URL
query_params = st.experimental_get_query_params()
page_name = query_params.get('page', ['Home'])[0]

# Inisialisasi session state untuk halaman saat pertama kali dibuka
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Home'

# Update halaman saat ini berdasarkan query params
st.session_state.current_page = page_name

# Render sidebar menu
render_sidebar()

# Konten halaman utama di sebelah kanan sidebar
st.markdown('<div class="content">', unsafe_allow_html=True)

# Menampilkan halaman yang sesuai dengan navigasi
display_page(st.session_state.current_page)

st.markdown('</div>', unsafe_allow_html=True)
