import requests
from bs4 import BeautifulSoup
import re
import time
import random
import threading
from thefuzz import fuzz

# ─────────────────────────────────────────────────────────────────────────────
# CATALOGUE BACKMARKET (électronique grand public)
# ─────────────────────────────────────────────────────────────────────────────

BACKMARKET_CATALOG = {
    'iphone 16 pro':        {'category': '📱 Téléphones', 'keywords': ['iphone', '16 pro', 'apple']},
    'iphone 16':            {'category': '📱 Téléphones', 'keywords': ['iphone', '16', 'apple']},
    'iphone 15 pro':        {'category': '📱 Téléphones', 'keywords': ['iphone', '15 pro', 'apple']},
    'iphone 15':            {'category': '📱 Téléphones', 'keywords': ['iphone', '15', 'apple']},
    'iphone 14 pro':        {'category': '📱 Téléphones', 'keywords': ['iphone', '14 pro', 'apple']},
    'iphone 14':            {'category': '📱 Téléphones', 'keywords': ['iphone', '14', 'apple']},
    'iphone 13 pro':        {'category': '📱 Téléphones', 'keywords': ['iphone', '13 pro', 'apple']},
    'iphone 13':            {'category': '📱 Téléphones', 'keywords': ['iphone', '13', 'apple']},
    'iphone 12':            {'category': '📱 Téléphones', 'keywords': ['iphone', '12', 'apple']},
    'iphone 11':            {'category': '📱 Téléphones', 'keywords': ['iphone', '11', 'apple']},
    'iphone xr':            {'category': '📱 Téléphones', 'keywords': ['iphone', 'xr', 'apple']},
    'iphone xs':            {'category': '📱 Téléphones', 'keywords': ['iphone', 'xs', 'apple']},
    'iphone x':             {'category': '📱 Téléphones', 'keywords': ['iphone', ' x ', 'apple']},
    'iphone se':            {'category': '📱 Téléphones', 'keywords': ['iphone', 'se', 'apple']},
    'samsung galaxy s24 ultra': {'category': '📱 Téléphones', 'keywords': ['samsung', 'galaxy', 's24', 'ultra']},
    'samsung galaxy s24':   {'category': '📱 Téléphones', 'keywords': ['samsung', 'galaxy', 's24']},
    'samsung galaxy s23':   {'category': '📱 Téléphones', 'keywords': ['samsung', 'galaxy', 's23']},
    'samsung galaxy s22':   {'category': '📱 Téléphones', 'keywords': ['samsung', 'galaxy', 's22']},
    'google pixel 8 pro':   {'category': '📱 Téléphones', 'keywords': ['pixel', '8 pro', 'google']},
    'google pixel 8':       {'category': '📱 Téléphones', 'keywords': ['pixel', '8', 'google']},
    'macbook pro m3':       {'category': '💻 Ordinateurs', 'keywords': ['macbook', 'pro', 'm3', 'apple']},
    'macbook pro m2':       {'category': '💻 Ordinateurs', 'keywords': ['macbook', 'pro', 'm2', 'apple']},
    'macbook pro m1':       {'category': '💻 Ordinateurs', 'keywords': ['macbook', 'pro', 'm1', 'apple']},
    'macbook air m2':       {'category': '💻 Ordinateurs', 'keywords': ['macbook', 'air', 'm2', 'apple']},
    'macbook air m1':       {'category': '💻 Ordinateurs', 'keywords': ['macbook', 'air', 'm1', 'apple']},
    'ipad pro':             {'category': '📱 Tablettes', 'keywords': ['ipad', 'pro', 'apple']},
    'ipad air':             {'category': '📱 Tablettes', 'keywords': ['ipad', 'air', 'apple']},
    'ps5':                  {'category': '🎮 Gaming', 'keywords': ['ps5', 'playstation 5', 'sony']},
    'ps4 pro':              {'category': '🎮 Gaming', 'keywords': ['ps4 pro', 'playstation 4 pro']},
    'xbox series x':        {'category': '🎮 Gaming', 'keywords': ['xbox', 'series x', 'microsoft']},
    'nintendo switch oled': {'category': '🎮 Gaming', 'keywords': ['switch', 'oled', 'nintendo']},
    'steam deck':           {'category': '🎮 Gaming', 'keywords': ['steam deck', 'valve']},
    'airpods pro 2':        {'category': '🎧 Audio', 'keywords': ['airpods', 'pro 2', 'apple']},
    'sony wh-1000xm5':      {'category': '🎧 Audio', 'keywords': ['sony', 'xm5', 'casque']},
    'dyson v15':            {'category': '🏠 Électroménager', 'keywords': ['dyson', 'v15', 'aspirateur']},
    'dyson v12':            {'category': '🏠 Électroménager', 'keywords': ['dyson', 'v12', 'aspirateur']},
    'dyson airwrap':        {'category': '🏠 Électroménager', 'keywords': ['dyson', 'airwrap']},
    'thermomix tm6':        {'category': '🏠 Électroménager', 'keywords': ['thermomix', 'tm6', 'vorwerk']},
    'apple watch ultra':    {'category': '⌚ Montres', 'keywords': ['apple watch', 'ultra']},
    'apple watch series 9': {'category': '⌚ Montres', 'keywords': ['apple watch', 'series 9']},
}

