"""
DASHBOARD AVANZADO - Antropoceno Energético
Dashboard interactivo profesional con múltiples vistas y análisis en tiempo real.
"""

from datetime import datetime
from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
import xarray as xr

# Configuración de la página
st.set_page_config(
    page_title="Antropoceno Energético - Dashboard Avanzado",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título principal con estilo
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    '<h1 class="main-header">🌍 Dashboard Avanzado - Análisis Climático</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    "**Proyecto Antropoceno Energético** | Visualización interactiva de datos ERA5 y análisis científico"
)

# ============================================================================
# SIDEBAR - CONFIGURACIÓN
# ============================================================================
with st.sidebar:
    st.header("⚙️ Configuración del Análisis")

    # 1. Selección de archivo
    st.subheader("📂 Datos")
    data_dir = Path("Datos/crudos/reanalisis")
    nc_files = list(data_dir.glob("*.nc"))

    if not nc_files:
        st.error("No se encontraron archivos .nc")
        st.info("Ejecuta primero:")
        st.code("python descarga_era5.py --variable temperatura --year 2020")
        st.stop()

    selected_file = st.selectbox(
        "Seleccionar archivo ERA5",
        [f.name for f in nc_files],
        help="Selecciona un archivo NetCDF descargado",
    )
    file_path = data_dir / selected_file

    # 2. Variables de análisis
    st.subheader("📊 Variables")
    try:
        ds = xr.open_dataset(file_path)
        available_vars = list(ds.data_vars.keys())
        selected_var = st.selectbox("Variable a analizar", available_vars)

        # Dimensiones disponibles
        dims = list(ds.dims.keys())
        time_dim = next((d for d in ["valid_time", "time", "t"] if d in dims), None)
        lat_dim = next((d for d in ["latitude", "lat"] if d in dims), None)
        lon_dim = next((d for d in ["longitude", "lon"] if d in dims), None)

        # Si tiene dimensiones espaciales, permitir seleccionar región
        if lat_dim and lon_dim:
            st.subheader("🗺️ Región de Análisis")

            # Valores por defecto (Europa)
            lat_min, lat_max = st.slider("Latitud", -90.0, 90.0, (35.0, 45.0))
            lon_min, lon_max = st.slider("Longitud", -180.0, 180.0, (-10.0, 5.0))

            # Convertir a índices de ERA5 (0-360)
            lon_min_era = lon_min if lon_min >= 0 else lon_min + 360
            lon_max_era = lon_max if lon_max >= 0 else lon_max + 360

            # Recortar dataset
            ds_cropped = ds.sel(
                {
                    lat_dim: slice(
                        lat_max, lat_min
                    ),  # Invertido porque ERA5 va de 90 a -90
                    lon_dim: slice(lon_min_era, lon_max_era),
                }
            )
        else:
            ds_cropped = ds

    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        st.stop()

    # 3. Opciones de visualización
    st.subheader("🎨 Visualización")
    theme = st.selectbox(
        "Tema de colores",
        ["plotly", "plotly_white", "plotly_dark", "ggplot2", "seaborn"],
    )
    pio.templates.default = theme

    # 4. Botón para análisis avanzado
    st.subheader("🔬 Análisis Avanzado")
    run_advanced = st.button(
        "🚀 Ejecutar Análisis Completo", type="primary", use_container_width=True
    )


# ============================================================================
# FUNCIONES DE VISUALIZACIÓN AVANZADA
# ============================================================================
def create_spatial_map(ds, variable, time_idx=0):
    """Crea mapa interactivo espacial."""
    if "latitude" not in ds.dims or "longitude" not in ds.dims:
        return None

    # Seleccionar tiempo si existe dimensión temporal
    if "valid_time" in ds.dims:
        data = ds[variable].isel(valid_time=time_idx)
        title = f"{variable} - {pd.to_datetime(str(ds.valid_time[time_idx].values))}"
    else:
        data = ds[variable]
        title = f"{variable} - Promedio Temporal"

    # Convertir a DataFrame para Plotly
    lats = ds.latitude.values
    lons = ds.longitude.values
    values = data.values

    # Crear figura
    fig = go.Figure(
        data=go.Contour(
            z=values,
            x=lons,
            y=lats,
            colorscale="Viridis",
            contours=dict(showlabels=True, labelfont=dict(size=12, color="white")),
            colorbar=dict(title=ds[variable].attrs.get("units", ""), titleside="right"),
        )
    )

    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=16)),
        xaxis_title="Longitud",
        yaxis_title="Latitud",
        height=600,
        template=theme,
    )

    return fig


