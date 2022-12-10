# Aplicación desarrollada en Streamlit para visualización de datos de biodiversidad
# Autor: Luis Gómez Mantilla (Luiscarlosgomez2000@gmail.com)
# Fecha de creación: 2022-12-9

import streamlit as st

import pandas as pd
import geopandas as gpd

import plotly.express as px

import folium
from folium import Marker
from folium.plugins import MarkerCluster
from folium.plugins import HeatMap
from streamlit_folium import folium_static

#
# Configuración de la página
#
st.set_page_config(layout='wide')

#
# TÍTULO Y DESCRIPCIÓN DE LA APLICACIÓN
#

st.tittle('Proyecto final Programación SIG')
st.markdown('Esta aplicación presenta visualizaciones tabulares, gráficas y geoespaciales de datos de biodiversidad de los felinos que siguen el estándar [Darwin Core (DwC)](https://dwc.tdwg.org/terms/).')
st.markdown('El usuario debe seleccionar un archivo CSV basado en el DwC y posteriormente elegir una de las especies con datos contenidos en el archivo. **El archivo debe estar separado por tabuladores**. Este tipo de archivos puede obtenerse, entre otras formas, en el portal de la [Infraestructura Mundial de Información en Biodiversidad (GBIF)](https://www.gbif.org/).')
st.markdown('La aplicación muestra un conjunto de tablas, gráficos y mapas correspondientes a la distribución de la especie en el tiempo y en el espacio.')

