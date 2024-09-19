import streamlit as st
import pandas as pd
from sqlalchemy import create_engine  # Pastikan Anda mengimpor SQLAlchemy untuk koneksi database

# Ganti dengan nama modul tempat fungsi db_connection berada
def get_engine():
    # Contoh koneksi, sesuaikan dengan koneksi database Anda
    return create_engine('mssql+pyodbc://sa:S4D3v@103.81.249.209:4399/IFINANCING_PSAK71?driver=ODBC+Driver+17+for+SQL+Server')

def scaling_arima_page():
    def fetch_result_summary():
        try:
            engine = get_engine()
            with engine.connect() as conn:
                query = "SELECT * FROM result_summary"
                df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            st.error(f"Error connecting to the database: {e}")
            return pd.DataFrame()  # Return an empty DataFrame on error

    def drop_bucket_table():
        try:
            engine = get_engine()
            with engine.connect() as conn:
                cursor = conn.execution_options(autocommit=True).connection.cursor()
                drop_query = "IF OBJECT_ID('BUCKET', 'U') IS NOT NULL DROP TABLE BUCKET;"
                cursor.execute(drop_query)
        except Exception as e:
            st.error(f"Error dropping BUCKET table: {e}")

    def insert_data_into_bucket():
        try:
            engine = get_engine()
            with engine.connect() as conn:
                cursor = conn.execution_options(autocommit=True).connection.cursor()

                 # Drop the BUCKET table if it already exists
                drop_query = "IF OBJECT_ID('BUCKET', 'U') IS NOT NULL DROP TABLE BUCKET;"
                cursor.execute(drop_query)

                insert_query = """
                -- Query Anda untuk memasukkan data ke dalam BUCKET
                WITH TTC_MPD AS (
                SELECT  REPORTING_DATE,MIA_Year AS BUCKET,
                       m1 + m2 + m3 + m4 + m5 + m6 + m7 + m8 + m9 + m10 + m11 + m12 AS TTC_MPD_1,
                       m13 + m14 + m15 + m16 + m17 + m18 + m19 + m20 + m21 + m22 + m23 + m24 AS TTC_MPD_2
                FROM PD_WEIGHTED_AVERAGE
                WHERE reporting_date = (
                    SELECT TOP 1 EOMONTH(DATEADD(MONTH, 1, (date)))
                    FROM TRANSFORMATION_OF_MEV
                    ORDER BY date DESC
                )
                  AND code = 'MPD'
                  AND type = 'K'
                  AND MIA_Year <> 0
                ),
                Logit_TTC AS (
                SELECT BUCKET,
                       CASE 
                           WHEN TTC_MPD_1 >= 1 - 1E-10 AND TTC_MPD_1 < 1 THEN NULL
                           WHEN TTC_MPD_1 > 0 AND TTC_MPD_1 < 1 THEN LOG(TTC_MPD_1 / (1 - TTC_MPD_1))
                           ELSE NULL
                       END AS Logit_TTC_1,
                       CASE 
                           WHEN TTC_MPD_2 >= 1 - 1E-10 AND TTC_MPD_2 < 1 THEN NULL
                           WHEN TTC_MPD_2 > 0 AND TTC_MPD_2 < 1 THEN LOG(TTC_MPD_2 / (1 - TTC_MPD_2))
                           ELSE NULL
                       END AS Logit_TTC_2
                FROM TTC_MPD
                ),
                Logit_PIT AS (
                SELECT BUCKET,
                       Logit_TTC_1 - 0.3275 AS Logit_PIT_1,
                       Logit_TTC_2 + 0.8772 AS Logit_PIT_2
                FROM Logit_TTC
                ),
                PIT_MPD AS (
                SELECT BUCKET,
                       1 / (1 + EXP(-Logit_PIT_1)) AS PIT_MPD_1,
                       1 / (1 + EXP(-Logit_PIT_2)) AS PIT_MPD_2
                FROM Logit_PIT
                ),
                Y_PIT AS (
                SELECT BUCKET,
                       PIT_MPD_1 AS Y1,
                       PIT_MPD_2 AS Y2
                FROM PIT_MPD
                ),
                BUCKET AS (
                SELECT BUCKET,
                       ISNULL(Y1, '0.99999999999999999') AS Y1,
                       ISNULL(Y2, '0') AS Y2
                FROM Y_PIT
                )
                SELECT * INTO BUCKET FROM (
                SELECT a.REPORTING_DATE,a.BUCKET,
                       a.TTC_MPD_1,
                       a.TTC_MPD_2,
                       ISNULL(d.PIT_MPD_1, a.TTC_MPD_1) AS PIT_MPD_1,
                       ISNULL(d.PIT_MPD_2, a.TTC_MPD_2) AS PIT_MPD_2,
                       b.Logit_TTC_1,
                       b.Logit_TTC_2,
                       c.Logit_PIT_1,
                       c.Logit_PIT_2,
                       e.Y1,
                       e.Y2
                FROM TTC_MPD a
                LEFT JOIN Logit_TTC b ON a.BUCKET = b.BUCKET
                LEFT JOIN Logit_PIT c ON a.BUCKET = c.BUCKET
                LEFT JOIN PIT_MPD d ON a.BUCKET = d.BUCKET
                LEFT JOIN BUCKET e ON a.BUCKET = e.BUCKET
                ) a
                """
                cursor.execute(insert_query)
        except Exception as e:
            st.error(f"Error inserting data into BUCKET: {e}")

    def fetch_bucket_data():
        try:
            engine = get_engine()
            with engine.connect() as conn:
                query =  query = """
            SELECT convert(nvarchar(10),BUCKET) BUCKET, TTC_MPD_1, TTC_MPD_2, PIT_MPD_1, PIT_MPD_2, Logit_TTC_1, Logit_TTC_2, Logit_PIT_1, Logit_PIT_2, Y1, Y2
            FROM BUCKET

            UNION ALL

            SELECT 'Total' AS BUCKET,
                   SUM(TTC_MPD_1) AS TTC_MPD_1,
                   SUM(TTC_MPD_2) AS TTC_MPD_2,
                   SUM(PIT_MPD_1) AS PIT_MPD_1,
                   SUM(PIT_MPD_2) AS PIT_MPD_2,
                   SUM(Logit_TTC_1) AS Logit_TTC_1,
                   SUM(Logit_TTC_2) AS Logit_TTC_2,
                   SUM(Logit_PIT_1) AS Logit_PIT_1,
                   SUM(Logit_PIT_2) AS Logit_PIT_2,
                   SUM(Y1) AS Y1,
                   SUM(Y2) AS Y2
            FROM BUCKET;
            """
                df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            st.error(f"Error fetching data from BUCKET: {e}")
            return pd.DataFrame()  # Return an empty DataFrame on error

    def delete_data_from_pd_scalar():
        try:
            engine = get_engine()
            with engine.connect() as conn:
                cursor = conn.execution_options(autocommit=True).connection.cursor()
                delete_query = """
                DELETE FROM PD_SCALAR
                WHERE REPORTING_DATE IN (
                    SELECT REPORTING_DATE
                    FROM BUCKET
                );
                """
                cursor.execute(delete_query)
        except Exception as e:
            st.error(f"Error deleting data from PD_SCALAR: {e}")

    def insert_data_from_bucket_to_pd_scalar():
        try:
            engine = get_engine()
            with engine.connect() as conn:
                cursor = conn.execution_options(autocommit=True).connection.cursor()
                insert_query = """
                -- Your query here
                INSERT INTO [dbo].[PD_SCALAR]
                           ([REPORTING_DATE]
                           ,[BUCKET]
                           ,[DESCRIPTION]
                           ,[M1],[M2],[M3],[M4],[M5],[M6],[M7],[M8],[M9],[M10],[M11],[M12]
                           ,[M13],[M14],[M15],[M16],[M17],[M18],[M19],[M20],[M21],[M22],[M23],[M24])
                SELECT b.REPORTING_DATE,
                       b.Bucket,
                       CASE WHEN b.Bucket = 1 THEN '0 Days'
                            WHEN b.Bucket = 2 THEN '1 - 30 Days'
                            WHEN b.Bucket = 3 THEN '31 - 60 Days'
                            WHEN b.Bucket = 4 THEN '61 - 90 Days'
                            WHEN b.Bucket = 5 THEN '> 90 Days' END,
                       FORMAT(b.Y1 /12, '0.00000000000000000') AS M1,
                       FORMAT(b.Y1 /12, '0.00000000000000000') AS M2,
                       FORMAT(b.Y1 /12, '0.00000000000000000') AS M3,
                       FORMAT(b.Y1 /12, '0.00000000000000000') AS M4,
                       FORMAT(b.Y1 /12, '0.00000000000000000') AS M5,
                       FORMAT(b.Y1 /12, '0.00000000000000000') AS M6,
                       FORMAT(b.Y1 /12, '0.00000000000000000') AS M7,
                       FORMAT(b.Y1 /12, '0.00000000000000000') AS M8,
                       FORMAT(b.Y1 /12, '0.00000000000000000') AS M9,
                       FORMAT(b.Y1 /12, '0.00000000000000000') AS M10,
                       FORMAT(b.Y1 /12, '0.00000000000000000') AS M11,
                       FORMAT(b.Y1 /12, '0.00000000000000000') AS M12,
                       FORMAT(b.Y2 /12, '0.00000000000000000') AS M13,
                       FORMAT(b.Y2 /12, '0.00000000000000000') AS M14,
                       FORMAT(b.Y2 /12, '0.00000000000000000') AS M15,
                       FORMAT(b.Y2 /12, '0.00000000000000000') AS M16,
                       FORMAT(b.Y2 /12, '0.00000000000000000') AS M17,
                       FORMAT(b.Y2 /12, '0.00000000000000000') AS M18,
                       FORMAT(b.Y2 /12, '0.00000000000000000') AS M19,
                       FORMAT(b.Y2 /12, '0.00000000000000000') AS M20,
                       FORMAT(b.Y2 /12, '0.00000000000000000') AS M21,
                       FORMAT(b.Y2 /12, '0.00000000000000000') AS M22,
                       FORMAT(b.Y2 /12, '0.00000000000000000') AS M23,
                       FORMAT(b.Y2 /12, '0.00000000000000000') AS M24
                FROM BUCKET b
                """
                cursor.execute(insert_query)
        except Exception as e:
            st.error(f"Error inserting data from BUCKET to PD_SCALAR: {e}")

    def scaling_arima():
        try:
            df_result_summary = fetch_result_summary()
            if df_result_summary.empty:
                st.write("Result summary is empty.")
                return

            st.write("Result Summary:")
            st.write(df_result_summary)

            drop_bucket_table()
            insert_data_into_bucket()

            df_bucket_data = fetch_bucket_data()
            if df_bucket_data.empty:
                st.write("Bucket data is empty.")
                return

            st.write("Bucket Data:")
            st.write(df_bucket_data)

            delete_data_from_pd_scalar()
            insert_data_from_bucket_to_pd_scalar()

            st.success("Scaling ARIMA process completed successfully.")
        except Exception as e:
            st.error(f"Error during scaling ARIMA process: {e}")

    st.title("Scaling ARIMA Page")
    
    # Menambahkan tombol dengan kunci unik untuk menghindari duplikasi
    if st.button("Run Scaling ARIMA", key="run_scaling_arima_button"):
        scaling_arima()

# Main entry point for the Streamlit app
if __name__ == "__main__":
    scaling_arima_page()
