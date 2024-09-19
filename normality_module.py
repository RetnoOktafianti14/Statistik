import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
from sqlalchemy import create_engine, text
from db_connection import get_engine  # Pastikan ini sesuai dengan fungsi get_engine() Anda
import time

def show_progress_bar():
    with st.spinner('Memproses data...'):
        time.sleep(2)  # Simulasi waktu proses

def color_map(value):
    if value == 'Pass':
        return 'background-color: #d4edda; color: #155724;'
    elif value == 'Drop':
        return 'background-color: #f8d7da; color: #721c24;'
    return ''

def normality_page():
    st.title("Analisis Normalitas")

    # Mengatur tombol dalam satu baris menggunakan Streamlit columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        start_process_button = st.button("Mulai Proses")

    with col2:
        save_button = st.button("Simpan Data")

    if start_process_button:
        show_progress_bar()  # Menampilkan progress bar saat proses berlangsung

        results_df, total_pass, total_drop, total_ks_pass, total_ks_drop, total_sw_pass, total_sw_drop = process_data()

        if results_df is not None:
            # Format dan styling DataFrame
            styled_df = results_df.style.format({
                'Kolmogorov-Smirnov Statistic': "{:.4f}",
                'Kolmogorov-Smirnov P-Value': "{:.4f}",
                'Shapiro-Wilk Statistic': "{:.4f}",
                'Shapiro-Wilk P-Value': "{:.4f}"
            }).applymap(color_map, subset=['Overall Hypothesis'])\
              .applymap(color_map, subset=['Hypothesis Kolmogorov-Smirnov'])\
              .applymap(color_map, subset=['Hypothesis Shapiro-Wilk'])

            # Menyembunyikan index dan kolom tertentu
            st.dataframe(styled_df, use_container_width=True, hide_index=True)

            # Menampilkan hasil total dengan styling yang lebih menarik
            st.subheader("Statistik Total Uji Normalitas")

            # Konversi total_pass dan total_drop ke int
            total_pass = int(total_pass)
            total_drop = int(total_drop)
            total_ks_pass = int(total_ks_pass)
            total_ks_drop = int(total_ks_drop)
            total_sw_pass = int(total_sw_pass)
            total_sw_drop = int(total_sw_drop)

            # Membuat kolom untuk menampilkan statistik
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.metric(label="Total Pass", value=total_pass, delta=total_drop - total_pass)
                st.metric(label="Total Drop", value=total_drop, delta=total_pass - total_drop)

            with col2:
                st.metric(label="Total Hypothesis Kolmogorov-Smirnov: Pass", value=total_ks_pass, delta=total_ks_drop - total_ks_pass)
                st.metric(label="Total Hypothesis Kolmogorov-Smirnov: Drop", value=total_ks_drop, delta=total_ks_pass - total_ks_drop)

            st.metric(label="Total Hypothesis Shapiro-Wilk: Pass", value=total_sw_pass, delta=total_sw_drop - total_sw_pass)
            st.metric(label="Total Hypothesis Shapiro-Wilk: Drop", value=total_sw_drop, delta=total_sw_pass - total_sw_drop)

    if save_button:
        if results_df is not None:
            save_data(results_df)
            st.success("Data berhasil disimpan ke database")
        else:
            st.error("Tidak ada data untuk disimpan. Silakan jalankan proses terlebih dahulu.")

