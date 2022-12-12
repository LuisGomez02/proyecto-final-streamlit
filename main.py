# Aplicación desarrollada en Streamlit para visualización de datos de biodiversidad
# Autores: Luis Gómez Mantilla (Luiscarlosgomez2000@gmail.com)
#          Marget Aracelly Martínez (margetmartinez@gmail.com)
# Fecha de creación: 2022-12-9


#Carga de bibliotecas

import streamlit as st

import pandas as pd
import geopandas as gpd

import folium
from folium import Marker
from folium.plugins import MarkerCluster
from folium.plugins import HeatMap
from streamlit_folium import folium_static

import plotly.express as px

import math


#
# Configuración de la página
#
st.set_page_config(layout='wide')


#
# TÍTULO Y DESCRIPCIÓN DE LA APLICACIÓN
#

st.title('Visualización de datos de biodiversidad')
st.markdown('Esta aplicación presenta visualizaciones tabulares, gráficas y geoespaciales de datos de biodiversidad que siguen el estándar [Darwin Core (DwC)](https://dwc.tdwg.org/terms/).')
st.markdown('El usuario debe seleccionar un archivo CSV basado en el DwC y posteriormente elegir una de las especies con datos contenidos en el archivo. **El archivo debe estar separado por tabuladores**. Este tipo de archivos puede obtenerse, entre otras formas, en el portal de la [Infraestructura Mundial de Información en Biodiversidad (GBIF)](https://www.gbif.org/).')
st.markdown('La aplicación muestra un conjunto de tablas, gráficos y mapas correspondientes a la distribución de la especie en el tiempo y en el espacio.')


#
# ENTRADAS
#

# Carga de datos
archivo_registros_presencia = st.sidebar.file_uploader('Seleccione un archivo CSV que siga el estándar DwC')

