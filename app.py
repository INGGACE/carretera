import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de la página
st.set_page_config(layout="wide", page_title="Avance de Obra Vial")
st.title("🚧 Visualizador de Avance Constructivo por Capas")

# 2. Cargar los datos desde la nube
@st.cache_data(ttl=600)
def cargar_datos():
    # PEGA TU ENLACE ENTRE LAS COMILLAS
    url =https://drive.google.com/file/d/1A0pKbDRB6OwM5FE0V-hj3dm0E9I6XD5j/view
    
    # Si usas Google Sheets, usa esta línea (déjala sin el símbolo #):
    df = pd.read_csv(url)
    
    # Si usas SharePoint, borra el # de la siguiente línea y pónselo a la línea de arriba:
    # df = pd.read_excel(url, engine='openpyxl')
    
    # Calcular la longitud del tramo para el eje X
    df['Longitud'] = df['Abscisa_Final'] - df['Abscisa_Inicial']
    
    # Ordenar las capas
    df['Capa'] = pd.Categorical(df['Capa'], categories=['Subrasante', 'Subbase', 'Base', 'Asfalto'], ordered=True)
    return df

df = cargar_datos()

# 3. Panel Lateral para Filtros
st.sidebar.header("Filtros de Visualización")
capas_seleccionadas = st.sidebar.multiselect("Filtrar por Capa", df['Capa'].dropna().unique(), default=df['Capa'].dropna().unique())
estado_seleccionado = st.sidebar.multiselect("Filtrar por Estado", df['Estado'].unique(), default=df['Estado'].unique())
