# =========================================================
# AZURE FUNCTION — api/analyze/__init__.py
#
# COSA FA (spiegato semplice):
# È come un cameriere al ristorante. Il browser (cliente)
# gli porta l'ordinazione (la config Cisco). Il cameriere
# va in cucina (Anthropic API), prende il piatto (JSON),
# e lo riporta al cliente. Il cliente non entra mai in cucina
# e non vede dove sono conservati gli ingredienti (API key).
# =========================================================

import azure.functions as func
import json
import os
import urllib.request
import urllib.error

def main(req: func.HttpRequest) -> func.HttpResponse:

    # --- CORS: permetti al frontend di chiamare questa function ---
    # CORS = "chi può bussare a questa porta?"
    # Senza questo header il browser rifiuta la risposta.
    headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
        "Content-Type": "application/json"
    }

    # Gestione preflight OPTIONS (il browser "bussa" prima di inviare)
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=headers)

    try:
        # --- LEGGI IL BODY della richiesta dal browser ---
        body = req.get_json()
        config_text = body.get("config", "")

        if not config_text:
            return func.HttpResponse(
                json.dumps({"error": "Nessuna config ricevuta"}),
                status_code=400, headers=headers
            )

        # --- LEGGI LA API KEY dalle variabili d'ambiente ---
        # In Azure questa variabile viene impostata nelle
        # "Application Settings" — non è nel codice, è segreta.
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            return func.HttpResponse(
                json.dumps({"error": "API key non configurata"}),
                status_code=500, headers=headers
            )

        # --- COSTRUISCI IL PROMPT per l'AI ---
        prompt = f"""Sei un parser di configurazioni Cisco IOS. Analizza questa running-config e restituisci SOLO JSON valido, zero testo aggiuntivo, zero backtick.

Struttura richiesta:
{{
  "devices": [
    {{
      "id": "id_unico_senza_spazi",
      "hostname": "nome",
      "type": "router|switch_l3|switch_l2|firewall",
      "interfaces": [
        {{ "name": "Gi0/0", "description": "", "ip": "10.0.0.1/24", "type": "routed|trunk|access", "vlan": "", "status": "up|down" }}
      ],
      "routing": "ospf|eigrp|bgp|static|none"
    }}
  ],
  "links": [
    {{ "source": "id1", "target": "id2", "label": "descrizione" }}
  ]
}}

Regole: se un solo device, links=[]. Deduci link da CDP, descrizioni, subnet condivise. SOLO JSON.

CONFIG:
{config_text}"""

        # --- CHIAMA L'API ANTHROPIC ---
        # urllib è la libreria Python standard per fare richieste HTTP.
        # Costruiamo la richiesta a mano: URL, headers, body JSON.
        request_body = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}]
        }).encode("utf-8")

        api_request = urllib.request.Request(
            url="https://api.anthropic.com/v1/messages",
            data=request_body,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            },
            method="POST"
        )

        with urllib.request.urlopen(api_request) as response:
            api_response = json.loads(response.read().decode("utf-8"))

        # Estraiamo il testo dalla risposta Anthropic
        result_text = api_response["content"][0]["text"]

        # Puliamo eventuali backtick residui e verifichiamo che sia JSON valido
        clean = result_text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean)  # se non è JSON valido, lancia eccezione

        # --- RISPOSTA AL BROWSER ---
        return func.HttpResponse(
            json.dumps(parsed),
            status_code=200,
            headers=headers
        )

    except json.JSONDecodeError as e:
        return func.HttpResponse(
            json.dumps({"error": f"L'AI non ha restituito JSON valido: {str(e)}"}),
            status_code=500, headers=headers
        )
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        return func.HttpResponse(
            json.dumps({"error": f"Errore Anthropic API: {error_body}"}),
            status_code=502, headers=headers
        )
    except Exception as e:
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500, headers=headers
        )
