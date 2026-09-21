import os
import requests
from datetime import datetime, timedelta

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Lista de palabras clave para buscar en el órgano de contratación o en la descripción
MUNICIPIOS_Y_ENTES = [
    "BADALONA", "SANTA COLOMA", "SANT ADRIA", "SANT ADRIÀ", 
    "MONTGAT", "TIANA", "MONTCADA", "AMB", "AREA METROPOLITANA DE BARCELONA",
    "ÀREA METROPOLITANA DE BARCELONA", "IMPSOL", "CONSORCI DEL BESOS", 
    "CONSORCI DEL BESÒS", "CONSORCI DE LA MINA"
]

def enviar_alerta_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    requests.post(url, data=payload)

def monitorizar_contratacion():
    # Consultar datos abiertos de Transparència Catalunya (Plataforma de Contractació)
    url_api = "https://analisi.transparenciacatalunya.cat/resource/632u-83fb.json"
    
    # Consultar los contratos más recientes (últimos 100 registros publicados)
    params = {
        "$limit": 100,
        "$order": "data_publicacio DESC"
    }
    
    respuesta = requests.get(url_api, params=params)
    if respuesta.status_code != 200:
        print("No se ha podido acceder a la API de contratación pública.")
        return

    licitaciones = respuesta.json()
    hallazgos = []

    # Fecha de ayer para no repetir contratos antiguos (en ejecuciones diarias)
    hace_24h = datetime.now() - timedelta(days=1)

    for item in licitaciones:
        organo = item.get("organ_contractacio", "").upper()
        objeto = item.get("objecte_contracte", "").upper()
        muni = item.get("municipi", "").upper()
        
        texto_busqueda = f"{organo} {objeto} {muni}"
        
        # Verificar si coincide con alguno de nuestros entes del Besòs
        if any(keyword in texto_busqueda for keyword in MUNICIPIOS_Y_ENTES):
            presupuesto = item.get("pressupost_licitacio", "No especificado")
            enlace = item.get("url_enllac_perfil_contractant", {}).get("url", "#")
            
            # Formatear el presupuesto a euros si es número
            try:
                presupuesto_fmt = f"{float(presupuesto):,.2f} €"
            except:
                presupuesto_fmt = str(presupuesto)

            hallazgos.append({
                "organo": item.get("organ_contractacio", "Desconocido"),
                "objeto": item.get("objecte_contracte", "Sin objeto definido"),
                "importe": presupuesto_fmt,
                "url": enlace
            })

    # Enviar alertas por Telegram
    if hallazgos:
        enviar_alerta_telegram(f"📜 <b>NUEVAS LICITACIONES/CONTRATOS - BESÒS Y ENTES</b>")
        
        for h in hallazgos[:10]:  # Limitar a máximo 10 alertas por mensaje para no saturar
            mensaje = (
                f"🏛️ <b>Organismo:</b> {h['organo']}\n"
                f"📝 <b>Contrato:</b> {h['objeto']}\n"
                f"💰 <b>Importe:</b> {h['importe']}\n"
                f"🔗 <a href='{h['url']}'>Ver ficha oficial del contrato</a>\n"
            )
            enviar_alerta_telegram(mensaje)
    else:
        print("No hay nuevas licitaciones públicas en las últimas horas.")

if __name__ == "__main__":
    monitorizar_contratacion()
