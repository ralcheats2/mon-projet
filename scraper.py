import requests
from bs4 import BeautifulSoup
import re
import time
import random
from thefuzz import fuzz

# ─── Base de données des objets de valeur avec prix de référence ───
VALUE_OBJECTS = {
    # Electronique
    'iphone 15 pro': {'ref_price': 1100, 'keywords': ['iphone', 'apple', 'smartphone', '15 pro'], 'category': '📱 Téléphones'},
    'iphone 14': {'ref_price': 750, 'keywords': ['iphone', 'apple', '14'], 'category': '📱 Téléphones'},
    'iphone 13': {'ref_price': 580, 'keywords': ['iphone', 'apple', '13'], 'category': '📱 Téléphones'},
    'samsung galaxy s24': {'ref_price': 900, 'keywords': ['samsung', 'galaxy', 's24'], 'category': '📱 Téléphones'},
    'samsung galaxy s23': {'ref_price': 700, 'keywords': ['samsung', 'galaxy', 's23'], 'category': '📱 Téléphones'},
    'macbook pro': {'ref_price': 1800, 'keywords': ['macbook', 'pro', 'apple', 'mac'], 'category': '💻 Ordinateurs'},
    'macbook air m2': {'ref_price': 1200, 'keywords': ['macbook', 'air', 'm2', 'apple'], 'category': '💻 Ordinateurs'},
    'ipad pro': {'ref_price': 900, 'keywords': ['ipad', 'apple', 'tablette'], 'category': '📱 Tablettes'},
    'ps5': {'ref_price': 500, 'keywords': ['ps5', 'playstation', 'sony', 'console'], 'category': '🎮 Gaming'},
    'xbox series x': {'ref_price': 500, 'keywords': ['xbox', 'series', 'microsoft', 'console'], 'category': '🎮 Gaming'},
    'nintendo switch oled': {'ref_price': 320, 'keywords': ['switch', 'nintendo', 'oled', 'console'], 'category': '🎮 Gaming'},
    'airpods pro': {'ref_price': 250, 'keywords': ['airpods', 'apple', 'ecouteurs'], 'category': '🎧 Audio'},
    'sony wh-1000xm5': {'ref_price': 350, 'keywords': ['sony', 'wh1000', 'casque', 'xm5'], 'category': '🎧 Audio'},
    'gopro hero': {'ref_price': 400, 'keywords': ['gopro', 'hero', 'camera', 'action'], 'category': '📷 Photo/Vidéo'},
    'dyson v15': {'ref_price': 700, 'keywords': ['dyson', 'aspirateur', 'v15', 'v12'], 'category': '🏠 Electroménager'},
    'dyson airwrap': {'ref_price': 550, 'keywords': ['dyson', 'airwrap', 'cheveux'], 'category': '🏠 Electroménager'},
    'thermomix': {'ref_price': 1200, 'keywords': ['thermomix', 'vorwerk', 'tm6', 'tm5'], 'category': '🏠 Electroménager'},
    'rolex': {'ref_price': 8000, 'keywords': ['rolex', 'montre', 'oyster', 'datejust', 'submariner'], 'category': '⌚ Montres'},
    'omega': {'ref_price': 3000, 'keywords': ['omega', 'seamaster', 'speedmaster', 'montre'], 'category': '⌚ Montres'},
    'tag heuer': {'ref_price': 1500, 'keywords': ['tag heuer', 'heuer', 'carrera', 'montre'], 'category': '⌚ Montres'},
    'casio g-shock': {'ref_price': 150, 'keywords': ['casio', 'gshock', 'g-shock', 'montre'], 'category': '⌚ Montres'},
    'louis vuitton': {'ref_price': 1000, 'keywords': ['louis vuitton', 'vuitton', 'lv', 'sac'], 'category': '👜 Luxe/Mode'},
    'chanel': {'ref_price': 2000, 'keywords': ['chanel', 'sac', 'cc'], 'category': '👜 Luxe/Mode'},
    'hermes': {'ref_price': 5000, 'keywords': ['hermes', 'hermes', 'birkin', 'kelly'], 'category': '👜 Luxe/Mode'},
    'yeezy': {'ref_price': 350, 'keywords': ['yeezy', 'adidas', 'boost', 'foam'], 'category': '👟 Sneakers'},
    'jordan 1': {'ref_price': 200, 'keywords': ['jordan', 'nike', 'aj1', 'air jordan'], 'category': '👟 Sneakers'},
    'nike dunk': {'ref_price': 150, 'keywords': ['nike', 'dunk', 'sb'], 'category': '👟 Sneakers'},
    'pokemon carte': {'ref_price': 100, 'keywords': ['pokemon', 'carte', 'charizard', 'pikachu', 'lot'], 'category': '🃏 Cartes/Jeux'},
    'lego': {'ref_price': 200, 'keywords': ['lego', 'technic', 'star wars', 'creator', 'set'], 'category': '🧱 LEGO'},
    'vinyle': {'ref_price': 50, 'keywords': ['vinyle', 'vinyl', 'disque', '33t', '45t'], 'category': '🎵 Vinyles'},
    'canon eos': {'ref_price': 1500, 'keywords': ['canon', 'eos', 'appareil', 'reflex', 'hybride'], 'category': '📷 Photo/Vidéo'},
    'sony alpha': {'ref_price': 2000, 'keywords': ['sony', 'alpha', 'a7', 'a6', 'appareil'], 'category': '📷 Photo/Vidéo'},
    'leica': {'ref_price': 3000, 'keywords': ['leica', 'appareil', 'm10', 'q2'], 'category': '📷 Photo/Vidéo'},
}

LOT_TRIGGER_WORDS = ['lot', 'ensemble', 'vrac', 'collection', 'boite', 'caisse', 'sac', 'divers', 'melange', 'assortiment']

HEADERS_POOL = [
    {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'},
    {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0'},
    {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15'},
]

def get_headers():
    return random.choice(HEADERS_POOL)

def delay():
    time.sleep(random.uniform(1.2, 2.5))

def extract_price(text):
    if not text:
        return None
    text = text.replace('\xa0', '').replace('\u202f', '').replace(' ', '').replace(',', '.')
    match = re.search(r'([\d]+\.?[\d]*)', text)
    if match:
        try:
            val = float(match.group(1))
            return val if val > 0 else None
        except:
            return None
    return None

def detect_value_objects(title, description=''):
    """Détecte les objets de valeur dans un texte, même dans un lot"""
    full_text = (title + ' ' + description).lower()
    detected = []
    seen = set()

    for obj_name, obj_data in VALUE_OBJECTS.items():
        if obj_name in seen:
            continue

        # Fuzzy matching sur le nom complet
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

        # Vérif par mots-clés : 2 correspondances minimum
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
            resp = self.session.get(url, headers=get_headers(), timeout=12)
            delay()
            soup = BeautifulSoup(resp.text, 'html5lib')

            # Sélecteurs LBC (robustes multi-versions)
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

                    if title and price and price < 50000:
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
            resp = self.session.get(url, headers=get_headers(), timeout=12)
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

                    if title and price and price < 50000:
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
            resp = self.session.get(url, headers=get_headers(), timeout=12)
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
                    if price < 50000:
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
            time.sleep(random.uniform(0.5, 1.2))
        # Déduplication
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