def create_time_series(ds, variable, lat_idx=None, lon_idx=None):
    """Crea serie temporal interactiva."""
    if "valid_time" not in ds.dims:
        return None

    # Si se especifican coordenadas, extraer punto específico
    if lat_idx is not None and lon_idx is not None:
        data = ds[variable].isel(latitude=lat_idx, longitude=lon_idx)
        lat_val = ds.latitude[lat_idx].values
        lon_val = ds.longitude[lon_idx].values
        title = f"{variable} en ({lat_val:.2f}°, {lon_val:.2f}°)"
    else:
        # Promedio sobre toda la región
        data = ds[variable].mean(dim=["latitude", "longitude"])
        title = f"{variable} - Promedio Regional"

    # Convertir a DataFrame
    df = pd.DataFrame(
        {"Fecha": pd.to_datetime(ds.valid_time.values), "Valor": data.values}
    )

    # Crear figura
    fig = px.line(df, x="Fecha", y="Valor", title=title)

    # Añadir estadísticas
    mean_val = df["Valor"].mean()
    std_val = df["Valor"].std()

    fig.add_hline(
        y=mean_val,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Media: {mean_val:.2f}",
    )
    fig.add_hrect(
        y0=mean_val - std_val,
        y1=mean_val + std_val,
        fillcolor="gray",
        opacity=0.2,
        annotation_text=f"±1σ: {std_val:.2f}",
    )

    fig.update_layout(
        xaxis_title="Fecha",
        yaxis_title=f"{variable} ({ds[variable].attrs.get('units', '')})",
        hovermode="x unified",
        height=500,
        template=theme,
    )

    return fig, df


def create_histogram(ds, variable):
    """Crea histograma interactivo de distribución."""
    data = ds[variable].values.flatten()
    data = data[~np.isnan(data)]

    fig = px.histogram(
        x=data,
        nbins=50,
        title=f"Distribución de {variable}",
        labels={"x": variable, "y": "Frecuencia"},
        opacity=0.7,
        color_discrete_sequence=["#636EFA"],
    )

    # Añadir líneas de estadísticas
    mean_val = np.mean(data)
    median_val = np.median(data)

    fig.add_vline(
        x=mean_val,
        line_dash="dash",
        line_color="red",
        annotation_text=f"Media: {mean_val:.2f}",
    )
    fig.add_vline(
        x=median_val,
        line_dash="dash",
        line_color="green",
        annotation_text=f"Mediana: {median_val:.2f}",
    )

    fig.update_layout(bargap=0.1, height=400, template=theme)

    return fig


def create_heatmap_correlation(ds, variables=None):
    """Crea mapa de calor de correlaciones entre variables."""
    if variables is None:
        variables = list(ds.data_vars.keys())

    if len(variables) < 2:
        return None

    # Calcular correlaciones
    corr_matrix = np.zeros((len(variables), len(variables)))
    for i, var1 in enumerate(variables):
        for j, var2 in enumerate(variables):
            data1 = ds[var1].values.flatten()
            data2 = ds[var2].values.flatten()

            # Eliminar NaNs
            mask = ~np.isnan(data1) & ~np.isnan(data2)
            if np.sum(mask) > 10:  # Mínimo de puntos
                corr = np.corrcoef(data1[mask], data2[mask])[0, 1]
                corr_matrix[i, j] = corr
            else:
                corr_matrix[i, j] = np.nan

    # Crear heatmap
    fig = go.Figure(
        data=go.Heatmap(
            z=corr_matrix,
            x=variables,
            y=variables,
            colorscale="RdBu",
            zmid=0,
            text=np.round(corr_matrix, 2),
            texttemplate="%{text}",
            textfont={"size": 10},
        )
    )

    fig.update_layout(
        title="Matriz de Correlación entre Variables",
        xaxis_title="Variables",
        yaxis_title="Variables",
        height=500,
        template=theme,
    )

    return fig


