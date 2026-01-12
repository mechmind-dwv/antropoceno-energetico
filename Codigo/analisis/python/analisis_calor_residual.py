#!/usr/bin/env python3
"""
Análisis de resultados del Experimento 1: Calor Residual
Autor: Benjamín Cabeza Duran
Fecha: Enero 2026
"""

import logging
from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalizadorCalorResidual:
    """Clase para análisis de experimentos de calor residual"""

    def __init__(self, ruta_datos):
        self.ruta_datos = Path(ruta_datos)
        self.datos = {}

    def cargar_experimentos(self, experimentos):
        """Cargar datos de múltiples experimentos"""
        for nombre, archivo in experimentos.items():
            try:
                logger.info(f"Cargando {nombre}: {archivo}")
                self.datos[nombre] = xr.open_dataset(archivo)
            except Exception as e:
                logger.error(f"Error cargando {archivo}: {e}")

    def calcular_diferencias(self, control="control", experimento="calor_residual"):
        """Calcular diferencias entre experimento y control"""
        if control not in self.datos or experimento not in self.datos:
            raise ValueError("Experimentos no cargados")

        diff = self.datos[experimento] - self.datos[control]
        return diff

    def analizar_temperatura_superficial(self, diff_ds):
        """Análisis de temperatura superficial"""
        if "T2" not in diff_ds:
            logger.warning("Variable T2 no encontrada")
            return None

        t2_diff = diff_ds["T2"]

        resultados = {
            "media_global": float(t2_diff.mean().values),
            "maximo": float(t2_diff.max().values),
            "minimo": float(t2_diff.min().values),
            "desviacion": float(t2_diff.std().values),
            "percentil_95": float(t2_diff.quantile(0.95).values),
        }

        return resultados

    def visualizar_diferencias(
        self,
        diff_ds,
        variable="T2",
        titulo="Diferencia de Temperatura (Experimento - Control)",
    ):
        """Visualizar diferencias espaciales"""
        fig = plt.figure(figsize=(12, 8))
        ax = plt.axes(projection=ccrs.PlateCarree())

        if variable in diff_ds:
            data = diff_ds[variable].mean(dim="Time")

            # Plot
            im = data.plot(
                ax=ax, transform=ccrs.PlateCarree(), cmap="RdBu_r", add_colorbar=True
            )

            # Añadir características geográficas
            ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
            ax.add_feature(cfeature.BORDERS, linewidth=0.3)
            ax.add_feature(cfeature.LAND, facecolor="lightgray", alpha=0.3)
            ax.add_feature(cfeature.OCEAN, facecolor="lightblue", alpha=0.3)

            # Título y etiquetas
            ax.set_title(titulo, fontsize=14, fontweight="bold")
            ax.set_xlabel("Longitud")
            ax.set_ylabel("Latitud")

            plt.tight_layout()
            return fig
        else:
            logger.warning(f"Variable {variable} no encontrada")
            return None

    def generar_reporte(self, resultados, archivo_salida="reporte_calor_residual.txt"):
        """Generar reporte de resultados"""
        with open(archivo_salida, "w") as f:
            f.write("=" * 60 + "\n")
            f.write("REPORTE: EXPERIMENTO CALOR RESIDUAL\n")
            f.write("=" * 60 + "\n\n")

            f.write("RESULTADOS PRINCIPALES:\n")
            f.write("-" * 40 + "\n")

            for clave, valor in resultados.items():
                f.write(f"{clave.replace('_', ' ').title()}: {valor:.4f}\n")

            f.write("\nINTERPRETACIÓN:\n")
            f.write("-" * 40 + "\n")

            if resultados["media_global"] > 0.1:
                f.write("✓ Impacto significativo detectado (> 0.1°C)\n")
            elif resultados["media_global"] > 0.01:
                f.write("○ Impacto moderado detectado (0.01-0.1°C)\n")
            else:
                f.write("✗ Impacto mínimo o despreciable (< 0.01°C)\n")

            f.write("\n" + "=" * 60 + "\n")
            f.write("Fin del reporte\n")

        logger.info(f"Reporte guardado en {archivo_salida}")


def main():
    """Función principal"""
    # Configurar rutas (ajustar según tu configuración)
    experimentos = {
        "control": "Experimentos/1_Calor_Residual/output/control/wrfout_d01.nc",
        "calor_residual": "Experimentos/1_Calor_Residual/output/experimento/wrfout_d01.nc",
    }

    # Inicializar analizador
    analizador = AnalizadorCalorResidual("Experimentos/1_Calor_Residual")

    # Cargar datos
    analizador.cargar_experimentos(experimentos)

    # Calcular diferencias
    diferencias = analizador.calcular_diferencias()

    # Analizar temperatura
    resultados = analizador.analizar_temperatura_superficial(diferencias)

    if resultados:
        # Generar visualización
        figura = analizador.visualizar_diferencias(diferencias)
        if figura:
            figura.savefig(
                "Resultados/figuras/diferencias_temperatura.png",
                dpi=300,
                bbox_inches="tight",
            )

        # Generar reporte
        analizador.generar_reporte(resultados)

        # Mostrar resultados en consola
        print("\n" + "=" * 60)
        print("RESUMEN DE RESULTADOS:")
        print("=" * 60)
        for clave, valor in resultados.items():
            print(f"{clave.replace('_', ' ').title():<20}: {valor:.4f}")
        print("=" * 60)


if __name__ == "__main__":
    main()
