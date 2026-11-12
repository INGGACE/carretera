import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración y Seguridad
st.set_page_config(layout="wide", page_title="Avance de Obra Vial")

if "acceso_permitido" not in st.session_state:
    st.session_state["acceso_permitido"] = False

if not st.session_state["acceso_permitido"]:
    st.title("🔒 Acceso Restringido")
    st.write("Ingresa la contraseña para visualizar el avance de la obra.")
    clave_ingresada = st.text_input("Contraseña:", type="password")
    if st.button("Ingresar"):
        if clave_ingresada == "Obra2026":
            st.session_state["acceso_permitido"] = True
            st.rerun()
        else:
            st.error("Contraseña incorrecta. Intenta nuevamente.")
    st.stop()

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
    
    # Manejo de columnas estándar
    columnas_texto = ['UF', 'TR', 'calzada', 'CARRIL']
    for col in columnas_texto:
        if col in df.columns:
            df[col] = df[col].fillna(f"Sin {col}").astype(str)
            
    # Manejo de las nuevas columnas de ensayos (Se crean vacías si no existen en tu Excel aún)
    ensayos = ['Planicidad', 'Densidad', 'Textura', 'Deslizamiento']
    for ensayo in ensayos:
        if ensayo in df.columns:
            df[ensayo] = df[ensayo].fillna("No reportado").astype(str)
        else:
            df[ensayo] = "Columna no encontrada"
            
    if 'CARRIL' in df.columns:
        df['Capa_Carril'] = df['Capa'] + " | " + df['CARRIL']
    else:
        df['Capa_Carril'] = df['Capa']
        
    return df

df = cargar_datos()

# 3. Menú Lateral Global
st.sidebar.header("🔘 Filtros Globales")
if st.sidebar.button("Salir / Cerrar Sesión"):
    st.session_state["acceso_permitido"] = False
    st.rerun()

st.sidebar.markdown("---")
def agregar_todos(lista): return ["Todos"] + list(lista)

if 'UF' in df.columns:
    uf_seleccionada = st.sidebar.radio("Unidad Funcional (UF):", agregar_todos(df['UF'].unique()), horizontal=True)
else:
    uf_seleccionada = "Todos"

if 'TR' in df.columns:
    tr_seleccionado = st.sidebar.radio("Tramo (TR):", agregar_todos(df['TR'].unique()), horizontal=True)
else:
    tr_seleccionado = "Todos"

if 'calzada' in df.columns:
    calzada_seleccionada = st.sidebar.radio("Calzada:", agregar_todos(df['calzada'].unique()), horizontal=True)
else:
    calzada_seleccionada = "Todos"

st.sidebar.markdown("---")
if 'CARRIL' in df.columns:
    carril_seleccionados = st.sidebar.multiselect("Filtrar por Carril:", df['CARRIL'].unique(), default=df['CARRIL'].unique())
else:
    carril_seleccionados = []

capas_seleccionadas = st.sidebar.multiselect("Filtrar por Capa:", df['Capa'].unique(), default=df['Capa'].unique())

# Filtro general aplicado a todo
df_filtrado = df.copy()
if uf_seleccionada != "Todos": df_filtrado = df_filtrado[df_filtrado['UF'] == uf_seleccionada]
if tr_seleccionado != "Todos": df_filtrado = df_filtrado[df_filtrado['TR'] == tr_seleccionado]
if calzada_seleccionada != "Todos": df_filtrado = df_filtrado[df_filtrado['calzada'] == calzada_seleccionada]
if 'CARRIL' in df.columns: df_filtrado = df_filtrado[df_filtrado['CARRIL'].isin(carril_seleccionados)]
df_filtrado = df_filtrado[df_filtrado['Capa'].isin(capas_seleccionadas)]


# ==========================================
# 4. SISTEMA DE PESTAÑAS (TABS)
# ==========================================
st.title("🚧 Sistema de Gestión Vial")
tab1, tab2 = st.tabs(["📊 Avance Físico (Trazabilidad)", "🔬 Control de Ensayos (Laboratorio)"])

# ----- PESTAÑA 1: AVANCE FÍSICO (Como estaba antes) -----
with tab1:
    st.subheader("Avance Constructivo por Capas")
    if df_filtrado.empty:
        st.warning("No hay datos para mostrar.")
    else:
        fig1 = px.bar(
            df_filtrado, base="Abscisa_Inicial", x="Longitud", y="Capa_Carril", color="Capa",    
            orientation='h', hover_name="Capa",
            hover_data={'Abscisa_Inicial': True, 'Abscisa_Final': True, 'Longitud': False, 'Capa_Carril': False, 'Capa': False, 'FECHA DE EXTENSIÓN': True, 'calzada': True, 'observación': True}
        )
        fig1.update_layout(xaxis_title="Abscisas", yaxis_title="Capa | Carril", barmode='overlay', height=700, plot_bgcolor='white', hoverdistance=10)
        fig1.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', tick0=0, dtick=500, showspikes=True, spikemode="across", spikesnap="cursor", showline=True, spikedash="solid", spikecolor="red", spikethickness=2)
        fig1.update_yaxes(categoryorder='category ascending', showspikes=True, spikemode="across", spikesnap="cursor", spikedash="solid", spikecolor="red", spikethickness=2)
        st.plotly_chart(fig1, use_container_width=True)

# ----- PESTAÑA 2: CONTROL DE ENSAYOS -----
with tab2:
    st.subheader("Estado de Ensayos Técnicos")
    st.write("Selecciona el ensayo que deseas evaluar. El gráfico coloreará los tramos según el estado del resultado.")
    
    # Selector exclusivo de la pestaña 2 para elegir qué ensayo queremos revisar
    ensayo_a_revisar = st.radio("Ensayo a visualizar:", ['Planicidad', 'Densidad', 'Textura', 'Deslizamiento'], horizontal=True)
    
    if df_filtrado.empty:
        st.warning("No hay datos para mostrar.")
    else:
        # Aquí coloreamos usando la columna del ensayo seleccionado en lugar de la 'Capa'
        fig2 = px.bar(
            df_filtrado, base="Abscisa_Inicial", x="Longitud", y="Capa_Carril", 
            color=ensayo_a_revisar, # MAGIA AQUÍ: El color depende del ensayo
            orientation='h', hover_name="Capa",
            hover_data={
                'Abscisa_Inicial': True, 'Abscisa_Final': True, 'Longitud': False, 'Capa_Carril': False, 'Capa': False,
                'Planicidad': True, 'Densidad': True, 'Textura': True, 'Deslizamiento': True
            }
        )
        fig2.update_layout(xaxis_title="Abscisas", yaxis_title="Capa | Carril", barmode='overlay', height=700, plot_bgcolor='white', hoverdistance=10)
        fig2.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', tick0=0, dtick=500, showspikes=True, spikemode="across", spikesnap="cursor", showline=True, spikedash="solid", spikecolor="red", spikethickness=2)
        fig2.update_yaxes(categoryorder='category ascending', showspikes=True, spikemode="across", spikesnap="cursor", spikedash="solid", spikecolor="red", spikethickness=2)
        st.plotly_chart(fig2, use_container_width=True)

# Tabla visible en ambas pestañas al final de la página
st.markdown("---")
st.subheader("Base de Datos Dinámica")
st.dataframe(df_filtrado, use_container_width=True)
