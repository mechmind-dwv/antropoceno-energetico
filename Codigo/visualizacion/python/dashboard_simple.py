"""
Dashboard simple y rápido para ver datos ERA5
"""

from pathlib import Path

import streamlit as st
import xarray as xr

st.set_page_config(page_title="ERA5 Simple", layout="wide")
st.title("🌡️ Visualización Rápida de Datos ERA5")

# Listar archivos disponibles
data_dir = Path("Datos/crudos/reanalisis")
files = list(data_dir.glob("*.nc"))

if files:
    selected = st.selectbox("Selecciona archivo", [f.name for f in files])

    with st.spinner("Cargando datos..."):
        ds = xr.open_dataset(data_dir / selected)
        st.success(f"✅ Datos cargados: {list(ds.data_vars.keys())[0]}")

        # Mostrar información básica
        st.subheader("Información del Dataset")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Variable:** {list(ds.data_vars.keys())[0]}")
            st.write(f"**Dimensión:** {ds.dims}")
        with col2:
            st.write(f"**Coordenadas:** {list(ds.coords.keys())}")

        # Estadísticas
        var_name = list(ds.data_vars.keys())[0]
        data = ds[var_name]
        st.subheader("Estadísticas")
        st.write(f"**Media:** {float(data.mean()):.2f}")
        st.write(f"**Mínimo:** {float(data.min()):.2f}")
        st.write(f"**Máximo:** {float(data.max()):.2f}")

else:
    st.warning("No hay archivos .nc en Datos/crudos/reanalisis/")
    st.info("Descarga datos primero:")
    st.code(
        "python Codigo/utiles/python/descarga_era5.py --variable temperatura --year 2020 --month 1"
    )
