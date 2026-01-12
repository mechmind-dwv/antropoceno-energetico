#!/usr/bin/env python3
"""
Análisis básico de datos ERA5 descargados.
"""
import argparse
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import xarray as xr

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
    print(f"📅 Rango temporal: {ds.time.min().values} a {ds.time.max().values}")
    print(f"🌍 Dimensión espacial: {ds.latitude.shape[0]}x{ds.longitude.shape[0]}")

    # Análisis de la primera variable
    primera_var = list(ds.data_vars.keys())[0]
    datos = ds[primera_var]

    print(f"\n📈 Estadísticas para '{primera_var}':")
    print(f"   Media global: {float(datos.mean().values):.2f}")
    print(f"   Desviación estándar: {float(datos.std().values):.2f}")
    print(f"   Mínimo: {float(datos.min().values):.2f}")
    print(f"   Máximo: {float(datos.max().values):.2f}")

    # Generar gráfico simple
    if "time" in datos.dims:
        # Promedio espacial a lo largo del tiempo
        serie_temporal = datos.mean(dim=["latitude", "longitude"])

        plt.figure(figsize=(10, 5))
        serie_temporal.plot()
        plt.title(f"Serie Temporal de {primera_var} (Promedio Global)")
        plt.xlabel("Fecha")
        plt.ylabel(primera_var)
        plt.grid(True, alpha=0.3)

        # Guardar figura
        output_dir = Path("Resultados/intermedios/figuras")
        output_dir.mkdir(parents=True, exist_ok=True)

        archivo_figura = output_dir / f"era5_{primera_var}_serie_temporal.png"
        plt.savefig(archivo_figura, dpi=150, bbox_inches="tight")
        plt.close()

        print(f"\n📊 Gráfico guardado en: {archivo_figura}")

    print("\n" + "=" * 60)
    print("✅ Análisis completado. El dataset está listo para análisis avanzado.")
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
        return

    analizar_archivo_era5(args.archivo)


if __name__ == "__main__":
    main()
