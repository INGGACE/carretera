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

# 3. Panel Lateral para Filtros (NUEVO FORMATO TIPO BOTÓN/TOGGLE)
st.sidebar.header("🔘 Filtros Rápidos")
st.sidebar.write("Haz clic para encender o apagar cada opción:")

# -- FILTRO UF --
if 'UF' in df.columns:
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Unidad Funcional (UF)**")
    uf_unicas = df['UF'].unique().tolist()
    # Crea un interruptor por cada UF y guarda los que estén encendidos (value=True)
    uf_seleccionadas = [uf for uf in uf_unicas if st.sidebar.checkbox(uf, value=True, key=f"uf_{uf}")]
else:
    uf_seleccionadas = []

# -- FILTRO TRAMO --
if 'TR' in df.columns:
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Tramo (TR)**")
    tr_unicas = df['TR'].unique().tolist()
    tr_seleccionados = [tr for tr in tr_unicas if st.sidebar.checkbox(tr, value=True, key=f"tr_{tr}")]
else:
    tr_seleccionados = []

# -- FILTRO CALZADA --
if 'calzada' in df.columns:
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Calzada**")
    calzada_unicas = df['calzada'].unique().tolist()
    calzada_seleccionada = [calzada for calzada in calzada_unicas if st.sidebar.checkbox(calzada, value=True, key=f"cal_{calzada}")]
else:
    calzada_seleccionada = []
    
# -- FILTRO CARRIL --
if 'CARRIL' in df.columns:
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Carril**")
    carril_unicos = df['CARRIL'].unique().tolist()
    carril_seleccionado = [carril for carril in carril_unicos if st.sidebar.checkbox(carril, value=True, key=f"car_{carril}")]
else:
    carril_seleccionado = []

# -- FILTRO CAPA --
st.sidebar.markdown("---")
st.sidebar.markdown("**Capa Estructural**")
capas_unicas = df['Capa'].unique().tolist()
capas_seleccionadas = [capa for capa in capas_unicas if st.sidebar.checkbox(capa, value=True, key=f"capa_{capa}")]

# Aplicar filtros al DataFrame
df_filtrado = df.copy()
if 'UF' in df.columns:
    df_filtrado = df_filtrado[df_filtrado['UF'].isin(uf_seleccionadas)]
if 'TR' in df.columns:
    df_filtrado = df_filtrado[df_filtrado['TR'].isin(tr_seleccionados)]
if 'calzada' in df.columns:
    df_filtrado = df_filtrado[df_filtrado['calzada'].isin(calzada_seleccionada)]
if 'CARRIL' in df.columns:
    df_filtrado = df_filtrado[df_filtrado['CARRIL'].isin(carril_seleccionado)]
    
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
    
    # Eje X con línea vertical roja gruesa
    fig.update_xaxes(
        showgrid=True, gridwidth=1, gridcolor='lightgray', tick0=0, dtick=500,
        showspikes=True, spikemode="across", spikesnap="cursor", showline=True, 
        spikedash="solid", spikecolor="red", spikethickness=2
    )
    
    # Eje Y con línea horizontal roja gruesa (completa la cruz)
    fig.update_yaxes(
        categoryorder='category ascending',
        showspikes=True, spikemode="across", spikesnap="cursor", 
        spikedash="solid", spikecolor="red", spikethickness=2
    )

    st.plotly_chart(fig, use_container_width=True)

st.subheader("Base de Datos Dinámica")
st.dataframe(df_filtrado, use_container_width=True)
