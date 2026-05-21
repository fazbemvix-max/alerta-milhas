import os
import requests
from twilio.rest import Client
from datetime import datetime, timedelta

# Credenciais Twilio
TWILIO_SID = os.environ["TWILIO_SID"]
TWILIO_TOKEN = os.environ["TWILIO_TOKEN"]
TWILIO_WHATSAPP_FROM = os.environ["TWILIO_WHATSAPP_FROM"]
WHATSAPP_DESTINO = os.environ["WHATSAPP_DESTINO"]

# Rotas para monitorar
ROTAS = [
    ("VIX", "SCL"),
    ("VIX", "LIM"),
    ("VIX", "BOG"),
    ("VIX", "CTG"),
    ("VIX", "ADZ"),
    ("VIX", "MDZ"),
    ("VIX", "CUN"),
    ("GRU", "SCL"),
    ("GRU", "LIM"),
    ("GRU", "BOG"),
    ("GRU", "CTG"),
    ("GRU", "ADZ"),
    ("GRU", "MDZ"),
    ("GRU", "CUN"),
    ("GIG", "SCL"),
    ("GIG", "LIM"),
    ("GIG", "BOG"),
    ("GIG", "CTG"),
    ("GIG", "ADZ"),
    ("GIG", "MDZ"),
    ("GIG", "CUN"),
]

# Limites de milhas
LIMITE_SMILES = 30000
LIMITE_LATAM = 25000

# Limites de preço em dinheiro (R$) por destino
LIMITES_DINHEIRO = {
    "SCL": 1000,
    "LIM": 1800,
    "BOG": 1800,
    "CTG": 2200,
    "ADZ": 3200,
    "MDZ": 1500,
    "CUN": 2500,
}

# Gerar datas dos próximos 24 meses (1 por mês)
def gerar_datas():
    datas = []
    hoje = datetime.today()
    for i in range(1, 25):
        data = hoje + timedelta(days=30 * i)
        datas.append(data.strftime("%Y-%m-%d"))
    return datas

def buscar_smiles(origem, destino, data):
    try:
        url = "https://api-air-flightsearch-prd.smiles.com.br/v1/airlines/search"
        params = {
            "adults": 1,
            "children": 0,
            "infants": 0,
            "isFlexibleDateChecked": False,
            "originAirportCode": origem,
            "destinationAirportCode": destino,
            "departureDate": data,
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
        data_json = resp.json()
        voos = data_json.get("requestedFlightSegmentList", [{}])[0].get("flightList", [])
        for voo in voos:
            milhas = voo.get("fare", {}).get("miles", 9999999)
            if milhas <= LIMITE_SMILES:
                return milhas
        return None
    except Exception as e:
        print(f"Erro Smiles {origem}→{destino} {data}: {e}")
        return None

def buscar_latam(origem, destino, data):
    try:
        url = "https://bff.latam.com/ws/proxy/booking-webapp-bff/v1/public/revenue/recommendations/oneway"
        params = {
            "country": "BR",
            "language": "PT",
            "home": "pt_br",
            "origin": origem,
            "destination": destino,
            "departure": data,
            "adult": 1,
            "infant": 0,
            "child": 0,
            "cabin": "Y"
        }
        resp = requests.get(url, params=params, timeout=15)
        data_json = resp.json()
        voos = data_json.get("data", {}).get("flights", [])
        for voo in voos:
            milhas = voo.get("offers", [{}])[0].get("milesAmount", 9999999)
            if milhas <= LIMITE_LATAM:
                return milhas
        return None
    except Exception as e:
        print(f"Erro LATAM {origem}→{destino} {data}: {e}")
        return None

def buscar_preco_dinheiro(origem, destino, data):
    try:
        url = "https://api.travelpayouts.com/v1/prices/cheap"
        params = {
            "origin": origem,
            "destination": destino,
            "depart_date": data[:7],
            "currency": "BRL",
            "token": "74d37523aac7bdca6b71a2e28d01d8a1"
        }
        resp = requests.get(url, params=params, timeout=15)
        data_json = resp.json()
        precos = data_json.get("data", {}).get(destino, {})
        if precos:
            menor = min(v.get("price", 9999999) for v in precos.values())
            limite = LIMITES_DINHEIRO.get(destino, 9999999)
            if menor <= limite:
                return menor
        return None
    except Exception as e:
        print(f"Erro preço {origem}→{destino} {data}: {e}")
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
    datas = gerar_datas()

    for origem, destino in ROTAS:
        for data in datas:
            smiles = buscar_smiles(origem, destino, data)
            if smiles:
                alertas.append(f"✈️ MILHAS Smiles: {smiles:,} milhas | {origem}→{destino} | {data}")

            latam = buscar_latam(origem, destino, data)
            if latam:
                alertas.append(f"✈️ MILHAS LATAM: {latam:,} milhas | {origem}→{destino} | {data}")

            preco = buscar_preco_dinheiro(origem, destino, data)
            if preco:
                alertas.append(f"💰 DINHEIRO: R$ {preco:,.0f} | {origem}→{destino} | {data}")

    if alertas:
        msg = "🚨 *Alerta de Milhas e Passagens!*\n\n" + "\n".join(alertas)
        enviar_whatsapp(msg)
    else:
        print("Nenhuma oferta encontrada abaixo do limite.")

if __name__ == "__main__":
    main()
