import pyodbc

# ==================================================
# CONFIGURATION - CHANGE THESE VALUES
# Must match the database created from database/ddl/SQLddl.sql
# (default name there is renewable_energy)
# ==================================================
SERVER_NAME = ""  #TODO
DATABASE_NAME = "renewable_energy"
USE_WINDOWS_AUTH = True

# Server Authentication if server has (username/password)
DB_USERNAME = ""  # USE_WINDOWS_AUTH = False
DB_PASSWORD = ""  # USE_WINDOWS_AUTH = False


def get_connection_string():
    if USE_WINDOWS_AUTH:
        raw = f"""
            DRIVER={{ODBC Driver 17 for SQL Server}};
            SERVER={SERVER_NAME};
            DATABASE={DATABASE_NAME};
            Trusted_Connection=yes;
        """
    else:
        raw = f"""
            DRIVER={{ODBC Driver 17 for SQL Server}};
            SERVER={SERVER_NAME};
            DATABASE={DATABASE_NAME};
            UID={DB_USERNAME};
            PWD={DB_PASSWORD};
        """
    return " ".join(raw.split())


def get_connection():
    """Returns a new database connection."""
    return pyodbc.connect(get_connection_string())