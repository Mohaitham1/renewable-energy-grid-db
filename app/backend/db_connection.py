import pyodbc

# ==================================================
# CONFIGURATION - CHANGE THESE VALUES
# ==================================================
SERVER_NAME   = "" #TODO: Put server name
DATABASE_NAME = "RenewableEnergyGrid"
USE_WINDOWS_AUTH = True

# Server Authentication if server has (username/password) 
DB_USERNAME = "" #USE_WINDOWS_AUTH = False
DB_PASSWORD = "" #USE_WINDOWS_AUTH = False

# ==================================================
# CONNECTION STRING
# ==================================================
def get_connection_string():
    if USE_WINDOWS_AUTH:
        return f"""
            DRIVER={{ODBC Driver 17 for SQL Server}};
            SERVER={SERVER_NAME};
            DATABASE={DATABASE_NAME};
            Trusted_Connection=yes;
        """
    else:
        return f"""
            DRIVER={{ODBC Driver 17 for SQL Server}};
            SERVER={SERVER_NAME};
            DATABASE={DATABASE_NAME};
            UID={DB_USERNAME};
            PWD={DB_PASSWORD};
        """

def get_connection():
    """Returns a new database connection."""
    conn_str = get_connection_string()
    return pyodbc.connect(conn_str)