def process_data():
    results_df = None
    total_pass = 0
    total_drop = 0
    total_ks_pass = 0
    total_ks_drop = 0
    total_sw_pass = 0
    total_sw_drop = 0

    try:
        engine = get_engine()

        # Menghapus data lama dari tabel NormalizationResults
        with engine.connect() as connection:
            connection.execute(text('DELETE FROM NormalizationResults'))
            connection.commit()  # Commit untuk memastikan data terhapus

        # Membaca data dari tabel
        query = 'SELECT * FROM TRANSFORMATION_OF_MEV'
        df = pd.read_sql(query, engine)
        
        if df is None or df.empty:
            st.error("Data dari query tidak ditemukan atau kosong.")
            return None, total_pass, total_drop, total_ks_pass, total_ks_drop, total_sw_pass, total_sw_drop

        # Ambil kolom numerik
        df_numeric = df.select_dtypes(include=[np.number])

        if df_numeric.empty:
            st.error("Data tidak memiliki kolom numerik untuk analisis normalitas.")
            return None, total_pass, total_drop, total_ks_pass, total_ks_drop, total_sw_pass, total_sw_drop

        results = []
        # Iterasi tiap kolom numerik
        for column in df_numeric.columns:
            data = df_numeric[column].dropna()
            n = len(data)
            df_value = n - 1  # Degrees of Freedom untuk Kolmogorov-Smirnov dan Shapiro-Wilk

            # Uji Kolmogorov-Smirnov
            k_stat, k_p_value = stats.kstest(data, 'norm')
            k_hypothesis = "Pass" if k_p_value > 0.05 else "Drop"

            # Uji Shapiro-Wilk
            s_stat, s_p_value = stats.shapiro(data)
            s_hypothesis = "Pass" if s_p_value > 0.05 else "Drop"

            # Kesimpulan
            overall_hypothesis = "Pass" if k_p_value > 0.05 and s_p_value > 0.05 else "Drop"

            # Simpan hasil ke list
            results.append({
                "Variable": column,
                "Kolmogorov-Smirnov Statistic": k_stat,
                "Kolmogorov-Smirnov P-Value": k_p_value,
                "DF Kolmogorov-Smirnov": df_value,
                "Hypothesis Kolmogorov-Smirnov": k_hypothesis,
                "Shapiro-Wilk Statistic": s_stat,
                "Shapiro-Wilk P-Value": s_p_value,
                "DF Shapiro-Wilk": df_value,
                "Hypothesis Shapiro-Wilk": s_hypothesis,
                "Overall Hypothesis": overall_hypothesis
            })

            # Hitung total untuk Kolmogorov-Smirnov dan Shapiro-Wilk
            if k_hypothesis == 'Pass':
                total_ks_pass += 1
            else:
                total_ks_drop += 1

            if s_hypothesis == 'Pass':
                total_sw_pass += 1
            else:
                total_sw_drop += 1

        # Konversi hasil ke dataframe
        results_df = pd.DataFrame(results)

        # Hitung total pass dan drop
        total_pass = results_df['Overall Hypothesis'].value_counts().get('Pass', 0)
        total_drop = results_df['Overall Hypothesis'].value_counts().get('Drop', 0)

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses data: {e}")

    return results_df, total_pass, total_drop, total_ks_pass, total_ks_drop, total_sw_pass, total_sw_drop

def save_data(results_df):
    try:
        engine = get_engine()
        with engine.connect() as connection:
            for _, row in results_df.iterrows():
                connection.execute(
                    text(
                        'INSERT INTO NormalizationResults (Variable, Kolmogorov_Smirnov_Statistic, Kolmogorov_Smirnov_P_Value, Hypothesis_Kolmogorov_Smirnov, Shapiro_Wilk_Statistic, Shapiro_Wilk_P_Value, Hypothesis_Shapiro_Wilk, Overall_Hypothesis) VALUES (:variable, :ks_stat, :ks_p_value, :ks_hypothesis, :sw_stat, :sw_p_value, :sw_hypothesis, :overall_hypothesis)'
                    ),
                    {
                        'variable': row['Variable'],
                        'ks_stat': row['Kolmogorov-Smirnov Statistic'],
                        'ks_p_value': row['Kolmogorov-Smirnov P-Value'],
                        'ks_hypothesis': row['Hypothesis Kolmogorov-Smirnov'],
                        'sw_stat': row['Shapiro-Wilk Statistic'],
                        'sw_p_value': row['Shapiro-Wilk P-Value'],
                        'sw_hypothesis': row['Hypothesis Shapiro-Wilk'],
                        'overall_hypothesis': row['Overall Hypothesis']
                    }
                )
            connection.commit()

    except Exception as e:
        st.error(f"Terjadi kesalahan saat menyimpan data: {e}")

if __name__ == "__main__":
    normality_page()
