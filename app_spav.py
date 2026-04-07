import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

# === CONFIGURACIÓN DE INTERFAZ ===
st.set_page_config(page_title="TRACKER SPAV PRO", layout="wide", page_icon="🛰️")

# Estilo personalizado 
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

# === LÓGICA DEL BACK-END (MOTOR) ===

def inferir_nse(direccion):
    referencias = {
        "Esmeralda": "A/B (Alta)", "Satelite": "C+ (Media Alta)", 
        "Santa Monica": "C+ (Media Alta)", "Viveros": "C+ (Media Alta)",
        "Echegaray": "C+ (Media Alta)", "Valle Dorado": "C (Media)",
        "Centro": "C (Media)", "San Javier": "C (Media)", "Lomas": "B/C+"
    }
    for palabra, nivel in referencias.items():
        if palabra.lower() in direccion.lower(): return nivel
    return "C (Por validar)"

def obtener_detalles_profundos(place_id, api_key):
    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=formatted_phone_number,website,user_ratings_total,reviews,photos,rating,geometry&key={api_key}"
    try:
        res = requests.get(url).json().get('result', {})
        return {
            "tel": res.get('formatted_phone_number', 'N/D'),
            "web": res.get('website', 'N/D'),
            "rating": res.get('rating', 0),
            "resenas": res.get('user_ratings_total', 0),
            "fotos": len(res.get('photos', [])),
            "lat": res.get('geometry', {}).get('location', {}).get('lat'),
            "lng": res.get('geometry', {}).get('location', {}).get('lng')
        }
    except: return None

# === FRONT-END (INTERFAZ) ===

st.title("🛰️ GEOLEAD ENGINE: Inteligencia Geográfica")
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/854/854878.png", width=100)
st.sidebar.header("Configuración de Misión")

# Sidebar - Inputs base
api_key = st.sidebar.text_input("🔑 Google API Key", type="password", help="Pega aquí tu clave de Google Cloud")
coords = st.sidebar.text_input("📍 Coordenadas Centrales", "19.5255,-99.2265", help="Latitud, Longitud")
radio = st.sidebar.slider("📏 Radio de acción (Metros)", 500, 20000, 5000)

st.sidebar.divider()
st.sidebar.subheader("Filtros de Calidad")
min_rating = st.sidebar.slider("⭐ Puntuación mínima", 0.0, 5.0, 0.0, 0.5)
min_fotos = st.sidebar.number_input("📸 Mínimo de fotos", 0, 50, 0)

# Cuerpo Principal - Personalización de Nichos
st.subheader("🎯 Definición de Objetivos")
nicho_input = st.text_input("Ingresa los nichos o empresas a buscar (separados por comas)", 
                            "preparatoria, bachillerato, secundaria, centro de capacitacion")

col1, col2, col3 = st.columns([1,1,1])
with col2:
    btn_ejecutar = st.button("🚀 INICIAR BARRIDO TOTAL")

if btn_ejecutar:
    if not api_key or not coords:
        st.error("⚠️ Falta API Key o Coordenadas.")
    else:
        with st.spinner("Peinando zona y analizando prospectos..."):
            url_search = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={coords}&radius={radio}&keyword={nicho_input}&key={api_key}"
            response = requests.get(url_search).json().get('results', [])
            
            final_data = []
            map_data = []

            for p in response:
                detalles = obtener_detalles_profundos(p.get('place_id'), api_key)
                if detalles and detalles['rating'] >= min_rating and detalles['fotos'] >= min_fotos:
                    direccion = p.get('vicinity', 'N/D')
                    row = {
                        "Nombre": p.get('name'),
                        "NSE": inferir_nse(direccion),
                        "Rating": detalles['rating'],
                        "Reseñas": detalles['resenas'],
                        "Fotos": detalles['fotos'],
                        "Teléfono": detalles['tel'],
                        "Sitio Web": detalles['web'],
                        "Dirección": direccion
                    }
                    final_data.append(row)
                    map_data.append({"lat": detalles['lat'], "lon": detalles['lng']})
                time.sleep(0.05)

            if final_data:
                df = pd.DataFrame(final_data).drop_duplicates(subset=['Nombre', 'Dirección'])
                
                # Visualización: Mapa y Tabla
                st.success(f"✅ Se localizaron {len(df)} prospectos de alto valor.")
                
                tab1, tab2 = st.tabs(["🗺️ Mapa de Calor", "📊 Base de Datos"])
                
                with tab1:
                    st.map(pd.DataFrame(map_data))
                
                with tab2:
                    st.dataframe(df, use_container_width=True)
                    
                    # Botón de Descarga
                    csv = df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Descargar Excel (CSV)",
                        data=csv,
                        file_name=f"SPAV_REPORTE_{datetime.now().strftime('%d%m_%H%M')}.csv",
                        mime='text/csv'
                    )
            else:
                st.warning("No se encontraron resultados con esos filtros.")
