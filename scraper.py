import requests
from bs4 import BeautifulSoup
import re
import time
import random
import threading
from thefuzz import fuzz

# ─────────────────────────────────────────────────────────────────────────────
# PRIX DE RÉFÉRENCE EN TEMPS RÉEL
#
# Stratégie hybride :
#   • Électronique (téléphones, ordi, tablettes, gaming, audio…)
#     → scraping BackMarket.fr en direct, prix "Bon état", cache 6h en mémoire
#   • Luxe, montres, sneakers, cartes, LEGO, vinyles
#     → prix fixes (BackMarket ne les couvre pas)
# ─────────────────────────────────────────────────────────────────────────────

# Catalogue BackMarket : slug de recherche → nom canonique + catégorie
# Le slug est utilisé dans l'URL backmarket.fr/fr-fr/search?q=<slug>
BACKMARKET_CATALOG = {
    # Téléphones Apple
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
    # Téléphones Samsung
    'samsung galaxy s24 ultra': {'category': '📱 Téléphones', 'keywords': ['samsung', 'galaxy', 's24', 'ultra']},
    'samsung galaxy s24':   {'category': '📱 Téléphones', 'keywords': ['samsung', 'galaxy', 's24']},
    'samsung galaxy s23':   {'category': '📱 Téléphones', 'keywords': ['samsung', 'galaxy', 's23']},
    'samsung galaxy s22':   {'category': '📱 Téléphones', 'keywords': ['samsung', 'galaxy', 's22']},
    # Google / autres
    'google pixel 8 pro':   {'category': '📱 Téléphones', 'keywords': ['pixel', '8 pro', 'google']},
    'google pixel 8':       {'category': '📱 Téléphones', 'keywords': ['pixel', '8', 'google']},
    'oneplus 12':           {'category': '📱 Téléphones', 'keywords': ['oneplus', '12']},
    # Mac
    'macbook pro m3':       {'category': '💻 Ordinateurs', 'keywords': ['macbook', 'pro', 'm3', 'apple']},
    'macbook pro m2':       {'category': '💻 Ordinateurs', 'keywords': ['macbook', 'pro', 'm2', 'apple']},
    'macbook pro m1':       {'category': '💻 Ordinateurs', 'keywords': ['macbook', 'pro', 'm1', 'apple']},
    'macbook air m2':       {'category': '💻 Ordinateurs', 'keywords': ['macbook', 'air', 'm2', 'apple']},
    'macbook air m1':       {'category': '💻 Ordinateurs', 'keywords': ['macbook', 'air', 'm1', 'apple']},
    'imac m1':              {'category': '💻 Ordinateurs', 'keywords': ['imac', 'm1', 'apple']},
    'dell xps':             {'category': '💻 Ordinateurs', 'keywords': ['dell', 'xps']},
    'thinkpad x1':          {'category': '💻 Ordinateurs', 'keywords': ['thinkpad', 'x1', 'lenovo']},
    # Tablettes
    'ipad pro':             {'category': '📱 Tablettes', 'keywords': ['ipad', 'pro', 'apple']},
    'ipad air':             {'category': '📱 Tablettes', 'keywords': ['ipad', 'air', 'apple']},
    'ipad':                 {'category': '📱 Tablettes', 'keywords': ['ipad', 'apple', 'tablette']},
    'samsung galaxy tab s9':{'category': '📱 Tablettes', 'keywords': ['samsung', 'galaxy tab', 's9']},
    # Gaming
    'ps5':                  {'category': '🎮 Gaming', 'keywords': ['ps5', 'playstation 5', 'sony']},
    'ps4 pro':              {'category': '🎮 Gaming', 'keywords': ['ps4 pro', 'playstation 4 pro']},
    'ps4':                  {'category': '🎮 Gaming', 'keywords': ['ps4', 'playstation 4']},
    'xbox series x':        {'category': '🎮 Gaming', 'keywords': ['xbox', 'series x', 'microsoft']},
    'xbox series s':        {'category': '🎮 Gaming', 'keywords': ['xbox', 'series s', 'microsoft']},
    'nintendo switch oled': {'category': '🎮 Gaming', 'keywords': ['switch', 'oled', 'nintendo']},
    'nintendo switch':      {'category': '🎮 Gaming', 'keywords': ['switch', 'nintendo', 'console']},
    'steam deck':           {'category': '🎮 Gaming', 'keywords': ['steam deck', 'valve']},
    # Audio
    'airpods pro 2':        {'category': '🎧 Audio', 'keywords': ['airpods', 'pro 2', 'apple']},
    'airpods pro':          {'category': '🎧 Audio', 'keywords': ['airpods', 'pro', 'apple']},
    'sony wh-1000xm5':      {'category': '🎧 Audio', 'keywords': ['sony', 'xm5', 'casque']},
    'sony wh-1000xm4':      {'category': '🎧 Audio', 'keywords': ['sony', 'xm4', 'casque']},
    'bose qc45':            {'category': '🎧 Audio', 'keywords': ['bose', 'qc45', 'quietcomfort']},
    # Photo
    'gopro hero 12':        {'category': '📷 Photo/Vidéo', 'keywords': ['gopro', 'hero 12']},
    'gopro hero 11':        {'category': '📷 Photo/Vidéo', 'keywords': ['gopro', 'hero 11']},
    'canon eos r':          {'category': '📷 Photo/Vidéo', 'keywords': ['canon', 'eos r', 'hybride']},
    'canon eos':            {'category': '📷 Photo/Vidéo', 'keywords': ['canon', 'eos', 'reflex']},
    'sony alpha a7':        {'category': '📷 Photo/Vidéo', 'keywords': ['sony', 'alpha', 'a7']},
    'sony alpha a6':        {'category': '📷 Photo/Vidéo', 'keywords': ['sony', 'alpha', 'a6']},
    'drone dji':            {'category': '📷 Photo/Vidéo', 'keywords': ['dji', 'drone', 'mavic']},
    # Électroménager
    'dyson v15':            {'category': '🏠 Électroménager', 'keywords': ['dyson', 'v15', 'aspirateur']},
    'dyson v12':            {'category': '🏠 Électroménager', 'keywords': ['dyson', 'v12', 'aspirateur']},
    'dyson v11':            {'category': '🏠 Électroménager', 'keywords': ['dyson', 'v11', 'aspirateur']},
    'dyson v10':            {'category': '🏠 Électroménager', 'keywords': ['dyson', 'v10', 'aspirateur']},
    'dyson airwrap':        {'category': '🏠 Électroménager', 'keywords': ['dyson', 'airwrap']},
    'thermomix tm6':        {'category': '🏠 Électroménager', 'keywords': ['thermomix', 'tm6', 'vorwerk']},
    'thermomix tm5':        {'category': '🏠 Électroménager', 'keywords': ['thermomix', 'tm5', 'vorwerk']},
    'roomba':               {'category': '🏠 Électroménager', 'keywords': ['roomba', 'irobot']},
    # Apple Watch
    'apple watch ultra':    {'category': '⌚ Montres', 'keywords': ['apple watch', 'ultra']},
    'apple watch series 9': {'category': '⌚ Montres', 'keywords': ['apple watch', 'series 9']},
    'apple watch series 8': {'category': '⌚ Montres', 'keywords': ['apple watch', 'series 8']},
}

