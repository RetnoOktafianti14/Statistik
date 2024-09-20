import streamlit as st
from streamlit_option_menu import option_menu
from correlation_module import correlation_page
from normality_module import normality_page
from regression_module import regression_page
from forecasting_module import forecasting_mev_page
from scalingarima_module import scaling_arima_page
import os

# Cek path gambar logo
logo_path = "D:/python/Psak_web/logo/logo_app.png"

# CSS untuk latar belakang
st.markdown(
    """
    <style>
    .reportview-container {
        background-color: #D3D3D3;  /* Warna abu-abu */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Menampilkan logo aplikasi di sidebar
with st.sidebar:
    if os.path.exists(logo_path):
        st.image(logo_path, width=250)
    else:
        st.write("Logo aplikasi tidak ditemukan!")

    st.write("")  # Tambahkan spasi
    st.write("")  # Tambahkan spasi

    # Menggunakan option_menu untuk navigasi
    selected = option_menu(
        menu_title="PSAK71",
        options=["Home", "Korelasi", "Normalitas", "Regresi", "Forecasting MEV", "Scaling ARIMA"],
        icons=["house", "bar-chart", "check-square", "graph-up", "graph-up", "calculator"],
        menu_icon="list-task",
        default_index=0,
        orientation="vertical",
        styles={
            "container": {"padding": "0!important", "background-color": "#D3D3D3"},
            "icon": {"color": "black", "font-size": "20px"},
            "nav-link": {
                "font-size": "16px",
                "text-align": "left",
                "margin": "0px",
                "--hover-color": "#eee",
            },
            "nav-link-selected": {"background-color": "#3FBAD8"},
        },
    )

# Fungsi untuk menampilkan halaman yang sesuai
def display_page(menu):
    if menu == "Home":
        st.title("Selamat datang di Aplikasi Data Analysis!")
        st.write("Pilih salah satu opsi dari menu di sebelah kiri.")
    elif menu == "Korelasi":
        correlation_page()
    elif menu == "Normalitas":
        normality_page()
    elif menu == "Regresi":
        regression_page()
    elif menu == "Forecasting MEV":
        forecasting_mev_page()
    elif menu == "Scaling ARIMA":
        scaling_arima_page()

# Render halaman sesuai dengan pilihan
display_page(selected)