def create_3d_surface(ds, variable, time_idx=0):
    """Crea superficie 3D interactiva."""
    if "latitude" not in ds.dims or "longitude" not in ds.dims:
        return None

    # Seleccionar tiempo
    if "valid_time" in ds.dims:
        data = ds[variable].isel(valid_time=time_idx)
    else:
        data = ds[variable]

    # Preparar datos
    lats = ds.latitude.values
    lons = ds.longitude.values
    values = data.values

    # Crear malla
    X, Y = np.meshgrid(lons, lats)

    fig = go.Figure(
        data=[
            go.Surface(
                z=values,
                x=X,
                y=Y,
                colorscale="Viridis",
                contours={
                    "z": {
                        "show": True,
                        "usecolormap": True,
                        "highlightcolor": "limegreen",
                        "project": {"z": True},
                    }
                },
            )
        ]
    )

    fig.update_layout(
        title=f"Superficie 3D - {variable}",
        scene=dict(
            xaxis_title="Longitud",
            yaxis_title="Latitud",
            zaxis_title=variable,
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.5)),
        ),
        height=600,
        template=theme,
    )

    return fig


# ============================================================================
# INTERFAZ PRINCIPAL
# ============================================================================
def main():
    # Cargar datos
    with st.spinner("Cargando y procesando datos..."):
        ds_loaded = ds_cropped
        data_var = ds_loaded[selected_var]

    # Mostrar información del dataset
    st.sidebar.success(f"✅ Dataset cargado: {selected_file}")

    # ========================================================================
    # SECCIÓN 1: RESUMEN Y MÉTRICAS
    # ========================================================================
    st.header("📊 Resumen del Dataset")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Variable Principal", selected_var)

    with col2:
        unit = data_var.attrs.get("units", "N/A")
        st.metric("Unidades", unit)

    with col3:
        st.metric("Dimensión", f"{data_var.shape}")

    with col4:
        mean_val = float(data_var.mean().values)
        st.metric("Valor Medio", f"{mean_val:.2f}")

    # ========================================================================
    # SECCIÓN 2: VISUALIZACIONES PRINCIPALES
    # ========================================================================
    st.header("📈 Visualizaciones Interactivas")

    # Tabs para diferentes tipos de visualización
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "🗺️ Mapa Espacial",
            "📅 Serie Temporal",
            "📊 Distribución",
            "🔗 Correlaciones",
            "🎨 3D Surface",
        ]
    )

    with tab1:
        st.subheader("Mapa Espacial Interactivo")

        # Control para seleccionar tiempo
        if "valid_time" in ds_loaded.dims:
            time_idx = st.slider(
                "Seleccionar tiempo",
                0,
                len(ds_loaded.valid_time) - 1,
                0,
                format="Índice %d",
            )
        else:
            time_idx = 0

        # Crear y mostrar mapa
        map_fig = create_spatial_map(ds_loaded, selected_var, time_idx)
        if map_fig:
            st.plotly_chart(map_fig, use_container_width=True)

            # Exportar opciones
            col_map1, col_map2 = st.columns(2)
            with col_map1:
                if st.button("💾 Guardar Mapa como PNG"):
                    map_fig.write_image("mapa_espacial.png")
                    st.success("Mapa guardado como mapa_espacial.png")
            with col_map2:
                st.download_button(
                    label="📥 Descargar Datos del Mapa",
                    data=ds_loaded[selected_var].to_dataframe().to_csv(),
                    file_name="datos_mapa.csv",
                    mime="text/csv",
                )

    with tab2:
        st.subheader("Análisis de Series Temporales")

        # Opciones para selección de punto
        col_ts1, col_ts2 = st.columns(2)

        with col_ts1:
            analysis_mode = st.radio(
                "Modo de análisis",
                ["Promedio Regional", "Punto Específico"],
                horizontal=True,
            )

        if (
            analysis_mode == "Punto Específico"
            and "latitude" in ds_loaded.dims
            and "longitude" in ds_loaded.dims
        ):
            with col_ts2:
                # Selector de coordenadas
                lat_val = st.slider(
                    "Latitud",
                    float(ds_loaded.latitude.min()),
                    float(ds_loaded.latitude.max()),
                    float(ds_loaded.latitude.mean()),
                )
                lon_val = st.slider(
                    "Longitud",
                    float(ds_loaded.longitude.min()),
                    float(ds_loaded.longitude.max()),
                    float(ds_loaded.longitude.mean()),
                )

            # Encontrar índices más cercanos
            lat_idx = np.abs(ds_loaded.latitude - lat_val).argmin()
            lon_idx = np.abs(ds_loaded.longitude - lon_val).argmin()

            ts_fig, ts_data = create_time_series(
                ds_loaded, selected_var, lat_idx, lon_idx
            )
        else:
            ts_fig, ts_data = create_time_series(ds_loaded, selected_var)

        if ts_fig:
            st.plotly_chart(ts_fig, use_container_width=True)

            # Estadísticas de la serie
            if ts_data is not None:
                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                with col_stat1:
                    st.metric("Media Temporal", f"{ts_data['Valor'].mean():.2f}")
                with col_stat2:
                    st.metric("Desviación Estándar", f"{ts_data['Valor'].std():.2f}")
                with col_stat3:
                    st.metric("Mínimo", f"{ts_data['Valor'].min():.2f}")
                with col_stat4:
                    st.metric("Máximo", f"{ts_data['Valor'].max():.2f}")

                # Análisis de tendencia
                if len(ts_data) > 1:
                    x = np.arange(len(ts_data))
                    y = ts_data["Valor"].values
                    coeff = np.polyfit(x, y, 1)
                    trend = coeff[0] * len(ts_data)  # Cambio total en el período

                    st.info(
                        f"📈 Tendencia en el período: {trend:.4f} (pendiente: {coeff[0]:.6f} por paso de tiempo)"
                    )

    with tab3:
        st.subheader("Distribución de Valores")

        hist_fig = create_histogram(ds_loaded, selected_var)
        if hist_fig:
            st.plotly_chart(hist_fig, use_container_width=True)

            # Percentiles
            data_flat = ds_loaded[selected_var].values.flatten()
            data_flat = data_flat[~np.isnan(data_flat)]

            col_per1, col_per2, col_per3, col_per4 = st.columns(4)
            with col_per1:
                st.metric("Percentil 25", f"{np.percentile(data_flat, 25):.2f}")
            with col_per2:
                st.metric("Mediana (P50)", f"{np.median(data_flat):.2f}")
            with col_per3:
                st.metric("Percentil 75", f"{np.percentile(data_flat, 75):.2f}")
            with col_per4:
                st.metric("Percentil 90", f"{np.percentile(data_flat, 90):.2f}")

    with tab4:
        st.subheader("Análisis de Correlaciones")

        # Seleccionar variables para correlación
        available_vars = list(ds_loaded.data_vars.keys())
        if len(available_vars) > 1:
            selected_corr_vars = st.multiselect(
                "Seleccionar variables para correlación",
                available_vars,
                default=available_vars[: min(5, len(available_vars))],
            )

            if len(selected_corr_vars) >= 2:
                corr_fig = create_heatmap_correlation(ds_loaded, selected_corr_vars)
                if corr_fig:
                    st.plotly_chart(corr_fig, use_container_width=True)

                    # Identificar correlaciones fuertes
                    st.subheader("🔍 Correlaciones Destacadas")

                    # Calcular todas las correlaciones por pares
                    correlations = []
                    for i, var1 in enumerate(selected_corr_vars):
                        for j, var2 in enumerate(selected_corr_vars):
                            if i < j:
                                data1 = ds_loaded[var1].values.flatten()
                                data2 = ds_loaded[var2].values.flatten()
                                mask = ~np.isnan(data1) & ~np.isnan(data2)
                                if np.sum(mask) > 10:
                                    corr = np.corrcoef(data1[mask], data2[mask])[0, 1]
                                    correlations.append(
                                        {
                                            "Variable 1": var1,
                                            "Variable 2": var2,
                                            "Correlación": corr,
                                            "|Corr|": abs(corr),
                                        }
                                    )

                    if correlations:
                        df_corr = pd.DataFrame(correlations)
                        df_corr = df_corr.sort_values("|Corr|", ascending=False)

                        # Mostrar tabla de correlaciones
                        st.dataframe(
                            df_corr[["Variable 1", "Variable 2", "Correlación"]].head(
                                10
                            ),
                            use_container_width=True,
                        )
            else:
                st.warning(
                    "Selecciona al menos 2 variables para análisis de correlación"
                )
        else:
            st.info("Se necesitan múltiples variables para análisis de correlación")

    with tab5:
        st.subheader("Visualización 3D")

        if "latitude" in ds_loaded.dims and "longitude" in ds_loaded.dims:
            if "valid_time" in ds_loaded.dims:
                time_3d = st.slider(
                    "Seleccionar tiempo para 3D",
                    0,
                    len(ds_loaded.valid_time) - 1,
                    0,
                    key="3d_time",
                )
            else:
                time_3d = 0

            surface_fig = create_3d_surface(ds_loaded, selected_var, time_3d)
            if surface_fig:
                st.plotly_chart(surface_fig, use_container_width=True)

                # Controles de cámara 3D
                st.caption(
                    "💡 Usa el mouse para rotar, hacer zoom y pan en la visualización 3D"
                )
        else:
            st.warning("Se necesitan dimensiones espaciales para visualización 3D")

    # ========================================================================
    # SECCIÓN 3: ANÁLISIS AVANZADO (solo si se solicita)
    # ========================================================================
    if run_advanced:
        st.header("🔬 Análisis Avanzado")

        with st.expander("📐 Análisis de Gradientes Espaciales", expanded=True):
            st.subheader("Gradientes de Temperatura")

            if "latitude" in ds_loaded.dims and "longitude" in ds_loaded.dims:
                # Calcular gradientes norte-sur y este-oeste
                data = ds_loaded[selected_var]

                # Gradiente norte-sur (promedio por latitud)
                if "valid_time" in data.dims:
                    data_mean = data.mean(dim="valid_time")
                else:
                    data_mean = data

                lat_profile = data_mean.mean(dim="longitude")

                fig_grad = go.Figure()
                fig_grad.add_trace(
                    go.Scatter(
                        x=ds_loaded.latitude.values,
                        y=lat_profile.values,
                        mode="lines+markers",
                        name="Perfil Norte-Sur",
                        line=dict(color="blue", width=2),
                    )
                )

                # Calcular gradiente
                lat_diff = np.gradient(lat_profile.values, ds_loaded.latitude.values)
                fig_grad.add_trace(
                    go.Scatter(
                        x=ds_loaded.latitude.values,
                        y=lat_diff,
                        mode="lines",
                        name="Gradiente (°C/°)",
                        line=dict(color="red", width=1, dash="dash"),
                        yaxis="y2",
                    )
                )

                fig_grad.update_layout(
                    title="Perfil Latitudinal y Gradiente",
                    xaxis_title="Latitud (°)",
                    yaxis_title=f"{selected_var} ({unit})",
                    yaxis2=dict(title="Gradiente (°C/°)", overlaying="y", side="right"),
                    height=400,
                    template=theme,
                )

                st.plotly_chart(fig_grad, use_container_width=True)

                # Estadísticas del gradiente
                max_grad_idx = np.argmax(np.abs(lat_diff))
                st.metric(
                    "Gradiente Máximo",
                    f"{lat_diff[max_grad_idx]:.4f} °C/°",
                    f"en {ds_loaded.latitude.values[max_grad_idx]:.2f}°",
                )

        with st.expander("🔄 Análisis de Variabilidad Temporal", expanded=False):
            st.subheader("Descomposición Temporal")

            if "valid_time" in ds_loaded.dims and len(ds_loaded.valid_time) > 24:
                # Convertir a serie temporal
                ts_region = ds_loaded[selected_var].mean(dim=["latitude", "longitude"])

                # Crear DataFrame para análisis
                df_ts = pd.DataFrame(
                    {
                        "valor": ts_region.values,
                        "fecha": pd.to_datetime(ts_region.valid_time.values),
                    }
                )
                df_ts.set_index("fecha", inplace=True)

                # Análisis de componentes (simple)
                df_ts["media_movil_24h"] = (
                    df_ts["valor"].rolling(window=24, center=True).mean()
                )
                df_ts["residuo"] = df_ts["valor"] - df_ts["media_movil_24h"]

                fig_comp = go.Figure()
                fig_comp.add_trace(
                    go.Scatter(
                        x=df_ts.index,
                        y=df_ts["valor"],
                        mode="lines",
                        name="Original",
                        line=dict(color="blue", width=1),
                    )
                )
                fig_comp.add_trace(
                    go.Scatter(
                        x=df_ts.index,
                        y=df_ts["media_movil_24h"],
                        mode="lines",
                        name="Media Móvil 24h",
                        line=dict(color="red", width=2),
                    )
                )

                fig_comp.update_layout(
                    title="Descomposición Temporal",
                    xaxis_title="Fecha",
                    yaxis_title=selected_var,
                    height=400,
                    template=theme,
                )

                st.plotly_chart(fig_comp, use_container_width=True)

    # ========================================================================
    # SECCIÓN 4: EXPORTACIÓN DE RESULTADOS
    # ========================================================================
    st.header("💾 Exportación de Resultados")

    col_exp1, col_exp2, col_exp3 = st.columns(3)

    with col_exp1:
        # Exportar datos procesados
        st.download_button(
            label="📥 Descargar Datos Procesados (CSV)",
            data=ds_loaded[selected_var].to_dataframe().to_csv(),
            file_name=f"datos_procesados_{selected_var}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_exp2:
        # Exportar estadísticas
        stats_dict = {
            "Variable": selected_var,
            "Media": float(data_var.mean().values),
            "Desviación Estándar": float(data_var.std().values),
            "Mínimo": float(data_var.min().values),
            "Máximo": float(data_var.max().values),
            "Percentil_25": float(np.percentile(data_var.values.flatten(), 25)),
            "Mediana": float(np.median(data_var.values.flatten())),
            "Percentil_75": float(np.percentile(data_var.values.flatten(), 75)),
        }

        stats_df = pd.DataFrame([stats_dict])
        st.download_button(
            label="📊 Descargar Estadísticas (CSV)",
            data=stats_df.to_csv(index=False),
            file_name=f"estadisticas_{selected_var}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with col_exp3:
        # Generar reporte
        if st.button("📄 Generar Reporte Automático", use_container_width=True):
            with st.spinner("Generando reporte..."):
                # Crear reporte simple
                report = f"""
                ============================================
                REPORTE DE ANÁLISIS - ANTROPOCENO ENERGÉTICO
                ============================================

                Archivo analizado: {selected_file}
                Variable: {selected_var}
                Fecha de análisis: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

                ESTADÍSTICAS PRINCIPALES:
                - Media: {stats_dict['Media']:.2f}
                - Desviación Estándar: {stats_dict['Desviación Estándar']:.2f}
                - Rango: {stats_dict['Mínimo']:.2f} a {stats_dict['Máximo']:.2f}
                - Mediana: {stats_dict['Mediana']:.2f}

                DIMENSIONES:
                - Forma del dataset: {data_var.shape}
                - Dimensiones: {list(data_var.dims)}

                OBSERVACIONES:
                Análisis generado automáticamente por el Dashboard Avanzado.
                """

                st.download_button(
                    label="📥 Descargar Reporte (TXT)",
                    data=report,
                    file_name=f"reporte_{selected_var}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

    # ========================================================================
    # FOOTER
    # ========================================================================
    st.markdown("---")

    col_foot1, col_foot2 = st.columns([2, 1])

    with col_foot1:
        st.caption(
            """
        **Dashboard Avanzado - Proyecto Antropoceno Energético**
        Desarrollado por Benjamín Cabeza Duran (@mechmind-dwv)
        Herramientas: Streamlit, Plotly, Xarray, Pandas, NumPy
        """
        )

    with col_foot2:
        st.caption(
            f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )


if __name__ == "__main__":
    main()