# Prix fixes pour catégories non couvertes par BackMarket
FIXED_PRICES = {
    # Montres mécaniques
    'rolex submariner':  {'ref_price': 9000,  'category': '⌚ Montres', 'keywords': ['rolex', 'submariner']},
    'rolex datejust':    {'ref_price': 6500,  'category': '⌚ Montres', 'keywords': ['rolex', 'datejust']},
    'rolex':             {'ref_price': 7000,  'category': '⌚ Montres', 'keywords': ['rolex', 'montre', 'oyster']},
    'omega seamaster':   {'ref_price': 2800,  'category': '⌚ Montres', 'keywords': ['omega', 'seamaster']},
    'omega speedmaster': {'ref_price': 3500,  'category': '⌚ Montres', 'keywords': ['omega', 'speedmaster']},
    'tag heuer':         {'ref_price': 1200,  'category': '⌚ Montres', 'keywords': ['tag heuer', 'carrera']},
    'breitling':         {'ref_price': 2500,  'category': '⌚ Montres', 'keywords': ['breitling', 'navitimer']},
    'seiko':             {'ref_price': 150,   'category': '⌚ Montres', 'keywords': ['seiko', 'srpd', 'skx']},
    'casio g-shock':     {'ref_price': 80,    'category': '⌚ Montres', 'keywords': ['casio', 'g-shock', 'gshock']},
    # Luxe / Sacs
    'hermes birkin':     {'ref_price': 8000,  'category': '👜 Luxe/Mode', 'keywords': ['hermes', 'birkin']},
    'hermes kelly':      {'ref_price': 6000,  'category': '👜 Luxe/Mode', 'keywords': ['hermes', 'kelly']},
    'hermes':            {'ref_price': 3000,  'category': '👜 Luxe/Mode', 'keywords': ['hermes', 'sac']},
    'chanel classic':    {'ref_price': 5000,  'category': '👜 Luxe/Mode', 'keywords': ['chanel', 'classic flap']},
    'chanel':            {'ref_price': 2000,  'category': '👜 Luxe/Mode', 'keywords': ['chanel', 'sac', 'cc']},
    'louis vuitton neverfull': {'ref_price': 900, 'category': '👜 Luxe/Mode', 'keywords': ['louis vuitton', 'neverfull']},
    'louis vuitton speedy':    {'ref_price': 600, 'category': '👜 Luxe/Mode', 'keywords': ['louis vuitton', 'speedy']},
    'louis vuitton':     {'ref_price': 700,   'category': '👜 Luxe/Mode', 'keywords': ['louis vuitton', 'vuitton', 'lv']},
    'dior':              {'ref_price': 800,   'category': '👜 Luxe/Mode', 'keywords': ['dior', 'sac']},
    'gucci':             {'ref_price': 500,   'category': '👜 Luxe/Mode', 'keywords': ['gucci', 'sac']},
    # Sneakers
    'yeezy 350':         {'ref_price': 220,   'category': '👟 Sneakers', 'keywords': ['yeezy', '350', 'adidas']},
    'yeezy':             {'ref_price': 200,   'category': '👟 Sneakers', 'keywords': ['yeezy', 'adidas']},
    'jordan 1 retro':    {'ref_price': 170,   'category': '👟 Sneakers', 'keywords': ['jordan 1', 'air jordan', 'aj1']},
    'jordan 4':          {'ref_price': 200,   'category': '👟 Sneakers', 'keywords': ['jordan 4', 'aj4']},
    'nike dunk':         {'ref_price': 110,   'category': '👟 Sneakers', 'keywords': ['nike', 'dunk']},
    'new balance 550':   {'ref_price': 120,   'category': '👟 Sneakers', 'keywords': ['new balance', '550']},
    # Cartes / Jeux
    'carte pokemon charizard': {'ref_price': 200, 'category': '🃏 Cartes/Jeux', 'keywords': ['pokemon', 'charizard', 'carte']},
    'pokemon lot':       {'ref_price': 80,    'category': '🃏 Cartes/Jeux', 'keywords': ['pokemon', 'cartes', 'lot']},
    'one piece carte':   {'ref_price': 60,    'category': '🃏 Cartes/Jeux', 'keywords': ['one piece', 'carte']},
    'magic gathering':   {'ref_price': 100,   'category': '🃏 Cartes/Jeux', 'keywords': ['magic', 'gathering', 'mtg']},
    # LEGO
    'lego technic':      {'ref_price': 180,   'category': '🧱 LEGO', 'keywords': ['lego', 'technic']},
    'lego star wars':    {'ref_price': 200,   'category': '🧱 LEGO', 'keywords': ['lego', 'star wars']},
    'lego creator':      {'ref_price': 150,   'category': '🧱 LEGO', 'keywords': ['lego', 'creator']},
    'lego':              {'ref_price': 100,   'category': '🧱 LEGO', 'keywords': ['lego', 'boite', 'set']},
    # Vinyles
    'vinyle':            {'ref_price': 40,    'category': '🎵 Vinyles', 'keywords': ['vinyle', 'vinyl', 'disque', '33t']},
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

# ─────────────────────────────────────────────────────────────────────────────
# CACHE DES PRIX BACKMARKET (en mémoire, durée de vie = 6h)
# ─────────────────────────────────────────────────────────────────────────────
_bm_price_cache = {}          # {product_name: prix_float}
_bm_cache_ts    = {}          # {product_name: timestamp_last_fetch}
_bm_cache_lock  = threading.Lock()
BM_CACHE_TTL    = 6 * 3600   # 6 heures en secondes


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


# ─────────────────────────────────────────────────────────────────────────────
# SCRAPING BACKMARKET EN TEMPS RÉEL
# ─────────────────────────────────────────────────────────────────────────────

def scrape_backmarket_price(product_name: str) -> float | None:
    """
    Scrape le prix 'Bon état' de BackMarket pour un produit donné.
    Retourne le prix minimum trouvé, ou None si échec.
    Cache le résultat 6h en mémoire.
    """
    now = time.time()
    with _bm_cache_lock:
        ts = _bm_cache_ts.get(product_name, 0)
        if now - ts < BM_CACHE_TTL and product_name in _bm_price_cache:
            return _bm_price_cache[product_name]

    try:
        query = requests.utils.quote(product_name)
        # BackMarket recherche + filtre "bon état" (grade=9 = bon état)
        url = f'https://www.backmarket.fr/fr-fr/search?q={query}&grade=9'
        headers = get_headers()
        headers['Accept-Language'] = 'fr-FR,fr;q=0.9'
        headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'

        resp = requests.get(url, headers=headers, timeout=15)
        delay(short=True)

        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, 'html5lib')

        # Sélecteurs BackMarket (plusieurs tentatives pour robustesse)
        price_candidates = []

        # Méthode 1 : balises de prix structurées
        for el in soup.select('[data-qa="product-price"], [class*="price"], [class*="Price"]'):
            txt = el.get_text(strip=True)
            p = extract_price(txt)
            if p and 10 < p < 20000:
                price_candidates.append(p)

        # Méthode 2 : recherche dans le JSON embarqué (Next.js __NEXT_DATA__)
        if not price_candidates:
            script = soup.find('script', {'id': '__NEXT_DATA__'})
            if script and script.string:
                # Extraction rapide sans parser tout le JSON
                matches = re.findall(r'"price"\s*:\s*"?([\d]+\.?[\d]*)"?', script.string)
                for m in matches:
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
            print(f'[BackMarket] {product_name} → {best_price}€ (live)')
            return best_price

    except Exception as e:
        print(f'[BackMarket] Erreur pour "{product_name}": {e}')

    return None


