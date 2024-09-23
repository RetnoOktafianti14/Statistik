import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
from sqlalchemy import create_engine, text
from db_connection import get_engine

def load_variables():
    try:
        engine = get_engine()
        query = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'combined_results_table'
              AND COLUMN_NAME NOT IN ('ODR', 'Date')
        """
        columns_df = pd.read_sql(query, engine)
        variables = columns_df['COLUMN_NAME'].tolist()
        return variables
    except Exception as e:
        st.error(f"Error loading variables: {e}")
        return []

def forecast_data(selected_variables):
    try:
        if not selected_variables:
            st.error("Please select at least one variable for forecasting.")
            return

        engine = get_engine()
        query = """
            SELECT DISTINCT
                a.*, 
                b.ODR AS "ODR actual",
                b.LOG_ODR as "ODR1"
            FROM 
                combined_results_table a
            LEFT JOIN 
                ODR_PIVOT b
            ON 
                a.Date = b.Reporting_Date
        """
        df = pd.read_sql(query, engine)
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['ODR actual'].fillna(0, inplace=True)
        df['ODR1'].fillna(0, inplace=True)
        df.sort_values(by='Date', inplace=True)
        df_filtered = df[df['ODR actual'] > 0].copy()
        X_filtered = df_filtered[selected_variables].apply(pd.to_numeric, errors='coerce')
        X_filtered.dropna(inplace=True)
        X_filtered = add_constant(X_filtered)
        y_filtered = pd.to_numeric(df_filtered['ODR1'], errors='coerce')
        model = OLS(y_filtered, X_filtered).fit()
        X_full = df[selected_variables].apply(pd.to_numeric, errors='coerce')
        X_full.dropna(inplace=True)
        X_full = add_constant(X_full)
        df['ODR Fitted'] = model.predict(X_full)
        df['ODD'] = np.exp(df['ODR Fitted'])
        df['ODR Model EXP'] = df['ODD'] / (1 + df['ODD'])
        df['Error'] = df['ODR actual'] - df['ODR Model EXP']
        df['Sqr error'] = df['Error'] ** 2

        last_val = df['ODD'].iloc[-1]
        max_val = df['ODD'].max()
        min_val = df['ODD'].min()
        avg_val = df['ODD'].mean()
        pit = avg_val
        avrg_odr = df['ODR actual'].mean()

        st.write(f"**Max ODD:** {max_val:.2f}")
        st.write(f"**Min ODD:** {min_val:.2f}")
        st.write(f"**Average ODD:** {avg_val:.2f}")
        st.write(f"**Last ODD:** {last_val:.2f}")
        st.write(f"**PIT (Average ODD):** {pit:.2f}")
        st.write(f"**Average ODR:** {avrg_odr:.2f}")

        st.write("### Results Table")
        st.dataframe(df[['Date', 'ODR actual', 'ODR Fitted', 'ODR Model EXP', 'ODD', 'Error', 'Sqr error']])

        st.write("### Forecasting Plot")
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(df['Date'], df['ODR actual'], label='ODR Actual', color='blue', linestyle='--', marker='o')
        ax.plot(df['Date'], df['ODD'], label='ODD', color='red', linestyle='-', marker='x')
        ax.set_xlabel('Date')
        ax.set_ylabel('ODR')
        ax.set_title('ODR Forecasting')
        ax.legend()
        st.pyplot(fig)

        # Save results automatically after forecasting
        save_results(df)

    except Exception as e:
        st.error(f"Error in forecasting data: {e}")

def save_results(df):
    try:
        if df.empty:
            st.info("No data to save.")
            return

        engine = get_engine()
        df.to_sql('forecasting_results_temp', con=engine, if_exists='replace', index=False)

        with engine.connect() as connection:
            try:
                truncate_query = "TRUNCATE TABLE result_summary;"
                connection.execute(text(truncate_query))

                insert_query = """
                WITH RankedData AS (
                    SELECT
                        'History' as Description,
                        ODD as Last,
                        [date],
                        ROW_NUMBER() OVER (ORDER BY [date] DESC) AS rn
                    FROM forecasting_results_temp
                    WHERE CONVERT(DECIMAL(18, 17), [odr actual]) > 0

                    UNION ALL

                    SELECT
                        CONVERT(NVARCHAR(5), YEAR([date])) as Description,
                        ODD as Last,
                        [date],
                        ROW_NUMBER() OVER (PARTITION BY YEAR([date]) ORDER BY [date] DESC) AS rn
                    FROM forecasting_results_temp
                    WHERE CONVERT(DECIMAL(18, 17), [odr actual]) <= 0
                    ),

                MaxValuesPerYear AS (
                    SELECT 'History' as Description, 
                        MAX(convert(decimal(18,17),ODD)) AS MaxODD,
                        MIN(convert(decimal(18,17),ODD)) AS MinODD,
                        AVG(convert(decimal(18,17),ODD)) AS AVGODD,
                        AVG(convert(decimal(18,17),ODD)) AS PIT,
                        AVG(convert(decimal(18,17),[ODR ACTUAL])) AS AVGODR
                    FROM forecasting_results_temp
                    WHERE CONVERT(DECIMAL(18, 17), [odr actual]) > 0
                    UNION ALL
                    SELECT
                        CONVERT(NVARCHAR(5), YEAR([date])) as Description,
                        MAX(convert(decimal(18,17),ODD)) AS MaxODD,
                        MIN(convert(decimal(18,17),ODD)) AS MinODD,
                        AVG(convert(decimal(18,17),ODD)) AS AVGODD,
                        AVG(convert(decimal(18,17),ODD)) AS PIT,
                        AVG(convert(decimal(18,17),[ODR ACTUAL])) AS AVGODR
                    FROM forecasting_results_temp
                    WHERE CONVERT(DECIMAL(18, 17), [odr actual]) <= 0
                    GROUP BY YEAR([date])
                )

                INSERT INTO result_summary (Description, Last, MaxODD, MinODD, AVGODD, PIT, AVGODR)
                SELECT
                    rd.Description,
                    rd.Last,
                    mv.MaxODD,
                    mv.MinODD,
                    mv.AVGODD,
                    mv.PIT,
                    mv.AVGODR
                FROM RankedData rd
                LEFT JOIN MaxValuesPerYear mv
                    ON rd.Description = mv.Description
                WHERE rd.rn = 1;
                """
                connection.execute(text(insert_query))

                st.success("Results saved to temporary table 'forecasting_results_temp' and summary table updated.")

            except Exception as exec_error:
                st.error(f"Error executing queries: {exec_error}")

    except Exception as e:
        st.error(f"Error saving results: {e}")

def forecasting_mev_page():
    st.title("Forecasting MEV Page")

    # Load variables and selection on the main page
    st.header("Select Variables for Forecasting")
    variables = load_variables()
    if not variables:
        return

    selected_variables = st.multiselect("Select variables for forecasting", variables)

    if st.button("Run Forecast"):
        forecast_data(selected_variables)

if __name__ == "__main__":
    forecasting_mev_page()
