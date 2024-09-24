import streamlit as st
import pandas as pd
import numpy as np
import logging
from datetime import datetime
from db_connection import get_engine
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error, mean_absolute_percentage_error
from scipy import stats

# Setup logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_columns():
    try:
        engine = get_engine()
        query = "SELECT Variable FROM normalization_temp"
        df = pd.read_sql(query, engine)
        return df.Variable.tolist()
    except Exception as e:
        logging.error(f"Error loading columns: {e}")
        return []

def save_to_summary_table(df):
    try:
        engine = get_engine()
        df.to_sql('summary_table', engine, if_exists='replace', index=False)
        logging.info("Data successfully saved to 'summary_table'.")
    except Exception as e:
        logging.error(f"Error saving data: {e}")

#def save_forecast_to_summary_table(forecast_results):
    #try:
        #engine = get_engine()
        #if forecast_results.empty:
            #raise ValueError("Forecast results DataFrame is empty.")
        
        #forecast_results.to_sql('arima_forecast_table', engine, if_exists='replace', index=True)
        #logging.info("Forecast data successfully saved to 'arima_forecast_table'.")
    #except Exception as e:
        #logging.error(f"Error saving forecast data: {e}")


def merge_and_save():
    try:
        engine = get_engine()
        union_query = """
        SELECT *
        FROM summary_table
        UNION ALL
        SELECT *
        FROM arima_forecast_table
        """
        combined_df = pd.read_sql(union_query, engine)
        combined_df.to_sql('combined_results_table', engine, if_exists='replace', index=False)
        logging.info("Data successfully merged and saved to 'combined_results_table'.")
    except Exception as e:
        logging.error(f"Error merging and saving tables: {e}")
        st.error(f"Error merging and saving tables: {e}")


def process_data(y_col, x_cols):
    try:
        engine = get_engine()
        query = f'SELECT [Date], [{y_col}], {", ".join([f"[{col}]" for col in x_cols])} FROM TRANSFORMATION_OF_MEV ORDER BY [Date]'
        df = pd.read_sql(query, engine)

        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df.dropna(subset=[y_col], inplace=True)

        y_data = df[y_col]
        x_data = df[x_cols]
        x_data = sm.add_constant(x_data)

        model = sm.OLS(y_data, x_data).fit()

        columns_order = ['Date'] + [col for col in x_cols if col in df.columns]
        df = df[columns_order]

        save_to_summary_table(df)

        model_summary = {
            "Model": ["Model"],
            "R": [model.rsquared],
            "R Square": [model.rsquared],
            "Adjusted R Square": [model.rsquared_adj],
            "Std. Error of The Estimate": [model.bse.mean()]
        }
        model_summary_df = pd.DataFrame(model_summary)

        # ANOVA
        ss_total = ((y_data - y_data.mean()) ** 2).sum()
        ss_reg = ((model.fittedvalues - y_data.mean()) ** 2).sum()
        ss_res = ((y_data - model.fittedvalues) ** 2).sum()

        df_total = len(y_data) - 1
        df_reg = len(x_data.columns) - 1
        df_res = df_total - df_reg

        ms_reg = ss_reg / df_reg
        ms_res = ss_res / df_res

        f_value = ms_reg / ms_res
        p_value = 1 - stats.f.cdf(f_value, df_reg, df_res)

        anova_summary = {
            "Model": ["Regression", "Residual", "Total"],
            "Sum of Squares": [ss_reg, ss_res, ss_total],
            "df": [df_reg, df_res, df_total],
            "Mean Square": [ms_reg, ms_res, None],
            "F": [f_value, None, None],
            "Sig.": [p_value, None, None]
        }
        anova_df = pd.DataFrame(anova_summary)

        coefficients_df = pd.DataFrame({
            "Model": model.params.index,
            "Unstandardized Coef": model.params.values,
            "Std. Error": model.bse,
            "Standardized Coefficients": model.params / model.bse,
            "t": model.tvalues,
            "Sig.": model.pvalues
        })
        coefficients_df.index = ['Model'] * len(coefficients_df)

        # RMSE
        rmse = np.sqrt(mean_squared_error(y_data, model.fittedvalues))

        return model_summary_df, anova_df, coefficients_df, rmse

    except Exception as e:
        logging.error(f"Error during processing: {e}")
        return None, None, None, None

def process_arima():
    try:
        engine = get_engine()
        query = "SELECT * FROM summary_table ORDER BY Date ASC;"
        df = pd.read_sql(query, engine)

        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        df.drop(columns=['Date'], inplace=True, errors='ignore')

        if df.empty:
            st.warning("Data untuk model ARIMA kosong.")
            return None

        target_variables = df.columns.tolist()
        model_results = []

        for target in target_variables:
            # Model configurations
            p_values = [0, 1, 2]
            d_values = [0, 1]
            q_values = [0, 1, 2]

            for p in p_values:
                for d in d_values:
                    for q in q_values:
                        try:
                            model = ARIMA(df[target], order=(p, d, q))
                            model_fit = model.fit()

                            # Calculate RMSE
                            rmse = np.sqrt(mean_squared_error(df[target], model_fit.fittedvalues))

                            # Store results
                            model_results.append({
                                "Model": f"ARIMA({p},{d},{q})",
                                "RMSE": rmse,
                            })

                        except Exception as e:
                            logging.warning(f"Model ARIMA({p},{d},{q}) failed: {e}")

        if model_results:
            results_df = pd.DataFrame(model_results)
            results_df.sort_values(by="RMSE", ascending=True, inplace=True)
            save_forecast_to_summary_results(results_df)
            #merge_and_save()
            return results_df
        else:
            st.warning("No valid ARIMA models were found.")
            return None

    except Exception as e:
        logging.error(f"Error during ARIMA processing: {e}")
        st.error(f"Error during ARIMA processing: {e}")
        return None