def prefetch_backmarket_prices(product_names: list):
    """
    Pré-charge les prix BackMarket en arrière-plan pour une liste de produits.
    Appelé au démarrage de l'app pour alimenter le cache.
    """
    def _fetch_all():
        for name in product_names:
            now = time.time()
            with _bm_cache_lock:
                ts = _bm_cache_ts.get(name, 0)
                already_fresh = now - ts < BM_CACHE_TTL and name in _bm_price_cache
            if not already_fresh:
                scrape_backmarket_price(name)
                time.sleep(random.uniform(1.0, 2.0))  # respectueux du serveur

    t = threading.Thread(target=_fetch_all, daemon=True)
    t.start()
    return t


def get_ref_price(product_name: str):
    """
    Retourne le prix de référence pour un produit.
    - Pour les produits du catalogue BackMarket : prix live (avec fallback sur le cache)
    - Pour les produits fixes : valeur codée
    Retourne aussi la source du prix ('live' | 'fixed' | 'fallback')
    """
    if product_name in BACKMARKET_CATALOG:
        live = scrape_backmarket_price(product_name)
        if live:
            return live, 'live'
        # Fallback : dernière valeur connue en cache même expirée
        with _bm_cache_lock:
            cached = _bm_price_cache.get(product_name)
        if cached:
            return cached, 'fallback'
        # Fallback absolu : prix estimés de secours (jamais affichés sans label)
        _emergency = {
            'iphone 16 pro': 950, 'iphone 16': 720, 'iphone 15 pro': 820,
            'iphone 15': 580, 'iphone 14 pro': 600, 'iphone 14': 430,
            'iphone 13 pro': 480, 'iphone 13': 310, 'iphone 12': 210,
            'iphone 11': 150, 'iphone xr': 110, 'iphone xs': 120,
            'iphone x': 95, 'iphone se': 130,
            'samsung galaxy s24 ultra': 900, 'samsung galaxy s24': 530,
            'samsung galaxy s23': 360, 'samsung galaxy s22': 240,
            'google pixel 8 pro': 550, 'google pixel 8': 380,
            'macbook pro m3': 1600, 'macbook pro m2': 1200, 'macbook pro m1': 900,
            'macbook air m2': 850, 'macbook air m1': 620, 'imac m1': 1000,
            'ipad pro': 700, 'ipad air': 450, 'ipad': 250,
            'ps5': 380, 'ps4 pro': 180, 'ps4': 130,
            'xbox series x': 350, 'xbox series s': 180,
            'nintendo switch oled': 230, 'nintendo switch': 160, 'steam deck': 360,
            'airpods pro 2': 160, 'airpods pro': 120,
            'sony wh-1000xm5': 240, 'sony wh-1000xm4': 160, 'bose qc45': 200,
            'dyson v15': 420, 'dyson v12': 330, 'dyson v11': 260,
            'dyson v10': 190, 'dyson airwrap': 380,
            'apple watch ultra': 650, 'apple watch series 9': 300, 'apple watch series 8': 230,
        }
        return _emergency.get(product_name, 0), 'fallback'

    if product_name in FIXED_PRICES:
        return FIXED_PRICES[product_name]['ref_price'], 'fixed'

    return 0, 'unknown'