# Se continúa con el procesamiento solo si hay un archivo de datos cargado
if archivo_registros_presencia is not None:
    # Carga de registros de presencia en un dataframe
    registros_presencia = pd.read_csv(archivo_registros_presencia, delimiter='\t', encoding="iso-8859-1")
    # Conversión del dataframe de registros de presencia a geodataframe
    registros_presencia = gpd.GeoDataFrame(registros_presencia, 
                                           geometry=gpd.points_from_xy(registros_presencia.decimalLongitude, 
                                                                       registros_presencia.decimalLatitude),
                                           crs='EPSG:4326')


    # Carga de geojson de los cantones
    canton = gpd.read_file("datos/canton.geojson")



    # Limpieza de datos
    # Eliminación de registros con valores nulos en la columna 'species'
    registros_presencia = registros_presencia[registros_presencia['species'].notna()]
    # Cambio del tipo de datos del campo de fecha
    registros_presencia["eventDate"] = pd.to_datetime(registros_presencia["eventDate"])

    # Especificación de filtros
    # Especie
    lista_especies = registros_presencia.species.unique().tolist()
    lista_especies.sort()
    filtro_especie = st.sidebar.selectbox('Seleccione la especie', lista_especies)


    #
    # PROCESAMIENTO
    #

    # Filtrado
    registros_presencia = registros_presencia[registros_presencia['species'] == filtro_especie]

    # Cálculo de la cantidad de registros en los cantones
    # "Join" espacial de las capas de cantones y registros de presencia de especies
    canton_contienen_registros = canton.sjoin(registros_presencia, how="left", predicate="contains")
    # Conteo de registros de presencia en cada provincia
    canton_registros = canton_contienen_registros.groupby("CODNUM").agg(cantidad_registros_presencia = ("gbifID","count"))
    canton_registros = canton_registros.reset_index() # para convertir a dataframe



    #
    # SALIDAS ------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    #

    # Tabla de registros de presencia
    st.header('Registros de presencia de especies')
    st.dataframe(registros_presencia[['eventDate','species', 'stateProvince', 'locality']].rename(columns = {'eventDate':'Fecha_y_Hora', 'species':'Especie', 'stateProvince':'Provincia', 'locality':'Localidad'}))


    # Definición de columnas de la parte visual de nuestra aplicación en dos columnas
    col1, col2 = st.columns(2)
    col3 = st.columns(1)


    # Gráficos de cantidad de registros de presencia por provincia
    # "Join" para agregar la columna con el conteo a la capa de cantón, aunque se utilizará las provincias
    canton_registros = canton_registros.join(canton.set_index('CODNUM'), on='CODNUM', rsuffix='_b')
    # Dataframe filtrado para usar en graficación
    canton_registros_grafico = canton_registros.loc[canton_registros['cantidad_registros_presencia'] > 0, 
                                                            ["provincia", "cantidad_registros_presencia"]].sort_values("cantidad_registros_presencia", ascending=True) 
    canton_registros_grafico = canton_registros_grafico.set_index('provincia')  


    with col1:
        # Gráficos de registros de presencia por provincias
        st.header('Registros por provincia por provincia')

        fig = px.bar(canton_registros_grafico, 
                    labels={'provincia':'Provincia', 'cantidad_registros_presencia':'Registros de presencia'})    

        fig.update_layout(barmode='stack', xaxis={'categoryorder': 'total descending'})
        st.plotly_chart(fig)    
 
    
    # Gráficos de cantidad de registros de presencia por cantón
    # "Join" para agregar la columna con el conteo a la capa de cantón
    canton_registros = canton_registros.join(canton.set_index('CODNUM'), on='CODNUM', rsuffix='_b')
    # Dataframe filtrado para usar en graficación
    canton_registros_grafico = canton_registros.loc[canton_registros['cantidad_registros_presencia'] > 0, 
                                                            ["NCANTON", "cantidad_registros_presencia"]].sort_values("cantidad_registros_presencia")
    canton_registros_grafico = canton_registros_grafico.set_index('NCANTON')  

    with col2:
        # Gráficos de registros de presencia por canton
        st.header('Registros de presencia por cantón')

        fig = px.bar(canton_registros_grafico, 
                    labels={'NCANTON':'Cantón', 'cantidad_registros_presencia':'a'})    

        fig.update_layout(barmode='stack', xaxis={'categoryorder': 'total descending'})
        st.plotly_chart(fig)

    with col1:
        # Mapas de coropletas de presencia de especies por provincia, cantón y agrupados
        st.header('Mapa de registros de presencia de especies por provincia, cantón y agrupados')
       
        # Capa base
        m = folium.Map(
        location=[10, -84],
        tiles='CartoDB positron', 
        zoom_start=7,
        control_scale=True)


        # Se añaden capas base adicionales
        folium.TileLayer(
        tiles='CartoDB dark_matter', 
        name='CartoDB dark matter').add_to(m)


        # Capa de coropletas
        canton_map = folium.Choropleth(
            name="Mapa de coropletas de los registros por cantón",
            geo_data=canton,
            data=canton_registros,
            columns=['CODNUM', 'cantidad_registros_presencia'],
            bins=8,
            key_on='feature.properties.CODNUM',
            fill_color='Reds', 
            fill_opacity=0.5, 
            line_opacity=1,
            legend_name='Cantidad de registros de presencia por cantón',
            smooth_factor=0).add_to(m)
        
        folium.GeoJsonTooltip(['NCANTON', 'provincia']).add_to(canton_map.geojson)


        # Capa de registros de presencia agrupados
        mc = MarkerCluster(name='Registros agrupados')
        for idx, row in registros_presencia.iterrows():
            if not math.isnan(row['decimalLongitude']) and not math.isnan(row['decimalLatitude']):
                mc.add_child(
                    Marker([row['decimalLatitude'], row['decimalLongitude'], ], 
                                    popup= "Nombre de la especie: " + str(row["species"]) + "\n" + "Provincia: " + str(row["stateProvince"]) + "\n" + "Fecha: " + str(row["eventDate"]),
                                    icon=folium.Icon(color="green")))
        m.add_child(mc)

        
        provincia_map = folium.Choropleth(
            name="Mapa de coropletas de los registros por provincia",
            geo_data=canton,
            data=canton_registros,
            columns=['provincia', 'cantidad_registros_presencia'],
            bins=8,
            key_on='feature.properties.provincia',
            fill_color='Reds', 
            fill_opacity=0.5, 
            line_opacity=1,
            legend_name='Cantidad de registros de presencia por provincia',
            smooth_factor=0).add_to(m)

        folium.GeoJsonTooltip(['NCANTON', 'provincia']).add_to(provincia_map.geojson)

        # Control de capas
        folium.LayerControl().add_to(m) 
        # Despliegue del mapa
        folium_static(m) 
