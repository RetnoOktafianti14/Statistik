import streamlit as st
import pandas as pd
import numpy as np
import statsmodels.api as sm
import scipy.stats as stats
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error
from db_connection import get_engine
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_columns():
    try:
        engine = get_engine()
        query = "SELECT * FROM TRANSFORMATION_OF_MEV WHERE 1=0"
        df = pd.read_sql(query, engine)
        columns = df.columns.tolist()

        if 'Date' in columns:
            columns.remove('Date')
        if 'ODR' in columns:
            columns.remove('ODR')

        return columns
    except Exception as e:
        logging.error(f"Error loading columns: {e}")
        st.error(f"Error loading columns: {e}")
        return []

def process_data(selected_x_cols):
    try:
        y_col = 'ODR'

        if not selected_x_cols:
            st.error("Please select at least one independent variable.")
            return

        engine = get_engine()
        query = f'SELECT [Date], [{y_col}], {", ".join([f"[{col}]" for col in selected_x_cols])} FROM TRANSFORMATION_OF_MEV ORDER BY [Date]'
        df = pd.read_sql(query, engine)

        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=[y_col])  # Drop rows where dependent variable is missing

        y_data = df[y_col]
        x_data = df[selected_x_cols]

        x_data = sm.add_constant(x_data)

        # Build and fit regression model
        model = sm.OLS(y_data, x_data).fit()

        # Save data to summary table
        save_to_summary_table(df)

        # Model Summary Table
        model_summary = {
            "Model": ["Model"],
            "R": [model.rsquared],
            "R Square": [model.rsquared],
            "Adjusted R Square": [model.rsquared_adj],
            "Std. Error of The Estimate": [model.bse.mean()]
        }
        model_summary_df = pd.DataFrame(model_summary)
        model_summary_str = model_summary_df.to_string(index=False)

        # ANOVA Table
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
        anova_df_str = anova_df.to_string(index=False)

        # Coefficients Table
        coefficients_df = pd.DataFrame({
            "Model": model.params.index,
            "Unstandardized Coef": model.params.values,
            "Std. Error": model.bse,
            "Standardized Coefficients": model.params / model.bse,
            "t": model.tvalues,
            "Sig.": model.pvalues
        })
        coefficients_df.index = ['Model'] * len(coefficients_df)
        coefficients_df_str = coefficients_df.to_string(index=False)

        # Forecast for next 4 years with annual intervals
        forecast_years = 4  # Number of years to forecast
        future_dates = [df['Date'].max() + timedelta(days=365 * i) for i in range(1, forecast_years + 1)]

        future_x_data = pd.DataFrame({
            col: [x_data[col].mean() + (i * 0.05)] * forecast_years
            for i, col in enumerate(selected_x_cols)
        })
        future_x_data = sm.add_constant(future_x_data, has_constant='add')

        if len(future_x_data.columns) != len(x_data.columns):
            raise ValueError("Mismatch in number of columns between training data and future data")

        forecast = model.predict(future_x_data)
        forecast_df = pd.DataFrame({
            "Year": [date.year for date in future_dates],
            "Forecast": forecast
        })
        forecast_str = forecast_df.to_string(index=False)

        # Calculate RMSE
        rmse = np.sqrt(mean_squared_error(y_data, model.fittedvalues))
    
        process_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        result_text = f"Model Summary:\n{model_summary_str}\n\n"
        result_text += f"ANOVA:\n{anova_df_str}\n\n"
        result_text += f"Coefficients:\n{coefficients_df_str}\n\n"
        result_text += f"RMSE: {rmse:.4f}\n\n"
        result_text += f"Forecast for 4 Years Ahead:\n{forecast_str}\n\n"
        result_text += f"Processed on: {process_date}"

        st.text(result_text)

        # Process ARIMA after saving data
        process_arima()
    except Exception as e:
        logging.error(f"Error during processing: {e}")
        st.error(f"Error during processing: {e}")


def process_arima():
    try:
        engine = get_engine()
        query = "SELECT * FROM summary_table ORDER BY Date ASC;"
        df = pd.read_sql(query, engine)

        logging.info("Data from summary_table loaded successfully.")
    
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        df.drop(columns=['Date'], inplace=True, errors='ignore')

        target_variables = df.columns.tolist()
        forecasts = []

        logging.info(f"Target variables for ARIMA: {target_variables}")

        for target in target_variables:
            train_size = int(len(df) * 0.05)
            train, test = df[target][:train_size], df[target][train_size:]
    
            logging.info(f"Training ARIMA model for {target}.")

            model = ARIMA(train, order=(2, 1, 2))  # Sesuaikan parameter (p, d, q) sesuai kebutuhan
            model_fit = model.fit()

            y_pred = model_fit.predict(start=test.index[0], end=test.index[-1], typ='levels')
            mse = mean_squared_error(test, y_pred)
            logging.info(f"Mean Squared Error untuk {target}: {mse}")

            forecast_periods = 48
            forecast_index = pd.date_range(start=df.index.max() + pd.DateOffset(days=1), periods=forecast_periods, freq='ME')
            forecast = model_fit.get_forecast(steps=forecast_periods).predicted_mean
            forecast_df = pd.DataFrame({
                'Date': forecast_index,
                f'{target}_forecast': forecast
            }).set_index('Date')

            forecasts.append(forecast_df)

        forecast_results = pd.concat(forecasts, axis=1)

        logging.info("Forecast results compiled successfully.")

        save_forecast_to_summary_table(forecast_results)
        merge_and_save()
    except Exception as e:
        logging.error(f"Error during ARIMA processing: {e}")
        st.error(f"Error during ARIMA processing: {e}")

def save_to_db(df, table_name):
    try:
        engine = get_engine()
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        logging.info(f"Data successfully saved to '{table_name}'.")
    except Exception as e:
        logging.error(f"Error saving data to {table_name}: {e}")
        st.error(f"Error saving data to {table_name}: {e}")

# Modify save_to_summary_table function
def save_to_summary_table(df):
    save_to_db(df, 'summary_table')

# Modify save_forecast_to_summary_table function
def save_forecast_to_summary_table(forecast_results):
    save_to_db(forecast_results, 'arima_forecast_table')

# Modify merge_and_save function
def merge_and_save():
    try:
        engine = get_engine()
        df = pd.read_sql('summary_table', engine)
        arima_df = pd.read_sql('arima_forecast_table', engine)

        merged_df = pd.merge(df, arima_df, left_index=True, right_index=True, how='left')
        save_to_db(merged_df, 'merged_table')
    except Exception as e:
        logging.error(f"Error merging and saving data: {e}")
        st.error(f"Error merging and saving data: {e}")

def regression_page():
    st.header('Regresi Analisis')

    columns = load_columns()
    if columns:
        selected_x_cols = st.multiselect('Pilih Variabel Independen:', columns)
        if st.button('Proses Data'):
            with st.spinner('Memproses data...'):
                process_data(selected_x_cols)

def arima_page():
    st.header('Analisis ARIMA')
    if st.button('Jalankan ARIMA'):
        with st.spinner('Memproses ARIMA...'):
            process_arima()

# Main function remains the same
def main():
    st.title('Aplikasi Analisis Statistik')

    page = st.sidebar.selectbox('Pilih Halaman', ['Regresi', 'ARIMA'])

    if page == 'Regresi':
        regression_page()
    elif page == 'ARIMA':
        arima_page()

if __name__ == '__main__':
    main()

