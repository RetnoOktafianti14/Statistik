import streamlit as st
import pyodbc
import pandas as pd
from db_connection import get_engine

def scaling_arima_page():
    # Fetch data from result_summary
    def fetch_result_summary():
        try:
            engine = get_engine()
            with engine.connect() as conn:
                query = "SELECT * FROM result_summary"
                df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            st.error(f"Error connecting to the database: {e}")
            return pd.DataFrame()

    # Drop BUCKET table if it exists
    def drop_bucket_table():
        try:
            engine = get_engine()
            with engine.connect() as conn:
                cursor = conn.execution_options(autocommit=True).connection.cursor()
                drop_query = "IF OBJECT_ID('BUCKET', 'U') IS NOT NULL DROP TABLE BUCKET;"
                cursor.execute(drop_query)
        except Exception as e:
            st.error(f"Error dropping BUCKET table: {e}")

    # Insert data into BUCKET table
    def insert_data_into_bucket():
        try:
            engine = get_engine()
            with engine.connect() as conn:
                cursor = conn.execution_options(autocommit=True).connection.cursor()
                drop_query = "IF OBJECT_ID('BUCKET', 'U') IS NOT NULL DROP TABLE BUCKET;"
                cursor.execute(drop_query)

                insert_query = """
                -- Query Anda untuk memasukkan data ke dalam BUCKET
                	      
                """
                cursor.execute(insert_query)
                conn.commit()
        except Exception as e:
            st.error(f"Error inserting data into BUCKET: {e}")

    # Fetch data from BUCKET table
    def fetch_bucket_data():
        try:
            engine = get_engine()
            with engine.connect() as conn:
                query = "SELECT BUCKET, TTC_MPD_1, TTC_MPD_2, PIT_MPD_1, PIT_MPD_2 FROM BUCKET order by bucket"
                df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            st.error(f"Error fetching data from BUCKET: {e}")
            return pd.DataFrame()

    # Delete data from PD_SCALAR based on BUCKET
    def delete_data_from_pd_scalar():
        try:
            engine = get_engine()
            with engine.connect() as conn:
                cursor = conn.execution_options(autocommit=True).connection.cursor()
                delete_query = """
                DELETE FROM PD_SCALAR
                WHERE REPORTING_DATE IN (
                    SELECT REPORTING_DATE FROM BUCKET
                );
                """
                cursor.execute(delete_query)
                conn.commit()
        except Exception as e:
            st.error(f"Error deleting data from PD_SCALAR: {e}")

    # Insert data from BUCKET to PD_SCALAR
    def insert_data_from_bucket_to_pd_scalar():
        try:
            engine = get_engine()
            with engine.connect() as conn:
                cursor = conn.execution_options(autocommit=True).connection.cursor()
                insert_query = """
                -- Query Anda untuk memasukkan data dari BUCKET ke PD_SCALAR
                
                """
                cursor.execute(insert_query)
                conn.commit()
        except Exception as e:
            st.error(f"Error inserting data from BUCKET to PD_SCALAR: {e}")

    # Fetch data from PD_SCALAR
    def fetch_pd_scalar_data():
        try:
            engine = get_engine()
            with engine.connect() as conn:
                query = "SELECT * FROM PD_SCALAR ORDER BY BUCKET ASC"
                df = pd.read_sql(query, conn)
            return df
        except Exception as e:
            st.error(f"Error fetching data from PD_SCALAR: {e}")
            return pd.DataFrame()

    # Fetch TTC_MPD_1, TTC_MPD_2, and PIT_MPD_1 from BUCKET
    def fetch_ttc_mpd_1_and_2():
        try:
            engine = get_engine()
            with engine.connect() as conn:
                query = "SELECT TTC_MPD_1, TTC_MPD_2, PIT_MPD_1, PIT_MPD_2 FROM BUCKET WHERE BUCKET = 'Total'"
                ttc_mpd_data = pd.read_sql(query, conn)
            return ttc_mpd_data.iloc[0] if not ttc_mpd_data.empty else (None, None, None, None)
        except Exception as e:
            st.error(f"Error fetching TTC_MPD data: {e}")
            return None, None, None, None

    def goal_seek(input_value, initial_guess, target_type, tolerance=0.000001, max_iterations=100):
        guess = initial_guess
        iterations = 0

        while iterations < max_iterations:
            if target_type == "Target_1":
                Marginal_Scaling_1 = (Marginal_PD_1 / Marginal_PD_1_TTC * TTC_MPD_1_db) if Marginal_PD_1_TTC != 0 else None
                current_target = Marginal_Scaling_1 - PIT_MPD_1_db if Marginal_Scaling_1 is not None else None
            elif target_type == "Target_2":
                Marginal_Scaling_2 = (Marginal_PD_2 / Marginal_PD_2_TTC * TTC_MPD_2_db) if Marginal_PD_2_TTC != 0 else None
                current_target = Marginal_Scaling_2 - PIT_MPD_2_db if Marginal_Scaling_2 is not None else None
            else:
                return None

            if current_target is None:
                break

            if abs(current_target - input_value) < tolerance:
                return guess

            guess -= (current_target - input_value) * 0.1

            if guess < -1E10 or guess > 1E10:
                return guess

            iterations += 1

        return guess

    # Function to create a temporary table for storing results
    def delete_data_from_TempResults():
        try:
            engine = get_engine()
            with engine.connect() as conn:
                cursor = conn.execution_options(autocommit=True).connection.cursor()
                delete_query = """
                DELETE FROM TempResults
                """
                cursor.execute(delete_query)
                conn.commit()
        except Exception as e:
            st.error(f"Error clearing TempResults table: {e}")

        
    def save_results_to_temp_table(pit_pd_1, pit_pd_2, cpd_1, marginal_pd_1, marginal_pd_2,
                                ttc_pd_1, ttc_pd_2, cpd_1_ttc, marginal_pd_1_ttc, marginal_pd_2_ttc):
        try:
            engine = get_engine()
            with engine.connect() as conn:
                insert_query = """
                INSERT INTO TempResults (PIT_PD_1, PIT_PD_2, CPD_1, Marginal_PD_1, Marginal_PD_2, 
                                         TTC_PD_1, TTC_PD_2, CPD_1_TTC, Marginal_PD_1_TTC, Marginal_PD_2_TTC)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor = conn.execution_options(autocommit=True).connection.cursor()
                cursor.execute(insert_query, (pit_pd_1, pit_pd_2, cpd_1, marginal_pd_1, marginal_pd_2,
                                            ttc_pd_1, ttc_pd_2, cpd_1_ttc, marginal_pd_1_ttc, marginal_pd_2_ttc))
                conn.commit()
        except Exception as e:
            st.error(f"Error saving results to temporary table: {e}")

    # Process data and perform calculations
    if st.button("Proses Data"):
        st.subheader("Processing Data...")

        # Fetch result_summary data
        result_summary = fetch_result_summary()
        if result_summary.empty or result_summary.shape[0] < 4 or 'AVGODD' not in result_summary.columns or 'AVGODR' not in result_summary.columns:
            st.error("Tabel result_summary tidak memiliki data yang cukup atau kolom yang diperlukan.")
            return

        # Extract necessary values for calculations
        PIT_PD_1 = result_summary.loc[1, 'AVGODD']
        PIT_PD_2 = result_summary.loc[2, 'AVGODD']
        TTC_PD_1 = result_summary.loc[0, 'AVGODR']

        CPD_1 = PIT_PD_1
        Marginal_PD_1 = PIT_PD_1
        Marginal_PD_2 = PIT_PD_2 * (1 - CPD_1)

        TTC_PD_2 = TTC_PD_1
        Marginal_PD_1_TTC = TTC_PD_1
        CPD_1_TTC = Marginal_PD_1_TTC
        Marginal_PD_2_TTC = TTC_PD_2 * (1 - CPD_1_TTC)

        # Fetch TTC_MPD data for calculations
        TTC_MPD_1_db, TTC_MPD_2_db, PIT_MPD_1_db, PIT_MPD_2_db = fetch_ttc_mpd_1_and_2()
        Marginal_Scaling_1 = Marginal_PD_1 / Marginal_PD_1_TTC * TTC_MPD_1_db if TTC_MPD_1_db is not None and Marginal_PD_1_TTC != 0 else None
        Marginal_Scaling_2 = Marginal_PD_2 / Marginal_PD_2_TTC * TTC_MPD_2_db if TTC_MPD_2_db is not None and Marginal_PD_2_TTC != 0 else None

        # Calculate Target 1 and Target 2
        Target_1 = Marginal_Scaling_1 - PIT_MPD_1_db if Marginal_Scaling_1 is not None else None
        Target_2 = Marginal_Scaling_2 - PIT_MPD_2_db if Marginal_Scaling_2 is not None else None

        # Goal Seek Results
        initial_guess = 0  # Ganti dengan tebakan awal yang sesuai
        goal_seek_result_target_1 = goal_seek(Target_1, initial_guess, target_type="Target_1")
        goal_seek_result_target_2 = goal_seek(Target_2, initial_guess, target_type="Target_2")


        # CLEAR temporary table
        delete_data_from_TempResults()
        
        
        # Create two columns
        # Membuat dua kolom
        col1, col2 = st.columns(2)

        # Hasil perhitungan di kolom 1
        with col1:
            st.subheader("Hasil PIT")
            st.markdown("**Calculated Values:**")
            st.markdown(f"- **PIT PD +1**: {PIT_PD_1:.4f}")
            st.markdown(f"- **PIT PD +2**: {PIT_PD_2:.4f}")
            st.markdown(f"- **CPD +1 (PIT)**: {CPD_1:.4f}")
            st.markdown(f"- **Marginal PD +1 (PIT)**: {Marginal_PD_1:.4f}")
            st.markdown(f"- **Marginal PD +2 (PIT)**: {Marginal_PD_2:.4f}")
            

        # Hasil perhitungan di kolom 2
        with col2:
            st.subheader("Hasil TTC")
            st.markdown("**Calculated Values:**")
            st.markdown(f"- **TTC PD +1**: {TTC_PD_1:.4f}")
            st.markdown(f"- **TTC PD +2**: {TTC_PD_2:.4f}")
            st.markdown(f"- **CPD +1 (TTC)**: {CPD_1_TTC:.4f}")
            st.markdown(f"- **Marginal PD +1 (TTC)**: {Marginal_PD_1_TTC:.4f}")
            st.markdown(f"- **Marginal PD +2 (TTC)**: {Marginal_PD_2_TTC:.4f}")
            
        st.markdown(f"- **Marginal Scaling 1**: {Marginal_Scaling_1:.4f}")
        st.markdown(f"- **Marginal Scaling 2**: {Marginal_Scaling_2:.4f}")
            
        # Menampilkan hasil Goal Seek
        st.markdown("### Goal Seek Results")
        st.markdown(f"- **Target +1**: {Target_1:.4f}")
        st.markdown(f"- **Target +2**: {Target_2:.4f}")
        st.markdown(f"- **Scalar +1**: {goal_seek_result_target_1:.4f}" if goal_seek_result_target_1 is not None else "- **Scalar +1**: Error")
        st.markdown(f"- **Scalar +2**: {goal_seek_result_target_2:.4f}" if goal_seek_result_target_2 is not None else "- **Scalar +2**: Error")

        # Save results to the temporary table
        save_results_to_temp_table(PIT_PD_1, PIT_PD_2, CPD_1, Marginal_PD_1, Marginal_PD_2,
                                    TTC_PD_1, TTC_PD_2, CPD_1_TTC, Marginal_PD_1_TTC, Marginal_PD_2_TTC)


        # Drop, insert, and delete as needed
        drop_bucket_table()
        insert_data_into_bucket()
        delete_data_from_pd_scalar()
        insert_data_from_bucket_to_pd_scalar()

        # Display results from BUCKET
        bucket_data = fetch_bucket_data()
        st.subheader("Data from BUCKET")
        st.dataframe(bucket_data)

        # Display results from PD_SCALAR
        pd_scalar_data = fetch_pd_scalar_data()
        st.subheader("Data from PD_SCALAR")
        st.dataframe(pd_scalar_data)

# To run the app:
if __name__ == "__main__":
    scaling_arima_page()
