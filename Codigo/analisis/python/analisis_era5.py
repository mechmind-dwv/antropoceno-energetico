#!/usr/bin/env python3
"""
Análisis básico de datos ERA5 descargados.
Versión corregida para la estructura real de datos ERA5.
"""
import xarray as xr
import matplotlib.pyplot as plt
import argparse
from pathlib import Path
import logging
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def analizar_archivo_era5(archivo_nc):
    """Analiza un archivo NetCDF de ERA5."""

    logger.info(f"Analizando {archivo_nc}")

    # Abrir el dataset
    ds = xr.open_dataset(archivo_nc)

    print("\n" + "=" * 60)
    print(f"INFORMACIÓN DEL DATASET: {Path(archivo_nc).name}")
    print("=" * 60)

    # Información básica
    print(f"📊 Variables disponibles: {list(ds.data_vars.keys())}")
    print(f"📊 Dimensiones disponibles: {list(ds.dims.keys())}")
    print(f"📊 Coordenadas disponibles: {list(ds.coords.keys())}")

    # Encontrar la dimensión temporal (puede ser 'time' o 'valid_time')
    time_dim = None
    for possible_time in ["valid_time", "time", "t"]:
        if possible_time in ds.dims:
            time_dim = possible_time
            break

    if time_dim:
        print(f"📅 Dimensión temporal encontrada: '{time_dim}'")
        print(
            f"📅 Rango temporal: {ds[time_dim].min().values} a {ds[time_dim].max().values}"
        )
    else:
        print("⚠️  No se encontró dimensión temporal clara")

    # Información espacial
    lat_dim = "latitude" if "latitude" in ds.dims else "lat"
    lon_dim = "longitude" if "longitude" in ds.dims else "lon"

    if lat_dim in ds.dims and lon_dim in ds.dims:
        print(f"🌍 Resolución espacial: {ds[lat_dim].shape[0]}x{ds[lon_dim].shape[0]}")
        print(f"🌍 Latitud: [{float(ds[lat_dim].min())}, {float(ds[lat_dim].max())}]")
        print(f"🌍 Longitud: [{float(ds[lon_dim].min())}, {float(ds[lon_dim].max())}]")

    # Análisis de la primera variable
    if len(ds.data_vars) > 0:
        primera_var = list(ds.data_vars.keys())[0]
        datos = ds[primera_var]

        print(f"\n📈 Estadísticas para '{primera_var}':")
        print(f"   Unidades: {datos.attrs.get('units', 'No especificadas')}")
        print(f"   Media global: {float(datos.mean().values):.2f}")
        print(f"   Desviación estándar: {float(datos.std().values):.2f}")
        print(f"   Mínimo: {float(datos.min().values):.2f}")
        print(f"   Máximo: {float(datos.max().values):.2f}")

        # Generar gráfico si hay dimensión temporal
        if time_dim and time_dim in datos.dims:
            # Promedio espacial a lo largo del tiempo
            if lat_dim in datos.dims and lon_dim in datos.dims:
                serie_temporal = datos.mean(dim=[lat_dim, lon_dim])

                plt.figure(figsize=(10, 5))
                serie_temporal.plot()
                plt.title(f"Serie Temporal de {primera_var} (Promedio Espacial)")
                plt.xlabel("Fecha")
                plt.ylabel(f"{primera_var} ({datos.attrs.get('units', '')})")
                plt.grid(True, alpha=0.3)

                # Guardar figura
                output_dir = Path("Resultados/intermedios/figuras")
                output_dir.mkdir(parents=True, exist_ok=True)

                archivo_figura = output_dir / f"era5_{primera_var}_serie_temporal.png"
                plt.savefig(archivo_figura, dpi=150, bbox_inches="tight")
                plt.close()

                print(f"\n📊 Gráfico de serie temporal guardado en: {archivo_figura}")

            # Mapa de promedio temporal
            if datos.ndim >= 3:  # Tiene dimensiones espaciales
                mapa_promedio = datos.mean(dim=time_dim)

                plt.figure(figsize=(12, 6))
                mapa_promedio.plot(cmap="RdBu_r", robust=True)
                plt.title(f"Mapa de {primera_var} (Promedio Temporal - Enero 2020)")
                plt.xlabel("Longitud")
                plt.ylabel("Latitud")

                archivo_mapa = output_dir / f"era5_{primera_var}_mapa_promedio.png"
                plt.savefig(archivo_mapa, dpi=150, bbox_inches="tight")
                plt.close()

                print(f"📊 Mapa espacial guardado en: {archivo_mapa}")

    print("\n" + "=" * 60)
    print("✅ Análisis completado. Dataset listo para análisis avanzado.")
    print("=" * 60)

    return ds


def main():
    parser = argparse.ArgumentParser(description="Analizar archivos ERA5 descargados")
    parser.add_argument(
        "--archivo", "-a", required=True, help="Ruta al archivo NetCDF de ERA5"
    )

    args = parser.parse_args()

    if not Path(args.archivo).exists():
        logger.error(f"El archivo {args.archivo} no existe.")
        print("💡 Sugerencia: Primero descarga datos con:")
        print(
            "   python Codigo/utiles/python/descarga_era5.py --variable temperatura --year 2020 --month 1"
        )
        return

    analizar_archivo_era5(args.archivo)


if __name__ == "__main__":
    main()
