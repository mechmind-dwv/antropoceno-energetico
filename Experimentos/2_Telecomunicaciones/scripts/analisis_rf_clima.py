#!/usr/bin/env python3
"""
Experimento 2: Análisis de impacto de telecomunicaciones en el clima
Análisis de datos RF y su posible influencia climática.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RFClimateAnalyzer:
    """Analizador de impacto de radiofrecuencia en el clima"""

    def __init__(self):
        self.rf_data = None
        self.climate_data = None
        self.results = {}

    def load_rf_inventory(self, inventory_file: str) -> pd.DataFrame:
        """Cargar inventario de transmisores RF"""
        logger.info(f"Cargando inventario RF: {inventory_file}")

        # Formato esperado: CSV con columnas:
        # frequency_hz, power_w, latitude, longitude, height_m, type
        try:
            df = pd.read_csv(inventory_file)
            required_cols = ["frequency_hz", "power_w", "latitude", "longitude"]

            if not all(col in df.columns for col in required_cols):
                logger.error(f"Faltan columnas requeridas: {required_cols}")
                return None

            logger.info(f"Inventario cargado: {len(df)} transmisores")
            return df

        except Exception as e:
            logger.error(f"Error cargando inventario: {e}")
            return None

    def calculate_rf_power_density(
        self, df: pd.DataFrame, grid_resolution: float = 0.1
    ) -> xr.Dataset:
        """Calcular densidad de potencia RF en una grilla"""
        logger.info("Calculando densidad de potencia RF...")

        # Crear grilla
        lats = np.arange(-90, 90 + grid_resolution, grid_resolution)
        lons = np.arange(-180, 180 + grid_resolution, grid_resolution)

        # Inicializar matriz de densidad de potencia (W/m²)
        power_density = np.zeros((len(lats), len(lons)))

        # Modelo de propagación simple (inverso del cuadrado)
        for _, row in df.iterrows():
            # Encontrar celda más cercana
            lat_idx = np.argmin(np.abs(lats - row["latitude"]))
            lon_idx = np.argmin(np.abs(lons - row["longitude"]))

            # Suposición: potencia se distribuye en área de 1 km²
            # En realidad se necesitaría modelo de propagación complejo
            area_km2 = 1.0  # km²
            power_density[lat_idx, lon_idx] += row["power_w"] / (area_km2 * 1e6)

        # Crear Dataset xarray
        ds = xr.Dataset(
            {"rf_power_density": (["latitude", "longitude"], power_density)},
            coords={"latitude": lats, "longitude": lons},
        )

        ds.rf_power_density.attrs = {
            "units": "W/m²",
            "long_name": "RF Power Density",
            "description": "Estimated RF power density from transmitters",
        }

        logger.info(
            f"Densidad de potencia calculada. Máximo: {power_density.max():.2e} W/m²"
        )
        return ds

    def load_climate_data(self, era5_file: str) -> xr.Dataset:
        """Cargar datos climáticos ERA5"""
        logger.info(f"Cargando datos climáticos: {era5_file}")

        try:
            ds = xr.open_dataset(era5_file)
            logger.info(f"Datos climáticos cargados: {list(ds.data_vars.keys())}")
            return ds
        except Exception as e:
            logger.error(f"Error cargando datos climáticos: {e}")
            return None

    def analyze_correlation(
        self, rf_data: xr.Dataset, climate_data: xr.Dataset, climate_var: str = "t2m"
    ) -> Dict:
        """Analizar correlación entre RF y variable climática"""
        logger.info(f"Analizando correlación RF - {climate_var}")

        # Interpolar a misma grilla
        rf_interp = rf_data.rf_power_density.interp(
            latitude=climate_data.latitude,
            longitude=climate_data.longitude,
            method="linear",
        )

        # Promedio temporal de variable climática
        if "valid_time" in climate_data[climate_var].dims:
            climate_mean = climate_data[climate_var].mean(dim="valid_time")
        else:
            climate_mean = climate_data[climate_var]

        # Aplanar arrays para correlación
        rf_flat = rf_interp.values.flatten()
        climate_flat = climate_mean.values.flatten()

        # Eliminar NaNs
        mask = ~np.isnan(rf_flat) & ~np.isnan(climate_flat)
        rf_valid = rf_flat[mask]
        climate_valid = climate_flat[mask]

        if len(rf_valid) < 10:
            logger.warning("No hay suficientes datos para correlación")
            return None

        # Calcular correlación
        correlation = np.corrcoef(rf_valid, climate_valid)[0, 1]

        # Calcular regresión lineal
        coeff = np.polyfit(rf_valid, climate_valid, 1)

        results = {
            "correlation_coefficient": float(correlation),
            "regression_slope": float(coeff[0]),
            "regression_intercept": float(coeff[1]),
            "n_points": int(len(rf_valid)),
            "rf_mean": float(np.mean(rf_valid)),
            "rf_std": float(np.std(rf_valid)),
            "climate_mean": float(np.mean(climate_valid)),
            "climate_std": float(np.std(climate_valid)),
        }

        logger.info(f"Correlación RF-{climate_var}: {correlation:.4f}")
        return results

    def estimate_radiative_forcing(self, rf_data: xr.Dataset) -> Dict:
        """Estimar forzamiento radiativo de RF"""
        logger.info("Estimando forzamiento radiativo...")

        # Suposiciones para el cálculo:
        # 1. RF es absorbida por la atmósfera
        # 2. Eficiencia de conversión a calor
        # 3. Este es un cálculo MUY simplificado

        # Densidad de potencia promedio (W/m²)
        mean_power = float(rf_data.rf_power_density.mean().values)

        # Suponer que cierta fracción es absorbida
        # En realidad depende de frecuencia, humedad, etc.
        absorption_fraction = 0.01  # 1% (muy conservador)

        # Forzamiento radiativo estimado (W/m²)
        radiative_forcing = mean_power * absorption_fraction

        # Comparar con forzamiento por CO2 (~2.7 W/m²)
        co2_forcing = 2.7
        ratio = radiative_forcing / co2_forcing

        results = {
            "mean_rf_power_density_w_m2": mean_power,
            "absorption_fraction": absorption_fraction,
            "estimated_radiative_forcing_w_m2": radiative_forcing,
            "co2_forcing_ratio": ratio,
            "significance": (
                "VERY_LOW" if ratio < 0.001 else "LOW" if ratio < 0.01 else "MODERATE"
            ),
        }

        logger.info(f"Forzamiento radiativo estimado: {radiative_forcing:.2e} W/m²")
        logger.info(f"Ratio CO2: {ratio:.2e}")

        return results

    def generate_visualizations(
        self, rf_data: xr.Dataset, climate_data: xr.Dataset, output_dir: Path
    ):
        """Generar visualizaciones del análisis"""
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Mapa de densidad de potencia RF
        fig1, ax1 = plt.subplots(figsize=(12, 6))
        rf_data.rf_power_density.plot(ax=ax1, cmap="hot", add_colorbar=True)
        ax1.set_title("Densidad de Potencia RF Estimada (W/m²)")
        ax1.set_xlabel("Longitud")
        ax1.set_ylabel("Latitud")
        fig1.savefig(
            output_dir / "rf_power_density_map.png", dpi=300, bbox_inches="tight"
        )

        # 2. Comparación con temperatura
        if "t2m" in climate_data:
            fig2, (ax2a, ax2b) = plt.subplots(1, 2, figsize=(15, 6))

            # Mapa de temperatura
            if "valid_time" in climate_data.t2m.dims:
                temp_mean = climate_data.t2m.mean(dim="valid_time") - 273.15  # K to C
            else:
                temp_mean = climate_data.t2m - 273.15

            im1 = temp_mean.plot(ax=ax2a, cmap="RdBu_r", add_colorbar=True)
            ax2a.set_title("Temperatura Media (°C)")

            # Scatter plot correlación
            rf_interp = rf_data.rf_power_density.interp(
                latitude=climate_data.latitude, longitude=climate_data.longitude
            )

            rf_flat = rf_interp.values.flatten()
            temp_flat = temp_mean.values.flatten()
            mask = ~np.isnan(rf_flat) & ~np.isnan(temp_flat)

            ax2b.scatter(rf_flat[mask], temp_flat[mask], alpha=0.3, s=1)
            ax2b.set_xlabel("Densidad Potencia RF (W/m²)")
            ax2b.set_ylabel("Temperatura (°C)")
            ax2b.set_title("Correlación RF - Temperatura")
            ax2b.grid(True, alpha=0.3)

            fig2.savefig(
                output_dir / "rf_temperature_comparison.png",
                dpi=300,
                bbox_inches="tight",
            )

        plt.close("all")

    def save_results(self, results: Dict, output_dir: Path):
        """Guardar resultados del análisis"""
        output_dir.mkdir(parents=True, exist_ok=True)

        # Guardar como JSON
        results_file = output_dir / "analysis_results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        # Guardar resumen como texto
        summary_file = output_dir / "analysis_summary.txt"
        with open(summary_file, "w") as f:
            f.write("=" * 70 + "\n")
            f.write("RESULTADOS - EXPERIMENTO 2: TELECOMUNICACIONES\n")
            f.write("=" * 70 + "\n\n")

            f.write(
                f"Fecha análisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            )

            if "correlation_results" in results:
                f.write("CORRELACIÓN RF - CLIMA:\n")
                f.write("-" * 40 + "\n")
                for key, value in results["correlation_results"].items():
                    f.write(f"{key}: {value}\n")
                f.write("\n")

            if "radiative_forcing" in results:
                f.write("FORZAMIENTO RADIATIVO ESTIMADO:\n")
                f.write("-" * 40 + "\n")
                for key, value in results["radiative_forcing"].items():
                    f.write(f"{key}: {value}\n")

                rf = results["radiative_forcing"]["estimated_radiative_forcing_w_m2"]
                ratio = results["radiative_forcing"]["co2_forcing_ratio"]
                significance = results["radiative_forcing"]["significance"]

                f.write("\nINTERPRETACIÓN:\n")
                f.write(f"- Forzamiento RF: {rf:.2e} W/m²\n")
                f.write(f"- Ratio vs CO2: {ratio:.2e}\n")
                f.write(f"- Significancia: {significance}\n\n")

                if ratio < 0.001:
                    f.write(
                        "CONCLUSIÓN: El impacto de las telecomunicaciones en el forzamiento\n"
                    )
                    f.write("radiativo es despreciable (< 0.1% del efecto CO2).\n")
                elif ratio < 0.01:
                    f.write("CONCLUSIÓN: Impacto muy pequeño (< 1% del efecto CO2).\n")
                else:
                    f.write(
                        "CONCLUSIÓN: Impacto potencialmente significativo (> 1% del efecto CO2).\n"
                    )
                    f.write("Se requiere investigación más detallada.\n")

        logger.info(f"Resultados guardados en: {output_dir}")


def main():
    """Función principal del experimento"""
    analyzer = RFClimateAnalyzer()

    # Configurar rutas
    base_dir = Path("Experimentos/2_Telecomunicaciones")
    output_dir = base_dir / "output" / datetime.now().strftime("%Y%m%d_%H%M%S")

    # 1. Cargar inventario de transmisores (ejemplo)
    # En un experimento real, esto sería un inventario real
    inventory_file = base_dir / "data" / "rf_inventory_example.csv"

    # Si no existe, crear ejemplo
    if not inventory_file.exists():
        logger.info("Creando inventario RF de ejemplo...")
        inventory_file.parent.mkdir(parents=True, exist_ok=True)

        # Datos de ejemplo (transmisores en Europa)
        example_data = {
            "frequency_hz": [900e6, 1800e6, 2100e6, 2600e6],
            "power_w": [1000, 800, 600, 400],
            "latitude": [40.4, 41.4, 39.5, 42.0],
            "longitude": [-3.7, 2.2, -0.4, -8.0],
            "height_m": [30, 40, 35, 45],
            "type": ["GSM", "LTE", "UMTS", "LTE"],
        }

        pd.DataFrame(example_data).to_csv(inventory_file, index=False)

    # 2. Cargar y procesar inventario RF
    rf_inventory = analyzer.load_rf_inventory(inventory_file)
    if rf_inventory is None:
        logger.error("No se pudo cargar inventario RF")
        return

    # 3. Calcular densidad de potencia RF
    rf_power = analyzer.calculate_rf_power_density(rf_inventory, grid_resolution=0.5)

    # 4. Cargar datos climáticos (usar ERA5 descargado previamente)
    era5_file = Path("Datos/crudos/reanalisis/era5_2m_temperature_2020_01.nc")
    if not era5_file.exists():
        logger.error(f"No se encontraron datos ERA5: {era5_file}")
        logger.info(
            "Descarga primero con: python descarga_era5.py --variable temperatura --year 2020 --month 1"
        )

        # Usar datos de ejemplo como fallback
        era5_file = Path("Datos/ejemplo/datos_ejemplo_temperatura.nc")
        if not era5_file.exists():
            logger.error("No hay datos disponibles para análisis")
            return

    climate_data = analyzer.load_climate_data(era5_file)
    if climate_data is None:
        logger.error("No se pudieron cargar datos climáticos")
        return

    # 5. Analizar correlaciones
    correlation_results = analyzer.analyze_correlation(rf_power, climate_data, "t2m")

    # 6. Estimar forzamiento radiativo
    radiative_forcing = analyzer.estimate_radiative_forcing(rf_power)

    # 7. Generar visualizaciones
    analyzer.generate_visualizations(rf_power, climate_data, output_dir / "plots")

    # 8. Compilar y guardar resultados
    all_results = {
        "experiment": "2_Telecomunicaciones",
        "date": datetime.now().isoformat(),
        "rf_inventory_file": str(inventory_file),
        "climate_data_file": str(era5_file),
        "correlation_results": correlation_results,
        "radiative_forcing": radiative_forcing,
        "notes": "Análisis preliminar con datos de ejemplo. Para resultados científicos se requieren datos reales de mediciones RF.",
    }

    analyzer.save_results(all_results, output_dir)

    # 9. Mostrar resumen en consola
    print("\n" + "=" * 70)
    print("RESUMEN EJECUTIVO - EXPERIMENTO 2")
    print("=" * 70)

    if correlation_results:
        print(
            f"\n📈 Correlación RF-Temperatura: {correlation_results['correlation_coefficient']:.4f}"
        )

    if radiative_forcing:
        rf = radiative_forcing["estimated_radiative_forcing_w_m2"]
        ratio = radiative_forcing["co2_forcing_ratio"]
        print(f"\n🔥 Forzamiento radiativo estimado: {rf:.2e} W/m²")
        print(f"📊 Ratio vs CO2 antropogénico: {ratio:.2e}")

        if ratio < 0.001:
            print("\n✅ CONCLUSIÓN: Impacto despreciable (< 0.1% del efecto CO2)")
        elif ratio < 0.01:
            print("\n⚠️  CONCLUSIÓN: Impacto muy pequeño (< 1% del efecto CO2)")
        else:
            print("\n🔍 CONCLUSIÓN: Impacto potencialmente significativo")
            print("   Se requiere investigación más detallada con datos reales")

    print(f"\n📁 Resultados completos en: {output_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()
