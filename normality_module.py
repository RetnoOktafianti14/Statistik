import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
from sqlalchemy import text
from db_connection import get_engine

def normalization_page():
    st.title("📊 Normality Analysis")

    # Buat sidebar untuk navigasi
    st.sidebar.header("Menu")
    
    # Pilih kriteria filter dari CorrelationMatrix sebelum memulai proses
    filter_criteria = st.sidebar.selectbox(
        "Pilih Kriteria untuk Filter:",
        ["Hypothesis", "Trend", "CorrelationTest"]
    )
    
    start_button = st.sidebar.button("🔄 Mulai Proses")
    
    # Area untuk menampilkan hasil dan informasi
    output_area = st.empty()

    # Fungsi untuk memuat data yang ada di tabel normalization_temp
    def load_existing_data():
        """Fungsi untuk memuat dan menampilkan data hasil normalisasi dari tabel normalization_temp."""
        try:
            engine = get_engine()
            query = 'SELECT * FROM normalization_temp'
            df = pd.read_sql(query, engine)

            if df.empty:
                st.warning("⚠️ Tidak ada data hasil normalisasi.")
                return

        # Tampilkan hasil di output_area
            output_area.dataframe(df.style.applymap(style_table, subset=["Hypothesis K-S", "Hypothesis SW"]))  # Hanya apply pada kolom tertentu

        # Hitung dan tampilkan ringkasan total
            ks_pass = df['Hypothesis K-S'].value_counts().get('Pass', 0)
            ks_drop = df['Hypothesis K-S'].value_counts().get('Drop', 0)
            sw_pass = df['Hypothesis SW'].value_counts().get('Pass', 0)
            sw_drop = df['Hypothesis SW'].value_counts().get('Drop', 0)

            # Tampilkan ringkasan
            st.subheader("📋 Total Summary")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Total K-S**")
                st.write(f"✅ Hypothesis K-S: {ks_pass}")
                st.write(f"❌ Hypothesis K-S: {ks_drop}")

            with col2:
                st.markdown("**Total SW**")
                st.write(f"✅ Hypothesis SW: {sw_pass}")
                st.write(f"❌ Hypothesis SW: {sw_drop}")


        except Exception as e:
            st.error(f"❌ Terjadi kesalahan saat memuat data: {e}")
    
    def style_table(val):
        """Fungsi untuk memberikan warna pada tabel"""
        color = 'green' if val == 'Pass' else 'Red'
        symbol = '✅' if val == 'Pass' else '❌'
        return f'background-color: {color}; color: black; font-weight: bold;'

    def start_and_save_process():
        try:
            engine = get_engine()
            query = 'SELECT * FROM TRANSFORMATION_OF_MEV'
            df = pd.read_sql(query, engine)

            df_numeric = df.select_dtypes(include=[np.number])
            results = []  # Simpan hasil

            # Melakukan analisis normalisasi
            for column in df_numeric.columns:
                data = df_numeric[column].dropna()
                n = len(data)  # Jumlah data untuk DF

                # Kolmogorov-Smirnov Test
                k_stat, k_p_value = stats.kstest(data, 'norm', args=(np.mean(data), np.std(data)))
                # Shapiro-Wilk Test
                s_stat, s_p_value = stats.shapiro(data)

                # Menyimpan hasil sebagai "Pass" atau "Drop" tanpa simbol
                results.append([column,
                    k_stat, n - 1, k_p_value, 'Pass' if k_p_value > 0.05 else 'Drop',
                    s_stat, n - 1, s_p_value, 'Pass' if s_p_value > 0.05 else 'Drop'])

            df_results = pd.DataFrame(results, columns=[
                "Variable", "K-S Statistic", "DF K-S", "K-S Sig.", "Hypothesis K-S",
                "SW Statistic", "DF SW", "SW Sig.", "Hypothesis SW"
            ])

            # Simpan hasil ke tabel normalization_temp
            df_results.to_sql('normalization_temp', con=engine, if_exists='replace', index=False)

            # Hapus data yang ada di normalization_temp
            #with engine.connect() as conn:
                #conn.execute(text("DELETE FROM normalization_temp"))

            # Filter data berdasarkan CorrelationMatrix dengan kriteria yang dipilih
            filtered_query = f"""
            SELECT n.*
            FROM normalization_temp n
            JOIN CorrelationMatrix c ON n.Variable = c.Variable
            WHERE c.[{filter_criteria}] like '%Pass%'
            """
        
            # Debugging: Tampilkan query yang dijalankan
            #st.write("Query yang dijalankan:", filtered_query)

            df_filtered = pd.read_sql(filtered_query, engine)

            # Tampilkan jumlah data yang difilter
            #st.write("Jumlah data setelah filtering:", df_filtered.shape[0])
            # Tampilkan hasil yang difilter dengan simbol
            output_area.dataframe(df_filtered.style.applymap(style_table, subset=["Hypothesis K-S", "Hypothesis SW"]))

            # Hitung total ringkasan (summary) dari "Hypothesis K-S" dan "Hypothesis SW"
            ks_pass = df_filtered['Hypothesis K-S'].value_counts().get('Pass', 0)
            ks_drop = df_filtered['Hypothesis K-S'].value_counts().get('Drop', 0)
            sw_pass = df_filtered['Hypothesis SW'].value_counts().get('Pass', 0)
            sw_drop = df_filtered['Hypothesis SW'].value_counts().get('Drop', 0)

            # Tampilkan ringkasan
            st.subheader("📋 Total Summary")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Total K-S**")
                st.write(f"✅ Hypothesis K-S: {ks_pass}")
                st.write(f"❌ Hypothesis K-S: {ks_drop}")

            with col2:
                st.markdown("**Total SW**")
                st.write(f"✅ Hypothesis SW: {sw_pass}")
                st.write(f"❌ Hypothesis SW: {sw_drop}")

            # Simpan hasil ke tabel sementara di database (tanpa simbol)
            if not df_filtered.empty:
                df_filtered.to_sql('normalization_temp', con=engine, if_exists='replace', index=False)
                st.success("✅ Proses normalisasi selesai dan data yang memenuhi kriteria berhasil disimpan sementara ke database")
            else:
                st.warning(f"⚠️ Tidak ada data untuk disimpan.")

        except Exception as e:
            st.error(f"❌ Terjadi kesalahan saat memproses data: {e}")
            print(e)  # Tambahkan ini untuk mencetak kesalahan ke konsol

    # Menampilkan data lama jika tombol belum ditekan
    if not start_button:
        load_existing_data()

    # Jalankan proses saat tombol ditekan
    if start_button:
        start_and_save_process()

# Pemanggilan halaman Streamlit
if __name__ == "__main__":
    normalization_page()
