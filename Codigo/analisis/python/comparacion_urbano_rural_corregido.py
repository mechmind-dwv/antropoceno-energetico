#!/usr/bin/env python3
"""
Comparación científico-urbana CORREGIDA: Temperatura Madrid vs. zona rural
Coordenadas CORRECTAS para España.
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
    """Análisis principal CORREGIDO con coordenadas reales de España."""

    # Cargar datos
    archivo = "Datos/crudos/reanalisis/era5_2m_temperature_2020_01.nc"

    if not Path(archivo).exists():
        logger.error(f"Archivo no encontrado: {archivo}")
        return

    logger.info(f"Cargando datos de {archivo}")
    ds = xr.open_dataset(archivo)

    # Coordenadas CORRECTAS para España (Madrid: ~40.4N, 3.7W)
    # Nota: ERA5 usa longitudes de 0 a 360°, así que -3.7°W = 356.3°E
    puntos = [
        {"nombre": "Madrid Centro", "lat": 40.4168, "lon": 356.3},  # -3.7°W convertido
        {"nombre": "Sierra Norte (Rural)", "lat": 41.0, "lon": 356.3},
        {"nombre": "Toledo", "lat": 39.8628, "lon": 356.0},  # -4.0°W = 356.0°E
        {"nombre": "Zona rural Andalucía", "lat": 37.5, "lon": 355.0},
        {"nombre": "Barcelona", "lat": 41.3851, "lon": 358.5},  # 1.5°E = 358.5°E
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
    print("ANÁLISIS CORREGIDO: ISLA DE CALOR URBANA - ENERO 2020")
    print("Coordenadas REALES de España")
    print("=" * 70)

    resultados = []
    for nombre, serie in series.items():
        media = float(serie.mean())
        maximo = float(serie.max())
        minimo = float(serie.min())
        std = float(serie.std())

        # Convertir longitud ERA5 (0-360) a longitud normal (-180 a 180)
        lon_real = metadatos[nombre]["lon_real"]
        lon_normal = lon_real if lon_real <= 180 else lon_real - 360

        resultados.append(
            {
                "Ubicación": nombre,
                "Latitud": metadatos[nombre]["lat_real"],
                "Longitud_ERA5": lon_real,
                "Longitud_Normal": lon_normal,
                "Temperatura Media (°C)": round(media, 2),
                "Temperatura Máx (°C)": round(maximo, 2),
                "Temperatura Mín (°C)": round(minimo, 2),
                "Variabilidad (σ)": round(std, 2),
            }
        )

        print(f"\n📍 {nombre}:")
        print(
            f"   Coordenadas: {metadatos[nombre]['lat_real']:.3f}°N, {lon_normal:.3f}°E"
        )
        print(f"   Temperatura media: {media:.2f}°C")
        print(f"   Rango: {minimo:.2f}°C a {maximo:.2f}°C")
        print(f"   Variabilidad diaria: {std:.2f}°C")

    # Calcular diferencia urbano-rural
    # Buscar Madrid y Sierra Norte en resultados
    madrid_temp = next(
        r["Temperatura Media (°C)"] for r in resultados if "Madrid" in r["Ubicación"]
    )
    sierra_temp = next(
        r["Temperatura Media (°C)"]
        for r in resultados
        if "Sierra Norte" in r["Ubicación"]
    )

    diff_madrid_rural = madrid_temp - sierra_temp

    print(f"\n🔥 DIFERENCIA URBANO-RURAL (Isla de Calor):")
    print(f"   Madrid - Sierra Norte: {diff_madrid_rural:.2f}°C")

    if diff_madrid_rural > 0.5:
        print(f"   ✅ Efecto de isla de calor urbana DETECTADO (> 0.5°C)")
    elif diff_madrid_rural > 0:
        print(f"   ⚠️  Leve isla de calor ({diff_madrid_rural:.2f}°C)")
    elif diff_madrid_rural > -0.5:
        print(f"   🔄 Sin diferencia significativa ({diff_madrid_rural:.2f}°C)")
    else:
        print(
            f"   ❓ Patrón inusual: zona rural más cálida ({diff_madrid_rural:.2f}°C)"
        )
        print(f"   Posibles causas: inversión térmica, topografía, error en datos")

    # Visualización mejorada
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        "Análisis de Temperatura en España (Enero 2020) - Coordenadas Corregidas",
        fontsize=16,
    )

    # 1. Series temporales
    ax1 = axes[0, 0]
    for nombre, serie in series.items():
        ax1.plot(serie.valid_time, serie, label=nombre, linewidth=1.5, alpha=0.8)

    ax1.set_xlabel("Fecha")
    ax1.set_ylabel("Temperatura (°C)")
    ax1.set_title("Series Temporales")
    ax1.legend(loc="upper left", fontsize=8)
    ax1.grid(True, alpha=0.3)

    # 2. Comparación de promedios
    ax2 = axes[0, 1]
    nombres = [r["Ubicación"] for r in resultados]
    promedios = [r["Temperatura Media (°C)"] for r in resultados]

    colors = [
        "red" if "Madrid" in n else "green" if "Sierra" in n else "blue"
        for n in nombres
    ]
    bars = ax2.bar(nombres, promedios, color=colors, alpha=0.7)
    ax2.set_ylabel("Temperatura Media (°C)")
    ax2.set_title("Comparación de Temperaturas Medias")
    ax2.set_xticklabels(nombres, rotation=45, ha="right")
    ax2.grid(True, alpha=0.3, axis="y")

    # 3. Mapa de España con puntos
    ax3 = axes[1, 0]

    # Crear un mapa simple de España
    for i, resultado in enumerate(resultados):
        ax3.scatter(
            resultado["Longitud_Normal"],
            resultado["Latitud"],
            s=200,
            color=colors[i],
            label=resultado["Ubicación"],
            zorder=5,
        )
        ax3.annotate(
            resultado["Ubicación"].split()[0],
            (resultado["Longitud_Normal"], resultado["Latitud"]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
        )

    # Marcar área aproximada de España
    ax3.set_xlim(-10, 5)
    ax3.set_ylim(35, 44)
    ax3.set_xlabel("Longitud (°E)")
    ax3.set_ylabel("Latitud (°N)")
    ax3.set_title("Ubicaciones de Análisis en España")
    ax3.grid(True, alpha=0.3)
    ax3.legend(fontsize=8)

    # 4. Análisis horario (isla de calor es más fuerte de noche)
    ax4 = axes[1, 1]

    # Separar día (10-18h) vs noche (22-6h) para Madrid
    if "Madrid Centro" in series:
        madrid_series = series["Madrid Centro"]
        horas = madrid_series.valid_time.dt.hour

        temp_dia = madrid_series.where((horas >= 10) & (horas <= 18), drop=True)
        temp_noche = madrid_series.where((horas >= 22) | (horas <= 6), drop=True)

        tiempos = ["Día (10-18h)", "Noche (22-6h)"]
        valores = [float(temp_dia.mean()), float(temp_noche.mean())]

        bars2 = ax4.bar(tiempos, valores, color=["orange", "darkblue"], alpha=0.7)
        ax4.set_ylabel("Temperatura Media (°C)")
        ax4.set_title("Madrid: Temperatura Día vs Noche")
        ax4.grid(True, alpha=0.3, axis="y")

        for bar, valor in zip(bars2, valores):
            height = bar.get_height()
            ax4.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + 0.1,
                f"{valor:.2f}°C",
                ha="center",
                va="bottom",
            )

    plt.tight_layout()

    # Guardar resultados
    output_dir = Path("Resultados/finales/analisis_urbano_corregido")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Guardar figura
    fig_path = output_dir / "comparacion_madrid_rural_corregido.png"
    plt.savefig(fig_path, dpi=300, bbox_inches="tight")

    # Guardar datos como CSV
    df_resultados = pd.DataFrame(resultados)
    csv_path = output_dir / "resultados_temperatura_corregido.csv"
    df_resultados.to_csv(csv_path, index=False)

    # Guardar reporte mejorado
    reporte_path = output_dir / "reporte_analisis_corregido.txt"
    with open(reporte_path, "w") as f:
        f.write("=" * 70 + "\n")
        f.write("REPORTE CIENTÍFICO CORREGIDO: ANÁLISIS ISLA DE CALOR URBANA\n")
        f.write("=" * 70 + "\n\n")
        f.write("DATOS: ERA5 - Temperatura a 2m - Enero 2020\n")
        f.write("COORDENADAS CORREGIDAS para España\n")
        f.write(f"Diferencia Madrid-Rural: {diff_madrid_rural:.2f}°C\n")

        if diff_madrid_rural > 0.5:
            f.write("CONCLUSIÓN: ✅ Se detecta isla de calor urbana significativa\n")
        elif diff_madrid_rural > 0:
            f.write("CONCLUSIÓN: ⚠️  Isla de calor leve detectada\n")
        else:
            f.write("CONCLUSIÓN: 🔄 No se detecta isla de calor en este período\n")
            f.write("   Posibles explicaciones:\n")
            f.write("   - Inversión térmica en zonas rurales\n")
            f.write("   - Enero 2020 fue particularmente frío\n")
            f.write(
                "   - Resolución de ERA5 (31km) puede suavizar diferencias urbanas\n\n"
            )

        f.write("\nRESULTADOS DETALLADOS:\n")
        f.write("-" * 40 + "\n")
        for resultado in resultados:
            f.write(f"\n{resultado['Ubicación']}:\n")
            f.write(
                f"  Coordenadas: {resultado['Latitud']:.3f}°N, {resultado['Longitud_Normal']:.3f}°E\n"
            )
            f.write(f"  Temp Media: {resultado['Temperatura Media (°C)']}°C\n")
            f.write(
                f"  Rango: {resultado['Temperatura Mín (°C)']} a {resultado['Temperatura Máx (°C)']}°C\n"
            )
            f.write(f"  Variabilidad: {resultado['Variabilidad (σ)']}°C\n")

    print("\n" + "=" * 70)
    print("✅ ANÁLISIS CORREGIDO COMPLETADO")
    print("=" * 70)
    print(f"📊 Gráficos guardados en: {fig_path}")
    print(f"📈 Datos guardados en: {csv_path}")
    print(f"📝 Reporte guardado en: {reporte_path}")

    # Mostrar la figura
    plt.show()


if __name__ == "__main__":
    main()
