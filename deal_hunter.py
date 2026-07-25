import tkinter as tk
from tkinter import ttk
import threading, requests, re, time, random, webbrowser, urllib.parse, io, json, base64
from bs4 import BeautifulSoup

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

try:
    from thefuzz import fuzz
    FUZZY_OK = True
except ImportError:
    FUZZY_OK = False

try:
    from vision_furniture import (
        analyze_chair_deal, is_chair_listing,
        OPENAI_API_KEY as _VF_KEY, PREMIUM_CHAIR_CATALOG
    )
    VISION_FURNITURE_OK = True
except ImportError:
    VISION_FURNITURE_OK = False
    _VF_KEY = 'VOTRE_CLE_OPENAI_ICI'

# ══════════════════════════════════════════════
#  CONFIG API VISION (Google Vision - gratuit 1000 req/mois)
#  1. Va sur https://console.cloud.google.com/
#  2. Crée un projet → Active "Cloud Vision API"
#  3. Crée une clé API → Colle-la ici
# ══════════════════════════════════════════════
GOOGLE_VISION_KEY = 'VOTRE_CLE_ICI'

# ══════════════════════════════════════════════
#  BLACKLIST ACCESSOIRES / PIÈCES DÉTACHÉES
# ══════════════════════════════════════════════
ACCESSORY_WORDS = [
    'batterie', 'battery', 'coque', 'case', 'vitre', 'ecran casse', 'screen crack',
    'chargeur', 'charger', 'cable', 'adaptateur', 'piece detachee', 'piece de rechange',
    'reparation', 'facade', 'nappe', 'dock', 'connecteur',
    'protection', 'verre trempe', 'film protecteur', 'housse', 'etui',
    'cover', 'skin', 'sticker', 'autocollant', 'stylet', 'stylus',
    'oreillette', 'ecouteur', 'earbud', 'embout',
    'hors service', 'pour pieces', 'ne fonctionne pas', 'ne marche pas',
    'casse', 'brise', 'broken', 'defectueux', 'defectif',
    'mode emploi', 'boite vide', 'empty box', 'boite seule',
    'chargeur seul', 'cable seul', 'adaptateur seul',
    'sim', 'sim tray', 'tiroir sim', 'bouton', 'power button',
    'vitre arriere', 'vitre avant', 'chassis', 'cadre',
]

