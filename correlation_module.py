import streamlit as st
import pandas as pd
import numpy as np
from sqlalchemy import text
from db_connection import get_engine

def correlation_page():
    st.title("📊 Correlation Analysis")

    st.write("")  # Tambahkan spasi
    st.write("")  # Tambahkan spasi
    # Buat sidebar untuk navigasi
    st.sidebar.header("Correlation Calculate")
    start_button = st.sidebar.button("🔄Calculate")

    # Area untuk menampilkan hasil dan informasi
    output_area = st.empty()

    # Fungsi untuk memuat data yang ada di tabel CorrelationMatrix
    def load_existing_data():
        """Fungsi untuk memuat data yang ada dari tabel CorrelationMatrix dan menampilkan tabel serta total summary."""
        try:
            engine = get_engine()

            # Membaca data dari tabel CorrelationMatrix
            query = 'SELECT * FROM CorrelationMatrix'
            df = pd.read_sql(query, engine)

            if df.empty:
                st.warning("Tidak ada data di tabel CorrelationMatrix.")
                return

            # Highlight Tabel dengan style
            def style_table(val):
                color = 'green' if val == 'Pass' else 'red'
                return f'background-color: {color}; color: black;'

            # Tampilkan tabel hasil di Streamlit dengan style
            styled_df = df[[ 'Variable', 'Pearson', 'Hypothesis', 'Trend', 'CorrelationTest']].style.applymap(
                style_table, subset=['Hypothesis', 'Trend', 'CorrelationTest'])
            st.dataframe(styled_df)

            # Hitung total untuk kolom Hypothesis, Trend, dan CorrelationTest
            total_hypothesis = df['Hypothesis'].value_counts().to_dict()
            total_trend = df['Trend'].value_counts().to_dict()
            total_correlation_test = df['CorrelationTest'].value_counts().to_dict()

            # Menampilkan Total Summary dengan kolom bersebelahan
            st.subheader("📋 Total Summary")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**Total Hypothesis**")
                st.write(f"✅ Pass: {total_hypothesis.get('Pass', 0)}")
                st.write(f"❌ Drop: {total_hypothesis.get('Drop', 0)}")

            with col2:
                st.markdown("**Total Trend**")
                st.write(f"✅ Pass: {total_trend.get('Pass', 0)}")
                st.write(f"❌ Drop: {total_trend.get('Drop', 0)}")

            with col3:
                st.markdown("**Total Correlation Test**")
                st.write(f"✅ Pass: {total_correlation_test.get('Pass', 0)}")
                st.write(f"❌ Drop: {total_correlation_test.get('Drop', 0)}")

        except Exception as e:
            st.error(f"Terjadi kesalahan saat memuat data: {e}")

    # Fungsi untuk memulai proses korelasi dan menyimpan hasil ke database
    def start_process():
        try:
            engine = get_engine()

            # Menghapus data lama dari tabel CorrelationMatrix
            with engine.connect() as connection:
                connection.execute(text('DELETE FROM CorrelationMatrix'))
                connection.commit()

            # Membaca data dari tabel SQL
            query = 'SELECT * FROM TRANSFORMATION_OF_MEV'
            df = pd.read_sql(query, engine)

            # Menghapus kolom non-numerik
            df_numeric = df.select_dtypes(include=[np.number])

            # Menghitung matriks korelasi Pearson
            correlation_matrix = df_numeric.corr()

            # Mengubah matriks korelasi menjadi format DataFrame yang panjang
            correlation_df = correlation_matrix.reset_index().melt(id_vars='index', var_name='Variable', value_name='Pearson')
            correlation_df.rename(columns={'index': 'Variable1'}, inplace=True)

            # Filter untuk menampilkan hanya baris yang mengandung 'ODR' di Variable1 atau Variable
            correlation_df = correlation_df[
                (correlation_df['Variable'] == 'ODR') & (correlation_df['Variable1'] != 'ODR')
            ]

            # Menambahkan kolom tambahan
            correlation_df['Hypothesis'] = correlation_df['Pearson'].apply(
                lambda x: 'Drop' if abs(x) <= 0.25 else 'Pass'
            )
            correlation_df['Trend'] = correlation_df['Pearson'].apply(
                lambda x: 'Drop' if x > 0 else 'Pass'
            )
            correlation_df['CorrelationTest'] = correlation_df.apply(
                lambda row: 'Pass' if row['Hypothesis'] == 'Pass' and row['Trend'] == 'Pass' else 'Drop',
                axis=1
            )
            correlation_df['OwnerInfo'] = correlation_df['Variable'].apply(lambda x: f'[Owner Info {x}]')

            # Menambahkan nomor urut
            correlation_df.reset_index(drop=True, inplace=True)
            correlation_df['No'] = correlation_df.index + 1

            # Highlight Tabel dengan style
            def style_table(val):
                color = 'green' if val == 'Pass' else 'red'
                return f'background-color: {color}; color: white;'

            # Tampilkan tabel hasil di Streamlit dengan style
            styled_df = correlation_df[['Variable1', 'Pearson', 'Hypothesis', 'Trend', 'CorrelationTest']].style.applymap(
                style_table, subset=['Hypothesis', 'Trend', 'CorrelationTest'])
            output_area.dataframe(styled_df)

            # Hitung total untuk kolom Hypothesis, Trend, dan CorrelationTest
            total_hypothesis = correlation_df['Hypothesis'].value_counts().to_dict()
            total_trend = correlation_df['Trend'].value_counts().to_dict()
            total_correlation_test = correlation_df['CorrelationTest'].value_counts().to_dict()

            # Menampilkan Total Summary dengan kolom bersebelahan
            st.subheader("📋 Total Summary")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("**Total Hypothesis**")
                st.write(f"✅ Pass: {total_hypothesis.get('Pass', 0)}")
                st.write(f"❌ Drop: {total_hypothesis.get('Drop', 0)}")

            with col2:
                st.markdown("**Total Trend**")
                st.write(f"✅ Pass: {total_trend.get('Pass', 0)}")
                st.write(f"❌ Drop: {total_trend.get('Drop', 0)}")

            with col3:
                st.markdown("**Total Correlation Test**")
                st.write(f"✅ Pass: {total_correlation_test.get('Pass', 0)}")
                st.write(f"❌ Drop: {total_correlation_test.get('Drop', 0)}")

            # Simpan hasil ke database
            with engine.connect() as connection:
                for _, row in correlation_df.iterrows():
                    connection.execute(
                        text('INSERT INTO CorrelationMatrix (Variable, Pearson, Hypothesis, Trend, CorrelationTest) '
                             'VALUES (:variable, :pearson, :hypothesis, :trend, :correlationTest)'),
                        {'variable': row['Variable1'], 'pearson': row['Pearson'], 'hypothesis': row['Hypothesis'],
                         'trend': row['Trend'], 'correlationTest': row['CorrelationTest']}
                    )
                connection.commit()
            st.success("✅ Data berhasil disimpan ke database")

        except Exception as e:
            st.error(f"Terjadi kesalahan saat memproses data: {e}")

    # Menampilkan data lama jika tombol belum ditekan
    if not start_button:
        load_existing_data()

    # Jalankan proses saat tombol ditekan
    if start_button:
        start_process()

# Pemanggilan halaman Streamlit
if __name__ == "__main__":
    correlation_page()
