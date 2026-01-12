#!/usr/bin/env python3
"""
Script profesional de descarga de ERA5 para el proyecto Antropoceno Energético.
Autor: Benjamín Cabeza Duran (@mechmind-dwv)
Uso: python descarga_era5.py --variable temperatura --year 2020
"""
import argparse
import logging
from datetime import datetime
from pathlib import Path

import cdsapi

# Configurar logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Mapeo de variables amigables a códigos ERA5
VARIABLES_ERA5 = {
    "temperatura": "2m_temperature",
    "precipitacion": "total_precipitation",
    "presion": "mean_sea_level_pressure",
    "viento_u": "10m_u_component_of_wind",
    "viento_v": "10m_v_component_of_wind",
    "humedad": "2m_dewpoint_temperature",
    "radiacion_solar": "surface_solar_radiation_downwards",
}


def descargar_era5(
    variable, year, month=None, area=None, output_dir="Datos/crudos/reanalisis"
):
    """
    Descarga datos ERA5 para una variable y año específicos.

    Args:
        variable (str): Nombre de la variable (ver VARIABLES_ERA5)
        year (int): Año a descargar
        month (int, optional): Mes específico. Si es None, descarga todo el año.
        area (list, optional): [Norte, Oeste, Sur, Este] para recortar región.
        output_dir (str): Directorio de salida.
    """

    # Verificar variable
    if variable not in VARIABLES_ERA5:
        logger.error(
            f"Variable '{variable}' no reconocida. Opciones: {list(VARIABLES_ERA5.keys())}"
        )
        return None

    codigo_era5 = VARIABLES_ERA5[variable]

    # Crear directorio de salida
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Nombre del archivo
    if month:
        filename = f"era5_{codigo_era5}_{year}_{month:02d}.nc"
        meses = [f"{month:02d}"]
    else:
        filename = f"era5_{codigo_era5}_{year}_anual.nc"
        meses = [f"{m:02d}" for m in range(1, 13)]

    filepath = output_path / filename

    # Si el archivo ya existe, no descargar de nuevo
    if filepath.exists():
        logger.info(f"✓ El archivo {filename} ya existe. Saltando descarga.")
        return str(filepath)

    # Configurar solicitud a CDS API
    c = cdsapi.Client()

    request_params = {
        "product_type": "reanalysis",
        "format": "netcdf",
        "variable": codigo_era5,
        "year": str(year),
        "month": meses,
        "day": [f"{d:02d}" for d in range(1, 32)],  # Todos los días
        "time": [f"{h:02d}:00" for h in range(24)],  # Todas las horas
    }

    # Añadir área si se especifica
    if area and len(area) == 4:
        request_params["area"] = area

    logger.info(f"Iniciando descarga de {variable} ({codigo_era5}) para {year}...")

    try:
        # Solicitar datos
        c.retrieve("reanalysis-era5-single-levels", request_params, str(filepath))
        logger.info(
            f"✓ Descarga completada: {filename} ({filepath.stat().st_size / 1e9:.2f} GB)"
        )
        return str(filepath)

    except Exception as e:
        logger.error(f"✗ Error en la descarga: {e}")
        return None


def main():
    """Función principal con interfaz de línea de comandos."""

    parser = argparse.ArgumentParser(
        description="Descargar datos ERA5 para investigación climática"
    )
    parser.add_argument(
        "--variable",
        "-v",
        choices=list(VARIABLES_ERA5.keys()),
        default="temperatura",
        help="Variable climática a descargar",
    )
    parser.add_argument("--year", "-y", type=int, default=2020, help="Año a descargar")
    parser.add_argument("--month", "-m", type=int, help="Mes específico (opcional)")
    parser.add_argument(
        "--area",
        "-a",
        type=float,
        nargs=4,
        metavar=("NORTE", "OESTE", "SUR", "ESTE"),
        help="Área de recorte [N, O, S, E]",
    )
    parser.add_argument(
        "--list-vars", action="store_true", help="Listar variables disponibles"
    )

    args = parser.parse_args()

    if args.list_vars:
        print("Variables disponibles para descarga:")
        for var_key, var_code in VARIABLES_ERA5.items():
            print(f"  {var_key:20} -> {var_code}")
        return

    # Ejecutar descarga
    resultado = descargar_era5(
        variable=args.variable, year=args.year, month=args.month, area=args.area
    )

    if resultado:
        print(f"\n✅ Descarga exitosa. Archivo: {resultado}")
        print(
            f"📊 Usa: python Codigo/analisis/python/analisis_era5.py --archivo {resultado}"
        )
    else:
        print("\n❌ La descarga falló. Revisa los mensajes de error.")


if __name__ == "__main__":
    main()