# ══════════════════════════════════════════════
#  BASE DE DONNÉES — PRIX BACKMARKET
# ══════════════════════════════════════════════
VALUE_OBJECTS = {
    # ── ORDINATEURS
    'macbook pro m3': {'ref': 1650, 'cat': 'Ordinateurs',
        'kw': ['macbook', 'pro', 'm3'], 'context': ['m3', 'occasion', 'fonctionnel'],
        'variants': ['macbook pro m3 pro', 'macbook pro m3 max']},
    'macbook pro m2': {'ref': 1250, 'cat': 'Ordinateurs',
        'kw': ['macbook', 'pro', 'm2'], 'context': ['m2', 'occasion', 'fonctionnel'],
        'variants': ['mbp m2']},
    'macbook pro m1': {'ref': 950, 'cat': 'Ordinateurs',
        'kw': ['macbook', 'pro', 'm1'], 'context': ['m1', 'occasion', 'fonctionnel'],
        'variants': ['mbp m1']},
    'macbook air m2': {'ref': 900, 'cat': 'Ordinateurs',
        'kw': ['macbook', 'air', 'm2'], 'context': ['m2', 'occasion'],
        'variants': ['mba m2']},
    'macbook air m1': {'ref': 680, 'cat': 'Ordinateurs',
        'kw': ['macbook', 'air', 'm1'], 'context': ['m1', 'occasion'],
        'variants': ['mba m1']},
    'macbook pro intel': {'ref': 700, 'cat': 'Ordinateurs',
        'kw': ['macbook', 'pro', 'intel'], 'context': ['i7', 'i9', 'intel', 'occasion'],
        'variants': ['macbook pro 2019', 'macbook pro 2020']},
    'dell xps 15': {'ref': 900, 'cat': 'Ordinateurs',
        'kw': ['dell', 'xps', '15'], 'context': ['i7', 'i9', 'occasion', 'fonctionnel'],
        'variants': ['xps15']},
    'dell xps 13': {'ref': 650, 'cat': 'Ordinateurs',
        'kw': ['dell', 'xps', '13'], 'context': ['i7', 'occasion', 'fonctionnel'],
        'variants': ['xps13']},
    'thinkpad x1': {'ref': 700, 'cat': 'Ordinateurs',
        'kw': ['lenovo', 'thinkpad', 'x1'], 'context': ['i7', 'i5', 'occasion', 'professionnel'],
        'variants': ['thinkpad x1 carbon', 'x1 carbon']},
    'surface pro': {'ref': 650, 'cat': 'Ordinateurs',
        'kw': ['microsoft', 'surface pro'], 'context': ['i5', 'i7', 'occasion', 'fonctionnel'],
        'variants': ['surface pro 9', 'surface pro 8']},

    # ── GAMING
    'ps5 slim': {'ref': 400, 'cat': 'Gaming',
        'kw': ['ps5', 'slim'], 'context': ['console', 'sony', 'fonctionnel', 'manette'],
        'variants': ['playstation 5 slim']},
    'ps5': {'ref': 380, 'cat': 'Gaming',
        'kw': ['ps5', 'playstation 5'], 'context': ['console', 'manette', 'fonctionnel'],
        'variants': ['playstation5', 'ps 5']},
    'xbox series x': {'ref': 380, 'cat': 'Gaming',
        'kw': ['xbox', 'series x'], 'context': ['console', 'microsoft', 'fonctionnel'],
        'variants': ['xbox seriesx']},
    'switch oled': {'ref': 260, 'cat': 'Gaming',
        'kw': ['switch', 'nintendo', 'oled'], 'context': ['console', 'fonctionnel'],
        'variants': ['nintendo switch oled']},
    'switch': {'ref': 180, 'cat': 'Gaming',
        'kw': ['switch', 'nintendo'], 'context': ['console', 'fonctionnel', 'jeux'],
        'variants': ['nintendo switch v2']},
    'steam deck oled': {'ref': 480, 'cat': 'Gaming',
        'kw': ['steam', 'deck', 'oled'], 'context': ['portable', 'gaming', 'fonctionnel'],
        'variants': []},
    'steam deck': {'ref': 320, 'cat': 'Gaming',
        'kw': ['steam', 'deck'], 'context': ['portable', 'gaming', 'fonctionnel'],
        'variants': ['steamdeck']},

    # ── AUDIO
    'airpods pro 2': {'ref': 190, 'cat': 'Audio',
        'kw': ['airpods', 'pro', '2ème', '2nd', '2'], 'context': ['anc', 'occasion', 'boite'],
        'variants': ['airpods pro 2eme generation']},
    'airpods pro': {'ref': 150, 'cat': 'Audio',
        'kw': ['airpods', 'pro'], 'context': ['anc', 'occasion', 'boite', 'etui'],
        'variants': ['air pods pro']},
    'airpods 3': {'ref': 110, 'cat': 'Audio',
        'kw': ['airpods', '3ème', '3eme', 'troisième'], 'context': ['occasion', 'boite'],
        'variants': ['airpods 3eme generation']},
    'sony wh-1000xm5': {'ref': 250, 'cat': 'Audio',
        'kw': ['sony', 'xm5', 'wh-1000xm5'], 'context': ['casque', 'anc', 'occasion'],
        'variants': ['xm 5', '1000xm5']},
    'sony wh-1000xm4': {'ref': 170, 'cat': 'Audio',
        'kw': ['sony', 'xm4', 'wh-1000xm4'], 'context': ['casque', 'anc', 'occasion'],
        'variants': ['xm 4']},
    'bose qc45': {'ref': 200, 'cat': 'Audio',
        'kw': ['bose', 'qc45', 'quietcomfort'], 'context': ['casque', 'anc', 'occasion'],
        'variants': ['quiet comfort 45', 'qc 45']},
    'bose qc35': {'ref': 120, 'cat': 'Audio',
        'kw': ['bose', 'qc35'], 'context': ['casque', 'occasion'],
        'variants': ['quiet comfort 35']},

    # ── PHOTO / VIDÉO
    'gopro hero 12': {'ref': 280, 'cat': 'Photo',
        'kw': ['gopro', 'hero', '12'], 'context': ['camera', 'action', '4k', 'occasion'],
        'variants': ['go pro hero12']},
    'gopro hero 11': {'ref': 210, 'cat': 'Photo',
        'kw': ['gopro', 'hero', '11'], 'context': ['camera', '4k', 'occasion'],
        'variants': []},
    'canon eos r6': {'ref': 1600, 'cat': 'Photo',
        'kw': ['canon', 'eos', 'r6'], 'context': ['boitier', 'hybride', 'occasion'],
        'variants': ['eos r6 mark ii']},
    'sony a7 iv': {'ref': 2100, 'cat': 'Photo',
        'kw': ['sony', 'alpha', 'a7 iv', 'a7iv'], 'context': ['boitier', 'occasion'],
        'variants': ['sony a7iv']},
    'sony a7 iii': {'ref': 1300, 'cat': 'Photo',
        'kw': ['sony', 'alpha', 'a7 iii', 'a7iii'], 'context': ['boitier', 'occasion'],
        'variants': ['sony a7iii']},
    'fujifilm x-t5': {'ref': 1400, 'cat': 'Photo',
        'kw': ['fujifilm', 'x-t5', 'xt5'], 'context': ['boitier', 'occasion'],
        'variants': ['fuji xt5']},
    'fujifilm x100v': {'ref': 1100, 'cat': 'Photo',
        'kw': ['fujifilm', 'x100v', 'x100'], 'context': ['appareil', 'occasion'],
        'variants': ['fuji x100v']},
    'leica q2': {'ref': 3800, 'cat': 'Photo',
        'kw': ['leica', 'q2'], 'context': ['appareil', 'occasion'],
        'variants': []},
    'leica m11': {'ref': 6500, 'cat': 'Photo',
        'kw': ['leica', 'm11'], 'context': ['appareil', 'telemetrique', 'occasion'],
        'variants': []},
    'dji mini 4 pro': {'ref': 620, 'cat': 'Photo',
        'kw': ['dji', 'mini', '4 pro'], 'context': ['drone', 'occasion', 'fonctionnel'],
        'variants': []},
    'dji air 3': {'ref': 850, 'cat': 'Photo',
        'kw': ['dji', 'air', '3'], 'context': ['drone', 'occasion'],
        'variants': ['dji air3']},

    # ── ÉLECTROMÉNAGER
    'dyson v15 detect': {'ref': 500, 'cat': 'Électroménager',
        'kw': ['dyson', 'v15'], 'context': ['aspirateur', 'detect', 'fonctionnel', 'occasion'],
        'variants': ['dyson v15 detect absolute']},
    'dyson v12': {'ref': 380, 'cat': 'Électroménager',
        'kw': ['dyson', 'v12'], 'context': ['aspirateur', 'fonctionnel', 'occasion'],
        'variants': []},
    'dyson v11': {'ref': 300, 'cat': 'Électroménager',
        'kw': ['dyson', 'v11'], 'context': ['aspirateur', 'fonctionnel'],
        'variants': []},
    'dyson airwrap': {'ref': 450, 'cat': 'Électroménager',
        'kw': ['dyson', 'airwrap'], 'context': ['coiffeur', 'coffret', 'fonctionnel'],
        'variants': ['air wrap dyson']},
    'thermomix tm6': {'ref': 950, 'cat': 'Électroménager',
        'kw': ['thermomix', 'tm6', 'vorwerk'], 'context': ['robot', 'cuisine', 'fonctionnel'],
        'variants': ['tm 6', 'thermomix tm 6']},
    'thermomix tm5': {'ref': 600, 'cat': 'Électroménager',
        'kw': ['thermomix', 'tm5', 'vorwerk'], 'context': ['robot', 'cuisine'],
        'variants': ['tm 5']},
    'kitchenaid artisan': {'ref': 400, 'cat': 'Électroménager',
        'kw': ['kitchenaid', 'artisan'], 'context': ['robot', 'cuisine', 'occasion'],
        'variants': ['kitchen aid artisan']},

    # ── TABLETTES
    'ipad pro m4': {'ref': 900, 'cat': 'Tablettes',
        'kw': ['ipad', 'pro', 'm4'], 'context': ['tablette', 'occasion'],
        'variants': ['ipad pro 11 m4', 'ipad pro 13 m4']},
    'ipad pro m2': {'ref': 720, 'cat': 'Tablettes',
        'kw': ['ipad', 'pro', 'm2'], 'context': ['tablette', 'occasion'],
        'variants': ['ipad pro 11 m2']},
    'ipad air m2': {'ref': 520, 'cat': 'Tablettes',
        'kw': ['ipad', 'air', 'm2'], 'context': ['tablette', 'occasion'],
        'variants': []},
    'ipad air': {'ref': 400, 'cat': 'Tablettes',
        'kw': ['ipad', 'air'], 'context': ['tablette', 'occasion'],
        'variants': ['ipad air 5', 'ipad air 4']},

    # ── MOBILIER BUREAU PREMIUM (texte explicite — la Vision s'occupe des génériques)
    'herman miller aeron': {'ref': 600, 'cat': 'Mobilier bureau',
        'kw': ['herman miller', 'aeron'],
        'context': ['chaise', 'fauteuil', 'ergonomique', 'bureau', 'occasion'],
        'variants': ['herman-miller aeron', 'hm aeron', 'aeron taille b', 'aeron taille c']},
    'herman miller embody': {'ref': 900, 'cat': 'Mobilier bureau',
        'kw': ['herman miller', 'embody'],
        'context': ['chaise', 'fauteuil', 'bureau'],
        'variants': ['hm embody']},
    'herman miller mirra': {'ref': 300, 'cat': 'Mobilier bureau',
        'kw': ['herman miller', 'mirra'],
        'context': ['chaise', 'fauteuil', 'bureau'],
        'variants': ['hm mirra', 'mirra 2']},
    'herman miller cosm': {'ref': 800, 'cat': 'Mobilier bureau',
        'kw': ['herman miller', 'cosm'],
        'context': ['chaise', 'fauteuil', 'bureau'],
        'variants': []},
    'steelcase leap v2': {'ref': 500, 'cat': 'Mobilier bureau',
        'kw': ['steelcase', 'leap'],
        'context': ['chaise', 'fauteuil', 'bureau', 'ergonomique'],
        'variants': ['steelcase leap v2', 'leap v2']},
    'steelcase gesture': {'ref': 600, 'cat': 'Mobilier bureau',
        'kw': ['steelcase', 'gesture'],
        'context': ['chaise', 'fauteuil', 'bureau'],
        'variants': []},
    'vitra eames daw': {'ref': 700, 'cat': 'Mobilier bureau',
        'kw': ['vitra', 'eames', 'daw'],
        'context': ['chaise', 'design', 'bureau'],
        'variants': ['eames daw', 'eames plastic arm chair']},
    'humanscale freedom': {'ref': 650, 'cat': 'Mobilier bureau',
        'kw': ['humanscale', 'freedom'],
        'context': ['chaise', 'fauteuil', 'bureau'],
        'variants': []},
    'knoll barcelona': {'ref': 2000, 'cat': 'Mobilier bureau',
        'kw': ['knoll', 'barcelona'],
        'context': ['fauteuil', 'chaise', 'design', 'occasion'],
        'variants': ['fauteuil barcelona', 'barcelona chair']},

    # ── MONTRES
    'rolex submariner': {'ref': 9500, 'cat': 'Montres',
        'kw': ['rolex', 'submariner'], 'context': ['montre', 'acier', 'occasion', 'boite'],
        'variants': ['rolex sub']},
    'rolex datejust': {'ref': 7000, 'cat': 'Montres',
        'kw': ['rolex', 'datejust'], 'context': ['montre', 'acier', 'occasion'],
        'variants': ['datejust 36', 'datejust 41']},
    'omega seamaster': {'ref': 3200, 'cat': 'Montres',
        'kw': ['omega', 'seamaster'], 'context': ['montre', 'acier', 'occasion'],
        'variants': ['seamaster 300']},
    'omega speedmaster': {'ref': 4500, 'cat': 'Montres',
        'kw': ['omega', 'speedmaster'], 'context': ['montre', 'occasion'],
        'variants': ['moonwatch']},
    'tag heuer carrera': {'ref': 1800, 'cat': 'Montres',
        'kw': ['tag heuer', 'carrera'], 'context': ['montre', 'occasion'],
        'variants': ['tag-heuer carrera']},
    'seiko presage': {'ref': 320, 'cat': 'Montres',
        'kw': ['seiko', 'presage'], 'context': ['montre', 'automatique', 'occasion'],
        'variants': []},
    'casio g-shock': {'ref': 100, 'cat': 'Montres',
        'kw': ['casio', 'g-shock'], 'context': ['montre', 'occasion'],
        'variants': ['gshock', 'g shock']},

    # ── LUXE
    'louis vuitton neverfull': {'ref': 1100, 'cat': 'Luxe',
        'kw': ['louis vuitton', 'neverfull'], 'context': ['sac', 'occasion', 'cuir', 'authentique'],
        'variants': ['lv neverfull']},
    'chanel classique': {'ref': 5500, 'cat': 'Luxe',
        'kw': ['chanel', 'classique', '2.55'], 'context': ['sac', 'occasion', 'cuir'],
        'variants': ['chanel 2.55', 'chanel flap']},
    'hermes birkin': {'ref': 9000, 'cat': 'Luxe',
        'kw': ['hermes', 'birkin'], 'context': ['sac', 'cuir', 'occasion'],
        'variants': ['hermès birkin', 'birkin 30', 'birkin 35']},
    'hermes kelly': {'ref': 8000, 'cat': 'Luxe',
        'kw': ['hermes', 'kelly'], 'context': ['sac', 'cuir', 'occasion'],
        'variants': ['hermès kelly']},

    # ── SNEAKERS
    'yeezy 350': {'ref': 220, 'cat': 'Sneakers',
        'kw': ['yeezy', '350'], 'context': ['baskets', 'chaussures', 'pointure', 'occasion'],
        'variants': ['yeezy boost 350', 'zebra', 'bred']},
    'jordan 1 retro': {'ref': 160, 'cat': 'Sneakers',
        'kw': ['jordan', 'retro', 'aj1'], 'context': ['baskets', 'chaussures', 'pointure', 'occasion'],
        'variants': ['air jordan 1 retro', 'aj1 retro']},
    'nike dunk low': {'ref': 120, 'cat': 'Sneakers',
        'kw': ['nike', 'dunk', 'low'], 'context': ['baskets', 'chaussures', 'pointure'],
        'variants': ['dunk low']},

    # ── LEGO
    'lego technic 42': {'ref': 280, 'cat': 'LEGO',
        'kw': ['lego', 'technic', '42'], 'context': ['boite', 'set', 'complet', 'neuf'],
        'variants': ['lego 42', 'technic 42']},
    'lego star wars': {'ref': 200, 'cat': 'LEGO',
        'kw': ['lego', 'star wars'], 'context': ['boite', 'set', 'complet'],
        'variants': []},

    # ── VINYLES
    'vinyle pressage original': {'ref': 60, 'cat': 'Vinyles',
        'kw': ['vinyle', 'vinyl', '33t', 'pressage'], 'context': ['disque', 'collection', 'original', 'rare'],
        'variants': ['vinyl lp', '33 tours']},
}

