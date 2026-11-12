# El parámetro ttl=600 le dice a Streamlit que vuelva a descargar los datos cada 600 segundos (10 minutos)
@st.cache_data(ttl=600)
def cargar_datos():
    url_google_sheets = "PEGA_AQUÍ_EL_ENLACE_QUE_COPIASTE"
    
    # Pandas lee directamente el CSV desde la nube
    df = pd.read_csv(url_google_sheets)
    
    # Cálculos necesarios para el gráfico
    df['Longitud'] = df['Abscisa_Final'] - df['Abscisa_Inicial']
    df['Capa'] = pd.Categorical(df['Capa'], categories=['Subrasante', 'Subbase', 'Base', 'Asfalto'], ordered=True)
    
    return df
