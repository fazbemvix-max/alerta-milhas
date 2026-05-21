import os
import requests
from twilio.rest import Client

# Credenciais Twilio
TWILIO_SID = os.environ["TWILIO_SID"]
TWILIO_TOKEN = os.environ["TWILIO_TOKEN"]
TWILIO_WHATSAPP_FROM = os.environ["TWILIO_WHATSAPP_FROM"]
WHATSAPP_DESTINO = os.environ["WHATSAPP_DESTINO"]

# Configurações da busca
ORIGEM = "VIX"
DESTINO = "SCL"
LIMITE_SMILES = 30000
LIMITE_LATAM = 25000

def buscar_smiles():
    try:
        url = "https://api-air-flightsearch-prd.smiles.com.br/v1/airlines/search"
        params = {
            "adults": 1,
            "children": 0,
            "infants": 0,
            "isFlexibleDateChecked": False,
            "originAirportCode": ORIGEM,
            "destinationAirportCode": DESTINO,
            "departureDate": "2025-07-01",
            "cabin": "ALL",
            "currencyCode": "BRL",
            "forceCongener": False,
            "r": "ar"
        }
        headers = {
            "x-api-key": "aJqPU7xNHl9qN3NVZnPaJ208aPo2Bh2p2ZV844tw",
            "region": "BRASIL",
            "channel": "Web"
        }
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        data = resp.json()
        voos = data.get("requestedFlightSegmentList", [{}])[0].get("flightList", [])
        for voo in voos:
            milhas = voo.get("fare", {}).get("miles", 9999999)
            if milhas <= LIMITE_SMILES:
                return milhas
        return None
    except Exception as e:
        print(f"Erro Smiles: {e}")
        return None

def buscar_latam():
    try:
        url = "https://bff.latam.com/ws/proxy/booking-webapp-bff/v1/public/revenue/recommendations/oneway"
        params = {
            "country": "BR",
            "language": "PT",
            "home": "pt_br",
            "origin": ORIGEM,
            "destination": DESTINO,
            "departure": "2025-07-01",
            "adult": 1,
            "infant": 0,
            "child": 0,
            "cabin": "Y"
        }
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        voos = data.get("data", {}).get("flights", [])
        for voo in voos:
            milhas = voo.get("offers", [{}])[0].get("milesAmount", 9999999)
            if milhas <= LIMITE_LATAM:
                return milhas
        return None
    except Exception as e:
        print(f"Erro LATAM: {e}")
        return None

def enviar_whatsapp(mensagem):
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    client.messages.create(
        body=mensagem,
        from_=TWILIO_WHATSAPP_FROM,
        to=WHATSAPP_DESTINO
    )
    print("Alerta enviado!")

def main():
    alertas = []

    smiles = buscar_smiles()
    if smiles:
        alertas.append(f"✈️ *Smiles:* {smiles:,} milhas para VIX→SCL!")

    latam = buscar_latam()
    if latam:
        alertas.append(f"✈️ *LATAM Pass:* {latam:,} milhas para VIX→SCL!")

    if alertas:
        msg = "🚨 *Alerta de Milhas!*\n\n" + "\n".join(alertas)
        enviar_whatsapp(msg)
    else:
        print("Nenhuma oferta encontrada abaixo do limite.")

if __name__ == "__main__":
    main()