LOT_WORDS = ['lot', 'vrac', 'ensemble', 'collection', 'boite', 'caisse',
             'assortiment', 'divers', 'melange', 'destockage', 'destock',
             'liquidation', 'bureau ferme', 'entreprise']

HEADERS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15',
]

def rh():
    return {'User-Agent': random.choice(HEADERS), 'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.5'}

def parse_price(text):
    if not text: return None
    t = re.sub(r'[^\d.,]', '', text.replace('\xa0','').replace('\u202f','').replace(' ',''))
    t = t.replace(',','.')
    m = re.search(r'\d+\.?\d*', t)
    try:
        v = float(m.group()) if m else None
        return v if v and 1 < v < 100000 else None
    except: return None

def is_accessory(text):
    tl = text.lower()
    for w in ACCESSORY_WORDS:
        if w in tl:
            return True, w
    return False, None

def context_score(text, obj_data):
    tl = text.lower()
    ctx_words = obj_data.get('context', [])
    if not ctx_words: return 50
    matches = sum(1 for w in ctx_words if w in tl)
    return min(100, int((matches / max(len(ctx_words), 1)) * 150))

def detect_objects(title, description=''):
    full_text = (title + ' ' + description).lower()
    title_low = title.lower()
    found = []
    seen = set()
    acc, acc_word = is_accessory(title)

    for name, d in VALUE_OBJECTS.items():
        if name in seen: continue
        matched = False
        match_confidence = 0

        if FUZZY_OK:
            score = fuzz.partial_ratio(name, title_low)
            if score >= 78:
                matched = True
                match_confidence = score

        if not matched:
            for v in d.get('variants', []):
                if v.lower() in title_low:
                    matched = True
                    match_confidence = 90
                    break

        if not matched:
            kw_matches = sum(1 for k in d['kw'] if k in full_text)
            if kw_matches >= 2:
                matched = True
                match_confidence = 55 + kw_matches * 8

        if not matched: continue
        if acc: continue

        ctx = context_score(full_text, d)
        if ctx < 20 and match_confidence < 80: continue

        final_confidence = int(match_confidence * 0.6 + ctx * 0.4)
        found.append((name, d['ref'], d['cat'], final_confidence))
        seen.add(name)

    is_lot = any(w in full_text for w in LOT_WORDS)
    return found, is_lot