# ─────────────────────────────────────────────────────────────────────────────
# DÉTECTION D'OBJETS + CALCUL DU DEAL
# ─────────────────────────────────────────────────────────────────────────────

# Base de tous les objets connus (BM + fixes)
ALL_OBJECTS = {}
for name, data in BACKMARKET_CATALOG.items():
    ALL_OBJECTS[name] = data
for name, data in FIXED_PRICES.items():
    ALL_OBJECTS[name] = data


def detect_value_objects(title, description=''):
    """Détecte les objets de valeur dans un texte, même caché dans un lot."""
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
                detected.append({
                    'name': obj_name,
                    'ref_price': ref_price,
                    'price_source': price_source,
                    'category': obj_data['category'],
                    'confidence': score
                })
                seen.add(obj_name)
                continue

        kw_matches = sum(1 for kw in obj_data['keywords'] if kw.lower() in full_text)
        if kw_matches >= 2:
            ref_price, price_source = get_ref_price(obj_name)
            if ref_price > 0:
                detected.append({
                    'name': obj_name,
                    'ref_price': ref_price,
                    'price_source': price_source,
                    'category': obj_data['category'],
                    'confidence': min(60 + kw_matches * 10, 90)
                })
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
# SCRAPING DES PLATEFORMES
# ─────────────────────────────────────────────────────────────────────────────

class DealScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(get_headers())
        # Précharge les prix BM en arrière-plan au démarrage
        print('[BackMarket] Chargement des prix en arrière-plan...')
        prefetch_backmarket_prices(list(BACKMARKET_CATALOG.keys())[:20])

    def scrape_leboncoin(self, query, max_results=30):
        results = []
        try:
            url = f'https://www.leboncoin.fr/recherche?text={requests.utils.quote(query)}&sort=time'
            resp = self.session.get(url, headers=get_headers(), timeout=15)
            delay()
            soup = BeautifulSoup(resp.text, 'html5lib')
            listings = (
                soup.select('[data-test-id="ad"]') or
                soup.select('article[class*="styles_adCard"]') or
                soup.select('article') or
                soup.select('li[class*="aditem"]')
            )
            for item in listings[:max_results]:
                try:
                    title_el = (
                        item.select_one('[class*="title"]') or
                        item.select_one('[class*="Title"]') or
                        item.find(['h2', 'h3', 'p'])
                    )
                    price_el = (
                        item.select_one('[class*="price"]') or
                        item.select_one('[class*="Price"]') or
                        item.find(string=re.compile(r'\d+\s*€'))
                    )
                    link_el = item if item.name == 'a' else item.find('a')
                    img_el = item.find('img')
                    title = title_el.get_text(strip=True) if title_el else ''
                    price_text = price_el.get_text(strip=True) if hasattr(price_el, 'get_text') else str(price_el or '')
                    price = extract_price(price_text)
                    href = link_el.get('href', '') if link_el else ''
                    link = ('https://www.leboncoin.fr' + href) if href.startswith('/') else href
                    img = img_el.get('src') or img_el.get('data-src', '') if img_el else ''
                    if title and price and 1 < price < 50000:
                        results.append({
                            'title': title, 'price': price, 'price_str': f'{price}€',
                            'link': link, 'image': img,
                            'platform': 'LeBonCoin', 'platform_color': '#F56B2A'
                        })
                except Exception:
                    continue
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
            listings = (
                soup.select('[data-testid="grid-item"]') or
                soup.select('.feed-grid__item') or
                soup.select('[class*="ItemBox"]') or
                soup.select('[class*="item-box"]')
            )
            for item in listings[:max_results]:
                try:
                    title_el = (
                        item.select_one('[class*="title"]') or
                        item.select_one('[class*="name"]') or
                        item.find(['h2', 'h3', 'p'])
                    )
                    price_el = item.select_one('[class*="price"]') or item.find(string=re.compile(r'\d'))
                    link_el = item.find('a')
                    img_el = item.find('img')
                    title = title_el.get_text(strip=True) if title_el else ''
                    price_text = price_el.get_text(strip=True) if hasattr(price_el, 'get_text') else str(price_el or '')
                    price = extract_price(price_text)
                    href = link_el.get('href', '') if link_el else ''
                    link = ('https://www.vinted.fr' + href) if href.startswith('/') else href
                    img = img_el.get('src') or img_el.get('data-src', '') if img_el else ''
                    if title and price and 1 < price < 50000:
                        results.append({
                            'title': title, 'price': price, 'price_str': f'{price}€',
                            'link': link, 'image': img,
                            'platform': 'Vinted', 'platform_color': '#09B1BA'
                        })
                except Exception:
                    continue
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
            listings = soup.select('.s-item') or soup.select('[class*="s-item"]')
            for item in listings[:max_results]:
                try:
                    title_el = item.select_one('.s-item__title') or item.select_one('[class*="title"]')
                    price_el = item.select_one('.s-item__price') or item.select_one('[class*="price"]')
                    link_el = item.select_one('a.s-item__link') or item.find('a')
                    img_el = item.find('img')
                    title = title_el.get_text(strip=True) if title_el else ''
                    price_text = price_el.get_text(strip=True) if price_el else ''
                    price = extract_price(price_text)
                    link = link_el.get('href', '') if link_el else ''
                    img = img_el.get('src') or img_el.get('data-src', '') if img_el else ''
                    if 'Shop on eBay' in title or not title or not price:
                        continue
                    if 1 < price < 50000:
                        results.append({
                            'title': title, 'price': price, 'price_str': f'{price}€',
                            'link': link, 'image': img,
                            'platform': 'eBay', 'platform_color': '#E53238'
                        })
                except Exception:
                    continue
        except Exception as e:
            print(f'[eBay] Erreur: {e}')
        return results

    def analyze_listings(self, listings, min_discount=40):
        deals = []
        for item in listings:
            title = item.get('title', '')
            price = item.get('price')
            if not price:
                continue
            detected_objects, is_lot = detect_value_objects(title)
            if not detected_objects:
                continue
            best_obj = max(detected_objects, key=lambda x: x['ref_price'])
            discount_pct, score = calculate_deal_score(
                price, best_obj['ref_price'], is_lot, len(detected_objects)
            )
            if discount_pct >= min_discount:
                deals.append({
                    **item,
                    'detected_objects': detected_objects,
                    'best_match': best_obj['name'],
                    'ref_price': best_obj['ref_price'],
                    'price_source': best_obj.get('price_source', 'fixed'),
                    'category': best_obj['category'],
                    'discount_pct': discount_pct,
                    'deal_score': score,
                    'is_lot': is_lot,
                    'savings': round(best_obj['ref_price'] - price, 2)
                })
        deals.sort(key=lambda x: x['deal_score'], reverse=True)
        return deals

    def search_deals(self, keywords, min_discount=40, platforms=None):
        if platforms is None:
            platforms = ['leboncoin', 'vinted', 'ebay']
        all_listings = []
        if 'leboncoin' in platforms:
            all_listings += self.scrape_leboncoin(keywords)
        if 'vinted' in platforms:
            all_listings += self.scrape_vinted(keywords)
        if 'ebay' in platforms:
            all_listings += self.scrape_ebay(keywords)
        deals = self.analyze_listings(all_listings, min_discount)
        return {'deals': deals, 'total_scanned': len(all_listings), 'total_deals': len(deals), 'query': keywords}

    def auto_hunt(self, min_discount=50, platforms=None):
        if platforms is None:
            platforms = ['leboncoin', 'vinted', 'ebay']
        hunt_queries = [
            'lot electronique', 'lot telephone', 'iphone occasion',
            'montre collection', 'lot carte pokemon', 'lego boite',
            'dyson aspirateur', 'lot divers vrac'
        ]
        all_listings = []
        for query in hunt_queries[:6]:
            if 'leboncoin' in platforms:
                all_listings += self.scrape_leboncoin(query, max_results=15)
            if 'ebay' in platforms:
                all_listings += self.scrape_ebay(query, max_results=15)
            time.sleep(random.uniform(0.8, 1.5))
        seen = set()
        unique = []
        for item in all_listings:
            link = item.get('link', '')
            if link and link not in seen:
                seen.add(link)
                unique.append(item)
        deals = self.analyze_listings(unique, min_discount)
        return {'deals': deals, 'total_scanned': len(unique), 'total_deals': len(deals), 'query': 'Auto Hunt'}

    def get_value_categories(self):
        cats = {}
        for obj_name, obj_data in ALL_OBJECTS.items():
            cat = obj_data['category']
            if cat not in cats:
                cats[cat] = []
            ref, src = get_ref_price(obj_name)
            cats[cat].append({'name': obj_name, 'ref_price': ref, 'price_source': src})
        return cats

    def get_cache_status(self):
        """Retourne l'état du cache BackMarket pour l'affichage dans l'UI."""
        now = time.time()
        with _bm_cache_lock:
            cached = [
                {
                    'name': k,
                    'price': _bm_price_cache[k],
                    'age_min': round((now - _bm_cache_ts[k]) / 60, 1)
                }
                for k in _bm_price_cache
            ]
        cached.sort(key=lambda x: x['name'])
        return {'cached_count': len(cached), 'items': cached}
