import streamlit as st
from streamlit_option_menu import option_menu
from correlation_module import correlation_page
from normality_module import normalization_page
from regression_module import regression_page
from forecasting_module import forecasting_mev_page
from scalingarima_module import scaling_arima_page
import os

# Cek path gambar logo
logo_path = "logo/logo_app.png"

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

# Cek status login
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# Fungsi login
def login():
    st.sidebar.title("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    
    if st.sidebar.button("Login"):
        if username == "admin" and password == "password":  # Ganti dengan logika yang lebih aman
            st.session_state["logged_in"] = True
            st.sidebar.success("Login successful!")
        else:
            st.sidebar.error("Invalid username or password.")

# Fungsi logout
def logout():
    st.session_state["logged_in"] = False
    st.sidebar.success("Logout successful!")
    # Tidak perlu memanggil rerun, status login sudah diubah

# Jika belum login, tampilkan form login
if not st.session_state["logged_in"]:
    login()
else:
    # Menampilkan logo aplikasi di sidebar
    with st.sidebar:
        if os.path.exists(logo_path):
            st.image(logo_path, width=250)
        else:
            st.write("Logo aplikasi tidak ditemukan!")

        st.write("")  # Tambahkan spasi

        # Tombol logout
        if st.sidebar.button("Logout"):
            logout()

        # Menggunakan option_menu untuk navigasi
        selected = option_menu(
            menu_title="Psak 71",
            options=["Home", "Correlation", "Normality", "Regression", "Forecasting MEV", "Scaling ARIMA"],
            icons=["house", "bar-chart", "check-square", "graph-up", "activity", "calculator"],
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

    # Render halaman sesuai dengan pilihan
    if selected == "Home":
        st.title("Selamat datang di Aplikasi Data Analysis!")
        st.write("Pilih salah satu opsi dari menu di sebelah kiri.")
    elif selected == "Correlation":
        correlation_page()
    elif selected == "Normality":
        normalization_page()
    elif selected == "Regression":
        regression_page()
    elif selected == "Forecasting MEV":
        forecasting_mev_page()
    elif selected == "Scaling ARIMA":
        scaling_arima_page()
