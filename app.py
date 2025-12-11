import threading
import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from bs4 import BeautifulSoup
import os

app = Flask(__name__)
CORS(app)  # Autorise ton frontend à appeler cette API

# --- CONFIGURATION RENDER ---
# ⚠️ IMPORTANT : après ton premier déploiement, remplace cette URL par celle que Render t'affiche !
RENDER_EXTERNAL_URL = "https://VOTRE-APP-NAME.onrender.com"


def keep_alive():
    """
    Thread qui tourne en fond pour pinger le serveur toutes les 7 minutes.
    Empêche Render Free Tier de s'endormir.
    """
    while True:
        time.sleep(420)  # 7 minutes
        try:
            if "VOTRE-APP-NAME" in RENDER_EXTERNAL_URL:
                print("⚠️ Configurez RENDER_EXTERNAL_URL pour activer le Self-Ping")
            else:
                print(f"⏰ Self-Ping vers {RENDER_EXTERNAL_URL}/ping ...")
                requests.get(f"{RENDER_EXTERNAL_URL}/ping")
        except Exception as e:
            print(f"❌ Erreur Ping: {e}")


# Lancer le thread de maintien en vie (self-ping)
threading.Thread(target=keep_alive, daemon=True).start()


@app.route('/ping', methods=['GET'])
def ping():
    return "Pong! Je suis réveillé.", 200


@app.route('/api/scrape', methods=['POST'])
def scrape_job():
    data = request.json
    url_to_scrape = data.get('url')

    if not url_to_scrape:
        return jsonify({"error": "URL manquante"}), 400

    print(f"🤖 Scraping demandé pour : {url_to_scrape}")

    # Headers pour simuler un navigateur normal
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/91.0.4472.124 Safari/537.36'
        )
    }

    try:
        response = requests.get(url_to_scrape, headers=headers, timeout=10)

        if response.status_code != 200:
            return jsonify({"error": f"Erreur HTTP {response.status_code}"}), 500

        soup = BeautifulSoup(response.text, 'html.parser')

        # Nettoyage : retirer JS, CSS et navigation
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.extract()

        # Extraction du texte propre
        text = soup.get_text()
        clean_text = " ".join(text.split())

        return jsonify({
            "status": "success",
            "extracted_text": clean_text[:5000]  # limite raisonnable
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Render fournit PORT automatiquement
    app.run(host='0.0.0.0', port=port)
