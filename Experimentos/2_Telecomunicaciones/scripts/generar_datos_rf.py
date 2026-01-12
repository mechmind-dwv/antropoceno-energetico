#!/usr/bin/env python3
"""
Generar datos de ejemplo para el Experimento 2 (Telecomunicaciones)
"""
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_rf_measurements(output_dir: Path):
    """Generar mediciones RF de ejemplo"""
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Datos de espectro RF (1 MHz - 30 GHz)
    frequencies = np.logspace(6, 10, 1000)  # 1 MHz a 10 GHz
    times = pd.date_range("2024-01-01", "2024-01-07", freq="H")

    # Crear patrón típico de espectro RF
    # Picos en bandas de comunicaciones
    bands = {
        "FM Radio": 88e6,
        "TV VHF": 200e6,
        "GSM 900": 900e6,
        "GSM 1800": 1800e6,
        "UMTS": 2100e6,
        "LTE": 2600e6,
        "WiFi": 2400e6,
        "5G": 3500e6,
    }

    spectrum_data = np.zeros((len(times), len(frequencies)))

    for i, time in enumerate(times):
        # Nivel de ruido base
        base_noise = -100  # dBm

        # Variación diurna (más tráfico durante el día)
        hour = time.hour
        diurnal_factor = 1.0 + 0.5 * np.sin(2 * np.pi * (hour - 12) / 24)

        spectrum = np.full_like(frequencies, base_noise)

        # Añadir picos en bandas de comunicación
        for band_name, freq in bands.items():
            idx = np.argmin(np.abs(frequencies - freq))
            bandwidth = freq * 0.1  # 10% de ancho de banda

            # Intensidad depende del tipo de banda y hora
            if "GSM" in band_name or "LTE" in band_name or "5G" in band_name:
                intensity = -60 * diurnal_factor  # Más intenso
            else:
                intensity = -80  # Menos intenso

            # Crear pico gaussiano
            peak = intensity * np.exp(-(((frequencies - freq) / bandwidth) ** 2))
            spectrum += peak

        spectrum_data[i, :] = spectrum

    # Crear Dataset
    ds = xr.Dataset(
        {"rf_power": (["time", "frequency"], spectrum_data)},
        coords={"time": times, "frequency": frequencies},
    )

    ds.rf_power.attrs = {
        "units": "dBm",
        "long_name": "RF Power Spectrum",
        "description": "Simulated RF power spectrum measurements",
    }

    # Guardar
    output_file = output_dir / "rf_spectrum_measurements.nc"
    ds.to_netcdf(output_file)
    logger.info(f"Mediciones RF guardadas: {output_file}")

    # 2. Datos de inventario de transmisores
    transmitters = []
    for city, (lat, lon) in {
        "Madrid": (40.4168, -3.7038),
        "Barcelona": (41.3851, 2.1734),
        "Valencia": (39.4699, -0.3763),
        "Sevilla": (37.3891, -5.9845),
        "Bilbao": (43.2630, -2.9350),
    }.items():
        for freq in [900e6, 1800e6, 2100e6, 2600e6, 3500e6]:
            transmitters.append(
                {
                    "city": city,
                    "latitude": lat,
                    "longitude": lon,
                    "frequency_hz": freq,
                    "power_w": np.random.uniform(100, 1000),
                    "height_m": np.random.uniform(20, 50),
                    "type": np.random.choice(["GSM", "LTE", "UMTS", "5G"]),
                }
            )

    df_transmitters = pd.DataFrame(transmitters)
    inventory_file = output_dir / "rf_transmitter_inventory.csv"
    df_transmitters.to_csv(inventory_file, index=False)
    logger.info(f"Inventario de transmisores guardado: {inventory_file}")

    # 3. Datos de mediciones puntuales
    measurement_points = []
    for i in range(100):
        # Puntos alrededor de Madrid
        lat = 40.4 + np.random.uniform(-0.5, 0.5)
        lon = -3.7 + np.random.uniform(-0.5, 0.5)

        measurement_points.append(
            {
                "measurement_id": f"MP_{i:03d}",
                "latitude": lat,
                "longitude": lon,
                "distance_to_nearest_antenna_km": np.random.exponential(2),
                "rf_power_density_w_m2": np.random.exponential(1e-6),
                "temperature_c": 15 + np.random.normal(0, 3),
                "humidity_percent": 50 + np.random.normal(0, 15),
                "measurement_date": "2024-01-15",
            }
        )

    df_measurements = pd.DataFrame(measurement_points)
    measurements_file = output_dir / "field_measurements.csv"
    df_measurements.to_csv(measurements_file, index=False)
    logger.info(f"Mediciones de campo guardadas: {measurements_file}")

    return {
        "spectrum_file": output_file,
        "inventory_file": inventory_file,
        "measurements_file": measurements_file,
    }


