"""
Cargador universal de datos para el proyecto
"""

import logging
import warnings
from pathlib import Path
from typing import Dict, List, Union

import numpy as np
import pandas as pd
import xarray as xr


class DataLoader:
    """Cargador inteligente de datos climáticos"""

    def __init__(self, base_path: Union[str, Path] = "Datos"):
        self.base_path = Path(base_path)
        self.logger = logging.getLogger(__name__)
        self.supported_formats = [".nc", ".h5", ".zarr", ".csv", ".parquet"]

    def load_era5(
        self, variables: List[str], years: range, domain: Dict = None
    ) -> xr.Dataset:
        """Cargar datos ERA5"""
        # Implementar
        pass

    def load_wrf_output(self, experiment_path: Path) -> xr.Dataset:
        """Cargar salidas de WRF"""
        # Implementar
        pass

    def load_satellite_data(
        self, mission: str, product: str, time_range: tuple
    ) -> xr.Dataset:
        """Cargar datos satelitales"""
        # Implementar
        pass
