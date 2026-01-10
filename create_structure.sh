#!/bin/bash

echo "Creando estructura del proyecto Antropoceno Energético..."

# Directorios principales
mkdir -p {Experimentos,Documentacion,Datos,Codigo,Resultados,Infraestructura}

# Estructura de Experimentos
mkdir -p Experimentos/{1_Calor_Residual,2_Telecomunicaciones,3_Ionosfera,4_Modelos_Globales}/{{data,scripts,config,output,analysis,plots},{protocolos,instrumentacion}}

# Documentación
mkdir -p Documentacion/{propuestas,protocolos,publicaciones,presentaciones,revisiones_bibliograficas,manuales}

# Datos
mkdir -p Datos/{crudos,procesados,derivados}/{satelitales,terrestres,modelos,reanalisis,observacionales}

# Código
mkdir -p Codigo/{modelado,analisis,visualizacion,utiles}/{python,R,bash,fortran,julia}

# Resultados
mkdir -p Resultados/{intermedios,finales}/{figuras,tablas,datasets,modelos}

# Infraestructura
mkdir -p Infraestructura/{hpc_config,docker,kubernetes,monitoreo,backup}

# Archivos de configuración base
touch README.md .gitignore LICENSE .env.example
touch requirements.txt environment.yml Dockerfile
touch Makefile setup.py

echo "Estructura creada exitosamente!"
