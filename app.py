import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de la página
st.set_page_config(layout="wide", page_title="Avance de Obra Vial")
st.title("🚧 Visualizador de Avance Constructivo por Capas y Carriles")

# 2. Cargar los datos
@st.cache_data(ttl=600)
def cargar_datos():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTO7xn_vRtSKs38siACAWRJgQ00_nmwv4J3dRDczwsbWNtOVhnHIP45zcl9UILR_g/pub?gid=403930580&single=true&output=csv"
    df = pd.read_csv(url)
    
    df.columns = df.columns.str.strip()
    
    df['Abscisa_Inicial'] = df['Abscisa_Inicial'].astype(str).str.replace(r'[a-zA-Z\+]', '', regex=True)
    df['Abscisa_Inicial'] = pd.to_numeric(df['Abscisa_Inicial'], errors='coerce')
    
    df['Abscisa_Final'] = df['Abscisa_Final'].astype(str).str.replace(r'[a-zA-Z\+]', '', regex=True)
    df['Abscisa_Final'] = pd.to_numeric(df['Abscisa_Final'], errors='coerce')
    
    df['Longitud'] = df['Abscisa_Final'] - df['Abscisa_Inicial']
    df['Capa'] = df['Capa'].fillna("Sin definir").astype(str)
    
    if 'UF' in df.columns:
        df['UF'] = df['UF'].fillna("Sin UF").astype(str)
    if 'TR' in df.columns:
        df['TR'] = df['TR'].fillna("Sin TR").astype(str)
    if 'calzada' in df.columns:
        df['calzada'] = df['calzada'].fillna("Sin calzada").astype(str)
    if 'CARRIL' in df.columns:
        df['CARRIL'] = df['CARRIL'].fillna("Sin carril").astype(str)
        
    if 'CARRIL' in df.columns:
        df['Capa_Carril'] = df['Capa'] + " | " + df['CARRIL']
    else:
        df['Capa_Carril'] = df['Capa']
        
    return df

df = cargar_datos()

# 3. Panel Lateral para Filtros
st.sidebar.header("🔘 Filtros Rápidos")

def agregar_todos(lista):
    return ["Todos"] + list(lista)

if 'UF' in df.columns:
    uf_unicas = df['UF'].unique().tolist()
    uf_seleccionada = st.sidebar.radio("Unidad Funcional (UF):", agregar_todos(uf_unicas), horizontal=True)
else:
    uf_seleccionada = "Todos"

if 'TR' in df.columns:
    tr_unicas = df['TR'].unique().tolist()
    tr_seleccionado = st.sidebar.radio("Tramo (TR):", agregar_todos(tr_unicas), horizontal=True)
else:
    tr_seleccionado = "Todos"

if 'calzada' in df.columns:
    calzada_unicas = df['calzada'].unique().tolist()
    calzada_seleccionada = st.sidebar.radio("Calzada:", agregar_todos(calzada_unicas), horizontal=True)
else:
    calzada_seleccionada = "Todos"

# -- FILTRO CARRIL RESTAURADO --
if 'CARRIL' in df.columns:
    carril_unicos = df['CARRIL'].unique().tolist()
    carril_seleccionado = st.sidebar.radio("Carril:", agregar_todos(carril_unicos), horizontal=True)
else:
    carril_seleccionado = "Todos"

st.sidebar.markdown("---")
capas_unicas = df['Capa'].unique().tolist()
capas_seleccionadas = st.sidebar.multiselect("Filtrar por Capa (puedes elegir varias):", capas_unicas, default=capas_unicas)

# Aplicar filtros al DataFrame
df_filtrado = df.copy()

if uf_seleccionada != "Todos":
    df_filtrado = df_filtrado[df_filtrado['UF'] == uf_seleccionada]
if tr_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['TR'] == tr_seleccionado]
if calzada_seleccionada != "Todos":
    df_filtrado = df_filtrado[df_filtrado['calzada'] == calzada_seleccionada]
if carril_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['CARRIL'] == carril_seleccionado]
    
df_filtrado = df_filtrado[df_filtrado['Capa'].isin(capas_seleccionadas)]

# 4. Configuración del Gráfico
if df_filtrado.empty:
    st.warning("No hay datos para mostrar con los filtros seleccionados.")
else:
    fig = px.bar(
        df_filtrado,
        base="Abscisa_Inicial",
        x="Longitud",
        y="Capa_Carril",
        color="Capa",    
        orientation='h',
        hover_name="Capa",
        hover_data={
            'Abscisa_Inicial': True,
            'Abscisa_Final': True,
            'Longitud': False,
            'Capa_Carril': False,
            'Capa': False,
            'FECHA DE EXTENSIÓN': True,
            'calzada': True,
            'CARRIL': True,
            'UF': True,
            'TR': True,
            'observación': True
        },
        title="Diagrama de Vía (Desglosado por Carriles)"
    )

    fig.update_layout(
        xaxis_title="Abscisas (Metros lineales)",
        yaxis_title="Capa | Carril",
        barmode='overlay',
        height=700,
        plot_bgcolor='white',
        hoverlabel=dict(bgcolor="white", font_size=14),
        hoverdistance=10, 
    )
    
    fig.update_xaxes(
        showgrid=True, gridwidth=1, gridcolor='lightgray', tick0=0, dtick=500,
        showspikes=True, spikemode="across", spikesnap="cursor", showline=True, 
        spikedash="solid", spikecolor="red", spikethickness=2
    )
    
    fig.update_yaxes(
        categoryorder='category ascending',
        showspikes=True, spikemode="across", spikesnap="cursor", 
        spikedash="solid", spikecolor="red", spikethickness=2
    )

    st.plotly_chart(fig, use_container_width=True)

st.subheader("Base de Datos Dinámica")
st.dataframe(df_filtrado, use_container_width=True)
