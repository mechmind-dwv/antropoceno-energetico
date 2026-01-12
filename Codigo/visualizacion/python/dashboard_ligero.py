"""
Dashboard ligero para pruebas rápidas
"""

from pathlib import Path

import plotly.express as px
import streamlit as st
import xarray as xr

st.set_page_config(layout="wide")
st.title("Dashboard Ligero - Antropoceno Energético")

# Cargar datos
data_dir = Path("Datos/crudos/reanalisis")
files = list(data_dir.glob("*.nc"))

if files:
    file = st.selectbox("Seleccionar archivo", files)
    ds = xr.open_dataset(file)

    # Mostrar información básica
    st.write(f"**Variable:** {list(ds.data_vars.keys())[0]}")
    st.write(f"**Dimensión:** {ds.dims}")

    # Gráfico simple
    if "valid_time" in ds.dims:
        var = list(ds.data_vars.keys())[0]
        ts = ds[var].mean(dim=["latitude", "longitude"])

        fig = px.line(x=ts.valid_time.values, y=ts.values)
        st.plotly_chart(fig, use_container_width=True)
