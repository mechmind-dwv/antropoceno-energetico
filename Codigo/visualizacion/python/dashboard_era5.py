"""
Dashboard interactivo para análisis ERA5 en Antropoceno Energético
"""

import streamlit as st
import xarray as xr
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import numpy as np
import pandas as pd

st.set_page_config(page_title="ERA5 Climate Dashboard", page_icon="🌡️", layout="wide")

# Título principal
st.title("🌡️ Dashboard de Análisis ERA5 - Antropoceno Energético")
st.markdown("Visualización interactiva de datos climáticos del reanálisis ERA5")

# Sidebar para configuración
with st.sidebar:
    st.header("⚙️ Configuración")

    # Selección de archivo
    data_dir = Path("Datos/crudos/reanalisis")
    nc_files = list(data_dir.glob("*.nc"))

    if nc_files:
        file_options = [f.name for f in nc_files]
        selected_file = st.selectbox("Seleccionar archivo ERA5", file_options)
        file_path = data_dir / selected_file
    else:
        st.warning("No hay archivos .nc en Datos/crudos/reanalisis/")
        st.info("Ejecuta primero:")
        st.code(
            "python Codigo/utiles/python/descarga_era5.py --variable temperatura --year 2020 --month 1"
        )
        st.stop()

    # Cargar datos
    try:
        ds = xr.open_dataset(file_path)
        var_name = list(ds.data_vars.keys())[0]
        data_var = ds[var_name]

        st.success(f"✅ Datos cargados: {var_name}")
        st.caption(f"Dimensión: {data_var.shape}")

    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        st.stop()

# Pestañas principales
tab1, tab2, tab3 = st.tabs(["📊 Resumen", "📈 Series Temporales", "🗺️ Mapas Espaciales"])

with tab1:
    st.header("Resumen del Dataset")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Información General")
        st.write(f"**Variable:** {var_name}")
        st.write(f"**Unidades:** {data_var.attrs.get('units', 'N/A')}")
        st.write(f"**Dimensión:** {data_var.shape}")

        # Estadísticas básicas
        stats_df = pd.DataFrame(
            {
                "Estadística": ["Media", "Mínimo", "Máximo", "Desviación Estándar"],
                "Valor": [
                    float(data_var.mean().values),
                    float(data_var.min().values),
                    float(data_var.max().values),
                    float(data_var.std().values),
                ],
            }
        )
        st.dataframe(stats_df, use_container_width=True)

    with col2:
        st.subheader("Dimensiones")
        for dim_name, dim_size in data_var.dims.items():
            st.write(f"**{dim_name}:** {dim_size} puntos")

        # Histograma simple
        if data_var.size < 1000000:  # Si no es demasiado grande
            fig_hist, ax_hist = plt.subplots(figsize=(8, 4))
            flat_data = data_var.values.flatten()
            flat_data = flat_data[~np.isnan(flat_data)]

            if len(flat_data) > 0:
                ax_hist.hist(flat_data[:10000], bins=50, alpha=0.7, color="steelblue")
                ax_hist.set_xlabel(var_name)
                ax_hist.set_ylabel("Frecuencia")
                ax_hist.set_title("Distribución de Valores")
                ax_hist.grid(True, alpha=0.3)
                st.pyplot(fig_hist)

with tab2:
    st.header("Análisis de Series Temporales")

    # Encontrar dimensión temporal
    time_dim = None
    for possible in ["valid_time", "time", "t"]:
        if possible in data_var.dims:
            time_dim = possible
            break

    if time_dim:
        # Promedio espacial a lo largo del tiempo
        lat_dim = "latitude" if "latitude" in data_var.dims else "lat"
        lon_dim = "longitude" if "longitude" in data_var.dims else "lon"

        if lat_dim in data_var.dims and lon_dim in data_var.dims:
            time_series = data_var.mean(dim=[lat_dim, lon_dim])

            # Convertir a DataFrame para Plotly
            time_df = pd.DataFrame(
                {"Tiempo": time_series[time_dim].values, "Valor": time_series.values}
            )

            fig_time = px.line(
                time_df,
                x="Tiempo",
                y="Valor",
                title=f"Serie Temporal de {var_name} (Promedio Global)",
                labels={"Valor": var_name},
            )

            fig_time.update_layout(hovermode="x unified")
            st.plotly_chart(fig_time, use_container_width=True)

            # Estadísticas de la serie
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Valor Medio", f"{float(time_series.mean().values):.2f}")
            with col2:
                st.metric("Variabilidad", f"{float(time_series.std().values):.2f}")
            with col3:
                st.metric(
                    "Rango",
                    f"{float(time_series.max().values - time_series.min().values):.2f}",
                )
        else:
            st.warning("No se encontraron dimensiones espaciales para promediar")
    else:
        st.warning("No se encontró dimensión temporal en los datos")

with tab3:
    st.header("Visualización Espacial")

    lat_dim = "latitude" if "latitude" in data_var.dims else "lat"
    lon_dim = "longitude" if "longitude" in data_var.dims else "lon"

    if lat_dim in data_var.dims and lon_dim in data_var.dims:
        # Seleccionar tiempo específico si existe dimensión temporal
        if time_dim and time_dim in data_var.dims:
            time_idx = st.slider(
                "Índice de Tiempo",
                0,
                data_var.shape[list(data_var.dims).index(time_dim)] - 1,
                0,
            )
            spatial_data = data_var.isel({time_dim: time_idx})
        else:
            spatial_data = data_var

        # Crear mapa con Plotly
        fig_map = go.Figure(
            data=go.Heatmap(
                z=spatial_data.values,
                x=spatial_data[lon_dim].values,
                y=spatial_data[lat_dim].values,
                colorscale="RdBu_r",
                colorbar=dict(title=var_name),
            )
        )

        fig_map.update_layout(
            title=f"Mapa de {var_name}",
            xaxis_title="Longitud",
            yaxis_title="Latitud",
            height=600,
        )

        st.plotly_chart(fig_map, use_container_width=True)

        # Controles para el mapa
        col1, col2 = st.columns(2)
        with col1:
            show_stats = st.checkbox("Mostrar estadísticas espaciales", value=True)

        if show_stats:
            st.write(
                f"**Valor medio espacial:** {float(spatial_data.mean().values):.2f}"
            )
            st.write(f"**Mínimo espacial:** {float(spatial_data.min().values):.2f}")
            st.write(f"**Máximo espacial:** {float(spatial_data.max().values):.2f}")
    else:
        st.warning("Los datos no tienen dimensiones espaciales claras")

# Footer
st.markdown("---")
st.caption(
    "Dashboard desarrollado para el proyecto Antropoceno Energético | Benjamín Cabeza Duran (@mechmind-dwv)"
)
