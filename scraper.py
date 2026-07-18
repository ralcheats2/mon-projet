import requests
from bs4 import BeautifulSoup
import re
import time
import random
from thefuzz import fuzz

# ─────────────────────────────────────────────────────────────────────────────
# Prix de référence alignés sur BackMarket.fr (juillet 2026)
# Règle : on prend le prix "Bon état" de BackMarket comme référence marché
# pour l'occasion, ce qui est la vraie concurrence des annonces LBC/Vinted/eBay
# ─────────────────────────────────────────────────────────────────────────────
VALUE_OBJECTS = {

    # ── Téléphones ──────────────────────────────────────────────────────────
    # BackMarket FR "Bon état" juillet 2026
    'iphone 16 pro': {'ref_price': 950,  'keywords': ['iphone', '16 pro', 'apple'],                     'category': '📱 Téléphones'},
    'iphone 16':     {'ref_price': 720,  'keywords': ['iphone', '16', 'apple'],                          'category': '📱 Téléphones'},
    'iphone 15 pro': {'ref_price': 820,  'keywords': ['iphone', '15 pro', 'apple'],                     'category': '📱 Téléphones'},
    'iphone 15':     {'ref_price': 580,  'keywords': ['iphone', '15', 'apple'],                          'category': '📱 Téléphones'},
    'iphone 14 pro': {'ref_price': 600,  'keywords': ['iphone', '14 pro', 'apple'],                     'category': '📱 Téléphones'},
    'iphone 14':     {'ref_price': 430,  'keywords': ['iphone', '14', 'apple'],                          'category': '📱 Téléphones'},
    'iphone 13 pro': {'ref_price': 480,  'keywords': ['iphone', '13 pro', 'apple'],                     'category': '📱 Téléphones'},
    'iphone 13':     {'ref_price': 310,  'keywords': ['iphone', '13', 'apple'],                          'category': '📱 Téléphones'},
    'iphone 12':     {'ref_price': 210,  'keywords': ['iphone', '12', 'apple'],                          'category': '📱 Téléphones'},
    'iphone 11':     {'ref_price': 150,  'keywords': ['iphone', '11', 'apple'],                          'category': '📱 Téléphones'},
    'iphone xr':     {'ref_price': 110,  'keywords': ['iphone', 'xr', 'apple'],                          'category': '📱 Téléphones'},
    'iphone xs':     {'ref_price': 120,  'keywords': ['iphone', 'xs', 'apple'],                          'category': '📱 Téléphones'},
    'iphone x':      {'ref_price': 95,   'keywords': ['iphone', ' x ', 'apple'],                         'category': '📱 Téléphones'},
    'iphone se':     {'ref_price': 130,  'keywords': ['iphone', 'se', 'apple'],                          'category': '📱 Téléphones'},
    'samsung galaxy s24 ultra': {'ref_price': 900, 'keywords': ['samsung', 'galaxy', 's24', 'ultra'],   'category': '📱 Téléphones'},
    'samsung galaxy s24': {'ref_price': 530,  'keywords': ['samsung', 'galaxy', 's24'],                  'category': '📱 Téléphones'},
    'samsung galaxy s23': {'ref_price': 360,  'keywords': ['samsung', 'galaxy', 's23'],                  'category': '📱 Téléphones'},
    'samsung galaxy s22': {'ref_price': 240,  'keywords': ['samsung', 'galaxy', 's22'],                  'category': '📱 Téléphones'},
    'google pixel 8 pro': {'ref_price': 550,  'keywords': ['pixel', '8 pro', 'google'],                  'category': '📱 Téléphones'},
    'google pixel 8':     {'ref_price': 380,  'keywords': ['pixel', '8', 'google'],                      'category': '📱 Téléphones'},
    'oneplus 12':    {'ref_price': 380,  'keywords': ['oneplus', '12', 'one plus'],                      'category': '📱 Téléphones'},

    # ── Ordinateurs ─────────────────────────────────────────────────────────
    'macbook pro m3': {'ref_price': 1600, 'keywords': ['macbook', 'pro', 'm3', 'apple'],                 'category': '💻 Ordinateurs'},
    'macbook pro m2': {'ref_price': 1200, 'keywords': ['macbook', 'pro', 'm2', 'apple'],                 'category': '💻 Ordinateurs'},
    'macbook pro m1': {'ref_price': 900,  'keywords': ['macbook', 'pro', 'm1', 'apple'],                 'category': '💻 Ordinateurs'},
    'macbook air m2': {'ref_price': 850,  'keywords': ['macbook', 'air', 'm2', 'apple'],                 'category': '💻 Ordinateurs'},
    'macbook air m1': {'ref_price': 620,  'keywords': ['macbook', 'air', 'm1', 'apple'],                 'category': '💻 Ordinateurs'},
    'imac m1':        {'ref_price': 1000, 'keywords': ['imac', 'm1', 'apple'],                           'category': '💻 Ordinateurs'},
    'dell xps':       {'ref_price': 700,  'keywords': ['dell', 'xps', 'laptop'],                         'category': '💻 Ordinateurs'},
    'thinkpad x1':    {'ref_price': 550,  'keywords': ['thinkpad', 'x1', 'lenovo'],                      'category': '💻 Ordinateurs'},

    # ── Tablettes ────────────────────────────────────────────────────────────
    'ipad pro m2':    {'ref_price': 750,  'keywords': ['ipad', 'pro', 'm2', 'apple'],                    'category': '📱 Tablettes'},
    'ipad pro m1':    {'ref_price': 580,  'keywords': ['ipad', 'pro', 'm1', 'apple'],                    'category': '📱 Tablettes'},
    'ipad air m1':    {'ref_price': 450,  'keywords': ['ipad', 'air', 'm1', 'apple'],                    'category': '📱 Tablettes'},
    'ipad':           {'ref_price': 250,  'keywords': ['ipad', 'apple', 'tablette'],                     'category': '📱 Tablettes'},
    'samsung galaxy tab s9': {'ref_price': 500, 'keywords': ['samsung', 'galaxy tab', 's9'],             'category': '📱 Tablettes'},

    # ── Gaming ───────────────────────────────────────────────────────────────
    'ps5':                 {'ref_price': 380,  'keywords': ['ps5', 'playstation 5', 'sony'],             'category': '🎮 Gaming'},
    'ps4 pro':             {'ref_price': 180,  'keywords': ['ps4 pro', 'playstation 4 pro', 'sony'],     'category': '🎮 Gaming'},
    'ps4':                 {'ref_price': 130,  'keywords': ['ps4', 'playstation 4', 'sony'],             'category': '🎮 Gaming'},
    'xbox series x':       {'ref_price': 350,  'keywords': ['xbox', 'series x', 'microsoft'],           'category': '🎮 Gaming'},
    'xbox series s':       {'ref_price': 180,  'keywords': ['xbox', 'series s', 'microsoft'],           'category': '🎮 Gaming'},
    'nintendo switch oled':{'ref_price': 230,  'keywords': ['switch', 'oled', 'nintendo'],              'category': '🎮 Gaming'},
    'nintendo switch':     {'ref_price': 160,  'keywords': ['switch', 'nintendo', 'console'],           'category': '🎮 Gaming'},
    'steam deck':          {'ref_price': 360,  'keywords': ['steam deck', 'valve', 'gaming'],           'category': '🎮 Gaming'},

    # ── Audio ────────────────────────────────────────────────────────────────
    'airpods pro 2':   {'ref_price': 160,  'keywords': ['airpods', 'pro', 'apple', 'ecouteurs'],         'category': '🎧 Audio'},
    'airpods pro':     {'ref_price': 120,  'keywords': ['airpods', 'apple', 'ecouteurs'],                'category': '🎧 Audio'},
    'sony wh-1000xm5': {'ref_price': 240,  'keywords': ['sony', 'wh1000xm5', 'xm5', 'casque'],         'category': '🎧 Audio'},
    'sony wh-1000xm4': {'ref_price': 160,  'keywords': ['sony', 'wh1000xm4', 'xm4', 'casque'],         'category': '🎧 Audio'},
    'bose qc45':       {'ref_price': 200,  'keywords': ['bose', 'qc45', 'quietcomfort', 'casque'],      'category': '🎧 Audio'},

    # ── Photo / Vidéo ─────────────────────────────────────────────────────────
    'gopro hero 12':   {'ref_price': 280,  'keywords': ['gopro', 'hero 12', 'action cam'],              'category': '📷 Photo/Vidéo'},
    'gopro hero 11':   {'ref_price': 200,  'keywords': ['gopro', 'hero 11', 'action cam'],              'category': '📷 Photo/Vidéo'},
    'canon eos r':     {'ref_price': 900,  'keywords': ['canon', 'eos r', 'hybride', 'reflex'],         'category': '📷 Photo/Vidéo'},
    'canon eos':       {'ref_price': 550,  'keywords': ['canon', 'eos', 'reflex', 'appareil'],          'category': '📷 Photo/Vidéo'},
    'sony alpha a7':   {'ref_price': 1200, 'keywords': ['sony', 'alpha', 'a7', 'hybride'],              'category': '📷 Photo/Vidéo'},
    'sony alpha a6':   {'ref_price': 500,  'keywords': ['sony', 'alpha', 'a6', 'hybride'],              'category': '📷 Photo/Vidéo'},
    'fujifilm x-t':    {'ref_price': 600,  'keywords': ['fujifilm', 'fuji', 'x-t', 'hybride'],         'category': '📷 Photo/Vidéo'},
    'leica':           {'ref_price': 2500, 'keywords': ['leica', 'm10', 'q2', 'appareil'],              'category': '📷 Photo/Vidéo'},
    'drone dji':       {'ref_price': 400,  'keywords': ['dji', 'drone', 'mini', 'mavic'],               'category': '📷 Photo/Vidéo'},

    # ── Électroménager ────────────────────────────────────────────────────────
    'dyson v15':       {'ref_price': 420,  'keywords': ['dyson', 'v15', 'aspirateur'],                  'category': '🏠 Électroménager'},
    'dyson v12':       {'ref_price': 330,  'keywords': ['dyson', 'v12', 'aspirateur'],                  'category': '🏠 Électroménager'},
    'dyson v11':       {'ref_price': 260,  'keywords': ['dyson', 'v11', 'aspirateur'],                  'category': '🏠 Électroménager'},
    'dyson v10':       {'ref_price': 190,  'keywords': ['dyson', 'v10', 'aspirateur'],                  'category': '🏠 Électroménager'},
    'dyson airwrap':   {'ref_price': 380,  'keywords': ['dyson', 'airwrap', 'coiffure'],                'category': '🏠 Électroménager'},
    'thermomix tm6':   {'ref_price': 900,  'keywords': ['thermomix', 'tm6', 'vorwerk'],                 'category': '🏠 Électroménager'},
    'thermomix tm5':   {'ref_price': 600,  'keywords': ['thermomix', 'tm5', 'vorwerk'],                 'category': '🏠 Électroménager'},
    'robot cooking':   {'ref_price': 200,  'keywords': ['monsieur cuisine', 'cooking chef', 'robot'],   'category': '🏠 Électroménager'},
    'roomba':          {'ref_price': 180,  'keywords': ['roomba', 'irobot', 'aspirateur robot'],        'category': '🏠 Électroménager'},

    # ── Montres ───────────────────────────────────────────────────────────────
    'rolex submariner':{'ref_price': 9000,  'keywords': ['rolex', 'submariner'],                        'category': '⌚ Montres'},
    'rolex datejust':  {'ref_price': 6500,  'keywords': ['rolex', 'datejust'],                          'category': '⌚ Montres'},
    'rolex':           {'ref_price': 7000,  'keywords': ['rolex', 'montre', 'oyster'],                  'category': '⌚ Montres'},
    'omega seamaster': {'ref_price': 2800,  'keywords': ['omega', 'seamaster'],                         'category': '⌚ Montres'},
    'omega speedmaster':{'ref_price': 3500, 'keywords': ['omega', 'speedmaster'],                       'category': '⌚ Montres'},
    'tag heuer':       {'ref_price': 1200,  'keywords': ['tag heuer', 'heuer', 'carrera'],              'category': '⌚ Montres'},
    'breitling':       {'ref_price': 2500,  'keywords': ['breitling', 'navitimer', 'montre'],           'category': '⌚ Montres'},
    'seiko':           {'ref_price': 150,   'keywords': ['seiko', 'srpd', 'skx', 'montre'],             'category': '⌚ Montres'},
    'casio g-shock':   {'ref_price': 80,    'keywords': ['casio', 'g-shock', 'gshock'],                 'category': '⌚ Montres'},
    'apple watch ultra':{'ref_price': 650,  'keywords': ['apple watch', 'ultra'],                       'category': '⌚ Montres'},
    'apple watch s9':  {'ref_price': 300,   'keywords': ['apple watch', 'series 9', 'watch'],           'category': '⌚ Montres'},
    'apple watch s8':  {'ref_price': 230,   'keywords': ['apple watch', 'series 8', 'watch'],           'category': '⌚ Montres'},

    # ── Luxe / Mode ──────────────────────────────────────────────────────────
    'louis vuitton neverfull': {'ref_price': 900,  'keywords': ['louis vuitton', 'neverfull', 'lv'],    'category': '👜 Luxe/Mode'},
    'louis vuitton speedy':    {'ref_price': 600,  'keywords': ['louis vuitton', 'speedy', 'lv'],       'category': '👜 Luxe/Mode'},
    'louis vuitton':   {'ref_price': 700,  'keywords': ['louis vuitton', 'vuitton', 'lv', 'sac'],      'category': '👜 Luxe/Mode'},
    'chanel classic':  {'ref_price': 5000, 'keywords': ['chanel', 'classic flap', 'sac'],               'category': '👜 Luxe/Mode'},
    'chanel':          {'ref_price': 2000, 'keywords': ['chanel', 'sac', 'cc', 'cambon'],               'category': '👜 Luxe/Mode'},
    'hermes birkin':   {'ref_price': 8000, 'keywords': ['hermes', 'birkin'],                            'category': '👜 Luxe/Mode'},
    'hermes kelly':    {'ref_price': 6000, 'keywords': ['hermes', 'kelly'],                             'category': '👜 Luxe/Mode'},
    'hermes':          {'ref_price': 3000, 'keywords': ['hermes', 'hermès', 'sac'],                     'category': '👜 Luxe/Mode'},
    'gucci':           {'ref_price': 500,  'keywords': ['gucci', 'sac', 'ceinture'],                    'category': '👜 Luxe/Mode'},
    'dior':            {'ref_price': 800,  'keywords': ['dior', 'sac', 'christian dior'],               'category': '👜 Luxe/Mode'},

    # ── Sneakers ─────────────────────────────────────────────────────────────
    'yeezy 350':       {'ref_price': 220,  'keywords': ['yeezy', '350', 'adidas', 'boost'],             'category': '👟 Sneakers'},
    'yeezy':           {'ref_price': 200,  'keywords': ['yeezy', 'adidas', 'foam runner'],              'category': '👟 Sneakers'},
    'jordan 1 retro':  {'ref_price': 170,  'keywords': ['jordan 1', 'air jordan', 'aj1'],               'category': '👟 Sneakers'},
    'jordan 4':        {'ref_price': 200,  'keywords': ['jordan 4', 'air jordan 4', 'aj4'],             'category': '👟 Sneakers'},
    'nike dunk':       {'ref_price': 110,  'keywords': ['nike', 'dunk', 'sb dunk'],                     'category': '👟 Sneakers'},
    'new balance 550': {'ref_price': 120,  'keywords': ['new balance', '550', 'nb550'],                 'category': '👟 Sneakers'},
    'asics gel-lyte':  {'ref_price': 90,   'keywords': ['asics', 'gel-lyte', 'gellyte'],                'category': '👟 Sneakers'},

    # ── Cartes / Jeux ────────────────────────────────────────────────────────
    'carte pokemon charizard': {'ref_price': 200, 'keywords': ['pokemon', 'charizard', 'carte'],        'category': '🃏 Cartes/Jeux'},
    'pokemon lot':     {'ref_price': 80,   'keywords': ['pokemon', 'cartes', 'lot', 'collection'],      'category': '🃏 Cartes/Jeux'},
    'one piece carte': {'ref_price': 60,   'keywords': ['one piece', 'carte', 'jcc'],                   'category': '🃏 Cartes/Jeux'},
    'magic gathering': {'ref_price': 100,  'keywords': ['magic', 'gathering', 'mtg', 'cartes'],         'category': '🃏 Cartes/Jeux'},

    # ── LEGO ─────────────────────────────────────────────────────────────────
    'lego technic':    {'ref_price': 180,  'keywords': ['lego', 'technic'],                             'category': '🧱 LEGO'},
    'lego star wars':  {'ref_price': 200,  'keywords': ['lego', 'star wars'],                           'category': '🧱 LEGO'},
    'lego creator':    {'ref_price': 150,  'keywords': ['lego', 'creator', 'expert'],                   'category': '🧱 LEGO'},
    'lego':            {'ref_price': 100,  'keywords': ['lego', 'boite', 'set', 'pieces'],              'category': '🧱 LEGO'},

    # ── Vinyles ───────────────────────────────────────────────────────────────
    'vinyle':          {'ref_price': 40,   'keywords': ['vinyle', 'vinyl', 'disque', '33t', '45t'],     'category': '🎵 Vinyles'},
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

def get_headers():
    return random.choice(HEADERS_POOL)

def delay():
    time.sleep(random.uniform(1.5, 3.0))

def extract_price(text):
    if not text:
        return None
    text = text.replace('\xa0', '').replace('\u202f', '').replace(' ', '').replace(',', '.')
    match = re.search(r'([\d]+\.?[\d]*)', text)
    if match:
        try:
            val = float(match.group(1))
            return val if val > 0 else None
        except Exception:
            return None
    return None

def detect_value_objects(title, description=''):
    """Détecte les objets de valeur dans un texte, même caché dans un lot."""
    full_text = (title + ' ' + description).lower()
    detected = []
    seen = set()

    for obj_name, obj_data in VALUE_OBJECTS.items():
        if obj_name in seen:
            continue

        # 1. Fuzzy matching sur le nom complet
        score = fuzz.partial_ratio(obj_name.lower(), full_text)
        if score >= 78:
            detected.append({
                'name': obj_name,
                'ref_price': obj_data['ref_price'],
                'category': obj_data['category'],
                'confidence': score
            })
            seen.add(obj_name)
            continue

        # 2. Multi-keywords : 2 correspondances minimum
        kw_matches = sum(1 for kw in obj_data['keywords'] if kw.lower() in full_text)
        if kw_matches >= 2:
            detected.append({
                'name': obj_name,
                'ref_price': obj_data['ref_price'],
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


class DealScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(get_headers())

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
            'jordan yeezy sneakers', 'dyson aspirateur', 'lot divers vrac'
        ]
        all_listings = []
        for query in hunt_queries[:6]:
            if 'leboncoin' in platforms:
                all_listings += self.scrape_leboncoin(query, max_results=15)
            if 'ebay' in platforms:
                all_listings += self.scrape_ebay(query, max_results=15)
            time.sleep(random.uniform(0.8, 1.5))
        # Déduplication par lien
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
        for obj_name, obj_data in VALUE_OBJECTS.items():
            cat = obj_data['category']
            if cat not in cats:
                cats[cat] = []
            cats[cat].append({'name': obj_name, 'ref_price': obj_data['ref_price']})
        return cats
