import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

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
    
    # 🔴 NUEVO: Procesar el Ancho y calcular el Área
    if 'Ancho' in df.columns:
        df['Ancho'] = df['Ancho'].astype(str).str.replace(r'[^\d.,]', '', regex=True).str.replace(',', '.')
        df['Ancho'] = pd.to_numeric(df['Ancho'], errors='coerce').fillna(0)
        df['Area'] = df['Longitud'] * df['Ancho']
    else:
        df['Area'] = 0
    
    columnas_texto = ['UF', 'TR', 'calzada', 'CARRIL', 'num', 'FECHA DE EXTENSIÓN']
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
col1.metric(label="Tramos Registrados", value=f"{total_tramos}")

longitud_total = df_filtrado['Longitud'].sum()
col2.metric(label="Longitud Ejecutada (m)", value=f"{longitud_total:,.0f} m")

km_totales = longitud_total / 1000
col3.metric(label="Kilómetros Totales (km)", value=f"{km_totales:,.2f} km")

if 'Planicidad' in df_filtrado.columns:
    tramos_sin_planicidad = len(df_filtrado[df_filtrado['Planicidad'].str.contains('No reportado|Falta', case=False, na=True)])
    col4.metric(label="Sin ensayo de Planicidad", value=f"{tramos_sin_planicidad} tramos")
else:
    col4.metric(label="Filtro Activo", value="Sí")

st.markdown("---")

# Paleta de colores Realista
mapa_colores = {}
for capa in df['Capa'].unique():
    nombre_capa = str(capa).lower()
    if 'rodadura' in nombre_capa: mapa_colores[capa] = '#3b3b3b' 
    elif 'intermedia' in nombre_capa: mapa_colores[capa] = '#696969' 
    elif 'base' in nombre_capa and 'sub' not in nombre_capa: mapa_colores[capa] = '#8b5a2b'
    elif 'subbase' in nombre_capa: mapa_colores[capa] = '#c2b280'
    elif 'subrasante' in nombre_capa: mapa_colores[capa] = '#5c4033'
    else: mapa_colores[capa] = '#4B8BBE'

# 4. SISTEMA DE PESTAÑAS
tab1, tab2 = st.tabs(["🛣️ Vista en Planta (Avance Físico)", "🔬 Control de Ensayos y Lotes"])

with tab1:
    if df_filtrado.empty:
        st.warning("No hay datos para mostrar.")
    else:
        fig1 = px.bar(
            df_filtrado, base="Abscisa_Inicial", x="Longitud", y="Capa_Carril", color="Capa",    
            orientation='h', hover_name="Capa",
            color_discrete_map=mapa_colores, 
            hover_data={'Abscisa_Inicial': True, 'Abscisa_Final': True, 'Longitud': False, 'Capa_Carril': False, 'Capa': False, 'num': True, 'FECHA DE EXTENSIÓN': True, 'calzada': True, 'observación': True}
        )
        fig1.update_layout(xaxis_title="Abscisas (Metros lineales)", yaxis_title="", barmode='overlay', height=600, plot_bgcolor='#f4f7f6', paper_bgcolor='white', hoverdistance=10, showlegend=True, bargap=0.1)
        fig1.update_xaxes(showgrid=True, gridwidth=1, gridcolor='white', tick0=0, dtick=500, showspikes=True, spikemode="across", spikesnap="cursor", showline=True, linecolor='gray', spikedash="solid", spikecolor="orange", spikethickness=2)
        fig1.update_yaxes(categoryorder='category ascending', showgrid=False, showspikes=True, spikemode="across", spikesnap="cursor", spikedash="solid", spikecolor="orange", spikethickness=2, tickfont=dict(size=13, color='black', weight='bold'))
        st.plotly_chart(fig1, use_container_width=True)