def save_forecast_to_summary_results(results_df):
    try:
        engine = get_engine()
        results_df.to_sql('arima_forecast_results', engine, if_exists='replace', index=False)
        logging.info("Forecast results successfully saved to 'arima_forecast_results'.")
    except Exception as e:
        logging.error(f"Error saving forecast results: {e}")

def process_arima2():
    try:
        engine = get_engine()
        query = "SELECT * FROM summary_table ORDER BY Date ASC;"
        df = pd.read_sql(query, engine)

        # Pastikan kolom 'Date' dalam format datetime dan jadikan sebagai index
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)

        # Menghapus kolom 'Date' jika masih ada (untuk berjaga-jaga)
        df.drop(columns=['Date'], inplace=True, errors='ignore')

        # List variabel target yang akan di-forecast
        target_variables = df.columns.tolist()
        forecasts = []

        # Proyeksi selama 48 bulan (4 tahun)
        forecast_periods = 48

        for target in target_variables:
            # Tentukan jumlah data yang akan digunakan sebagai training (misalnya 95% dari data)
            train_size = int(len(df) * 0.05)
            train, test = df[target][:train_size], df[target][train_size:]

            # Buat model ARIMA, disesuaikan dengan data (order=(2, 1, 2) dapat diubah sesuai kebutuhan)
            model = ARIMA(train, order=(2, 0, 2))
            model_fit = model.fit()

            # Buat index tanggal untuk 48 bulan ke depan (asumsi data bulanan)
            forecast_index = pd.date_range(start=df.index.max() + pd.DateOffset(months=1), periods=forecast_periods, freq='M')

            # Lakukan forecasting selama 48 bulan
            forecast = model_fit.get_forecast(steps=forecast_periods).predicted_mean

            # Simpan hasil forecast dalam DataFrame
            forecast_df = pd.DataFrame({
                'Date': forecast_index,
                f'{target}_forecast': forecast
            }).set_index('Date')

            # Gabungkan hasil forecast dari setiap variabel
            forecasts.append(forecast_df)

        # Gabungkan semua hasil forecast untuk setiap variabel menjadi satu DataFrame
        forecast_results = pd.concat(forecasts, axis=1)

        # Simpan hasil forecast ke dalam tabel summary_table
        save_forecast_to_summary_table(forecast_results)
        merge_and_save()

        # Tampilkan hasil forecast dalam aplikasi
        st.dataframe(forecast_results)

    except Exception as e:
        st.error(f"Error during ARIMA processing: {e}")


def save_forecast_to_summary_table(forecast_results):
    try:
        engine = get_engine()
        if forecast_results.empty:
            raise ValueError("Forecast results DataFrame is empty.")
        
        forecast_results.to_sql('arima_forecast_table', engine, if_exists='replace', index=True)
        logging.info("Forecast data successfully saved to 'arima_forecast_table'.")
    except Exception as e:
        logging.error(f"Error saving forecast data: {e}")
        st.error(f"Error saving forecast data: {e}")


def regression_page():
    st.title("Regresi dan ARIMA")

    x_cols = load_columns()
    y_col = 'ODR'

    selected_x = st.multiselect("Pilih Variabel Independen (X):", x_cols)

    if st.button("Mulai Proses"):
        if not selected_x:
            st.warning("Silakan pilih setidaknya satu variabel independen.")
        else:
            model_summary_df, anova_df, coefficients_df, rmse = process_data(y_col, selected_x)

            if model_summary_df is not None:
                st.subheader("Ringkasan Model")
                st.write(model_summary_df)

                st.subheader("ANOVA")
                st.write(anova_df)

                st.subheader("Koefisien")
                st.write(coefficients_df)

                #st.subheader("RMSE")
                #st.write(f"RMSE: {rmse:.4f}")

                # Proses ARIMA dan tampilkan hasilnya
                arima_results_df = process_arima()

                if arima_results_df is not None:
                    st.subheader("Hasil ARIMA")
                    st.write(arima_results_df)

                      # Menentukan koefisien terbaik
                    if coefficients_df is not None and not coefficients_df.empty:
                        best_coefficient = coefficients_df.loc[coefficients_df['Sig.'] < 0.05].nlargest(1, 'Unstandardized Coef')
                        st.subheader("Koefisien Terbaik")
                        st.write(best_coefficient)

                    # Menentukan model ARIMA terbaik
                    if not arima_results_df.empty:
                        best_arima_model = arima_results_df.nsmallest(1, 'RMSE')
                        st.subheader("Model ARIMA Terbaik")
                        st.write(best_arima_model)

                    
                # Call process_arima2 and display results
                st.subheader("Hasil Proses ARIMA 2")
                arima2_results_df = process_arima2()
                if arima2_results_df is not None:
                    st.write(arima2_results_df)

if __name__ == "__main__":
    regression_page()
