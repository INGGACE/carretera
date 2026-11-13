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
    
    # Limpiar y extraer espesores (ESP cm)
    if 'ESP cm' in df.columns:
        df['ESP cm'] = df['ESP cm'].astype(str).str.replace(r'[^\d.,]', '', regex=True).str.replace(',', '.')
        df['ESP cm'] = pd.to_numeric(df['ESP cm'], errors='coerce').fillna(0)
    
    columnas_texto = ['UF', 'TR', 'calzada', 'CARRIL', 'num']
    for col in columnas_texto:
        if col in df.columns:
            df[col] = df[col].fillna(f"Sin {col}").astype(str)
            
    ensayos = ['Planicidad', 'Densidad', 'Textura', 'Deslizamiento']
    for ensayo in ensayos:
        if ensayo in df.columns:
            df[ensayo] = df[ensayo].fillna("No reportado").astype(str)
        else:
            df[ensayo] = "Columna no encontrada"
            
    if 'CARRIL' in df.columns and 'num' in df.columns:
        df['Capa_Carril'] = df['Capa'] + " " + df['num'] + " | " + df['CARRIL']
    elif 'CARRIL' in df.columns:
        df['Capa_Carril'] = df['Capa'] + " | " + df['CARRIL']
    elif 'num' in df.columns:
         df['Capa_Carril'] = df['Capa'] + " " + df['num']
    else:
        df['Capa_Carril'] = df['Capa']
        
    return df

df = cargar_datos()

# 3. Menú Lateral Global (FILTROS EN CASCADA)
st.sidebar.header("🔘 Filtros en Cascada")
if st.sidebar.button("Salir / Cerrar Sesión"):
    st.session_state["acceso_permitido"] = False
    st.rerun()

st.sidebar.markdown("---")
def agregar_todos(lista): return ["Todos"] + list(lista)

df_filtrado = df.copy()

if 'UF' in df_filtrado.columns:
    opciones_uf = agregar_todos(df_filtrado['UF'].unique())
    uf_seleccionada = st.sidebar.radio("Unidad Funcional (UF):", opciones_uf, horizontal=True)
    if uf_seleccionada != "Todos":
        df_filtrado = df_filtrado[df_filtrado['UF'] == uf_seleccionada]

if 'TR' in df_filtrado.columns:
    opciones_tr = agregar_todos(df_filtrado['TR'].unique())
    tr_seleccionado = st.sidebar.radio("Tramo (TR):", opciones_tr, horizontal=True)
    if tr_seleccionado != "Todos":
        df_filtrado = df_filtrado[df_filtrado['TR'] == tr_seleccionado]

if 'calzada' in df_filtrado.columns:
    opciones_calzada = agregar_todos(df_filtrado['calzada'].unique())
    calzada_seleccionada = st.sidebar.radio("Calzada:", opciones_calzada, horizontal=True)
    if calzada_seleccionada != "Todos":
        df_filtrado = df_filtrado[df_filtrado['calzada'] == calzada_seleccionada]

st.sidebar.markdown("---")

if 'CARRIL' in df_filtrado.columns:
    opciones_carril = df_filtrado['CARRIL'].unique()
    carril_seleccionados = st.sidebar.multiselect("Filtrar por Carril:", opciones_carril, default=opciones_carril)
    df_filtrado = df_filtrado[df_filtrado['CARRIL'].isin(carril_seleccionados)]

opciones_capa = df_filtrado['Capa'].unique()
capas_seleccionadas = st.sidebar.multiselect("Filtrar por Tipo de Capa:", opciones_capa, default=opciones_capa)
df_filtrado = df_filtrado[df_filtrado['Capa'].isin(capas_seleccionadas)]

if 'num' in df_filtrado.columns:
    opciones_num = df_filtrado['num'].unique()
    num_capa_seleccionados = st.sidebar.multiselect("Filtrar por Número de Capa:", opciones_num, default=opciones_num)
    df_filtrado = df_filtrado[df_filtrado['num'].isin(num_capa_seleccionados)]

st.title("🚧 Sistema de Gestión Vial")

# 📈 TARJETAS DE INDICADORES
st.markdown("### Resumen de Ejecución")
col1, col2, col3, col4 = st.columns(4)

total_tramos = len(df_filtrado)
col1.metric(label="Tramos Registrados", value=f"{total