def analyze_image_google_vision(img_url):
    if GOOGLE_VISION_KEY == 'VOTRE_CLE_ICI' or not img_url:
        return []
    try:
        r = requests.get(img_url, headers=rh(), timeout=8)
        r.raise_for_status()
        img_b64 = base64.b64encode(r.content).decode('utf-8')
        payload = {
            'requests': [{
                'image': {'content': img_b64},
                'features': [
                    {'type': 'LABEL_DETECTION', 'maxResults': 15},
                    {'type': 'LOGO_DETECTION',  'maxResults': 5},
                    {'type': 'TEXT_DETECTION',  'maxResults': 1},
                ]
            }]
        }
        api_url = f'https://vision.googleapis.com/v1/images:annotate?key={GOOGLE_VISION_KEY}'
        resp = requests.post(api_url, json=payload, timeout=15)
        if resp.status_code != 200:
            return []
        data = resp.json()
        result = data.get('responses', [{}])[0]
        concepts = []
        for lbl in result.get('labelAnnotations', []):
            if lbl.get('score', 0) > 0.75:
                concepts.append(lbl['description'].lower())
        for logo in result.get('logoAnnotations', []):
            concepts.append(logo['description'].lower())
        text_annotations = result.get('textAnnotations', [])
        if text_annotations:
            full_text = text_annotations[0].get('description', '').lower()
            words = re.findall(r'\b[a-zA-Z0-9\-]{2,12}\b', full_text)
            concepts.extend(words[:20])
        return concepts
    except Exception as e:
        print(f'[Vision API] {e}')
        return []

def deal_score(price, ref, is_lot=False, n=1):
    if not price or price <= 0: return 0, 0
    eff = ref * (min(n,3)*0.6) if is_lot and n > 1 else ref
    pct = (eff - price) / eff * 100
    if pct <= 0: sc = 0
    elif pct < 20: sc = pct * 1.5
    elif pct < 40: sc = 30 + (pct-20)*2
    elif pct < 60: sc = 70 + (pct-40)
    else: sc = min(90 + (pct-60)*0.5, 100)
    return round(pct,1), round(sc)

# ══════════════════════════════════════════════
#  SCRAPERS
# ══════════════════════════════════════════════

def scrape_ebay(query, max_r=40):
    results = []
    try:
        url = f'https://www.ebay.fr/sch/i.html?_nkw={urllib.parse.quote(query)}&_sop=10&LH_BIN=1&_ipg=48'
        r = requests.get(url, headers=rh(), timeout=15)
        soup = BeautifulSoup(r.text, 'html5lib')
        for item in soup.select('.s-item')[:max_r]:
            try:
                title = item.select_one('.s-item__title')
                price = item.select_one('.s-item__price')
                link  = item.select_one('a.s-item__link')
                img   = item.select_one('img.s-item__image-img, .s-item__image img')
                desc  = item.select_one('.s-item__subtitle, .s-item__detail')
                t = title.get_text(strip=True) if title else ''
                if not t or 'Shop on eBay' in t: continue
                p = parse_price(price.get_text() if price else '')
                if not p: continue
                img_url = ''
                if img:
                    img_url = img.get('src') or img.get('data-src','')
                    if img_url and img_url.startswith('data:'): img_url = ''
                results.append({
                    'title': t, 'price': p,
                    'link': link['href'] if link else '',
                    'img': img_url,
                    'desc': desc.get_text(strip=True) if desc else '',
                    'platform': 'eBay', 'color': '#E53238'
                })
            except: continue
    except Exception as e:
        print(f'[eBay] {e}')
    return results

def scrape_lbc_rss(query, max_r=30):
    results = []
    try:
        url = f'https://www.leboncoin.fr/recherche?text={urllib.parse.quote(query)}&sort=time'
        r = requests.get(url, headers=rh(), timeout=15)
        soup = BeautifulSoup(r.text, 'html5lib')
        script = soup.find('script', id='__NEXT_DATA__')
        if script:
            data = json.loads(script.string)
            try:
                ads = data['props']['pageProps']['searchData']['ads']
                for ad in ads[:max_r]:
                    title = ad.get('subject','')
                    price = ad.get('price',[None])
                    price = price[0] if isinstance(price, list) and price else price
                    link  = 'https://www.leboncoin.fr' + ad.get('url','')
                    imgs  = ad.get('images',{}).get('urls_large') or ad.get('images',{}).get('urls',[])
                    img   = imgs[0] if imgs else ''
                    desc  = ad.get('body','')
                    try: p = float(price)
                    except: p = None
                    if title and p:
                        results.append({
                            'title': title, 'price': p, 'link': link,
                            'img': img, 'desc': desc,
                            'platform': 'LeBonCoin', 'color': '#F56B2A'
                        })
            except (KeyError, TypeError): pass
        if not results:
            for item in soup.select('li[data-qa-id="aditem_container"], article')[:max_r]:
                try:
                    t_el = item.select_one('[class*="title"],[class*="Title"],h2,h3')
                    p_el = item.select_one('[class*="price"],[class*="Price"]')
                    a_el = item.find('a')
                    i_el = item.find('img')
                    t = t_el.get_text(strip=True) if t_el else ''
                    p = parse_price(p_el.get_text() if p_el else '')
                    href = a_el.get('href','') if a_el else ''
                    link = ('https://www.leboncoin.fr'+href) if href.startswith('/') else href
                    img_url = ''
                    if i_el: img_url = i_el.get('src') or i_el.get('data-src','')
                    if t and p:
                        results.append({'title':t,'price':p,'link':link,
                            'img':img_url,'desc':'',
                            'platform':'LeBonCoin','color':'#F56B2A'})
                except: continue
    except Exception as e:
        print(f'[LBC] {e}')
    return results

