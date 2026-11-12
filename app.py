import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de la página
st.set_page_config(layout="wide", page_title="Avance de Obra Vial")
st.title("🚧 Visualizador de Avance Constructivo por Capas")

# 2. Cargar los datos desde tu Google Sheets real
@st.cache_data(ttl=600)
def cargar_datos():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTO7xn_vRtSKs38siACAWRJgQ00_nmwv4J3dRDczwsbWNtOVhnHIP45zcl9UILR_g/pub?gid=403930580&single=true&output=csv"
    
    # Leemos el archivo CSV
    df = pd.read_csv(url)
    
    # Limpiar espacios invisibles en los nombres de las columnas
    df.columns = df.columns.str.strip()
    
    # TRUCO NUEVO: Limpiar las abscisas (quitar letras, K, signos +) y forzarlas a ser números
    df['Abscisa_Inicial'] = df['Abscisa_Inicial'].astype(str).str.replace(r'[a-zA-Z\+]', '', regex=True)
    df['Abscisa_Inicial'] = pd.to_numeric(df['Abscisa_Inicial'], errors='coerce')
    
    df['Abscisa_Final'] = df['Abscisa_Final'].astype(str).str.replace(r'[a-zA-Z\+]', '', regex=True)
    df['Abscisa_Final'] = pd.to_numeric(df['Abscisa_Final'], errors='coerce')
    
    # Calcular la longitud del tramo para el eje X
    df['Longitud'] = df['Abscisa_Final'] - df['Abscisa_Inicial']
    
    # Ordenar las capas de forma lógica
    df['Capa'] = pd.Categorical(df['Capa'], categories=['Subrasante', 'Subbase', 'Base', 'Asfalto'], ordered=True)
    
    return df

# Ejecutar la función
df = cargar_datos()

# 3. Panel Lateral para Filtros
st.sidebar.header("Filtros de Visualización")
capas_seleccionadas = st.sidebar.multiselect("Filtrar por Capa", df['Capa'].dropna().unique(), default=df['Capa'].dropna().unique())

# Verificamos si existe la columna "Estado" o usamos otra para colorear
if 'Estado' in df.columns:
    estado_seleccionado = st.sidebar.multiselect("Filtrar por Estado", df['Estado'].dropna().unique(), default=df['Estado'].dropna().unique())
    df_filtrado = df[(df['Capa'].isin(capas_seleccionadas)) & (df['Estado'].isin(estado_seleccionado))]
    color_col = "Estado"
    color_map = {
        'Aprobado': '#2ecc71',
        'Ejecución': '#f1c40f',
        'Interferencia': '#e74c3c',
        'Vacío': '#95a5a6'
    }
else:
    # Si no tienes la columna "Estado", colorearemos el gráfico por la "Capa"
    df_filtrado = df[(df['Capa'].isin(capas_seleccionadas))]
    color_col = "Capa"
    color_map = None

# 4. Configuración del Gráfico de Plotly
fig = px.bar(
    df_filtrado,
    base="Abscisa_Inicial",
    x="Longitud",
    y="Capa",
    color=color_col,
    orientation='h',
    color_discrete_map=color_map,
    hover_name=color_col,
    hover_data={
        'Abscisa_Inicial': True,
        'Abscisa_Final': True,
        'Longitud': False,
        'Capa': False,
        'FECHA DE EXTENSIÓN': True, # Se agregó desde tu Excel
        'calzada': True,            # Se agregó desde tu Excel
        'CARRIL': True,             # Se agregó desde tu Excel
        'observación': True         # Se agregó desde tu Excel
    },
    title="Diagrama de Vía (Pasa el cursor sobre los tramos para ver detalles)"
)

# Ajustes estéticos
fig.update_layout(
    xaxis_title="Abscisas (Metros lineales)",
    yaxis_title="Estructura del Pavimento",
    barmode='overlay',
    height=400,
    plot_bgcolor='white',
    hoverlabel=dict(bgcolor="white", font_size=14)
)
fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', tick0=0, dtick=500)

# 5. Renderizar elementos en la pantalla
st.plotly_chart(fig, use_container_width=True)

st.subheader("Base de Datos Dinámica")
st.dataframe(df_filtrado, use_container_width=True)
