import pyodbc
from sqlalchemy import create_engine

def get_connection():
    # Format koneksi ODBC untuk pyodbc (menggunakan username dan password)
    connection_str = "Driver={SQL Server};Server=103.81.249.209,4399;Database=IFINANCING_PSAK71;UID=your_username;PWD=your_password;"
    return pyodbc.connect(connection_str)

def close_connection(conn):
    conn.close()

def get_engine():
    # Format koneksi untuk SQLAlchemy
    connection_string = 'mssql+pyodbc://sa:S4D3v@103.81.249.209:4399/IFINANCING_PSAK71?driver=ODBC+Driver+17+for+SQL+Server'
    try:
        engine = create_engine(connection_string)
        print("Engine created successfully!")
        return engine
    except Exception as e:
        print(f"Failed to create engine: {str(e)}")

# Test the functions
if __name__ == "__main__":
    # Test connection
    try:
        conn = get_connection()
        print("Connection to SQL Server successful!")
        close_connection(conn)
    except Exception as e:
        print(f"Connection failed: {str(e)}")

    # Test engine creation
    engine = get_engine()
