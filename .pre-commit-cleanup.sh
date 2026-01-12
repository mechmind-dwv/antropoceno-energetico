#!/bin/bash
# Script para limpiar y commit automático con pre-commit

echo "🔧 Ejecutando pre-commit en archivos modificados..."

# Ejecutar pre-commit
pre-commit run --all-files

# Añadir archivos limpiados por pre-commit
git add -u

# Mostrar estado
echo "📊 Estado después de pre-commit:"
git status --short

# Preguntar por mensaje de commit
read -p "📝 Mensaje de commit: " commit_msg

if [ -n "$commit_msg" ]; then
    git commit -m "$commit_msg"
    echo "✅ Commit creado"
else
    echo "⚠️  Sin mensaje, no se creó commit"
fi
