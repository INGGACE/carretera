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
            
    # Asignar un "peso" a cada capa para ordenarlas estructuralmente
    def obtener_peso(capa):
        c = str(capa).lower()
        if 'rodadura' in c: return 50
        if 'intermedia' in c: return 40
        if 'base' in c and 'sub' not in c: return 30
        if 'subbase' in c: return 20
        if 'subrasante' in c: return 10
        return 0 
    
    df['Peso_Capa'] = df['Capa'].apply(obtener_peso)
    
    if 'num' in df.columns:
        df['Num_Valor'] = pd.to_numeric(df['num'], errors='coerce').fillna(1)
        df['Capa_Num'] = df['Capa'] + " " + df['num'].astype(str)
    else:
        df['Num_Valor'] = 1
        df['Capa_Num'] = df['Capa']
        
    if 'CARRIL' in df.columns and 'num' in df.columns:
        df['Capa_Carril'] = df['Capa_Num'] + " | " + df['CARRIL']
    elif 'CARRIL' in df.columns:
        df['Capa_Carril'] = df['Capa'] + " | " + df['CARRIL']
    else:
        df['Capa_Carril'] = df['Capa_Num']
        
    df = df.sort_values(by=['Peso_Capa', 'Num_Valor', 'Abscisa_Inicial'])
        
    return df

df = cargar_datos()

# 3. Menú Lateral Global
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
    if uf_seleccionada != "Todos": df_filtrado = df_filtrado[df_filtrado['UF'] == uf_seleccionada]

if 'TR' in df_filtrado.columns:
    opciones_tr = agregar_todos(df_filtrado['TR'].unique())
    tr_seleccionado = st.sidebar.radio("Tramo (TR):", opciones_tr, horizontal=True)
    if tr_seleccionado != "Todos": df_filtrado = df_filtrado[df_filtrado['TR'] == tr_seleccionado]

if 'calzada' in df_filtrado.columns:
    opciones_calzada = agregar_todos(df_filtrado['calzada'].unique())
    calzada_seleccionada = st.sidebar.radio("Calzada:", opciones_calzada, horizontal=True)
    if calzada_seleccionada != "Todos": df_filtrado = df_filtrado[df_filtrado['calzada'] == calzada_seleccionada]

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

orden_capa_carril = df_filtrado['Capa_Carril'].unique().tolist()
orden_capas = df_filtrado['Capa'].unique().tolist()

# 4. SISTEMA DE PESTAÑAS
tab1, tab2, tab3 = st.tabs(["📊 Avance Físico (Trazabilidad)", "🔬 Control de Ensayos (Laboratorio)", "📏 Perfil de Espesores"])

with tab1:
    if df_filtrado.empty:
        st.warning("No hay datos para mostrar.")
    else:
        fig1 = px.bar(
            df_filtrado, base="Abscisa_Inicial", x="Longitud", y="Capa_Carril", color="Capa",    
            orientation='h', hover_name="Capa",
            hover_data={'Abscisa_Inicial': True, 'Abscisa_Final': True, 'Longitud': False, 'Capa_Carril': False, 'Capa': False, 'num': True, 'FECHA DE EXTENSIÓN': True, 'calzada': True, 'observación': True},
            category_orders={"Capa_Carril": orden_capa_carril, "Capa": orden_capas}
        )
        fig1.update_layout(xaxis_title="Abscisas", yaxis_title="Capa (Num) | Carril", barmode='overlay', height=700, plot_bgcolor='white', hoverdistance=10)
        fig1.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', tick0=0, dtick=500, showspikes=True, spikemode="across", spikesnap="cursor", showline=True, spikedash="solid", spikecolor="red", spikethickness=2)
        fig1.update_yaxes(showspikes=True, spikemode="across", spikesnap="cursor", spikedash="solid", spikecolor="red", spikethickness=2)
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
            hover_data={'Abscisa_Inicial': True, 'Abscisa_Final': True, 'Longitud': False, 'Capa_Carril': False, 'Capa': False, 'num': True, 'Planicidad': True, 'Densidad': True, 'Textura': True, 'Deslizamiento': True},
            category_orders={"Capa_Carril": orden_capa_carril}
        )
        fig2.update_layout(xaxis_title="Abscisas", yaxis_title="Capa (Num) | Carril", barmode='overlay', height=700, plot_bgcolor='white', hoverdistance=10)
        fig2.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', tick0=0, dtick=500, showspikes=True, spikemode="across", spikesnap="cursor", showline=True, spikedash="solid", spikecolor="red", spikethickness=2)
        fig2.update_yaxes(showspikes=True, spikemode="across", spikesnap="cursor", spikedash="solid", spikecolor="red", spikethickness=2)
        st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.subheader("Estructura del Pavimento (Perfil de Espesores)")
    
    if df_filtrado.empty or 'ESP cm' not in df_filtrado.columns:
        st.warning("No hay datos de espesor para mostrar. Verifica que tu Excel tenga la columna 'ESP cm'.")
    elif df_filtrado['ESP cm'].sum() == 0:
        st.warning("Todos los valores de espesor son cero o están vacíos en los tramos filtrados.")
    else:
        df_espesores = df_filtrado.copy()
        
        # 🔴 SOLUCIÓN AL ERROR: Eliminamos las filas donde no haya escrito un abscisado para evitar el colapso
        df_espesores = df_espesores.dropna(subset=['Abscisa_Inicial'])
        
        if df_espesores.empty:
            st.warning("No hay tramos con abscisa inicial válida para generar este gráfico.")
        else:
            df_espesores['Abscisa_Format'] = "K" + (df_espesores['Abscisa_Inicial'] // 1000).astype(int).astype(str) + "+" + (df_espesores['Abscisa_Inicial'] % 1000).astype(int).astype(str).str.zfill(3)
            
            orden_x = df_espesores.sort_values(by='Abscisa_Inicial')['Abscisa_Format'].unique().tolist()
            orden_capa_num = df_espesores['Capa_Num'].unique().tolist()
            
            carriles_presentes = df_espesores['CARRIL'].unique() if 'CARRIL' in df_espesores.columns else []
            
            alto_grafico = max(600, 300 * len(carriles_presentes)) if len(carriles_presentes) > 1 else 600
            
            fig3 = px.bar(
                df_espesores,
                x="Abscisa_Format",
                y="ESP cm",
                color="Capa_Num",
                facet_row="CARRIL" if len(carriles_presentes) > 1 else None,
                hover_name="Capa_Num",
                hover_data={'Abscisa_Format': False, 'Abscisa_Inicial': True, 'Abscisa_Final': True, 'ESP cm': True},
                title="Espesor Acumulado por Abscisa y Carril",
                barmode='stack',
                category_orders={"Abscisa_Format": orden_x, "Capa_Num": orden_capa_num} 
            )
                
            fig3.update_layout(
                xaxis_title="Abscisa de Inicio",
                yaxis_title="Espesor Total (cm)",
                height=alto_grafico,
                plot_bgcolor='white',
                hoverlabel=dict(bgcolor="white", font_size=14)
            )
            
            fig3.update_xaxes(showgrid=True, gridcolor='lightgray', type='category')
            fig3.update_yaxes(showgrid=True, gridcolor='lightgray')
            
            st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")
st.subheader("Base de Datos Dinámica")
st.dataframe(df_filtrado, use_container_width=True)
