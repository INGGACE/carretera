import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de la página
st.set_page_config(layout="wide", page_title="Avance de Obra Vial")
st.title("🚧 Visualizador de Avance Constructivo por Capas")

# 2. Cargar los datos
@st.cache_data(ttl=600)
def cargar_datos():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTO7xn_vRtSKs38siACAWRJgQ00_nmwv4J3dRDczwsbWNtOVhnHIP45zcl9UILR_g/pub?gid=403930580&single=true&output=csv"
    df = pd.read_csv(url)
    
    # Limpiar columnas y datos
    df.columns = df.columns.str.strip()
    
    df['Abscisa_Inicial'] = df['Abscisa_Inicial'].astype(str).str.replace(r'[a-zA-Z\+]', '', regex=True)
    df['Abscisa_Inicial'] = pd.to_numeric(df['Abscisa_Inicial'], errors='coerce')
    
    df['Abscisa_Final'] = df['Abscisa_Final'].astype(str).str.replace(r'[a-zA-Z\+]', '', regex=True)
    df['Abscisa_Final'] = pd.to_numeric(df['Abscisa_Final'], errors='coerce')
    
    df['Longitud'] = df['Abscisa_Final'] - df['Abscisa_Inicial']
    df['Capa'] = df['Capa'].fillna("Sin definir").astype(str)
    
    # Asegurar que UF, TR y calzada sean texto para evitar errores en los filtros
    if 'UF' in df.columns:
        df['UF'] = df['UF'].fillna("Sin UF").astype(str)
    if 'TR' in df.columns:
        df['TR'] = df['TR'].fillna("Sin TR").astype(str)
    if 'calzada' in df.columns:
        df['calzada'] = df['calzada'].fillna("Sin calzada").astype(str)
        
    return df

df = cargar_datos()

# 3. Panel Lateral para Filtros
st.sidebar.header("Filtros de Visualización")

# -- FILTRO UF --
if 'UF' in df.columns:
    uf_unicas = df['UF'].unique().tolist()
    uf_seleccionadas = st.sidebar.multiselect("Filtrar por UF (Unidad Funcional)", uf_unicas, default=uf_unicas)
else:
    uf_seleccionadas = []

# -- FILTRO TRAMO --
if 'TR' in df.columns:
    tr_unicas = df['TR'].unique().tolist()
    tr_seleccionados = st.sidebar.multiselect("Filtrar por Tramo (TR)", tr_unicas, default=tr_unicas)
else:
    tr_seleccionados = []

# -- FILTRO CALZADA (NUEVO) --
if 'calzada' in df.columns:
    calzada_unicas = df['calzada'].unique().tolist()
    calzada_seleccionada = st.sidebar.multiselect("Filtrar por Calzada", calzada_unicas, default=calzada_unicas)
else:
    calzada_seleccionada = []

# -- FILTRO CAPA --
capas_unicas = df['Capa'].unique().tolist()
capas_seleccionadas = st.sidebar.multiselect("Filtrar por Capa", capas_unicas, default=capas_unicas)

# Aplicar todos los filtros al DataFrame
df_filtrado = df.copy()
if 'UF' in df.columns:
    df_filtrado = df_filtrado[df_filtrado['UF'].isin(uf_seleccionadas)]
if 'TR' in df.columns:
    df_filtrado = df_filtrado[df_filtrado['TR'].isin(tr_seleccionados)]
if 'calzada' in df.columns:
    df_filtrado = df_filtrado[df_filtrado['calzada'].isin(calzada_seleccionada)]
    
df_filtrado = df_filtrado[df_filtrado['Capa'].isin(capas_seleccionadas)]

# 4. Configuración del Gráfico
if df_filtrado.empty:
    st.warning("No hay datos para mostrar con los filtros seleccionados.")
else:
    fig = px.bar(
        df_filtrado,
        base="Abscisa_Inicial",
        x="Longitud",
        y="Capa",
        color="Capa",
        orientation='h',
        hover_name="Capa",
        hover_data={
            'Abscisa_Inicial': True,
            'Abscisa_Final': True,
            'Longitud': False,
            'Capa': False,
            'FECHA DE EXTENSIÓN': True,
            'calzada': True,
            'CARRIL': True,
            'UF': True,
            'TR': True,
            'observación': True
        },
        title="Diagrama de Vía (Pasa el cursor sobre los tramos para ver detalles)"
    )

    fig.update_layout(
        xaxis_title="Abscisas (Metros lineales)",
        yaxis_title="Estructura del Pavimento",
        barmode='overlay',
        height=600,
        plot_bgcolor='white',
        hoverlabel=dict(bgcolor="white", font_size=14)
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', tick0=0, dtick=500)

    # 5. Renderizar elementos
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Base de Datos Dinámica")
st.dataframe(df_filtrado, use_container_width=True)