# ─────────────────────────────────────────────────────────────────────────────
# NICHES PREMIUM — objets peu connus du grand public, valeur élevée chez connaisseurs
# Stratégie : vendeur ne connaît pas → sous-prix → revente rapide
# ─────────────────────────────────────────────────────────────────────────────

FIXED_PRICES = {
    # MONTRES — marché connaisseur
    'rolex submariner':     {'ref_price': 9000,  'category': '⌚ Montres', 'keywords': ['rolex', 'submariner']},
    'rolex datejust':       {'ref_price': 6500,  'category': '⌚ Montres', 'keywords': ['rolex', 'datejust']},
    'rolex':                {'ref_price': 7000,  'category': '⌚ Montres', 'keywords': ['rolex', 'montre', 'oyster']},
    'omega seamaster':      {'ref_price': 2800,  'category': '⌚ Montres', 'keywords': ['omega', 'seamaster']},
    'omega speedmaster':    {'ref_price': 3500,  'category': '⌚ Montres', 'keywords': ['omega', 'speedmaster']},
    'tag heuer':            {'ref_price': 1200,  'category': '⌚ Montres', 'keywords': ['tag heuer', 'carrera']},
    'breitling':            {'ref_price': 2500,  'category': '⌚ Montres', 'keywords': ['breitling', 'navitimer']},
    'seiko':                {'ref_price': 150,   'category': '⌚ Montres', 'keywords': ['seiko', 'srpd', 'skx']},
    'casio g-shock':        {'ref_price': 80,    'category': '⌚ Montres', 'keywords': ['casio', 'g-shock', 'gshock']},

    # PHOTO — Leica inconnu des non-initiés, revente immédiate
    'leica m6':             {'ref_price': 2800,  'category': '📷 Photo Niche', 'keywords': ['leica', 'm6', 'argentique']},
    'leica m3':             {'ref_price': 1800,  'category': '📷 Photo Niche', 'keywords': ['leica', 'm3', 'argentique']},
    'leica m':              {'ref_price': 2200,  'category': '📷 Photo Niche', 'keywords': ['leica', 'telemetrique', 'rangefinder']},
    'leica':                {'ref_price': 1500,  'category': '📷 Photo Niche', 'keywords': ['leica', 'appareil']},
    'hasselblad':           {'ref_price': 2000,  'category': '📷 Photo Niche', 'keywords': ['hasselblad', 'moyen format']},
    'rolleiflex':           {'ref_price': 600,   'category': '📷 Photo Niche', 'keywords': ['rolleiflex', 'rollei', 'bi-objectif']},
    'contax':               {'ref_price': 400,   'category': '📷 Photo Niche', 'keywords': ['contax', 'zeiss']},
    'mamiya':               {'ref_price': 500,   'category': '📷 Photo Niche', 'keywords': ['mamiya', 'rb67', 'rz67']},
    'nikon f2':             {'ref_price': 350,   'category': '📷 Photo Niche', 'keywords': ['nikon', 'f2', 'argentique']},
    'canon ae-1':           {'ref_price': 180,   'category': '📷 Photo Niche', 'keywords': ['canon', 'ae-1', 'ae1', 'argentique']},

    # AUDIO VINTAGE — Bang & Olufsen, chaînes hifi, amplis
    'bang olufsen':         {'ref_price': 800,   'category': '🔊 Audio Vintage', 'keywords': ['bang olufsen', 'b&o', 'beolab', 'beosound', 'beoplay']},
    'bang olufsen beolit':  {'ref_price': 300,   'category': '🔊 Audio Vintage', 'keywords': ['beolit', 'b&o', 'bang olufsen']},
    'marantz':              {'ref_price': 400,   'category': '🔊 Audio Vintage', 'keywords': ['marantz', 'ampli', 'hifi', 'receivers']},
    'mcintosh':             {'ref_price': 2000,  'category': '🔊 Audio Vintage', 'keywords': ['mcintosh', 'ampli', 'mc']},
    'technics sl-1200':     {'ref_price': 900,   'category': '🔊 Audio Vintage', 'keywords': ['technics', 'sl-1200', 'platine']},
    'technics':             {'ref_price': 300,   'category': '🔊 Audio Vintage', 'keywords': ['technics', 'platine', 'vinyle', 'sl']},
    'sansui':               {'ref_price': 350,   'category': '🔊 Audio Vintage', 'keywords': ['sansui', 'ampli', 'tuner']},
    'yamaha hifi':          {'ref_price': 250,   'category': '🔊 Audio Vintage', 'keywords': ['yamaha', 'ampli', 'hifi', 'receiver']},
    'naim audio':           {'ref_price': 1200,  'category': '🔊 Audio Vintage', 'keywords': ['naim', 'nait', 'cd player']},
    'linn sondek':          {'ref_price': 1500,  'category': '🔊 Audio Vintage', 'keywords': ['linn', 'sondek', 'lp12', 'platine']},

    # INSTRUMENTS — Gibson, Fender vintage
    'gibson les paul':      {'ref_price': 2500,  'category': '🎸 Instruments', 'keywords': ['gibson', 'les paul', 'guitare']},
    'gibson sg':            {'ref_price': 1500,  'category': '🎸 Instruments', 'keywords': ['gibson', 'sg', 'guitare']},
    'gibson':               {'ref_price': 1800,  'category': '🎸 Instruments', 'keywords': ['gibson', 'guitare', 'electrique']},
    'fender stratocaster':  {'ref_price': 1200,  'category': '🎸 Instruments', 'keywords': ['fender', 'stratocaster', 'strat']},
    'fender telecaster':    {'ref_price': 1000,  'category': '🎸 Instruments', 'keywords': ['fender', 'telecaster', 'tele']},
    'martin guitar':        {'ref_price': 1500,  'category': '🎸 Instruments', 'keywords': ['martin', 'guitare', 'acoustique', 'd-28']},
    'selmer saxophone':     {'ref_price': 3000,  'category': '🎸 Instruments', 'keywords': ['selmer', 'saxophone', 'mark vi', 'super action']},
    'yamaha synth':         {'ref_price': 600,   'category': '🎸 Instruments', 'keywords': ['yamaha', 'dx7', 'synthesizer', 'synthe', 'cs']},
    'roland synth':         {'ref_price': 800,   'category': '🎸 Instruments', 'keywords': ['roland', 'juno', 'jupiter', 'synthe']},

    # DESIGN INDUSTRIEL — Braun, Dieter Rams (méconnu grand public, très cher chez collectionneurs)
    'braun dieter rams':    {'ref_price': 600,   'category': '🎨 Design Niche', 'keywords': ['braun', 'dieter rams', 'design', 'calculator']},
    'braun':                {'ref_price': 200,   'category': '🎨 Design Niche', 'keywords': ['braun', 'vintage', 'rasoir', 'radio']},
    'artek alvar aalto':    {'ref_price': 800,   'category': '🎨 Design Niche', 'keywords': ['artek', 'alvar aalto', 'stool', 'tabouret', 'chaise aalto']},
    'les arcs':             {'ref_price': 400,   'category': '🎨 Design Niche', 'keywords': ['charlotte perriand', 'les arcs', 'pierre jeanneret']},
    'knoll tulip':          {'ref_price': 600,   'category': '🎨 Design Niche', 'keywords': ['knoll', 'tulip', 'saarinen', 'eero']},
    'ercol':                {'ref_price': 350,   'category': '🎨 Design Niche', 'keywords': ['ercol', 'elm', 'windsor chair']},
    'USM haller':           {'ref_price': 1500,  'category': '🎨 Design Niche', 'keywords': ['usm', 'haller', 'meuble modulaire', 'chrome boules']},

    # MODE OUTDOOR — méconnu hors passionnés, revente garantie
    'arc teryx':            {'ref_price': 500,   'category': '🧥 Outdoor Premium', 'keywords': ['arc teryx', 'arcteryx', 'alpha', 'beta sl']},
    'patagonia':            {'ref_price': 200,   'category': '🧥 Outdoor Premium', 'keywords': ['patagonia', 'nano puff', 'down sweater', 'retro x']},
    'stone island':         {'ref_price': 400,   'category': '🧥 Outdoor Premium', 'keywords': ['stone island', 'veste', 'manteau']},
    'canada goose':         {'ref_price': 700,   'category': '🧥 Outdoor Premium', 'keywords': ['canada goose', 'expedition', 'chilliwack']},
    'moncler':              {'ref_price': 900,   'category': '🧥 Outdoor Premium', 'keywords': ['moncler', 'doudoune', 'gilet']},

    # LUXE / MAROQUINERIE
    'hermes birkin':        {'ref_price': 8000,  'category': '👜 Luxe/Mode', 'keywords': ['hermes', 'birkin']},
    'hermes kelly':         {'ref_price': 6000,  'category': '👜 Luxe/Mode', 'keywords': ['hermes', 'kelly']},
    'hermes':               {'ref_price': 3000,  'category': '👜 Luxe/Mode', 'keywords': ['hermes', 'sac']},
    'chanel classic':       {'ref_price': 5000,  'category': '👜 Luxe/Mode', 'keywords': ['chanel', 'classic flap']},
    'chanel':               {'ref_price': 2000,  'category': '👜 Luxe/Mode', 'keywords': ['chanel', 'sac', 'cc']},
    'louis vuitton neverfull': {'ref_price': 900,'category': '👜 Luxe/Mode', 'keywords': ['louis vuitton', 'neverfull']},
    'louis vuitton':        {'ref_price': 700,   'category': '👜 Luxe/Mode', 'keywords': ['louis vuitton', 'vuitton', 'lv']},
    'dior':                 {'ref_price': 800,   'category': '👜 Luxe/Mode', 'keywords': ['dior', 'sac']},
    'gucci':                {'ref_price': 500,   'category': '👜 Luxe/Mode', 'keywords': ['gucci', 'sac']},

    # SNEAKERS
    'yeezy 350':            {'ref_price': 220,   'category': '👟 Sneakers', 'keywords': ['yeezy', '350', 'adidas']},
    'jordan 1 retro':       {'ref_price': 170,   'category': '👟 Sneakers', 'keywords': ['jordan 1', 'air jordan', 'aj1']},
    'jordan 4':             {'ref_price': 200,   'category': '👟 Sneakers', 'keywords': ['jordan 4', 'aj4']},
    'nike dunk':            {'ref_price': 110,   'category': '👟 Sneakers', 'keywords': ['nike', 'dunk']},

    # LEGO sets recherchés
    'lego technic':         {'ref_price': 180,   'category': '🧱 LEGO', 'keywords': ['lego', 'technic']},
    'lego star wars':       {'ref_price': 200,   'category': '🧱 LEGO', 'keywords': ['lego', 'star wars']},
    'lego creator':         {'ref_price': 150,   'category': '🧱 LEGO', 'keywords': ['lego', 'creator']},
    'lego':                 {'ref_price': 100,   'category': '🧱 LEGO', 'keywords': ['lego', 'boite', 'set']},

    # VINYLES
    'vinyle':               {'ref_price': 40,    'category': '🎵 Vinyles', 'keywords': ['vinyle', 'vinyl', 'disque', '33t']},
}

