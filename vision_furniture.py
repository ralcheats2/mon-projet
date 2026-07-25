# ═══════════════════════════════════════════════════════════════════════════
#  VISION FURNITURE — Identification visuelle de chaises premium
#  Utilise GPT-4o Vision (OpenAI) pour analyser les photos d'annonces
#  de chaises de bureau et détecter Herman Miller, Steelcase, Vitra, etc.
#
#  SETUP :
#    pip install openai
#    Mets ta clé OpenAI dans OPENAI_API_KEY ci-dessous
#    Coût : ~0.001€ / image — très raisonnable
# ═══════════════════════════════════════════════════════════════════════════

import requests
import base64
import random
import re

# ─── CONFIG ───────────────────────────────────────────────────────────────
OPENAI_API_KEY = 'VOTRE_CLE_OPENAI_ICI'

# Mots-clés qui signalent qu'une annonce est probablement une chaise de bureau
CHAIR_TRIGGER_WORDS = [
    'chaise bureau', 'fauteuil bureau', 'siege bureau',
    'chaise ergonomique', 'fauteuil ergonomique', 'siege ergonomique',
    'chaise filet', 'chaise mesh', 'chaise gaming',
    'fauteuil gaming', 'chaise pivotante', 'siege pivotant',
    'chaise direction', 'fauteuil direction',
]

# Modèles premium connus avec leur prix marché reconditionnés
PREMIUM_CHAIR_CATALOG = {
    # Herman Miller
    'herman miller aeron':   {'market_price': 600,  'brand': 'Herman Miller'},
    'herman miller embody':  {'market_price': 900,  'brand': 'Herman Miller'},
    'herman miller mirra':   {'market_price': 300,  'brand': 'Herman Miller'},
    'herman miller cosm':    {'market_price': 800,  'brand': 'Herman Miller'},
    'herman miller sayl':    {'market_price': 350,  'brand': 'Herman Miller'},
    # Steelcase
    'steelcase leap v2':     {'market_price': 500,  'brand': 'Steelcase'},
    'steelcase gesture':     {'market_price': 600,  'brand': 'Steelcase'},
    'steelcase think':       {'market_price': 400,  'brand': 'Steelcase'},
    'steelcase amia':        {'market_price': 350,  'brand': 'Steelcase'},
    # Vitra
    'vitra eames daw':       {'market_price': 700,  'brand': 'Vitra'},
    'vitra eames dsw':       {'market_price': 600,  'brand': 'Vitra'},
    'vitra hal':             {'market_price': 450,  'brand': 'Vitra'},
    'vitra id chair':        {'market_price': 800,  'brand': 'Vitra'},
    # Humanscale
    'humanscale freedom':    {'market_price': 650,  'brand': 'Humanscale'},
    'humanscale diffrient':  {'market_price': 500,  'brand': 'Humanscale'},
    # Knoll
    'knoll barcelona':       {'market_price': 2000, 'brand': 'Knoll'},
    'knoll regeneration':    {'market_price': 600,  'brand': 'Knoll'},
    # Autres
    'okamura contessa':      {'market_price': 700,  'brand': 'Okamura'},
    'wilkhahn ON':           {'market_price': 800,  'brand': 'Wilkhahn'},
    'haworth fern':          {'market_price': 700,  'brand': 'Haworth'},
}


def is_chair_listing(title: str, description: str = '') -> bool:
    """Retourne True si l'annonce parle probablement d'une chaise de bureau."""
    text = (title + ' ' + description).lower()
    return any(trigger in text for trigger in CHAIR_TRIGGER_WORDS)


