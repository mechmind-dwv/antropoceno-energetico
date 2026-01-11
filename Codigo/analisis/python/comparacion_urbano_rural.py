#!/usr/bin/env python3
"""
Comparación científico-urbana: Temperatura Madrid vs. zona rural
Autor: Benjamín Cabeza Duran (@mechmind-dwv)
Proyecto: Antropoceno Energético
"""
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def extraer_serie_temporal(ds, lat, lon, nombre):
    """Extrae serie temporal para una coordenada específica."""
    # Encontrar el punto más cercano en la grilla
    lat_idx = np.abs(ds.latitude - lat).argmin()
    lon_idx = np.abs(ds.longitude - lon).argmin()

    # Extraer datos
    datos = ds["t2m"].isel(latitude=lat_idx, longitude=lon_idx)

    # Convertir de Kelvin a Celsius
    datos_celsius = datos - 273.15

    return datos_celsius, {
        "nombre": nombre,
        "lat_real": float(ds.latitude[lat_idx]),
        "lon_real": float(ds.longitude[lon_idx]),
        "lat_target": lat,
        "lon_target": lon,
    }


def main():
    """Análisis principal: Isla de calor urbana en Madrid."""

    # Cargar datos
    archivo = "Datos/crudos/reanalisis/era5_2m_temperature_2020_01.nc"

    if not Path(archivo).exists():
        logger.error(f"Archivo no encontrado: {archivo}")
        logger.info(
            "Descárgalo con: python Codigo/utiles/python/descarga_era5.py --variable temperatura --year 2020 --month 1"
        )
        return

    logger.info(f"Cargando datos de {archivo}")
    ds = xr.open_dataset(archivo)

    # Coordenadas (Madrid centro vs. zona rural)
    puntos = [
        {"nombre": "Madrid Centro", "lat": 40.4168, "lon": -3.7038},
        {"nombre": "Sierra Norte (Rural)", "lat": 40.9, "lon": -3.7},
        {"nombre": "Toledo (Ciudad Mediana)", "lat": 39.8628, "lon": -4.0273},
    ]

    # Extraer series temporales
    series = {}
    metadatos = {}

    for punto in puntos:
        serie, meta = extraer_serie_temporal(
            ds, punto["lat"], punto["lon"], punto["nombre"]
        )
        series[punto["nombre"]] = serie
        metadatos[punto["nombre"]] = meta

    # Análisis estadístico
    print("\n" + "=" * 70)
    print("ANÁLISIS: ISLA DE CALOR URBANA - ENERO 2020")
    print("=" * 70)

    resultados = []
    for nombre, serie in series.items():
        media = float(serie.mean())
        maximo = float(serie.max())
        minimo = float(serie.min())
        std = float(serie.std())

        resultados.append(
            {
                "Ubicación": nombre,
                "Latitud": metadatos[nombre]["lat_real"],
                "Longitud": metadatos[nombre]["lon_real"],
                "Temperatura Media (°C)": round(media, 2),
                "Temperatura Máx (°C)": round(maximo, 2),
                "Temperatura Mín (°C)": round(minimo, 2),
                "Variabilidad (σ)": round(std, 2),
            }
        )

        print(f"\n📍 {nombre}:")
        print(
            f"   Coordenadas reales: {metadatos[nombre]['lat_real']:.3f}°N, {metadatos[nombre]['lon_real']:.3f}°E"
        )
        print(f"   Temperatura media: {media:.2f}°C")
        print(f"   Rango: {minimo:.2f}°C a {maximo:.2f}°C")
        print(f"   Variabilidad diaria: {std:.2f}°C")

    # Calcular diferencia urbano-rural
    diff_madrid_rural = (
        resultados[0]["Temperatura Media (°C)"]
        - resultados[1]["Temperatura Media (°C)"]
    )
    print(f"\n🔥 DIFERENCIA URBANO-RURAL (Isla de Calor):")
    print(f"   Madrid - Sierra Norte: {diff_madrid_rural:.2f}°C")

    if diff_madrid_rural > 0:
        print(f"   → Efecto de isla de calor urbana DETECTADO")
    else:
        print(f"   → Patrón inesperado (investigar más)")

    # Visualización
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        "Análisis de Temperatura: Madrid vs. Zonas Alrededor (Enero 2020)", fontsize=16
    )

    # 1. Series temporales
    ax1 = axes[0, 0]
    for nombre, serie in series.items():
        ax1.plot(serie.valid_time, serie, label=nombre, linewidth=1.5)

    ax1.set_xlabel("Fecha")
    ax1.set_ylabel("Temperatura (°C)")
    ax1.set_title("Series Temporales de Temperatura")
    ax1.legend()
    ax1.grid(True, alpha=0.3)

    # 2. Comparación de promedios
    ax2 = axes[0, 1]
    nombres = [r["Ubicación"] for r in resultados]
    promedios = [r["Temperatura Media (°C)"] for r in resultados]

    bars = ax2.bar(nombres, promedios, color=["red", "green", "blue"], alpha=0.7)
    ax2.set_ylabel("Temperatura Media (°C)")
    ax2.set_title("Comparación de Temperaturas Medias")
    ax2.grid(True, alpha=0.3, axis="y")

    # Añadir valores en las barras
    for bar, valor in zip(bars, promedios):
        height = bar.get_height()
        ax2.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.1,
            f"{valor:.2f}°C",
            ha="center",
            va="bottom",
        )

    # 3. Mapa de ubicaciones
    ax3 = axes[1, 0]

    # Crear un mapa simple
    for i, resultado in enumerate(resultados):
        ax3.scatter(
            resultado["Longitud"],
            resultado["Latitud"],
            s=200,
            label=resultado["Ubicación"],
            zorder=5,
        )
        ax3.annotate(
            resultado["Ubicación"].split()[0],
            (resultado["Longitud"], resultado["Latitud"]),
            xytext=(5, 5),
            textcoords="offset points",
        )

    ax3.set_xlabel("Longitud")
    ax3.set_ylabel("Latitud")
    ax3.set_title("Ubicaciones de Análisis")
    ax3.grid(True, alpha=0.3)
    ax3.legend()

    # 4. Distribución de temperaturas
    ax4 = axes[1, 1]
    for nombre, serie in series.items():
        ax4.hist(serie.values, bins=30, alpha=0.5, label=nombre, density=True)

    ax4.set_xlabel("Temperatura (°C)")
    ax4.set_ylabel("Densidad")
    ax4.set_title("Distribución de Temperaturas")
    ax4.legend()
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()

    # Guardar resultados
    output_dir = Path("Resultados/finales/analisis_urbano")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Guardar figura
    fig_path = output_dir / "comparacion_madrid_rural.png"
    plt.savefig(fig_path, dpi=300, bbox_inches="tight")

    # Guardar datos como CSV
    df_resultados = pd.DataFrame(resultados)
    csv_path = output_dir / "resultados_temperatura.csv"
    df_resultados.to_csv(csv_path, index=False)

    # Guardar reporte
    reporte_path = output_dir / "reporte_analisis.txt"
    with open(reporte_path, "w") as f:
        f.write("=" * 70 + "\n")
        f.write("REPORTE CIENTÍFICO: ANÁLISIS ISLA DE CALOR URBANA\n")
        f.write("=" * 70 + "\n\n")
        f.write("DATOS: ERA5 - Temperatura a 2m - Enero 2020\n")
        f.write(f"Diferencia Madrid-Rural: {diff_madrid_rural:.2f}°C\n\n")

        for resultado in resultados:
            f.write(f"{resultado['Ubicación']}:\n")
            f.write(
                f"  Coordenadas: {resultado['Latitud']:.3f}°N, {resultado['Longitud']:.3f}°E\n"
            )
            f.write(f"  Temp Media: {resultado['Temperatura Media (°C)']}°C\n")
            f.write(
                f"  Rango: {resultado['Temperatura Mín (°C)']} a {resultado['Temperatura Máx (°C)']}°C\n"
            )
            f.write(f"  Variabilidad: {resultado['Variabilidad (σ)']}°C\n\n")

    print("\n" + "=" * 70)
    print("✅ ANÁLISIS COMPLETADO")
    print("=" * 70)
    print(f"📊 Gráficos guardados en: {fig_path}")
    print(f"📈 Datos guardados en: {csv_path}")
    print(f"📝 Reporte guardado en: {reporte_path}")
    print("\n🔥 CONCLUSIÓN PRELIMINAR:")
    if diff_madrid_rural > 1.0:
        print(
            f"   Se detecta una isla de calor urbana significativa ({diff_madrid_rural:.2f}°C)"
        )
    elif diff_madrid_rural > 0:
        print(f"   Existe una leve isla de calor urbana ({diff_madrid_rural:.2f}°C)")
    else:
        print(f"   Patrón inusual (se requiere investigación adicional)")

    plt.show()


if __name__ == "__main__":
    main()