LOT_TRIGGER_WORDS = [
    'lot', 'ensemble', 'vrac', 'collection', 'boite', 'caisse',
    'sac', 'divers', 'melange', 'assortiment', 'carton', 'palette'
]

HEADERS_POOL = [
    {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'},
    {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0'},
    {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15'},
    {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'},
]

_bm_price_cache = {}
_bm_cache_ts    = {}
_bm_cache_lock  = threading.Lock()
BM_CACHE_TTL    = 6 * 3600


# ─────────────────────────────────────────────────────────────────────────────
# MOBILIER PREMIUM MÉCONNU
# ─────────────────────────────────────────────────────────────────────────────

GENERIC_TITLES = [
    'chaise bureau', 'fauteuil bureau', 'siege bureau', 'chaise',
    'fauteuil', 'chaise ergonomique', 'chaise filet', 'chaise mesh',
    'siege ergonomique', 'chaise de travail', 'chaise gaming'
]

UNCERTAIN_PHRASES = [
    'je ne connais pas la marque', 'je ne sais pas', 'sans marque',
    'recuperation', 'debarras', 'vide bureau', 'provenance bureau',
    'ancien materiel', 'lot mobilier', 'trouve', 'succession',
    'pas la marque', 'marque inconnue', 'open space', 'liquidation',
    'vide local', 'ca appartenait', 'appartenait a mon entreprise'
]

PREMIUM_FURNITURE = {
    'herman miller aeron': {
        'brand': 'herman miller',
        'category': '🪑 Mobilier Premium',
        'market_price': 600,
        'strong_features': ['posturefit', 'posturefit sl', 'pellicle', 'aeron', 'taille b', 'taille c', 'taille a', 'support lombaire reglable', '8z pellicle'],
        'shape_features': ['maille', 'mesh', 'filet', 'molette inclinaison', 'accoudoirs reglables', 'dossier filet']
    },
    'herman miller embody': {
        'brand': 'herman miller',
        'category': '🪑 Mobilier Premium',
        'market_price': 900,
        'strong_features': ['embody', 'backfit', 'pixelated support', 'herman miller'],
        'shape_features': ['colonne centrale', 'dossier etroit en haut', 'ribs', 'assise multicouche']
    },
    'herman miller mirra': {
        'brand': 'herman miller',
        'category': '🪑 Mobilier Premium',
        'market_price': 300,
        'strong_features': ['mirra', 'herman miller', 'inclinaison avant'],
        'shape_features': ['dossier plastique perfore', 'dossier ventile', 'assise mesh suspendue']
    },
    'steelcase leap': {
        'brand': 'steelcase',
        'category': '🪑 Mobilier Premium',
        'market_price': 500,
        'strong_features': ['steelcase', 'leap', 'liveback', 'natural glide'],
        'shape_features': ['dossier flexible', 'soutien lombaire automatique', 'accoudoirs 4d']
    },
    'steelcase gesture': {
        'brand': 'steelcase',
        'category': '🪑 Mobilier Premium',
        'market_price': 600,
        'strong_features': ['steelcase', 'gesture', '360 arm'],
        'shape_features': ['accoudoirs 360', 'support tablette', 'accoudoirs pivotants']
    },
    'humanscale freedom': {
        'brand': 'humanscale',
        'category': '🪑 Mobilier Premium',
        'market_price': 650,
        'strong_features': ['humanscale', 'freedom'],
        'shape_features': ['appuie-tete integre', 'inclinaison automatique', 'reglage automatique']
    },
    'vitra eames': {
        'brand': 'vitra',
        'category': '🪑 Mobilier Premium',
        'market_price': 900,
        'strong_features': ['vitra', 'eames', 'lounge chair', 'daw', 'dsx'],
        'shape_features': ['coque plastique', 'pied tour eiffel', 'design annees 50']
    },
}


def detect_premium_furniture(title, description=''):
    text = (title + ' ' + description).lower()
    best_model = None
    best_score = 0
    for model_name, data in PREMIUM_FURNITURE.items():
        score = sum(3 for f in data['strong_features'] if f in text)
        score += sum(1 for f in data['shape_features'] if f in text)
        if score > best_score:
            best_score = score
            best_model = model_name
    if best_score >= 3:
        return best_model, min(best_score * 15, 95)
    return None, 0


def knowledge_gap_score(title, description='', detected_model=None):
    text = (title + ' ' + description).lower()
    score = 0
    if any(g in title.lower() for g in GENERIC_TITLES):
        score += 20
    if any(p in text for p in UNCERTAIN_PHRASES):
        score += 25
    if detected_model and detected_model in PREMIUM_FURNITURE:
        brand = PREMIUM_FURNITURE[detected_model]['brand']
        if brand not in title.lower():
            score += 20
        model_short = detected_model.split()[-1]
        if model_short not in title.lower():
            score += 15
    if len(title.split()) <= 3:
        score += 8
    if len(description.strip()) < 40:
        score += 6
    return min(score, 100)


# ─────────────────────────────────────────────────────────────────────────────
# UTILITAIRES
# ─────────────────────────────────────────────────────────────────────────────

def get_headers():
    return random.choice(HEADERS_POOL)

def delay(short=False):
    time.sleep(random.uniform(0.8, 1.5) if short else random.uniform(1.5, 3.0))

def extract_price(text):
    if not text:
        return None
    text = text.replace('\xa0', '').replace('\u202f', '').replace('\u00a0', '').replace(' ', '').replace(',', '.')
    match = re.search(r'([\d]+\.?[\d]*)', text)
    if match:
        try:
            val = float(match.group(1))
            return val if val > 0 else None
        except Exception:
            return None
    return None


def scrape_backmarket_price(product_name):
    now = time.time()
    with _bm_cache_lock:
        ts = _bm_cache_ts.get(product_name, 0)
        if now - ts < BM_CACHE_TTL and product_name in _bm_price_cache:
            return _bm_price_cache[product_name]
    try:
        query = requests.utils.quote(product_name)
        url = f'https://www.backmarket.fr/fr-fr/search?q={query}&grade=9'
        headers = get_headers()
        headers['Accept-Language'] = 'fr-FR,fr;q=0.9'
        headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        resp = requests.get(url, headers=headers, timeout=15)
        delay(short=True)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, 'html5lib')
        price_candidates = []
        for el in soup.select('[data-qa="product-price"], [class*="price"], [class*="Price"]'):
            p = extract_price(el.get_text(strip=True))
            if p and 10 < p < 20000:
                price_candidates.append(p)
        if not price_candidates:
            script = soup.find('script', {'id': '__NEXT_DATA__'})
            if script and script.string:
                for m in re.findall(r'"price"\s*:\s*"?([\d]+\.?[\d]*)"?', script.string):
                    try:
                        p = float(m)
                        if 10 < p < 20000:
                            price_candidates.append(p)
                    except Exception:
                        pass
        if price_candidates:
            best_price = min(price_candidates)
            with _bm_cache_lock:
                _bm_price_cache[product_name] = best_price
                _bm_cache_ts[product_name] = now
            print(f'[BackMarket] {product_name} → {best_price}€')
            return best_price
    except Exception as e:
        print(f'[BackMarket] Erreur "{product_name}": {e}')
    return None


def prefetch_backmarket_prices(product_names):
    def _fetch_all():
        for name in product_names:
            now = time.time()
            with _bm_cache_lock:
                already = now - _bm_cache_ts.get(name, 0) < BM_CACHE_TTL and name in _bm_price_cache
            if not already:
                scrape_backmarket_price(name)
                time.sleep(random.uniform(1.0, 2.0))
    threading.Thread(target=_fetch_all, daemon=True).start()


def get_ref_price(product_name):
    if product_name in BACKMARKET_CATALOG:
        live = scrape_backmarket_price(product_name)
        if live:
            return live, 'live'
        with _bm_cache_lock:
            cached = _bm_price_cache.get(product_name)
        if cached:
            return cached, 'fallback'
        emergency = {
            'iphone 16 pro': 950, 'iphone 16': 720, 'iphone 15 pro': 820,
            'iphone 15': 580, 'iphone 14 pro': 600, 'iphone 14': 430,
            'iphone 13': 310, 'iphone 12': 210, 'iphone 11': 150,
            'iphone xr': 110, 'ps5': 380, 'xbox series x': 350,
            'nintendo switch oled': 230, 'steam deck': 360,
            'macbook pro m3': 1600, 'macbook pro m2': 1200, 'macbook pro m1': 900,
            'macbook air m2': 850, 'macbook air m1': 620,
            'dyson v15': 420, 'dyson airwrap': 380,
        }
        return emergency.get(product_name, 0), 'fallback'
    if product_name in FIXED_PRICES:
        return FIXED_PRICES[product_name]['ref_price'], 'fixed'
    if product_name in PREMIUM_FURNITURE:
        return PREMIUM_FURNITURE[product_name]['market_price'], 'fixed'
    return 0, 'unknown'


# ─────────────────────────────────────────────────────────────────────────────
# DÉTECTION OBJETS
# ─────────────────────────────────────────────────────────────────────────────

ALL_OBJECTS = {}
for name, data in BACKMARKET_CATALOG.items():
    ALL_OBJECTS[name] = data
for name, data in FIXED_PRICES.items():
    ALL_OBJECTS[name] = data


def detect_value_objects(title, description=''):
    full_text = (title + ' ' + description).lower()
    detected = []
    seen = set()
    for obj_name, obj_data in ALL_OBJECTS.items():
        if obj_name in seen:
            continue
        score = fuzz.partial_ratio(obj_name.lower(), full_text)
        if score >= 78:
            ref_price, price_source = get_ref_price(obj_name)
            if ref_price > 0:
                detected.append({'name': obj_name, 'ref_price': ref_price, 'price_source': price_source, 'category': obj_data['category'], 'confidence': score})
                seen.add(obj_name)
                continue
        kw_matches = sum(1 for kw in obj_data['keywords'] if kw.lower() in full_text)
        if kw_matches >= 2:
            ref_price, price_source = get_ref_price(obj_name)
            if ref_price > 0:
                detected.append({'name': obj_name, 'ref_price': ref_price, 'price_source': price_source, 'category': obj_data['category'], 'confidence': min(60 + kw_matches * 10, 90)})
                seen.add(obj_name)
    is_lot = any(w in full_text for w in LOT_TRIGGER_WORDS)
    return detected, is_lot


def calculate_deal_score(price, ref_price, is_lot=False, nb_detected=0):
    if not price or not ref_price or price <= 0:
        return 0, 0
    effective_ref = ref_price
    if is_lot and nb_detected > 1:
        effective_ref = ref_price * min(nb_detected, 3) * 0.6
    discount_pct = ((effective_ref - price) / effective_ref) * 100
    if discount_pct <= 0:
        score = 0
    elif discount_pct < 20:
        score = discount_pct * 1.5
    elif discount_pct < 40:
        score = 30 + (discount_pct - 20) * 2
    elif discount_pct < 60:
        score = 70 + (discount_pct - 40) * 1
    else:
        score = min(90 + (discount_pct - 60) * 0.5, 100)
    return round(discount_pct, 1), round(score)


# ─────────────────────────────────────────────────────────────────────────────
# SCRAPER
# ─────────────────────────────────────────────────────────────────────────────

class DealScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(get_headers())
        print('[BackMarket] Pré-chargement des prix...')
        prefetch_backmarket_prices(list(BACKMARKET_CATALOG.keys())[:20])

    def _parse_listing(self, item, platform, platform_color):
        try:
            title_el = item.select_one('[class*="title"],[class*="Title"]') or item.find(['h2','h3','p'])
            price_el = item.select_one('[class*="price"],[class*="Price"]') or item.find(string=re.compile(r'\d+\s*€'))
            link_el = item if item.name == 'a' else item.find('a')
            img_el = item.find('img')
            title = title_el.get_text(strip=True) if title_el else ''
            price_text = price_el.get_text(strip=True) if hasattr(price_el, 'get_text') else str(price_el or '')
            price = extract_price(price_text)
            href = link_el.get('href', '') if link_el else ''
            link = ''
            if href.startswith('http'):
                link = href
            elif href.startswith('/'):
                domain = 'https://www.leboncoin.fr' if platform == 'LeBonCoin' else 'https://www.vinted.fr'
                link = domain + href
            img = ''
            if img_el:
                img = img_el.get('src') or img_el.get('data-src', '')
            if title and price and 1 < price < 50000:
                return {'title': title, 'price': price, 'price_str': f'{price}€', 'link': link, 'image': img, 'platform': platform, 'platform_color': platform_color}
        except Exception:
            pass
        return None

    def scrape_leboncoin(self, query, max_results=30):
        results = []
        try:
            url = f'https://www.leboncoin.fr/recherche?text={requests.utils.quote(query)}&sort=time'
            resp = self.session.get(url, headers=get_headers(), timeout=15)
            delay()
            soup = BeautifulSoup(resp.text, 'html5lib')
            listings = soup.select('[data-test-id="ad"]') or soup.select('article[class*="styles_adCard"]') or soup.select('article') or soup.select('li[class*="aditem"]')
            for item in listings[:max_results]:
                r = self._parse_listing(item, 'LeBonCoin', '#F56B2A')
                if r:
                    results.append(r)
        except Exception as e:
            print(f'[LBC] Erreur: {e}')
        return results

    def scrape_vinted(self, query, max_results=30):
        results = []
        try:
            url = f'https://www.vinted.fr/catalog?search_text={requests.utils.quote(query)}&order=newest_first'
            resp = self.session.get(url, headers=get_headers(), timeout=15)
            delay()
            soup = BeautifulSoup(resp.text, 'html5lib')
            listings = soup.select('[data-testid="grid-item"]') or soup.select('.feed-grid__item') or soup.select('[class*="ItemBox"]')
            for item in listings[:max_results]:
                r = self._parse_listing(item, 'Vinted', '#09B1BA')
                if r:
                    results.append(r)
        except Exception as e:
            print(f'[Vinted] Erreur: {e}')
        return results

    def scrape_ebay(self, query, max_results=30):
        results = []
        try:
            url = f'https://www.ebay.fr/sch/i.html?_nkw={requests.utils.quote(query)}&_sop=10&LH_BIN=1'
            resp = self.session.get(url, headers=get_headers(), timeout=15)
            delay()
            soup = BeautifulSoup(resp.text, 'html5lib')
            for item in (soup.select('.s-item') or [])[:max_results]:
                try:
                    title_el = item.select_one('.s-item__title')
                    price_el = item.select_one('.s-item__price')
                    link_el = item.select_one('a.s-item__link') or item.find('a')
                    img_el = item.find('img')
                    title = title_el.get_text(strip=True) if title_el else ''
                    if 'Shop on eBay' in title or not title:
                        continue
                    price = extract_price(price_el.get_text(strip=True) if price_el else '')
                    if price and 1 < price < 50000:
                        results.append({'title': title, 'price': price, 'price_str': f'{price}€', 'link': link_el.get('href','') if link_el else '', 'image': img_el.get('src','') if img_el else '', 'platform': 'eBay', 'platform_color': '#E53238'})
                except Exception:
                    continue
        except Exception as e:
            print(f'[eBay] Erreur: {e}')
        return results

    def analyze_listings(self, listings, min_discount=40):
        deals = []
        for item in listings:
            title = item.get('title', '')
            description = item.get('description', '')
            price = item.get('price')
            if not price:
                continue
            furniture_model, furniture_conf = detect_premium_furniture(title, description)
            kg_score = knowledge_gap_score(title, description, furniture_model)
            detected_objects, is_lot = detect_value_objects(title, description)
            if furniture_model and furniture_conf >= 30:
                fd = PREMIUM_FURNITURE[furniture_model]
                detected_objects.append({'name': furniture_model, 'ref_price': fd['market_price'], 'price_source': 'fixed', 'category': fd['category'], 'confidence': furniture_conf})
            if not detected_objects:
                continue
            best_obj = max(detected_objects, key=lambda x: x['ref_price'])
            discount_pct, base_score = calculate_deal_score(price, best_obj['ref_price'], is_lot, len(detected_objects))
            final_score = round(base_score * 0.55 + kg_score * 0.45)
            if discount_pct >= min_discount or (furniture_model and kg_score >= 50):
                result = {**item,
                    'detected_objects': detected_objects,
                    'best_match': best_obj['name'],
                    'ref_price': best_obj['ref_price'],
                    'price_source': best_obj.get('price_source', 'fixed'),
                    'category': best_obj['category'],
                    'discount_pct': discount_pct,
                    'deal_score': base_score,
                    'final_opportunity_score': final_score,
                    'knowledge_gap_score': kg_score,
                    'is_lot': is_lot,
                    'savings': round(best_obj['ref_price'] - price, 2),
                    'vendor_unaware': kg_score >= 50,
                }
                if furniture_model:
                    result['furniture_model'] = furniture_model
                    result['furniture_confidence'] = furniture_conf
                deals.append(result)
        deals.sort(key=lambda x: x.get('final_opportunity_score', x.get('deal_score', 0)), reverse=True)
        return deals

    def search_deals(self, keywords, min_discount=40, platforms=None):
        if platforms is None:
            platforms = ['leboncoin', 'vinted', 'ebay']
        all_listings = []
        if 'leboncoin' in platforms: all_listings += self.scrape_leboncoin(keywords)
        if 'vinted' in platforms: all_listings += self.scrape_vinted(keywords)
        if 'ebay' in platforms: all_listings += self.scrape_ebay(keywords)
        deals = self.analyze_listings(all_listings, min_discount)
        return {'deals': deals, 'total_scanned': len(all_listings), 'total_deals': len(deals), 'query': keywords}

    def auto_hunt(self, min_discount=50, platforms=None):
        if platforms is None:
            platforms = ['leboncoin', 'vinted', 'ebay']
        hunt_queries = [
            'lot electronique', 'lot telephone', 'iphone occasion',
            'montre collection', 'vide grenier appareil photo',
            'chaine hifi vintage', 'ampli hifi',
            'guitare electrique', 'saxophone',
            'leica appareil photo', 'chaise bureau ergonomique',
            'fauteuil ergonomique', 'mobilier bureau liquidation',
            'dyson aspirateur', 'lego boite',
            'veste patagonia', 'arc teryx veste',
            'platine vinyle technics', 'instrument musique lot'
        ]
        all_listings = []
        for query in hunt_queries[:10]:
            if 'leboncoin' in platforms: all_listings += self.scrape_leboncoin(query, max_results=15)
            if 'ebay' in platforms: all_listings += self.scrape_ebay(query, max_results=15)
            time.sleep(random.uniform(0.8, 1.5))
        seen = set()
        unique = [item for item in all_listings if item.get('link') and item['link'] not in seen and not seen.add(item['link'])]
        deals = self.analyze_listings(unique, min_discount)
        return {'deals': deals, 'total_scanned': len(unique), 'total_deals': len(deals), 'query': 'Auto Hunt'}

    def get_value_categories(self):
        cats = {}
        for obj_name, obj_data in ALL_OBJECTS.items():
            cat = obj_data['category']
            if cat not in cats: cats[cat] = []
            ref, src = get_ref_price(obj_name)
            cats[cat].append({'name': obj_name, 'ref_price': ref, 'price_source': src})
        return cats

    def get_cache_status(self):
        now = time.time()
        with _bm_cache_lock:
            cached = [{'name': k, 'price': _bm_price_cache[k], 'age_min': round((now - _bm_cache_ts[k]) / 60, 1)} for k in _bm_price_cache]
        cached.sort(key=lambda x: x['name'])
        return {'cached_count': len(cached), 'items': cached}