def identify_chair_vision(img_url: str, title: str = '', description: str = '') -> dict:
    """
    Envoie l'image de l'annonce à GPT-4o Vision pour identifier la chaise.
    Retourne un dict avec :
      - model  : nom du modèle détecté (ex: 'herman miller aeron') ou None
      - brand  : marque (ex: 'Herman Miller') ou None
      - confidence : 0-100
      - market_price : prix de référence ou 0
      - vision_raw : réponse brute du modèle (debug)
    """
    if OPENAI_API_KEY == 'VOTRE_CLE_OPENAI_ICI' or not img_url:
        return {'model': None, 'brand': None, 'confidence': 0,
                'market_price': 0, 'vision_raw': 'API non configurée'}

    try:
        # Télécharger et encoder l'image
        r = requests.get(img_url, timeout=10,
                         headers={'User-Agent': 'Mozilla/5.0'})
        r.raise_for_status()
        img_b64 = base64.b64encode(r.content).decode('utf-8')
        # Déterminer le content type
        ct = r.headers.get('Content-Type', 'image/jpeg').split(';')[0].strip()
        if ct not in ('image/jpeg', 'image/png', 'image/webp', 'image/gif'):
            ct = 'image/jpeg'

        prompt = (
            "Tu es un expert en mobilier de bureau premium d'occasion.\n"
            "Regarde cette image et identifie précisément le modèle de chaise ou fauteuil.\n"
            f"Titre de l'annonce : {title[:120]}\n"
            f"Description : {description[:200]}\n\n"
            "Réponds UNIQUEMENT dans ce format JSON strict :\n"
            '{\n'
            '  \"model\": \"herman miller aeron\",  // nom complet en minuscules, ou null\n'
            '  \"brand\": \"Herman Miller\",        // marque proprement capitalisée, ou null\n'
            '  \"confidence\": 85,                 // 0-100, ta certitude\n'
            '  \"details\": \"taille B, mesh noir, accoudoirs 4D\"  // indices visuels clés\n'
            '}\n'
            "Si ce n'est pas une chaise de bureau premium connue (herman miller, steelcase, vitra, humanscale, knoll, okamura, haworth, wilkhahn), "
            "mets model=null et confidence<30."
        )

        payload = {
            'model': 'gpt-4o',
            'max_tokens': 200,
            'messages': [{
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': prompt},
                    {'type': 'image_url',
                     'image_url': {'url': f'data:{ct};base64,{img_b64}', 'detail': 'low'}}
                ]
            }]
        }

        resp = requests.post(
            'https://api.openai.com/v1/chat/completions',
            json=payload,
            headers={'Authorization': f'Bearer {OPENAI_API_KEY}',
                     'Content-Type': 'application/json'},
            timeout=20
        )
        resp.raise_for_status()
        content = resp.json()['choices'][0]['message']['content'].strip()

        # Parser le JSON retourné
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if not json_match:
            return {'model': None, 'brand': None, 'confidence': 0,
                    'market_price': 0, 'vision_raw': content}

        import json
        data = json.loads(json_match.group())
        model_name = (data.get('model') or '').strip().lower() or None
        brand      = data.get('brand') or None
        confidence = int(data.get('confidence', 0))
        details    = data.get('details', '')

        # Chercher le prix dans le catalogue
        market_price = 0
        if model_name:
            # Correspondance exacte
            if model_name in PREMIUM_CHAIR_CATALOG:
                market_price = PREMIUM_CHAIR_CATALOG[model_name]['market_price']
            else:
                # Correspondance partielle
                for cat_key, cat_val in PREMIUM_CHAIR_CATALOG.items():
                    if cat_key in model_name or model_name in cat_key:
                        market_price = cat_val['market_price']
                        break

        return {
            'model':        model_name,
            'brand':        brand,
            'confidence':   confidence,
            'market_price': market_price,
            'details':      details,
            'vision_raw':   content,
        }

    except Exception as e:
        print(f'[VisionFurniture] Erreur: {e}')
        return {'model': None, 'brand': None, 'confidence': 0,
                'market_price': 0, 'vision_raw': str(e)}


def analyze_chair_deal(item: dict, min_confidence: int = 60) -> dict | None:
    """
    Pipeline complet pour une annonce de chaise :
      1. Vérifie que c'est bien une chaise de bureau
      2. Lance l'analyse Vision sur la première image
      3. Si modèle premium identifié avec assez de confiance → retourne les infos deal
      4. Sinon → retourne None

    item doit contenir : title, price, img, desc (optionnel), link, platform, color
    """
    title = item.get('title', '')
    desc  = item.get('desc', '')
    price = item.get('price', 0)
    img   = item.get('img', '')

    if not is_chair_listing(title, desc):
        return None
    if not img or not price:
        return None

    result = identify_chair_vision(img, title, desc)

    if not result['model'] or result['confidence'] < min_confidence:
        return None
    if result['market_price'] <= 0:
        return None

    # Calculer la décote
    ref = result['market_price']
    disc_pct = round((ref - price) / ref * 100, 1)
    savings  = round(ref - price, 2)

    if disc_pct < 20:  # Même une petite décote est intéressante si vendeur naïf
        # On garde quand même si la confiance est très haute (>80) — vendeur non identifié
        if result['confidence'] < 80:
            return None

    return {
        **item,
        'detected_by':   'vision_ai',
        'best':          result['model'],
        'brand':         result['brand'],
        'ref':           ref,
        'cat':           'Mobilier bureau',
        'pct':           disc_pct,
        'score':         min(int(disc_pct * 1.2 + result['confidence'] * 0.3), 100),
        'savings':       savings,
        'is_lot':        False,
        'objects':       [(result['model'], ref, 'Mobilier bureau', result['confidence'])],
        'vision_details': result.get('details', ''),
        'vision_confidence': result['confidence'],
        'vendor_unaware': True,  # Si le titre est générique + modèle détecté par vision → vendeur naïf
    }
