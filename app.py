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

# 4. SISTEMA DE PESTAÑAS
tab1, tab2, tab3 = st.tabs(["📊 Avance Físico (Trazabilidad)", "🔬 Control de Ensayos (Laboratorio)", "📏 Perfil de Espesores"])

with tab1:
    if df_filtrado.empty:
        st.warning("No hay datos para mostrar.")
    else:
        fig1 = px.bar(
            df_filtrado, base="Abscisa_Inicial", x="Longitud", y="Capa_Carril", color="Capa",    
            orientation='h', hover_name="Capa",
            hover_data={'Abscisa_Inicial': True, 'Abscisa_Final': True, 'Longitud': False, 'Capa_Carril': False, 'Capa': False, 'num': True, 'FECHA DE EXTENSIÓN': True, 'calzada': True, 'observación': True}
        )
        fig1.update_layout(xaxis_title="Abscisas", yaxis_title="Capa (Num) | Carril", barmode='overlay', height=700, plot_bgcolor='white', hoverdistance=10)
        fig1.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', tick0=0, dtick=500, showspikes=True, spikemode="across", spikesnap="cursor", showline=True, spikedash="solid", spikecolor="red", spikethickness=2)
        fig1.update_yaxes(categoryorder='category ascending', showspikes=True, spikemode="across", spikesnap="cursor", spikedash="solid", spikecolor="red", spikethickness=2)
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
        fig2.update_layout(xaxis_title="Abscisas", yaxis_title="Capa (Num) | Carril", barmode='overlay', height=700, plot_bgcolor='white', hoverdistance=10)
        fig2.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', tick0=0, dtick=500, showspikes=True, spikemode="across", spikesnap="cursor", showline=True, spikedash="solid", spikecolor="red", spikethickness=2)
        fig2.update_yaxes(categoryorder='category ascending', showspikes=True, spikemode="across", spikesnap="cursor", spikedash="solid", spikecolor="red", spikethickness=2)
        st.plotly_chart(fig2, use_container_width=True)

# ----- PESTAÑA 3: PERFIL DE ESPESORES ACUMULADO -----
with tab3:
    st.subheader("Estructura del Pavimento (Perfil de Espesores)")
    
    if df_filtrado.empty or 'ESP cm' not in df_filtrado.columns:
        st.warning("No hay datos de espesor para mostrar. Verifica que tu Excel tenga la columna 'ESP cm'.")
    elif df_filtrado['ESP cm'].sum() == 0:
        st.warning("Todos los valores de espesor son cero o están vacíos en los tramos filtrados.")
    else:
        df_espesores = df_filtrado.copy()
        
        # 1. Crear formato de abscisa tipo ingeniería (Ej: K1+500)
        df_espesores['Abscisa_Format'] = "K" + (df_espesores['Abscisa_Inicial'] // 1000).astype(int).astype(str) + "+" + (df_espesores['Abscisa_Inicial'] % 1000).astype(int).astype(str).str.zfill(3)
        
        # 2. Ordenar cronológicamente/espacialmente para que la gráfica tenga sentido
        df_espesores = df_espesores.sort_values(by=['Abscisa_Inicial', 'Capa'])
        orden_x = df_espesores['Abscisa_Format'].unique()
        
        # 3. Graficar con separación automática por Carril (facet_row)
        # Esto crea gráficos independientes hacia abajo si tienes más de un carril seleccionado
        carriles_presentes = df_espesores['CARRIL'].unique() if 'CARRIL' in df_espesores.columns else []
        
        if len(carriles_presentes) > 1:
            alto_grafico = max(600, 300 * len(carriles_presentes)) # Ajusta la altura si hay muchos carriles
            fig3 = px.bar(
                df_espesores,
                x="Abscisa_Format",
                y="ESP cm",
                color="Capa",
                facet_row="CARRIL", # Magia pura: crea una fila por cada carril
                hover_name="Capa",
                hover_data={'Abscisa_Format': False, 'Abscisa_Inicial': True, 'Abscisa_Final': True, 'num': True, 'ESP cm': True},
                title="Espesor Acumulado por Abscisa y Carril",
                barmode='stack' # Apila los centímetros uno sobre otro
            )
        else:
            alto_grafico = 600
            fig3 = px.bar(
                df_espesores,
                x="Abscisa_Format",
                y="ESP cm",
                color="Capa",
                hover_name="Capa",
                hover_data={'Abscisa_Format': False, 'Abscisa_Inicial': True, 'Abscisa_Final': True, 'num': True, 'ESP cm': True},
                title="Espesor Acumulado por Abscisa",
                barmode='stack'
            )
            
        fig3.update_layout(
            xaxis_title="Abscisa de Inicio",
            yaxis_title="Espesor Total (cm)",
            height=alto_grafico,
            plot_bgcolor='white',
            hoverlabel=dict(bgcolor="white", font_size=14)
        )
        
        # Forzar el orden correcto en el eje X
        fig3.update_xaxes(showgrid=True, gridcolor='lightgray', type='category', categoryorder='array', categoryarray=orden_x)
        fig3.update_yaxes(showgrid=True, gridcolor='lightgray')
        
        st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")
st.subheader("Base de Datos Dinámica")
st.dataframe(df_filtrado, use_container_width=True)
