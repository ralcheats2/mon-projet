# ═══════════════════════════════════════════════════════════════════════════
#  VISION FURNITURE — Identification visuelle de chaises premium
#  Utilise Google Cloud Vision API (GRATUIT 1000 req/mois)
#  Même clé que dans deal_hunter.py — pas de setup supplémentaire
#
#  SETUP (si pas encore fait) :
#    1. https://console.cloud.google.com/ → crée un projet
#    2. Active "Cloud Vision API"
#    3. APIs & Services → Identifiants → Créer une clé API
#    4. Colle-la dans GOOGLE_VISION_KEY dans deal_hunter.py
#       (vision_furniture.py la récupère automatiquement)
# ═══════════════════════════════════════════════════════════════════════════

import requests
import base64
import re
import json

# Récupérée depuis deal_hunter.py pour ne pas dupliquer la config
try:
    from deal_hunter import GOOGLE_VISION_KEY
except ImportError:
    GOOGLE_VISION_KEY = 'VOTRE_CLE_ICI'

# ─── MOTS-CLÉS DÉCLENCHEURS ───────────────────────────────────────────────
CHAIR_TRIGGER_WORDS = [
    'chaise bureau', 'fauteuil bureau', 'siege bureau',
    'chaise ergonomique', 'fauteuil ergonomique', 'siege ergonomique',
    'chaise filet', 'chaise mesh', 'chaise gaming',
    'fauteuil gaming', 'chaise pivotante', 'siege pivotant',
    'chaise direction', 'fauteuil direction',
]

# ─── CATALOGUE PREMIUM ────────────────────────────────────────────────────
# Prix marché occasion France (destockage entreprise, leboncoin, ebay)
PREMIUM_CHAIR_CATALOG = {
    # Herman Miller
    'herman miller aeron':   {'market_price': 600,  'brand': 'Herman Miller'},
    'herman miller embody':  {'market_price': 900,  'brand': 'Herman Miller'},
    'herman miller mirra':   {'market_price': 300,  'brand': 'Herman Miller'},
    'herman miller cosm':    {'market_price': 800,  'brand': 'Herman Miller'},
    'herman miller sayl':    {'market_price': 350,  'brand': 'Herman Miller'},
    # Steelcase
    'steelcase leap':        {'market_price': 500,  'brand': 'Steelcase'},
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
    'haworth fern':          {'market_price': 700,  'brand': 'Haworth'},
}

# ─── Logos / labels retournés par Google Vision → modèle catalogue ─────────
# Google Vision détecte des logos de marque et des labels génériques.
# On mappe les concepts visuels vers les entrées du catalogue.
VISION_LABEL_MAP = {
    # Logos de marques (logoAnnotations)
    'herman miller': 'herman miller aeron',   # par défaut Aeron (le plus commun)
    'steelcase':     'steelcase leap',
    'vitra':         'vitra eames daw',
    'humanscale':    'humanscale freedom',
    'knoll':         'knoll regeneration',
    'okamura':       'okamura contessa',
    'haworth':       'haworth fern',
    # Labels textuels détectés dans l'image (textAnnotations / labelAnnotations)
    'aeron':         'herman miller aeron',
    'embody':        'herman miller embody',
    'mirra':         'herman miller mirra',
    'cosm':          'herman miller cosm',
    'sayl':          'herman miller sayl',
    'leap':          'steelcase leap',
    'gesture':       'steelcase gesture',
    'think':         'steelcase think',
    'amia':          'steelcase amia',
    'eames':         'vitra eames daw',
    'barcelona':     'knoll barcelona',
    'contessa':      'okamura contessa',
}


def is_chair_listing(title: str, description: str = '') -> bool:
    """Retourne True si l'annonce parle probablement d'une chaise de bureau."""
    text = (title + ' ' + description).lower()
    return any(trigger in text for trigger in CHAIR_TRIGGER_WORDS)


