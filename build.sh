#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Entrar en la carpeta del proyecto
cd arkosStore

# 3. --- NUEVO --- EJECUTAR EL SCRIPT DE REPARACIÓN DE BBDD
# (Tenemos que volver atrás un momento porque el script está en la raíz)
cd ..
python fix_db.py
cd arkosStore
# -----------------------------------------------------------

# 4. Recopilar archivos estáticos
python manage.py collectstatic --no-input

# 5. Aplicar migraciones (Ahora debería funcionar)
python manage.py migrate

# 6. Seed condicional
if [ "$EJECUTAR_SEED" == "True" ]; then
    echo "⚠️ ATENCIÓN: Variable EJECUTAR_SEED detectada. Borrando y creando datos..."
    python manage.py seed_data
else
    echo "✅ Salto de seguridad: NO se ejecutará el seed."
fi