def scrape_vinted(query, max_r=30):
    results = []
    try:
        api_url = f'https://www.vinted.fr/api/v2/catalog/items?search_text={urllib.parse.quote(query)}&order=newest_first&per_page=48'
        r = requests.get(api_url, headers={**rh(),'Accept':'application/json'}, timeout=15)
        if r.status_code == 200:
            data = r.json()
            for item in data.get('items', [])[:max_r]:
                t = item.get('title','')
                p = item.get('price',{}).get('amount') or item.get('price')
                link = item.get('url','') or f"https://www.vinted.fr/items/{item.get('id','')}"
                photo = item.get('photo',{})
                img = photo.get('full_size_url') or photo.get('url','') if isinstance(photo,dict) else ''
                desc = item.get('description','')
                try: p = float(p)
                except: p = None
                if t and p:
                    results.append({'title':t,'price':p,'link':link,'img':img,
                        'desc':desc,'platform':'Vinted','color':'#09B1BA'})
        else:
            url = f'https://www.vinted.fr/catalog?search_text={urllib.parse.quote(query)}'
            r2 = requests.get(url, headers=rh(), timeout=15)
            soup = BeautifulSoup(r2.text, 'html5lib')
            for item in soup.select('[data-testid*="item"],[class*="ItemBox"]')[:max_r]:
                try:
                    t_el = item.select_one('[class*="title"],[class*="name"]')
                    p_el = item.select_one('[class*="price"]')
                    a_el = item.find('a')
                    i_el = item.find('img')
                    t = t_el.get_text(strip=True) if t_el else ''
                    p = parse_price(p_el.get_text() if p_el else '')
                    href = a_el.get('href','') if a_el else ''
                    link = ('https://www.vinted.fr'+href) if href.startswith('/') else href
                    img_url = i_el.get('src') or i_el.get('data-src','') if i_el else ''
                    if t and p:
                        results.append({'title':t,'price':p,'link':link,'img':img_url,
                            'desc':'','platform':'Vinted','color':'#09B1BA'})
                except: continue
    except Exception as e:
        print(f'[Vinted] {e}')
    return results

def analyze(listings, min_disc):
    deals = []
    seen_links = set()

    for item in listings:
        link = item.get('link', '')
        if link in seen_links:
            continue

        title = item.get('title', '')
        desc  = item.get('desc', '')
        price = item.get('price')
        if not price:
            continue

        # ── ÉTAPE 1 : détection textuelle classique ──
        objs, is_lot = detect_objects(title, desc)

        # ── ÉTAPE 2 : fallback Google Vision si rien trouvé ──
        if not objs and item.get('img') and GOOGLE_VISION_KEY != 'VOTRE_CLE_ICI':
            concepts = analyze_image_google_vision(item['img'])
            if concepts:
                visual_text = ' '.join(concepts)
                objs, is_lot = detect_objects(title + ' ' + visual_text, desc)

        # ── ÉTAPE 3 : VISION MOBILIER (GPT-4o) pour les chaises génériques ──
        # Si l'annonce semble être une chaise de bureau ET que le texte ne
        # donne pas de modèle premium → on envoie l'image à GPT-4o Vision
        chair_vision_deal = None
        if VISION_FURNITURE_OK and _VF_KEY != 'VOTRE_CLE_OPENAI_ICI':
            # Condition : pas déjà identifié comme mobilier premium par le texte
            already_furniture = any('Mobilier' in o[2] for o in objs)
            if not already_furniture and is_chair_listing(title, desc) and item.get('img'):
                chair_vision_deal = analyze_chair_deal(item, min_confidence=65)

        # ── ÉTAPE 4 : si deal mobilier détecté par Vision → l'ajouter directement ──
        if chair_vision_deal:
            if link: seen_links.add(link)
            deals.append(chair_vision_deal)
            continue

        # ── ÉTAPE 5 : pipeline classique pour les autres objets ──
        if not objs:
            continue

        best = max(objs, key=lambda x: x[1])
        pct, sc = deal_score(price, best[1], is_lot, len(objs))
        if pct >= min_disc:
            if link: seen_links.add(link)
            deals.append({
                **item,
                'objects': objs, 'best': best[0],
                'ref': best[1], 'cat': best[2], 'pct': pct,
                'score': sc, 'is_lot': is_lot,
                'savings': round(best[1]-price, 2),
                'detected_by': 'text',
                'vendor_unaware': False,
            })

    deals.sort(key=lambda x: x['score'], reverse=True)
    return deals

AUTO_QUERIES = [
    # Chaises bureau : requêtes génériques pour débusquer les Herman Miller cachés
    'chaise bureau', 'fauteuil bureau ergonomique', 'siege bureau occasion',
    'chaise ergonomique bureau', 'fauteuil ergonomique occasion',
    'destockage bureau mobilier', 'chaise steelcase occasion',
    'chaise herman miller', 'fauteuil direction occasion',
    # Autres catégories
    'lot electronique', 'ps5 console',
    'montre collection', 'lego boite',
    'jordan sneakers', 'dyson occasion', 'macbook',
    'lot informatique vrac',
    'ipad pro occasion', 'gopro occasion', 'drone dji occasion',
]

# ══════════════════════════════════════════════
#  CHARGEMENT IMAGE ASYNC
# ══════════════════════════════════════════════

