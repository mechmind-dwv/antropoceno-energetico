# 🚀 Manual de Instalación - Proyecto Antropoceno Energético

## 📋 Requisitos del Sistema

### Hardware Mínimo:
- **CPU**: 4 núcleos (recomendado 8+)
- **RAM**: 8 GB (recomendado 16+ GB)
- **Almacenamiento**: 100 GB libres (los datos ERA5 son grandes)
- **GPU**: Opcional (acelera visualizaciones)

### Software Requerido:
- **Sistema Operativo**: Linux (Ubuntu 20.04+), macOS, o WSL2 en Windows
- **Python**: 3.9 o superior
- **Git**: Para control de versiones
- **Disk Space**: Para datos climáticos (~1-10 GB por archivo ERA5)

## 🔧 Instalación Paso a Paso

### 1. Clonar el Repositorio
```bash
git clone https://github.com/mechmind-dwv/antropoceno-energetico.git
cd antropoceno-energetico
```

### 2. Configurar Entorno Virtual
```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno
# Linux/macOS:
source venv/bin/activate
# Windows:
# venv\Scripts\activate
```

### 3. Instalar Dependencias
```bash
# Actualizar pip
pip install --upgrade pip setuptools wheel

# Instalar dependencias principales
pip install -r requirements.txt

# Si hay conflictos, instalar versiones específicas:
pip install packaging==24.0 protobuf==5.28.0
```

### 4. Configurar API CDS (para datos ERA5)
```bash
# 1. Registrarse en: https://cds.climate.copernicus.eu
# 2. Crear archivo de configuración:
cat > ~/.cdsapirc << 'EOF'
url: https://cds.climate.copernicus.eu/api/v2
key: TU_ID:TU_CLAVE_SECRETA
