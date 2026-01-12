"""
Generar datos de ejemplo para pruebas del dashboard
"""

from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

# Crear datos sintéticos
time = pd.date_range("2020-01-01", "2020-01-31", freq="H")
lats = np.linspace(35, 45, 50)
lons = np.linspace(-10, 5, 50)

# Crear temperatura con patrón realista
lon_grid, lat_grid = np.meshgrid(lons, lats)
base_temp = 10 + 20 * np.cos(np.deg2rad(lat_grid))  # Gradiente latitudinal
daily_cycle = 5 * np.sin(2 * np.pi * np.arange(len(time))[:, None, None] / 24)
spatial_pattern = (
    2 * np.sin(2 * np.pi * lon_grid / 20) * np.cos(2 * np.pi * lat_grid / 10)
)

# Dataset completo
temperature = base_temp + daily_cycle[:, :, :] + spatial_pattern

ds = xr.Dataset(
    {"temperature": (["time", "lat", "lon"], temperature - 273.15)},  # En Celsius
    coords={"time": time, "lat": lats, "lon": lons},
)

# Guardar
output_dir = Path("Datos/ejemplo")
output_dir.mkdir(parents=True, exist_ok=True)
ds.to_netcdf(output_dir / "datos_ejemplo_temperatura.nc")
print(f"✅ Datos de ejemplo guardados en: {output_dir}/datos_ejemplo_temperatura.nc")