with tab2:
    st.write("Selecciona el ensayo que deseas evaluar. El gráfico coloreará los tramos según el estado del resultado.")
    ensayo_a_revisar = st.radio("Ensayo a visualizar:", ['Planicidad', 'Densidad', 'Textura', 'Deslizamiento'], horizontal=True)
    
    if df_filtrado.empty:
        st.warning("No hay datos para mostrar.")
    else:
        fig2 = px.bar(
            df_filtrado, base="Abscisa_Inicial", x="Longitud", y="Capa_Carril", color=ensayo_a_revisar, 
            orientation='h', hover_name="Capa",
            hover_data={
                'Abscisa_Inicial': True, 'Abscisa_Final': True, 'Longitud': False, 'Capa_Carril': False, 'Capa': False, 'num': True,
                'Planicidad': True, 'Densidad': True, 'Textura': True, 'Deslizamiento': True
            }
        )
        fig2.update_layout(xaxis_title="Abscisas", yaxis_title="Capa (Num) | Carril", barmode='overlay', height=500, plot_bgcolor='white', hoverdistance=10)
        fig2.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', tick0=0, dtick=500, showspikes=True, spikemode="across", spikesnap="cursor", showline=True, spikedash="solid", spikecolor="red", spikethickness=2)
        fig2.update_yaxes(categoryorder='category ascending', showspikes=True, spikemode="across", spikesnap="cursor", spikedash="solid", spikecolor="red", spikethickness=2)
        st.plotly_chart(fig2, use_container_width=True)
        
        # ==================================================
        # 📋 MÓDULO DE AUDITORÍA DE LOTES NORMATIVOS
        # ==================================================
        st.markdown("---")
        st.subheader("📋 Auditoría de Lotes (Cumplimiento Normativo)")
        st.info(f"Calculando lotes para el ensayo de **{ensayo_a_revisar}** agrupados por Jornada y Capa. (Regla: 1 Jornada, 500m lineales o 3,500m²)")
        
        # Filtramos datos que sí tengan fecha válida
        df_auditoria = df_filtrado[~df_filtrado['FECHA DE EXTENSIÓN'].str.contains("Sin FECHA", case=False, na=False)].copy()
        
        if not df_auditoria.empty and 'Area' in df_auditoria.columns and df_auditoria['Area'].sum() > 0:
            
            # Función para identificar si el ensayo realmente se hizo (Ignora los "Falta" o "No reportado")
            def es_ensayo_valido(val):
                val_str = str(val).lower()
                if "no reportado" in val_str or "falta" in val_str or "columna no encontrada" in val_str or val_str == "nan":
                    return 0
                return 1
            
            df_auditoria['Ensayo_Realizado'] = df_auditoria[ensayo_a_revisar].apply(es_ensayo_valido)
            
            # Agrupar por fecha de extensión (Jornada) y Capa
            resumen_lotes = df_auditoria.groupby(['FECHA DE EXTENSIÓN', 'Capa']).agg(
                Longitud_Total=('Longitud', 'sum'),
                Area_Total=('Area', 'sum'),
                Ensayos_Hechos=('Ensayo_Realizado', 'sum')
            ).reset_index()
            
            # MATEMÁTICA NORMATIVA (Redondeando hacia arriba con np.ceil)
            resumen_lotes['Lotes_Longitud'] = np.ceil(resumen_lotes['Longitud_Total'] / 500)
            resumen_lotes['Lotes_Area'] = np.ceil(resumen_lotes['Area_Total'] / 3500)
            
            # El requerimiento es el MÁXIMO entre el criterio de longitud y área (Garantizando mínimo 1 por jornada)
            resumen_lotes['Lotes Exigidos'] = resumen_lotes[['Lotes_Longitud', 'Lotes_Area']].max(axis=1).clip(lower=1).astype(int)
            
            # Evaluar estado final
            resumen_lotes['Estado Normativo'] = resumen_lotes.apply(
                lambda x: "✅ Cumple" if x['Ensayos_Hechos'] >= x['Lotes Exigidos'] 
                else f"❌ Faltan {int(x['Lotes Exigidos'] - x['Ensayos_Hechos'])} ensayos", axis=1
            )
            
            # Darle formato bonito para leerlo fácil
            resumen_lotes['Longitud_Total'] = resumen_lotes['Longitud_Total'].map("{:,.0f} m".format)
            resumen_lotes['Area_Total'] = resumen_lotes['Area_Total'].map("{:,.0f} m²".format)
            
            # Mostrar la tabla final
            tabla_final = resumen_lotes[['FECHA DE EXTENSIÓN', 'Capa', 'Longitud_Total', 'Area_Total', 'Lotes Exigidos', 'Ensayos_Hechos', 'Estado Normativo']]
            st.dataframe(tabla_final.sort_values(by='FECHA DE EXTENSIÓN', ascending=False), use_container_width=True)
            
        else:
            st.warning("⚠️ No se encontraron jornadas de trabajo válidas o los valores de 'Ancho' están en cero. Verifica el Excel.")

st.markdown("---")
st.subheader("Base de Datos Dinámica")
st.dataframe(df_filtrado, use_container_width=True)
