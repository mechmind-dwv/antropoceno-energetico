"""
Utilidades para el dashboard avanzado
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
import xarray as xr

logger = logging.getLogger(__name__)


class ERA5Analyzer:
    """Clase para análisis avanzado de datos ERA5"""

    def __init__(self, filepath: Path):
        self.filepath = Path(filepath)
        self.ds = None
        self._load_data()

    def _load_data(self):
        """Cargar datos ERA5"""
        try:
            self.ds = xr.open_dataset(self.filepath)
            logger.info(f"Datos cargados: {self.filepath.name}")
        except Exception as e:
            logger.error(f"Error cargando datos: {e}")
            raise

    def get_variable_info(self, variable: str) -> Dict[str, Any]:
        """Obtener información detallada de una variable"""
        if variable not in self.ds.data_vars:
            raise ValueError(f"Variable {variable} no encontrada")

        data = self.ds[variable]
        info = {
            "name": variable,
            "units": data.attrs.get("units", "N/A"),
            "dims": dict(data.dims),
            "shape": data.shape,
            "attributes": dict(data.attrs),
        }

        return info

    def calculate_statistics(
        self, variable: str, region: Optional[Tuple] = None
    ) -> Dict[str, float]:
        """Calcular estadísticas para una variable"""
        data = self.ds[variable]

        # Aplicar región si se especifica
        if region:
            lat_min, lat_max, lon_min, lon_max = region
            data = data.sel(
                latitude=slice(lat_max, lat_min), longitude=slice(lon_min, lon_max)
            )

        values = data.values.flatten()
        values = values[~np.isnan(values)]

        stats = {
            "mean": float(np.mean(values)),
            "std": float(np.std(values)),
            "min": float(np.min(values)),
            "max": float(np.max(values)),
            "median": float(np.median(values)),
            "q25": float(np.percentile(values, 25)),
            "q75": float(np.percentile(values, 75)),
            "count": int(len(values)),
        }

        return stats

    def extract_time_series(
        self, variable: str, lat: float, lon: float
    ) -> pd.DataFrame:
        """Extraer serie temporal en un punto específico"""
        # Encontrar índices más cercanos
        lat_idx = np.abs(self.ds.latitude - lat).argmin()
        lon_idx = np.abs(self.ds.longitude - lon).argmin()

        # Extraer datos
        data = self.ds[variable].isel(latitude=lat_idx, longitude=lon_idx)

        # Crear DataFrame
        df = pd.DataFrame(
            {
                "time": pd.to_datetime(data.valid_time.values),
                "value": data.values,
                "lat": float(self.ds.latitude[lat_idx]),
                "lon": float(self.ds.longitude[lon_idx]),
            }
        )

        return df

    def calculate_spatial_gradient(
        self, variable: str, time_idx: int = 0
    ) -> Dict[str, np.ndarray]:
        """Calcular gradientes espaciales"""
        if "valid_time" in self.ds[variable].dims:
            data = self.ds[variable].isel(valid_time=time_idx)
        else:
            data = self.ds[variable]

        # Calcular gradientes
        lat_grad = np.gradient(data.values, self.ds.latitude.values, axis=0)
        lon_grad = np.gradient(data.values, self.ds.longitude.values, axis=1)

        return {
            "latitude_gradient": lat_grad,
            "longitude_gradient": lon_grad,
            "magnitude": np.sqrt(lat_grad**2 + lon_grad**2),
        }

    def find_extreme_points(self, variable: str, n_points: int = 5) -> pd.DataFrame:
        """Encontrar puntos con valores extremos"""
        data = self.ds[variable]

        if "valid_time" in data.dims:
            data_mean = data.mean(dim="valid_time")
        else:
            data_mean = data

        # Aplanar y encontrar extremos
        values = data_mean.values.flatten()
        lat_grid, lon_grid = np.meshgrid(
            self.ds.latitude.values, self.ds.longitude.values, indexing="ij"
        )

        # Encontrar máximos
        max_indices = np.argpartition(values, -n_points)[-n_points:]
        max_points = []
        for idx in max_indices:
            lat_idx, lon_idx = np.unravel_index(idx, data_mean.shape)
            max_points.append(
                {
                    "type": "max",
                    "value": values[idx],
                    "latitude": lat_grid[lat_idx, lon_idx],
                    "longitude": lon_grid[lat_idx, lon_idx],
                }
            )

        # Encontrar mínimos
        min_indices = np.argpartition(values, n_points)[:n_points]
        min_points = []
        for idx in min_indices:
            lat_idx, lon_idx = np.unravel_index(idx, data_mean.shape)
            min_points.append(
                {
                    "type": "min",
                    "value": values[idx],
                    "latitude": lat_grid[lat_idx, lon_idx],
                    "longitude": lon_grid[lat_idx, lon_idx],
                }
            )

        return pd.DataFrame(max_points + min_points)


def create_download_links(dataframe: pd.DataFrame, filename: str) -> str:
    """Crear enlaces de descarga para diferentes formatos"""
    csv_data = dataframe.to_csv(index=False)
    json_data = dataframe.to_json(orient="records", indent=2)

    return f"""
    **Formatos disponibles:**
    - [CSV]({filename}.csv)
    - [JSON]({filename}.json)
    - [Excel]({filename}.xlsx)
    """
