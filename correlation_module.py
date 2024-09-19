import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from db_connection import get_engine  # Pastikan ini sesuai dengan fungsi get_engine() Anda
import time

def show_progress_bar():
    with st.spinner('Memproses data...'):
        time.sleep(2)  # Simulasi waktu proses

def color_map(value):
    if value == 'Pass':
        return 'background-color: #d4edda; color: #155724; font-weight: bold;'
    elif value == 'Drop':
        return 'background-color: #f8d7da; color: #721c24; font-weight: bold;'
    return ''

def correlation_page():
    st.title("Analisis Korelasi")

    # Mengatur tombol dalam satu baris menggunakan Streamlit columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        start_process_button = st.button("Mulai Proses")

    with col2:
        save_button = st.button("Simpan Data")

    if start_process_button:
        show_progress_bar()  # Menampilkan progress bar saat proses berlangsung

        correlation_df, total_hypothesis, total_trend, total_correlation_test = process_data()

        if correlation_df is not None:
            # Mengubah nama kolom 'Variable1' menjadi 'Variable'
            correlation_df = correlation_df[['No', 'Variable1', 'Pearson', 'Hypothesis', 'Trend', 'CorrelationTest']]
            correlation_df.rename(columns={'Variable1': 'Variable'}, inplace=True)

            # Format dan styling DataFrame
            styled_df = correlation_df.style.format({
                'Pearson': "{:.2f}"
            }).applymap(color_map, subset=['Hypothesis', 'Trend', 'CorrelationTest'])

            # Menyembunyikan index dan kolom tertentu
            st.dataframe(styled_df, use_container_width=True, hide_index=True)

            # Menampilkan hasil total dengan styling yang lebih menarik
            st.subheader("Total Statistik")

            # Membuat kolom untuk menampilkan statistik
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(label="Total Hypothesis: Pass", value=total_hypothesis.get('Pass', 0), delta=total_hypothesis.get('Drop', 0))
                st.metric(label="Total Hypothesis: Drop", value=total_hypothesis.get('Drop', 0))

            with col2:
                st.metric(label="Total Trend: Pass", value=total_trend.get('Pass', 0), delta=total_trend.get('Drop', 0))
                st.metric(label="Total Trend: Drop", value=total_trend.get('Drop', 0))

            with col3:
                st.metric(label="Total CorrelationTest: Pass", value=total_correlation_test.get('Pass', 0), delta=total_correlation_test.get('Drop', 0))
                st.metric(label="Total CorrelationTest: Drop", value=total_correlation_test.get('Drop', 0))

    if save_button:
        correlation_df, total_hypothesis, total_trend, total_correlation_test = process_data()
        if correlation_df is not None:
            save_data(correlation_df)
            st.success("Data berhasil disimpan ke database")

def process_data():
    correlation_df = None
    total_hypothesis = {}
    total_trend = {}
    total_correlation_test = {}

    try:
        engine = get_engine()

        # Menghapus data lama dari tabel CorrelationMatrix
        with engine.connect() as connection:
            connection.execute(text('DELETE FROM CorrelationMatrix'))
            connection.commit()  # Commit untuk memastikan data terhapus

        # Membaca data dari tabel
        query = 'SELECT * FROM TRANSFORMATION_OF_MEV'
        df = pd.read_sql(query, engine)
        
        if df is None or df.empty:
            st.error("Data dari query tidak ditemukan atau kosong.")
            return None, total_hypothesis, total_trend, total_correlation_test

        # Menghapus kolom non-numerik
        df_numeric = df.select_dtypes(include=[np.number])

        if df_numeric.empty:
            st.error("Data tidak memiliki kolom numerik untuk analisis korelasi.")
            return None, total_hypothesis, total_trend, total_correlation_test

        # Menghitung matriks korelasi Pearson
        correlation_matrix = df_numeric.corr()

        # Mengubah matriks korelasi menjadi format DataFrame yang panjang
        correlation_df = correlation_matrix.reset_index().melt(id_vars='index', var_name='Variable', value_name='Pearson')
        correlation_df.rename(columns={'index': 'Variable1'}, inplace=True)

        # Filter untuk menampilkan hanya baris yang mengandung 'ODR' di Variable1 atau Variable
        # dan 'Variable1' bukan 'ODR'
        correlation_df = correlation_df[(
            (correlation_df['Variable'] == 'ODR') & (correlation_df['Variable1'] != 'ODR')
        )]

        if correlation_df.empty:
            st.error("Data korelasi tidak ditemukan setelah pemfilteran.")
            return None, total_hypothesis, total_trend, total_correlation_test

        # Menambahkan kolom tambahan
        correlation_df['Hypothesis'] = correlation_df['Pearson'].apply(
            lambda x: 'Drop' if abs(x) <= 0.25 else 'Pass'
        )
        correlation_df['Trend'] = correlation_df['Pearson'].apply(
            lambda x: 'Pass' if x < 0 else 'Drop'
        )
        correlation_df['CorrelationTest'] = correlation_df.apply(
            lambda row: 'Pass' if row['Hypothesis'] == 'Pass' and row['Trend'] == 'Pass' else 'Drop',
            axis=1
        )

        # Menambahkan nomor urut
        correlation_df.reset_index(drop=True, inplace=True)
        correlation_df['No'] = correlation_df.index + 1

        # Hitung total untuk kolom Hypothesis, Trend, dan CorrelationTest
        total_hypothesis = correlation_df['Hypothesis'].value_counts().to_dict()
        total_trend = correlation_df['Trend'].value_counts().to_dict()
        total_correlation_test = correlation_df['CorrelationTest'].value_counts().to_dict()

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses data: {e}")

    return correlation_df, total_hypothesis, total_trend, total_correlation_test

def save_data(correlation_df):
    try:
        engine = get_engine()
        with engine.connect() as connection:
            for _, row in correlation_df.iterrows():
                connection.execute(
                    text(
                        'INSERT INTO CorrelationMatrix (Variable, Pearson, Hypothesis, Trend, CorrelationTest) VALUES (:variable, :pearson, :hypothesis, :trend, :correlationTest)'
                    ),
                    {
                        'variable': row['Variable'],
                        'pearson': row['Pearson'],
                        'hypothesis': row['Hypothesis'],
                        'trend': row['Trend'],
                        'correlationTest': row['CorrelationTest']
                    }
                )
            connection.commit()

    except Exception as e:
        st.error(f"Terjadi kesalahan saat menyimpan data: {e}")

if __name__ == "__main__":
    correlation_page()