def load_image_async(url, callback, size=(200, 150)):
    def _load():
        if not PIL_OK or not url: return
        try:
            r = requests.get(url, headers=rh(), timeout=8, stream=True)
            r.raise_for_status()
            img_data = io.BytesIO(r.content)
            img = Image.open(img_data).convert('RGBA')
            img.thumbnail(size, Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            callback(photo)
        except Exception:
            pass
    threading.Thread(target=_load, daemon=True).start()

# ══════════════════════════════════════════════
#  INTERFACE TKINTER
# ══════════════════════════════════════════════

BG     = '#0f0f13'
SURF   = '#16161e'
SURF2  = '#1e1e2a'
BORD   = '#2a2a38'
TEXT   = '#e8e8f0'
MUTED  = '#8888a0'
PRI    = '#7c6af7'
GREEN  = '#22c55e'
ORANGE = '#f59e0b'
RED    = '#ef4444'
GOLD   = '#d4a017'

class DealHunter(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('🔍 Deal Hunter — Chasseur de bonnes affaires')
        self.geometry('1300x800')
        self.minsize(900, 600)
        self.configure(bg=BG)
        self.deals = []
        self._image_refs = []
        self._build_ui()
        self._style_ttk()

    def _style_ttk(self):
        s = ttk.Style(self)
        s.theme_use('clam')
        s.configure('TFrame', background=BG)
        s.configure('TLabel', background=BG, foreground=TEXT, font=('Segoe UI', 10))
        s.configure('Vertical.TScrollbar', background=SURF2, troughcolor=BG, arrowcolor=MUTED)
        s.configure('TEntry', fieldbackground=SURF2, foreground=TEXT,
                    insertcolor=TEXT, borderwidth=1, relief='flat')
        s.configure('Horizontal.TProgressbar', troughcolor=SURF, background=PRI, thickness=4)

    def _build_ui(self):
        self.sidebar = tk.Frame(self, bg=SURF, width=270)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side='left', fill='both', expand=True)
        self._build_sidebar()
        self._build_content()

    def _build_sidebar(self):
        sb = self.sidebar
        tk.Frame(sb, bg=SURF, height=10).pack(fill='x')
        tk.Label(sb, text='🔍 Deal Hunter', bg=SURF, fg=PRI,
                 font=('Segoe UI', 15, 'bold')).pack(padx=14)
        tk.Label(sb, text='Chasseur de bonnes affaires', bg=SURF, fg=MUTED,
                 font=('Segoe UI', 9)).pack(pady=(0,8))
        tk.Frame(sb, bg=BORD, height=1).pack(fill='x')
        tk.Frame(sb, bg=SURF, height=8).pack(fill='x')
        tk.Label(sb, text='RECHERCHE', bg=SURF, fg=MUTED,
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', padx=14)
        self.search_var = tk.StringVar()
        se = ttk.Entry(sb, textvariable=self.search_var, font=('Segoe UI', 10))
        se.pack(fill='x', padx=14, pady=(4,4))
        se.bind('<Return>', lambda e: self.do_search())
        # Tags rapides
        tags = [
            ('📦 Lots élec',  'lot electronique'),
            ('🎮 PS5',         'ps5 console'),
            ('⌚ Montres',     'montre collection'),
            ('👟 Sneakers',    'jordan yeezy'),
            ('🖥 Mac',         'macbook'),
            ('🌀 Dyson',       'dyson aspirateur'),
            ('🪑 Chaises',     'chaise bureau'),
            ('🏢 Destockage',  'destockage bureau mobilier'),
            ('📷 Photo',       'leica appareil photo'),
            ('🎸 Instruments', 'guitare gibson fender'),
        ]
        tf = tk.Frame(sb, bg=SURF)
        tf.pack(fill='x', padx=10, pady=(0,8))
        for i,(label,val) in enumerate(tags):
            tk.Button(tf, text=label, bg=SURF2, fg=MUTED,
                      font=('Segoe UI', 8), relief='flat', bd=0,
                      cursor='hand2', pady=3, padx=5,
                      command=lambda v=val: self._quick_search(v)
                      ).grid(row=i//2, column=i%2, sticky='ew', padx=2, pady=2)
        tf.columnconfigure(0, weight=1)
        tf.columnconfigure(1, weight=1)
        tk.Frame(sb, bg=BORD, height=1).pack(fill='x')
        tk.Frame(sb, bg=SURF, height=4).pack(fill='x')
        tk.Label(sb, text='REMISE MINIMALE (vs marché)', bg=SURF, fg=MUTED,
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', padx=14)
        df = tk.Frame(sb, bg=SURF)
        df.pack(fill='x', padx=14)
        self.disc_var = tk.IntVar(value=40)
        self.disc_lbl = tk.Label(df, text='40%', bg=SURF, fg=PRI,
                                  font=('Segoe UI', 12, 'bold'), width=5)
        self.disc_lbl.pack(side='right')
        tk.Scale(df, from_=10, to=90, orient='horizontal',
                 variable=self.disc_var, bg=SURF, fg=TEXT,
                 highlightthickness=0, troughcolor=SURF2,
                 activebackground=PRI, sliderrelief='flat',
                 command=lambda v: self.disc_lbl.config(text=f'{v}%')
                 ).pack(side='left', fill='x', expand=True)
        tk.Frame(sb, bg=BORD, height=1).pack(fill='x', pady=4)
        tk.Label(sb, text='PLATEFORMES', bg=SURF, fg=MUTED,
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', padx=14)
        self.plat_lbc    = tk.BooleanVar(value=True)
        self.plat_vinted = tk.BooleanVar(value=True)
        self.plat_ebay   = tk.BooleanVar(value=True)
        for var, label in [(self.plat_lbc,'🟠 LeBonCoin'),
                           (self.plat_vinted,'🔵 Vinted'),
                           (self.plat_ebay,'🔴 eBay')]:
            tk.Checkbutton(sb, text=label, variable=var, bg=SURF, fg=TEXT,
                           selectcolor=SURF2, activebackground=SURF,
                           font=('Segoe UI', 10), cursor='hand2'
                           ).pack(anchor='w', padx=14, pady=2)
        tk.Frame(sb, bg=BORD, height=1).pack(fill='x', pady=6)
        tk.Button(sb, text='🔍  Rechercher',
                  bg=PRI, fg='white', font=('Segoe UI', 10, 'bold'),
                  relief='flat', bd=0, pady=10, cursor='hand2',
                  command=self.do_search).pack(fill='x', padx=14, pady=(0,6))
        tk.Button(sb, text='🎯  Auto-Hunt',
                  bg='#d97706', fg='white', font=('Segoe UI', 10, 'bold'),
                  relief='flat', bd=0, pady=10, cursor='hand2',
                  command=self.do_auto).pack(fill='x', padx=14, pady=(0,10))
        tk.Frame(sb, bg=BORD, height=1).pack(fill='x')
        # Statuts des APIs
        vision_gpt = '✅ GPT-4o Vision actif' if (VISION_FURNITURE_OK and _VF_KEY != 'VOTRE_CLE_OPENAI_ICI') else '⚠️ GPT-4o Vision non configuré'
        vision_google = '✅ Google Vision actif' if GOOGLE_VISION_KEY != 'VOTRE_CLE_ICI' else '⚠️ Google Vision non configuré'
        tk.Label(sb,
                 text=f'✅ Prix marché réels\n✅ Exclut pièces/accessoires\n✅ Images des annonces\n🪑 Chaises bureau scannées par IA\n{vision_gpt}\n{vision_google}',
                 bg=SURF, fg=MUTED, font=('Segoe UI', 8), justify='left').pack(padx=14, pady=10, anchor='w')

    def _build_content(self):
        top = tk.Frame(self.content, bg=BG)
        top.pack(fill='x', padx=20, pady=(16,8))
        self.title_lbl = tk.Label(top, text='Prêt à chasser les deals 🎯',
                                   bg=BG, fg=TEXT, font=('Segoe UI', 14, 'bold'))
        self.title_lbl.pack(side='left')
        # Barre de filtre texte
        self.filter_frame = tk.Frame(self.content, bg=BG)
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add('write', self._apply_filter)
        fe = ttk.Entry(self.filter_frame, textvariable=self.filter_var,
                       font=('Segoe UI', 10))
        fe.pack(side='left', fill='x', expand=True, padx=(0,4))
        tk.Button(self.filter_frame, text='✕', bg=SURF2, fg=MUTED,
                  relief='flat', font=('Segoe UI', 10), cursor='hand2',
                  command=lambda: self.filter_var.set('')
                  ).pack(side='left')
        self.stats_frame = tk.Frame(self.content, bg=BG)
        self.stats_frame.pack(fill='x', padx=20, pady=(0,8))
        self.stat_scanned = self._stat_card('0', 'Analysées')
        self.stat_deals   = self._stat_card('0', 'Deals trouvés')
        self.stat_best    = self._stat_card('-', 'Meilleure remise')
        self.stat_vision  = self._stat_card('0', '🪑 Vision IA')
        for w,_ in [self.stat_scanned, self.stat_deals, self.stat_best, self.stat_vision]:
            w.pack(side='left', padx=(0,10))
        self.progress = ttk.Progressbar(self.content, mode='indeterminate')
        self.status_lbl = tk.Label(self.content, text='', bg=BG, fg=MUTED, font=('Segoe UI', 9))
        outer = tk.Frame(self.content, bg=BG)
        outer.pack(fill='both', expand=True, padx=20, pady=(0,16))
        self.canvas = tk.Canvas(outer, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient='vertical', command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg=BG)
        self.scroll_frame.bind('<Configure>',
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.create_window((0,0), window=self.scroll_frame, anchor='nw')
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.canvas.pack(side='left', fill='both', expand=True)
        self.canvas.bind_all('<MouseWheel>',
            lambda e: self.canvas.yview_scroll(-1*(e.delta//120), 'units'))
        self._show_empty()

    def _stat_card(self, val, label):
        f = tk.Frame(self.stats_frame, bg=SURF, padx=16, pady=8,
                     highlightbackground=BORD, highlightthickness=1)
        v_lbl = tk.Label(f, text=val, bg=SURF, fg=GREEN, font=('Segoe UI', 18, 'bold'))
        v_lbl.pack()
        tk.Label(f, text=label, bg=SURF, fg=MUTED, font=('Segoe UI', 8)).pack()
        return f, v_lbl

    def _show_empty(self):
        for w in self.scroll_frame.winfo_children(): w.destroy()
        self.filter_frame.pack_forget()
        tk.Label(self.scroll_frame, text='🎯', bg=BG, font=('Segoe UI', 48)).pack(pady=(60,10))
        tk.Label(self.scroll_frame, text='Aucune recherche en cours',
                 bg=BG, fg=TEXT, font=('Segoe UI', 14, 'bold')).pack()
        tk.Label(self.scroll_frame, text='Lance une recherche ou Auto-Hunt pour commencer.',
                 bg=BG, fg=MUTED, font=('Segoe UI', 10)).pack(pady=4)

    def _apply_filter(self, *args):
        kw = self.filter_var.get().strip().lower()
        if not self.deals: return
        filtered = [d for d in self.deals
                    if kw in d['title'].lower() or kw in d.get('cat','').lower()
                    or kw in d.get('best','').lower()
                    ] if kw else self.deals
        self._render_deals(filtered)

    def _quick_search(self, val):
        self.search_var.set(val)
        self.do_search()

    def _get_platforms(self):
        p = []
        if self.plat_lbc.get():    p.append('lbc')
        if self.plat_vinted.get(): p.append('vinted')
        if self.plat_ebay.get():   p.append('ebay')
        return p or ['ebay']

    def _set_loading(self, msg):
        self.filter_frame.pack_forget()
        self.status_lbl.config(text=msg)
        self.status_lbl.pack(fill='x', padx=20)
        self.progress.pack(fill='x', padx=20, pady=(0,8))
        self.progress.start(12)
        for w in self.scroll_frame.winfo_children(): w.destroy()
        tk.Label(self.scroll_frame, text='⏳ Scraping en cours...',
                 bg=BG, fg=MUTED, font=('Segoe UI', 12)).pack(pady=80)

    def _set_done(self):
        self.progress.stop()
        self.progress.pack_forget()
        self.status_lbl.pack_forget()

    def do_search(self):
        kw = self.search_var.get().strip()
        if not kw: return
        plats = self._get_platforms()
        disc  = self.disc_var.get()
        self._set_loading(f'Scraping "{kw}"...')
        threading.Thread(target=self._run_search, args=(kw, disc, plats), daemon=True).start()

    def do_auto(self):
        plats = self._get_platforms()
        disc  = self.disc_var.get()
        self._set_loading('Auto-Hunt : scan de toutes les catégories + Vision IA chaises...')
        threading.Thread(target=self._run_auto, args=(disc, plats), daemon=True).start()

    def _run_search(self, kw, disc, plats):
        listings = []
        if 'lbc'    in plats: listings += scrape_lbc_rss(kw)
        if 'vinted' in plats: listings += scrape_vinted(kw)
        if 'ebay'   in plats: listings += scrape_ebay(kw)
        deals = analyze(listings, disc)
        self.after(0, self._show_results, deals, len(listings), f'Résultats : "{kw}"')

    def _run_auto(self, disc, plats):
        listings = []
        for q in AUTO_QUERIES:
            if 'lbc'  in plats: listings += scrape_lbc_rss(q, max_r=15)
            if 'ebay' in plats: listings += scrape_ebay(q, max_r=15)
            time.sleep(random.uniform(0.3,0.8))
        seen, uniq = set(), []
        for i in listings:
            if i['link'] not in seen:
                seen.add(i['link']); uniq.append(i)
        deals = analyze(uniq, disc)
        self.after(0, self._show_results, deals, len(uniq), 'Auto-Hunt IA')

    def _show_results(self, deals, scanned, title):
        self._set_done()
        self._image_refs.clear()
        self.deals = deals
        self.title_lbl.config(text=title)
        self.stat_scanned[1].config(text=str(scanned))
        self.stat_deals[1].config(text=str(len(deals)))
        best = f"-{deals[0]['pct']}%" if deals else '-'
        self.stat_best[1].config(text=best)
        # Compter les deals trouvés par Vision IA
        vision_count = sum(1 for d in deals if d.get('detected_by') == 'vision_ai')
        self.stat_vision[1].config(text=str(vision_count))
        if deals:
            self.filter_frame.pack(fill='x', padx=20, pady=(0,6))
        self._render_deals(deals)

    def _render_deals(self, deals):
        for w in self.scroll_frame.winfo_children(): w.destroy()
        if not deals:
            tk.Label(self.scroll_frame, text='😕 Aucun deal trouvé',
                     bg=BG, fg=TEXT, font=('Segoe UI', 13, 'bold')).pack(pady=60)
            tk.Label(self.scroll_frame,
                     text='Essaie de baisser la remise minimale ou change les mots-clés.',
                     bg=BG, fg=MUTED, font=('Segoe UI', 10)).pack()
            return
        grid = tk.Frame(self.scroll_frame, bg=BG)
        grid.pack(fill='both', expand=True)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)
        for i, deal in enumerate(deals):
            self._make_card(grid, deal, row=i//2, col=i%2)

    def _make_card(self, parent, d, row, col):
        is_vision = d.get('detected_by') == 'vision_ai'
        is_naive  = d.get('vendor_unaware', False)
        border_color = GOLD if is_naive else BORD

        outer = tk.Frame(parent, bg=BG, padx=6, pady=6)
        outer.grid(row=row, column=col, sticky='nsew')
        card = tk.Frame(outer, bg=SURF2, highlightbackground=border_color,
                        highlightthickness=2 if is_naive else 1)
        card.pack(fill='both', expand=True)
        tk.Frame(card, bg=d['color'], height=4).pack(fill='x')
        body = tk.Frame(card, bg=SURF2, padx=12, pady=10)
        body.pack(fill='both', expand=True)

        # Ligne du haut : plateforme + badges
        top_row = tk.Frame(body, bg=SURF2)
        top_row.pack(fill='x')
        tk.Label(top_row, text=d['platform'], bg=SURF2, fg=d['color'],
                 font=('Segoe UI', 9, 'bold')).pack(side='left')
        if is_vision:
            tk.Label(top_row, text=' 🤖 Vision IA ', bg='#1a1a3a', fg='#a78bfa',
                     font=('Segoe UI', 8, 'bold')).pack(side='left', padx=4)
        if is_naive:
            tk.Label(top_row, text=' 🤷 Naïf ', bg='#2d2500', fg=GOLD,
                     font=('Segoe UI', 8, 'bold')).pack(side='left', padx=2)
        badge_bg = '#7c3aed' if d['score'] >= 70 else RED
        tk.Label(top_row, text=f"  -{d['pct']}%  ", bg=badge_bg, fg='white',
                 font=('Segoe UI', 10, 'bold')).pack(side='right')

        # Image
        if PIL_OK and d.get('img'):
            img_frame = tk.Frame(body, bg='#12121a', height=160)
            img_frame.pack(fill='x', pady=(6,4))
            img_frame.pack_propagate(False)
            placeholder = tk.Label(img_frame, text='⏳ chargement...',
                                   bg='#12121a', fg=MUTED, font=('Segoe UI', 8))
            placeholder.pack(expand=True)
            def set_img(photo, lbl=placeholder):
                self._image_refs.append(photo)
                lbl.config(image=photo, text='', bg='#12121a')
            load_image_async(d['img'], set_img, size=(440, 155))
        elif not PIL_OK and d.get('img'):
            tk.Label(body, text='📷 Pillow requis pour afficher l\'image',
                     bg='#12121a', fg=MUTED, font=('Segoe UI', 8), pady=4).pack(fill='x')

        if d.get('is_lot'):
            tk.Label(body, text='📦 LOT — objet de valeur détecté à l\'intérieur',
                     bg='#2d2a00', fg=ORANGE, font=('Segoe UI', 8, 'bold')
                     ).pack(anchor='w', pady=(4,0))

        # Titre
        title_txt = d['title'][:72] + '...' if len(d['title']) > 72 else d['title']
        tk.Label(body, text=title_txt, bg=SURF2, fg=TEXT,
                 font=('Segoe UI', 10, 'bold'), wraplength=360, justify='left'
                 ).pack(anchor='w', pady=(6,2))

        # Détection
        if is_vision:
            det_txt = f"🪑 {d.get('best','?').title()} ({d.get('vision_confidence',0)}% confiance)"
            if d.get('vision_details'):
                det_txt += f" — {d['vision_details']}"
        else:
            objs_txt = ', '.join(o[0] for o in d.get('objects', [])[:3])
            det_txt = f'🎯 Détecté : {objs_txt}'
        tk.Label(body, text=det_txt, bg=SURF2, fg=PRI,
                 font=('Segoe UI', 9), wraplength=360, justify='left').pack(anchor='w')
        tk.Label(body, text=f'📂 {d["cat"]}',
                 bg=SURF2, fg=MUTED, font=('Segoe UI', 8)).pack(anchor='w', pady=(2,6))

        tk.Frame(body, bg=BORD, height=1).pack(fill='x')

        # Prix
        price_row = tk.Frame(body, bg=SURF2)
        price_row.pack(fill='x', pady=8)
        tk.Label(price_row, text=f"{d['price']} €",
                 bg=SURF2, fg=GREEN, font=('Segoe UI', 18, 'bold')).pack(side='left')
        rp = tk.Frame(price_row, bg=SURF2)
        rp.pack(side='right', anchor='e')
        tk.Label(rp, text=f"Réf marché : {d['ref']} €",
                 bg=SURF2, fg=MUTED, font=('Segoe UI', 8)).pack(anchor='e')
        tk.Label(rp, text=f"Économie ~{d['savings']} €",
                 bg=SURF2, fg=GREEN, font=('Segoe UI', 9, 'bold')).pack(anchor='e')

        # Barre score
        sc = d['score']
        bar_color = '#7c3aed' if sc >= 80 else (ORANGE if sc >= 60 else GREEN)
        bar_frame = tk.Frame(body, bg=SURF, height=5)
        bar_frame.pack(fill='x')
        tk.Frame(bar_frame, bg=bar_color, height=5, width=int(3.4*sc)).place(x=0,y=0)
        tk.Label(body, text=f'Score deal : {sc}/100',
                 bg=SURF2, fg=MUTED, font=('Segoe UI', 8)).pack(anchor='w', pady=(4,6))

        if d['link']:
            tk.Button(body, text='🔗  Voir l\'annonce →',
                      bg=PRI, fg='white', font=('Segoe UI', 9, 'bold'),
                      relief='flat', bd=0, pady=7, cursor='hand2',
                      command=lambda url=d['link']: webbrowser.open(url)
                      ).pack(fill='x')

if __name__ == '__main__':
    app = DealHunter()
    app.mainloop()
