import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

# Cargamos las variables del archivo .env
load_dotenv()

def get_db_connection():
    """Retorna una conexión limpia a MySQL usando las variables de entorno."""
    try:
        conexion = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            database=os.getenv('DB_NAME')
        )
        if conexion.is_connected():
            return conexion
    except Error as e:
        print(f"Error crítico al conectar a la base de datos: {e}")
        return None