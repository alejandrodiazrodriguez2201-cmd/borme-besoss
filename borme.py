import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

MUNICIPIOS_OBJETIVO = [
    "BADALONA", "SANTA COLOMA DE GRAMENET", "SANT ADRIA DE BESOS", 
    "SANT ADRIÀ DE BESÒS"
]
CODIGOS_POSTALES = [
    "08911", "08912", "08913", "08914", "08915", "08916", "08917", "08918",
    "08921", "08922", "08923", "08924", "08930"
]

def enviar_alerta_telegram(mensaje):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "HTML"
    }
    requests.post(url, data=payload)

def monitorizar_borme():
    hoy = datetime.now().strftime("%Y%m%d")
    url_api = f"https://www.boe.es/diario_borme/xml.php?id=BORME-S-{hoy}"
    
    respuesta = requests.get(url_api)
    if respuesta.status_code != 200:
        print("No hay BORME publicado hoy o no está accesible.")
        return

    root = ET.fromstring(respuesta.content)
    hallazgos = []

    for diario in root.findall(".//diario"):
        for item in diario.findall(".//item"):
            titulo = item.findtext("titulo", default="").upper()
            es_zona_besos = any(muni in titulo for muni in MUNICIPIOS_OBJETIVO) or \
                            any(cp in titulo for cp in CODIGOS_POSTALES)
            
            if es_zona_besos:
                url_pdf = f"https://www.boe.es{item.findtext('url_pdf')}"
                hallazgos.append((titulo, url_pdf))

    if hallazgos:
        enviar_alerta_telegram(f"🚨 <b>ALERTAS BORME - BESÒS ({datetime.now().strftime('%d/%m/%Y')})</b>")
        for titulo, url in hallazgos:
            mensaje = f"📍 <b>Detectado:</b>\n<code>{titulo}</code>\n\n📄 <a href='{url}'>Ver PDF</a>"
            enviar_alerta_telegram(mensaje)

if __name__ == "__main__":
    monitorizar_borme()
