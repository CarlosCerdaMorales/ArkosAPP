import os
import sys
import psycopg2
from urllib.parse import urlparse

def fix_database():
    print("🔧 INICIANDO REPARACIÓN DE ESQUEMA DE BASE DE DATOS...")
    
    # 1. Obtener la URL de la base de datos
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("❌ Error: No se encontró DATABASE_URL")
        sys.exit(1)

    # 2. Parsear la URL para sacar usuario y contraseña
    result = urlparse(db_url)
    username = result.username
    password = result.password
    database = result.path[1:]
    hostname = result.hostname
    port = result.port
    
    # Usamos el nombre de usuario como nombre del esquema (estándar en shared hosting)
    schema_name = username

    print(f"📡 Conectando a {hostname} para el usuario {username}...")

    try:
        # 3. Conexión manual (sin Django)
        conn = psycopg2.connect(
            database=database,
            user=username,
            password=password,
            host=hostname,
            port=port,
            sslmode='disable' # Importante para Filess.io
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # 4. INTENTO 1: Crear el esquema con el nombre del usuario
        print(f"🔨 Intentando crear esquema: '{schema_name}'...")
        try:
            cursor.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}";')
            print("✅ Esquema creado (o ya existía).")
        except Exception as e:
            print(f"⚠️ No se pudo crear el esquema (quizás ya existe o falta permisos): {e}")

        # 5. INTENTO 2: Forzar al usuario a usar ese esquema por defecto
        print(f"⚙️ Configurando search_path para el usuario...")
        cursor.execute(f'ALTER ROLE "{username}" SET search_path TO "{schema_name}";')
        print("✅ search_path configurado correctamente.")

        cursor.close()
        conn.close()
        print("🎉 REPARACIÓN COMPLETADA. Ahora Django debería funcionar.")

    except Exception as e:
        print(f"❌ ERROR FATAL EN EL SCRIPT DE REPARACIÓN:\n{e}")
        # No salimos con error sys.exit(1) para dejar que Django intente seguir,
        # pero es probable que falle si esto falló.

if __name__ == "__main__":
    fix_database()