def generate_satellite_rf_data(output_dir: Path):
    """Generar datos satelitales RF de ejemplo"""
    # Datos simulados de satélites SMAP/AMSR-E
    times = pd.date_range("2020-01-01", "2020-12-31", freq="D")
    lats = np.arange(-90, 91, 1)
    lons = np.arange(-180, 181, 1)

    # Temperatura de brillo en banda L (1.4 GHz)
    tb_data = np.zeros((len(times), len(lats), len(lons)))

    for i, time in enumerate(times):
        # Patrón base con gradiente latitudinal
        lat_grid, lon_grid = np.meshgrid(lats, lons, indexing="ij")
        base = 200 + 50 * np.cos(np.deg2rad(lat_grid))

        # Variación estacional
        day_of_year = time.dayofyear
        seasonal = 10 * np.sin(2 * np.pi * day_of_year / 365)

        # Añadir patrones antropogénicos (mayor TB cerca de ciudades)
        # Europa
        europe_mask = (
            (lat_grid > 35) & (lat_grid < 60) & (lon_grid > -10) & (lon_grid < 40)
        )
        tb_data[i][europe_mask] += 5

        # Este de Asia
        asia_mask = (
            (lat_grid > 20) & (lat_grid < 50) & (lon_grid > 100) & (lon_grid < 140)
        )
        tb_data[i][asia_mask] += 7

        # Este de EE.UU.
        usa_mask = (
            (lat_grid > 25) & (lat_grid < 50) & (lon_grid > -100) & (lon_grid < -70)
        )
        tb_data[i][usa_mask] += 6

        tb_data[i] = base + seasonal

    ds = xr.Dataset(
        {"brightness_temperature": (["time", "latitude", "longitude"], tb_data)},
        coords={"time": times, "latitude": lats, "longitude": lons},
    )

    ds.brightness_temperature.attrs = {
        "units": "K",
        "long_name": "Brightness Temperature",
        "frequency": "1.4 GHz",
        "description": "Simulated L-band brightness temperature (SMAP-like)",
    }

    output_file = output_dir / "satellite_rf_data.nc"
    ds.to_netcdf(output_file)
    logger.info(f"Datos satelitales RF guardados: {output_file}")

    return output_file


def main():
    """Generar todos los datos de ejemplo para Experimento 2"""
    base_dir = Path("Experimentos/2_Telecomunicaciones/data")

    logger.info("Generando datos de ejemplo para Experimento 2...")

    # 1. Mediciones RF terrestres
    rf_data = generate_rf_measurements(base_dir / "terrestrial")

    # 2. Datos satelitales RF
    satellite_data = generate_satellite_rf_data(base_dir / "satellite")

    # 3. Crear archivo README
    readme_content = f"""
    # Datos de Ejemplo - Experimento 2: Telecomunicaciones

    ## Archivos Generados:

    ### 1. Mediciones Terrestres RF
    - `{rf_data['spectrum_file'].relative_to(base_dir)}`: Espectro RF medido (1 MHz - 10 GHz)
    - `{rf_data['inventory_file'].relative_to(base_dir)}`: Inventario de transmisores
    - `{rf_data['measurements_file'].relative_to(base_dir)}`: Mediciones de campo puntuales

    ### 2. Datos Satelitales
    - `{satellite_data.relative_to(base_dir)}`: Temperatura de brillo en banda L (SMAP-like)

    ## Uso:
    Estos datos de ejemplo pueden usarse para:
    1. Probar el análisis del Experimento 2
    2. Desarrollar visualizaciones
    3. Validar métodos de análisis
    4. Entrenamiento y demostración

    ## Nota:
    Estos son datos SIMULADOS para desarrollo y prueba.
    Para análisis científicos reales se requieren datos reales de medición.

    Generado: $(date)
    """

    readme_file = base_dir / "README.md"
    with open(readme_file, "w") as f:
        f.write(readme_content)

    logger.info(f"Datos de ejemplo generados en: {base_dir}")
    logger.info(
        "Puedes usar estos datos con: python Experimentos/2_Telecomunicaciones/scripts/analisis_rf_clima.py"
    )


if __name__ == "__main__":
    main()