def identify_chair_google_vision(img_url: str) -> dict:
    """
    Analyse une image avec Google Cloud Vision API (gratuit 1000 req/mois).
    Retourne :
      - model        : clé catalogue détectée ou None
      - brand        : marque ou None
      - confidence   : 0-100 (basé sur le score Vision)
      - market_price : prix de référence ou 0
    """
    if GOOGLE_VISION_KEY == 'VOTRE_CLE_ICI' or not img_url:
        return {'model': None, 'brand': None, 'confidence': 0, 'market_price': 0}

    try:
        r = requests.get(img_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        r.raise_for_status()
        img_b64 = base64.b64encode(r.content).decode('utf-8')

        payload = {
            'requests': [{
                'image': {'content': img_b64},
                'features': [
                    {'type': 'LABEL_DETECTION', 'maxResults': 20},
                    {'type': 'LOGO_DETECTION',  'maxResults': 5},
                    {'type': 'TEXT_DETECTION',  'maxResults': 1},
                ]
            }]
        }
        api_url = f'https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_VISION_KEY}'
        resp = requests.post(api_url, json=payload, timeout=15)
        if resp.status_code != 200:
            return {'model': None, 'brand': None, 'confidence': 0, 'market_price': 0}

        data   = resp.json()
        result = data.get('responses', [{}])[0]

        # Collecter tous les concepts détectés avec leur score
        concepts = {}  # texte_lower → score

        for lbl in result.get('labelAnnotations', []):
            txt = lbl.get('description', '').lower()
            concepts[txt] = max(concepts.get(txt, 0), lbl.get('score', 0))

        for logo in result.get('logoAnnotations', []):
            txt = logo.get('description', '').lower()
            concepts[txt] = max(concepts.get(txt, 0), logo.get('score', 0.9))

        # Texte OCR dans l'image (étiquettes, logo imprimé sur le dossier, etc.)
        text_annots = result.get('textAnnotations', [])
        if text_annots:
            ocr_text = text_annots[0].get('description', '').lower()
            words = re.findall(r'[a-z][a-z0-9\-]{2,14}', ocr_text)
            for w in words:
                if w not in concepts:
                    concepts[w] = 0.6  # score OCR moyen

        # Chercher le meilleur match dans VISION_LABEL_MAP
        best_model = None
        best_score = 0.0

        for concept, score in concepts.items():
            for trigger, catalog_key in VISION_LABEL_MAP.items():
                if trigger in concept or concept in trigger:
                    if score > best_score:
                        best_score = score
                        best_model = catalog_key

        if not best_model:
            return {'model': None, 'brand': None, 'confidence': 0, 'market_price': 0}

        catalog_entry = PREMIUM_CHAIR_CATALOG.get(best_model, {})
        brand         = catalog_entry.get('brand')
        market_price  = catalog_entry.get('market_price', 0)
        confidence    = int(min(best_score * 100, 100))

        return {
            'model':        best_model,
            'brand':        brand,
            'confidence':   confidence,
            'market_price': market_price,
        }

    except Exception as e:
        print(f'[VisionFurniture] {e}')
        return {'model': None, 'brand': None, 'confidence': 0, 'market_price': 0}


def analyze_chair_deal(item: dict, min_confidence: int = 60) -> dict | None:
    """
    Pipeline complet pour une annonce de chaise :
      1. Vérifie que c'est une chaise de bureau (mots-clés titre/desc)
      2. Envoie la photo à Google Vision
      3. Si modèle premium détecté avec confiance ≥ min_confidence → retourne le deal
      4. Sinon → None

    item : dict avec title, price, img, desc, link, platform, color
    """
    title = item.get('title', '')
    desc  = item.get('desc', '')
    price = item.get('price', 0)
    img   = item.get('img', '')

    if not is_chair_listing(title, desc):
        return None
    if not img or not price:
        return None

    result = identify_chair_google_vision(img)

    if not result['model'] or result['confidence'] < min_confidence:
        return None
    if result['market_price'] <= 0:
        return None

    ref      = result['market_price']
    disc_pct = round((ref - price) / ref * 100, 1)
    savings  = round(ref - price, 2)

    # Garder même une petite décote si confiance très haute (vendeur naïf)
    if disc_pct < 20 and result['confidence'] < 80:
        return None

    return {
        **item,
        'detected_by':       'vision_ai',
        'best':              result['model'],
        'brand':             result['brand'],
        'ref':               ref,
        'cat':               'Mobilier bureau',
        'pct':               disc_pct,
        'score':             min(int(disc_pct * 1.2 + result['confidence'] * 0.3), 100),
        'savings':           savings,
        'is_lot':            False,
        'objects':           [(result['model'], ref, 'Mobilier bureau', result['confidence'])],
        'vision_details':    result.get('details', ''),
        'vision_confidence': result['confidence'],
        'vendor_unaware':    True,
    }
