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

# ══════════════════════════════════════════════
#  MOTS QUI INDIQUENT QUE CE N'EST PAS L'OBJET LUI-MÊME
#  (pièces détachées, accessoires, coques, etc.)
# ══════════════════════════════════════════════
ACCESSORY_WORDS = [
    'batterie', 'battery', 'coque', 'case', 'vitre', 'écran cassé', 'screen crack',
    'chargeur', 'charger', 'câble', 'cable', 'adaptateur', 'pièce', 'piece',
    'réparation', 'reparation', 'facade', 'nappe', 'dock', 'connecteur',
    'protection', 'verre trempé', 'film', 'housse', 'etui', 'étui',
    'cover', 'skin', 'sticker', 'autocollant', 'stylet', 'stylus',
    'oreillette', 'écouteur', 'earbud', 'tip', 'embout',
    'hs', 'hors service', 'pour pièces', 'pour piece', 'pour pieces',
    'ne fonctionne pas', 'ne marche pas', 'cassé', 'casse', 'brisé', 'brise',
    'broken', 'defective', 'défectueux', 'defectueux',
    'manuel', 'mode emploi', 'notice', 'boite vide', 'empty box',
    'stand', 'support', 'bras', 'holder', 'mount',
]

# ══════════════════════════════════════════════
#  BASE DE DONNÉES DES OBJETS DE VALEUR
#  Chaque objet a : ref (prix marché), kw (mots-clés), cat,
#  context (mots qui CONFIRMENT que c'est bien l'objet),
#  variants (noms alternatifs reconnus)
# ══════════════════════════════════════════════
VALUE_OBJECTS = {
    # ── TÉLÉPHONES
    'iphone 15 pro': {'ref': 1100, 'cat': 'Téléphones',
        'kw': ['iphone','15 pro','apple'],
        'context': ['débloqué','reconditionné','128gb','256gb','occasion','vendu','fonctionne','état'],
        'variants': ['i phone 15pro','iphone15pro']},
    'iphone 14':     {'ref': 650,  'cat': 'Téléphones',
        'kw': ['iphone','14'],
        'context': ['débloqué','reconditionné','128gb','occasion','fonctionne','état'],
        'variants': ['iphone14','i phone 14']},
    'iphone 13':     {'ref': 480,  'cat': 'Téléphones',
        'kw': ['iphone','13'],
        'context': ['débloqué','reconditionné','occasion','fonctionne'],
        'variants': ['iphone13']},
    'iphone 12':     {'ref': 320,  'cat': 'Téléphones',
        'kw': ['iphone','12'],
        'context': ['débloqué','occasion','fonctionne'],
        'variants': ['iphone12']},
    'samsung s24':   {'ref': 850,  'cat': 'Téléphones',
        'kw': ['samsung','s24','galaxy'],
        'context': ['débloqué','occasion','fonctionne'],
        'variants': ['galaxy s24']},
    'samsung s23':   {'ref': 600,  'cat': 'Téléphones',
        'kw': ['samsung','s23','galaxy'],
        'context': ['débloqué','occasion'],
        'variants': ['galaxy s23']},

    # ── ORDINATEURS
    'macbook pro':   {'ref': 1800, 'cat': 'Ordinateurs',
        'kw': ['macbook','pro','apple'],
        'context': ['m1','m2','m3','intel','retina','occasion','fonctionnel'],
        'variants': ['mac book pro','mbp']},
    'macbook air':   {'ref': 1100, 'cat': 'Ordinateurs',
        'kw': ['macbook','air','apple'],
        'context': ['m1','m2','occasion','fonctionnel'],
        'variants': ['mac book air','mba']},
    'dell xps':      {'ref': 1200, 'cat': 'Ordinateurs',
        'kw': ['dell','xps'],
        'context': ['i7','i9','intel','occasion','fonctionnel'],
        'variants': ['dell xps 15','dell xps 13']},
    'thinkpad':      {'ref': 900,  'cat': 'Ordinateurs',
        'kw': ['lenovo','thinkpad'],
        'context': ['i7','i5','occasion','professionnel'],
        'variants': ['think pad','ibm thinkpad']},

    # ── GAMING
    'ps5':           {'ref': 500,  'cat': 'Gaming',
        'kw': ['ps5','playstation 5'],
        'context': ['console','manette','edition','slim','digital','disc','fonctionnel'],
        'variants': ['playstation5','ps 5']},
    'xbox series x': {'ref': 500,  'cat': 'Gaming',
        'kw': ['xbox','series x'],
        'context': ['console','microsoft','fonctionnel'],
        'variants': ['xbox seriesx']},
    'switch oled':   {'ref': 320,  'cat': 'Gaming',
        'kw': ['switch','nintendo','oled'],
        'context': ['console','jeu','fonctionnel'],
        'variants': ['nintendo switch oled']},
    'steam deck':    {'ref': 420,  'cat': 'Gaming',
        'kw': ['steam','deck','valve'],
        'context': ['portable','gaming','fonctionnel'],
        'variants': ['steamdeck']},

    # ── AUDIO
    'airpods pro':   {'ref': 230,  'cat': 'Audio',
        'kw': ['airpods','pro','apple'],
        'context': ['anc','noise','occasion','boite'],
        'variants': ['air pods pro']},
    'sony xm5':      {'ref': 330,  'cat': 'Audio',
        'kw': ['sony','xm5'],
        'context': ['casque','anc','occasion'],
        'variants': ['wh-1000xm5','xm 5']},
    'sony xm4':      {'ref': 220,  'cat': 'Audio',
        'kw': ['sony','xm4'],
        'context': ['casque','anc','occasion'],
        'variants': ['wh-1000xm4']},
    'bose qc45':     {'ref': 280,  'cat': 'Audio',
        'kw': ['bose','qc45','quietcomfort'],
        'context': ['casque','anc','occasion'],
        'variants': ['quiet comfort 45']},

    # ── PHOTO
    'gopro hero':    {'ref': 350,  'cat': 'Photo',
        'kw': ['gopro','hero'],
        'context': ['action','caméra','4k','occasion'],
        'variants': ['go pro hero']},
    'canon eos r':   {'ref': 1400, 'cat': 'Photo',
        'kw': ['canon','eos','r5','r6','r7'],
        'context': ['boitier','hybride','occasion','professionnel'],
        'variants': ['canon eos r5','canon eos r6']},
    'sony alpha':    {'ref': 1800, 'cat': 'Photo',
        'kw': ['sony','alpha','a7'],
        'context': ['boitier','hybride','occasion','professionnel'],
        'variants': ['sony a7','alpha 7']},
    'leica':         {'ref': 3000, 'cat': 'Photo',
        'kw': ['leica'],
        'context': ['appareil','boitier','occasion'],
        'variants': ['leica m10','leica q2']},
    'fujifilm x':    {'ref': 800,  'cat': 'Photo',
        'kw': ['fujifilm','fuji','xt','xpro','x100'],
        'context': ['boitier','hybride','occasion'],
        'variants': ['fuji x-t4','fujifilm x100']},

    # ── ÉLECTROMÉNAGER
    'dyson v15':     {'ref': 650,  'cat': 'Électroménager',
        'kw': ['dyson','v15'],
        'context': ['aspirateur','detect','fonctionnel','occasion'],
        'variants': ['dyson detect']},
    'dyson v11':     {'ref': 450,  'cat': 'Électroménager',
        'kw': ['dyson','v11'],
        'context': ['aspirateur','fonctionnel','occasion'],
        'variants': []},
    'dyson airwrap': {'ref': 500,  'cat': 'Électroménager',
        'kw': ['dyson','airwrap'],
        'context': ['coiffeur','coffret','fonctionnel'],
        'variants': ['air wrap']},
    'thermomix tm6': {'ref': 1200, 'cat': 'Électroménager',
        'kw': ['thermomix','tm6','vorwerk'],
        'context': ['robot','cuisine','fonctionnel'],
        'variants': ['tm 6']},
    'kenwood chef':  {'ref': 600,  'cat': 'Électroménager',
        'kw': ['kenwood','chef','titanium'],
        'context': ['robot','cuisine','fonctionnel'],
        'variants': ['kenwood titanium']},

    # ── MOBILIER BUREAU DE VALEUR (revendeurs qui ne savent pas)
    'herman miller aeron': {'ref': 1400, 'cat': 'Mobilier bureau',
        'kw': ['herman miller','aeron'],
        'context': ['chaise','fauteuil','ergonomique','bureau','occasion'],
        'variants': ['herman-miller aeron','hm aeron']},
    'herman miller embody': {'ref': 1600, 'cat': 'Mobilier bureau',
        'kw': ['herman miller','embody'],
        'context': ['chaise','fauteuil','ergonomique','bureau'],
        'variants': ['hm embody']},
    'herman miller mirra': {'ref': 700, 'cat': 'Mobilier bureau',
        'kw': ['herman miller','mirra'],
        'context': ['chaise','fauteuil','bureau'],
        'variants': ['hm mirra']},
    'steelcase leap': {'ref': 1100, 'cat': 'Mobilier bureau',
        'kw': ['steelcase','leap'],
        'context': ['chaise','fauteuil','ergonomique','bureau'],
        'variants': ['steel case leap','steelcase v2']},
    'steelcase think': {'ref': 900, 'cat': 'Mobilier bureau',
        'kw': ['steelcase','think'],
        'context': ['chaise','fauteuil','bureau'],
        'variants': []},
    'vitra eames':   {'ref': 800,  'cat': 'Mobilier bureau',
        'kw': ['vitra','eames'],
        'context': ['chaise','fauteuil','bureau','design','occasion'],
        'variants': ['eames chair','eames daw','eames dsr']},
    'vitra hal':     {'ref': 500,  'cat': 'Mobilier bureau',
        'kw': ['vitra','hal'],
        'context': ['chaise','bureau','design'],
        'variants': []},
    'knoll barcelona': {'ref': 2000, 'cat': 'Mobilier bureau',
        'kw': ['knoll','barcelona'],
        'context': ['fauteuil','chaise','design','occasion'],
        'variants': ['chaise barcelona','barcelona chair']},
    'knoll tulip':   {'ref': 700,  'cat': 'Mobilier bureau',
        'kw': ['knoll','saarinen','tulip'],
        'context': ['chaise','design','occasion'],
        'variants': ['tulip chair']},
    'humanscale freedom': {'ref': 800, 'cat': 'Mobilier bureau',
        'kw': ['humanscale','freedom'],
        'context': ['chaise','fauteuil','ergonomique','bureau'],
        'variants': []},
    'bureau assis debout': {'ref': 900, 'cat': 'Mobilier bureau',
        'kw': ['assis debout','standing desk','elektrisch','sit stand'],
        'context': ['bureau','motorisé','électrique','occasion'],
        'variants': ['bureau réglable','flexispot','uplift desk','autonomous desk']},
    'flexispot':     {'ref': 550,  'cat': 'Mobilier bureau',
        'kw': ['flexispot'],
        'context': ['bureau','motorisé','occasion'],
        'variants': []},

    # ── MONTRES
    'rolex':         {'ref': 8000, 'cat': 'Montres',
        'kw': ['rolex'],
        'context': ['montre','submariner','datejust','oyster','acier','occasion'],
        'variants': ['rolex submariner','rolex datejust','rolex gmt']},
    'omega':         {'ref': 3000, 'cat': 'Montres',
        'kw': ['omega','seamaster','speedmaster'],
        'context': ['montre','acier','occasion'],
        'variants': ['omega seamaster','omega speedmaster']},
    'tag heuer':     {'ref': 1500, 'cat': 'Montres',
        'kw': ['tag heuer','tag','heuer'],
        'context': ['montre','carrera','occasion'],
        'variants': ['tag-heuer']},
    'casio gshock':  {'ref': 120,  'cat': 'Montres',
        'kw': ['casio','g-shock','gshock'],
        'context': ['montre','occasion'],
        'variants': ['g shock']},
    'seiko':         {'ref': 350,  'cat': 'Montres',
        'kw': ['seiko'],
        'context': ['montre','automatique','occasion'],
        'variants': ['seiko 5','seiko prospex','seiko presage']},

    # ── LUXE
    'louis vuitton': {'ref': 900,  'cat': 'Luxe',
        'kw': ['louis vuitton','vuitton','lv'],
        'context': ['sac','pochette','portefeuille','occasion','cuir'],
        'variants': ['louis vuition','lv bag']},
    'chanel':        {'ref': 2000, 'cat': 'Luxe',
        'kw': ['chanel'],
        'context': ['sac','pochette','occasion','cuir'],
        'variants': []},
    'hermes birkin': {'ref': 8000, 'cat': 'Luxe',
        'kw': ['hermes','birkin','kelly'],
        'context': ['sac','cuir','occasion'],
        'variants': ['hermès birkin','hermes kelly']},

    # ── SNEAKERS
    'yeezy':         {'ref': 320,  'cat': 'Sneakers',
        'kw': ['yeezy','adidas'],
        'context': ['baskets','chaussures','pointure','occasion'],
        'variants': ['yeezy boost','yeezy 350','yeezy 700']},
    'jordan 1':      {'ref': 180,  'cat': 'Sneakers',
        'kw': ['jordan','aj1','air jordan'],
        'context': ['baskets','chaussures','pointure','occasion'],
        'variants': ['jordan retro 1','air jordan 1']},
    'nike dunk':     {'ref': 140,  'cat': 'Sneakers',
        'kw': ['nike','dunk'],
        'context': ['baskets','chaussures','pointure','occasion'],
        'variants': ['dunk low','dunk high']},
    'new balance 550': {'ref': 130, 'cat': 'Sneakers',
        'kw': ['new balance','550'],
        'context': ['baskets','chaussures','pointure'],
        'variants': ['nb 550']},

    # ── COLLECTION
    'pokemon':       {'ref': 80,   'cat': 'Cartes',
        'kw': ['pokemon','pikachu','charizard'],
        'context': ['carte','cartes','collection','rare','holo'],
        'variants': ['pokémon','pokemone']},
    'lego technic':  {'ref': 250,  'cat': 'LEGO',
        'kw': ['lego','technic'],
        'context': ['boite','set','complet','neuf','occasion'],
        'variants': ['légo technic']},
    'lego creator':  {'ref': 180,  'cat': 'LEGO',
        'kw': ['lego','creator'],
        'context': ['boite','set','complet'],
        'variants': []},
    'lego star wars': {'ref': 200, 'cat': 'LEGO',
        'kw': ['lego','star wars'],
        'context': ['boite','set','complet'],
        'variants': []},
    'vinyle':        {'ref': 40,   'cat': 'Vinyles',
        'kw': ['vinyle','vinyl','33t','45t'],
        'context': ['disque','collection','pressage','occasion'],
        'variants': ['vinyl record','lp']},
    'ipad pro':      {'ref': 850,  'cat': 'Tablettes',
        'kw': ['ipad','pro'],
        'context': ['tablette','occasion','m1','m2'],
        'variants': ['ipad pro 11','ipad pro 12']},
}

LOT_WORDS = ['lot','vrac','ensemble','collection','boite','caisse','assortiment','divers','melange','destockage','destock']

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
    """Retourne True si le titre/description indique que c'est une pièce détachée ou accessoire"""
    tl = text.lower()
    for w in ACCESSORY_WORDS:
        if w in tl:
            return True, w
    return False, None

def context_score(text, obj_data):
    """Score de contexte : vérifie que les mots de contexte sont présents"""
    tl = text.lower()
    ctx_words = obj_data.get('context', [])
    if not ctx_words:
        return 50  # neutre si pas de context défini
    matches = sum(1 for w in ctx_words if w in tl)
    return min(100, int((matches / max(len(ctx_words), 1)) * 150))

def detect_objects(title, description=''):
    """Détection avancée avec validation contextuelle"""
    full_text = (title + ' ' + description).lower()
    title_low = title.lower()
    found = []
    seen = set()

    # Vérification accessoire/pièce d'abord
    acc, acc_word = is_accessory(title)

    for name, d in VALUE_OBJECTS.items():
        if name in seen: continue

        # ── Test 1 : fuzzy matching sur le titre
        matched = False
        match_confidence = 0

        if FUZZY_OK:
            score = fuzz.partial_ratio(name, title_low)
            if score >= 78:
                matched = True
                match_confidence = score

        # ── Test 2 : variants exacts
        if not matched:
            for v in d.get('variants', []):
                if v.lower() in title_low:
                    matched = True
                    match_confidence = 90
                    break

        # ── Test 3 : keywords (au moins 2 présents dans le texte complet)
        if not matched:
            kw_matches = sum(1 for k in d['kw'] if k in full_text)
            if kw_matches >= 2:
                matched = True
                match_confidence = 55 + kw_matches * 8

        if not matched:
            continue

        # ── Réduction si accessoire détecté
        if acc:
            # Si c'est manifestement une pièce détachée, exclure complètement
            match_confidence = 0
            continue

        # ── Score de contexte
        ctx = context_score(full_text, d)

        # Pénalité si contexte faible (objet mentionné mais contexte pas cohérent)
        if ctx < 20 and match_confidence < 80:
            continue  # Probablement un accessoire ou mention incidente

        final_confidence = int(match_confidence * 0.6 + ctx * 0.4)
        found.append((name, d['ref'], d['cat'], final_confidence))
        seen.add(name)

    is_lot = any(w in full_text for w in LOT_WORDS)
    return found, is_lot

def analyze_image_with_description(img_url, title):
    """
    Analyse contextuelle légère : on compare le titre
    avec les objets visuellement attendus via des heuristiques
    basées sur l'URL et les métadonnées de l'image.
    Pour une vraie analyse visuelle, utilise l'API Clarifai free tier.
    """
    # Heuristique : si l'image existe et le titre contient des indices visuels faibles
    # on tente une description via l'API Clarifai (gratuite jusqu'à 1000 appels/mois)
    # Retourne une liste de concepts détectés
    try:
        if not img_url: return []
        # API Clarifai general model (free)
        api_key = 'CLARIFAI_KEY'  # Remplace par ta clé gratuite sur clarifai.com
        if api_key == 'CLARIFAI_KEY':
            return []  # Pas de clé configurée
        headers_api = {'Authorization': f'Key {api_key}', 'Content-Type': 'application/json'}
        body = {'inputs': [{'data': {'image': {'url': img_url}}}]}
        r = requests.post(
            'https://api.clarifai.com/v2/models/general-image-recognition/versions/aa7f35c01e0642fda5cf400f543e7c40/outputs',
            headers=headers_api, json=body, timeout=10)
        if r.status_code == 200:
            concepts = r.json()['outputs'][0]['data']['concepts']
            return [c['name'].lower() for c in concepts[:15] if c['value'] > 0.80]
    except Exception:
        pass
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
                # Récupérer src ou data-src
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
                    if i_el:
                        img_url = i_el.get('src') or i_el.get('data-src','')
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
            for item in soup.select('[data-testid*="item"],[class*="ItemBox"],[class*="item-box"]')[:max_r]:
                try:
                    t_el = item.select_one('[class*="title"],[class*="name"]')
                    p_el = item.select_one('[class*="price"]')
                    a_el = item.find('a')
                    i_el = item.find('img')
                    t = t_el.get_text(strip=True) if t_el else ''
                    p = parse_price(p_el.get_text() if p_el else '')
                    href = a_el.get('href','') if a_el else ''
                    link = ('https://www.vinted.fr'+href) if href.startswith('/') else href
                    img_url = ''
                    if i_el: img_url = i_el.get('src') or i_el.get('data-src','')
                    if t and p:
                        results.append({'title':t,'price':p,'link':link,'img':img_url,
                            'desc':'','platform':'Vinted','color':'#09B1BA'})
                except: continue
    except Exception as e:
        print(f'[Vinted] {e}')
    return results

def analyze(listings, min_disc):
    deals = []
    for item in listings:
        full = item['title'] + ' ' + item.get('desc','')
        objs, is_lot = detect_objects(item['title'], item.get('desc',''))

        # Si aucun objet trouvé et image disponible, tenter analyse visuelle
        if not objs and item.get('img'):
            visual_concepts = analyze_image_with_description(item['img'], item['title'])
            if visual_concepts:
                visual_text = ' '.join(visual_concepts)
                objs, is_lot = detect_objects(item['title'] + ' ' + visual_text, item.get('desc',''))

        if not objs: continue

        best = max(objs, key=lambda x: x[1])
        pct, sc = deal_score(item['price'], best[1], is_lot, len(objs))
        if pct >= min_disc:
            deals.append({**item, 'objects':objs, 'best':best[0],
                'ref': best[1], 'cat': best[2], 'pct': pct,
                'score': sc, 'is_lot': is_lot,
                'savings': round(best[1]-item['price'],2)})
    deals.sort(key=lambda x: x['score'], reverse=True)
    return deals

AUTO_QUERIES = [
    'lot electronique', 'iphone occasion', 'ps5 console',
    'montre collection', 'lot carte pokemon', 'lego boite',
    'jordan sneakers', 'dyson occasion', 'macbook',
    'chaise bureau herman', 'fauteuil ergonomique bureau',
    'destockage bureau mobilier', 'chaise ergonomique occasion',
    'lot informatique vrac',
]

# ══════════════════════════════════════════════
#  CHARGEMENT IMAGE ASYNC
# ══════════════════════════════════════════════

def load_image_async(url, callback, size=(200, 150)):
    """Charge une image depuis une URL et appelle callback(ImageTk.PhotoImage)"""
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

class DealHunter(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('🔍 Deal Hunter — Chasseur de bonnes affaires')
        self.geometry('1300x800')
        self.minsize(900, 600)
        self.configure(bg=BG)
        self.deals = []
        self._image_refs = []  # Garder les références pour éviter le GC
        self._build_ui()
        self._style_ttk()

    def _style_ttk(self):
        s = ttk.Style(self)
        s.theme_use('clam')
        s.configure('TFrame', background=BG)
        s.configure('Sidebar.TFrame', background=SURF)
        s.configure('Card.TFrame', background=SURF2)
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
        # Logo
        tk.Frame(sb, bg=SURF, height=10).pack(fill='x')
        tk.Label(sb, text='🔍 Deal Hunter', bg=SURF, fg=PRI,
                 font=('Segoe UI', 15, 'bold')).pack(padx=14)
        tk.Label(sb, text='Chasseur de bonnes affaires', bg=SURF, fg=MUTED,
                 font=('Segoe UI', 9)).pack(pady=(0,8))
        tk.Frame(sb, bg=BORD, height=1).pack(fill='x')
        # Recherche
        tk.Frame(sb, bg=SURF, height=8).pack(fill='x')
        tk.Label(sb, text='RECHERCHE', bg=SURF, fg=MUTED,
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', padx=14)
        self.search_var = tk.StringVar()
        se = ttk.Entry(sb, textvariable=self.search_var, font=('Segoe UI', 10))
        se.pack(fill='x', padx=14, pady=(4,4))
        se.bind('<Return>', lambda e: self.do_search())
        # Tags rapides
        tags = [('📦 Lots élec','lot electronique'),('📱 iPhone','iphone'),
                ('🎮 PS5','ps5 console'),('⌚ Montres','montre collection'),
                ('🃏 Pokémon','pokemon carte'),('👟 Sneakers','jordan yeezy'),
                ('🖥 Mac','macbook'),('🌀 Dyson','dyson aspirateur'),
                ('🪑 Herman Miller','herman miller chaise'),('🏢 Destockage','destockage bureau mobilier')]
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
        # Remise minimale
        tk.Frame(sb, bg=SURF, height=4).pack(fill='x')
        tk.Label(sb, text='REMISE MINIMALE', bg=SURF, fg=MUTED,
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
        # Plateformes
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
        tk.Label(sb, text='✅ Validation contextuelle\n✅ Exclut pièces/accessoires\n✅ Images des annonces\n✅ Mobilier bureau inclus',
                 bg=SURF, fg=MUTED, font=('Segoe UI', 8), justify='left').pack(padx=14, pady=10, anchor='w')

    def _build_content(self):
        top = tk.Frame(self.content, bg=BG)
        top.pack(fill='x', padx=20, pady=(16,8))
        self.title_lbl = tk.Label(top, text='Prêt à chasser les deals 🎯',
                                   bg=BG, fg=TEXT, font=('Segoe UI', 14, 'bold'))
        self.title_lbl.pack(side='left')
        # Stats
        self.stats_frame = tk.Frame(self.content, bg=BG)
        self.stats_frame.pack(fill='x', padx=20, pady=(0,8))
        self.stat_scanned = self._stat_card('0', 'Analysées')
        self.stat_deals   = self._stat_card('0', 'Deals trouvés')
        self.stat_best    = self._stat_card('-', 'Meilleure remise')
        for w,_ in [self.stat_scanned, self.stat_deals, self.stat_best]:
            w.pack(side='left', padx=(0,10))
        # Progress
        self.progress = ttk.Progressbar(self.content, mode='indeterminate')
        self.status_lbl = tk.Label(self.content, text='', bg=BG, fg=MUTED, font=('Segoe UI', 9))
        # Zone scrollable
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
        tk.Label(self.scroll_frame, text='🎯', bg=BG, font=('Segoe UI', 48)).pack(pady=(60,10))
        tk.Label(self.scroll_frame, text='Aucune recherche en cours',
                 bg=BG, fg=TEXT, font=('Segoe UI', 14, 'bold')).pack()
        tk.Label(self.scroll_frame,
                 text='Lance une recherche ou Auto-Hunt pour commencer.',
                 bg=BG, fg=MUTED, font=('Segoe UI', 10)).pack(pady=4)

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
        self._set_loading('Auto-Hunt : scan de toutes les catégories...')
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
        outer = tk.Frame(parent, bg=BG, padx=6, pady=6)
        outer.grid(row=row, column=col, sticky='nsew')
        card = tk.Frame(outer, bg=SURF2, highlightbackground=BORD, highlightthickness=1)
        card.pack(fill='both', expand=True)

        # Header couleur plateforme
        tk.Frame(card, bg=d['color'], height=4).pack(fill='x')

        body = tk.Frame(card, bg=SURF2, padx=12, pady=10)
        body.pack(fill='both', expand=True)

        # Ligne 1 : plateforme + badge remise
        top_row = tk.Frame(body, bg=SURF2)
        top_row.pack(fill='x')
        tk.Label(top_row, text=d['platform'], bg=SURF2, fg=d['color'],
                 font=('Segoe UI', 9, 'bold')).pack(side='left')
        badge_bg = '#7c3aed' if d['score'] >= 70 else RED
        tk.Label(top_row, text=f"  -{d['pct']}%  ", bg=badge_bg, fg='white',
                 font=('Segoe UI', 10, 'bold')).pack(side='right')

        # ── IMAGE DE L'ANNONCE ──
        if PIL_OK and d.get('img'):
            img_frame = tk.Frame(body, bg=SURF2, height=160)
            img_frame.pack(fill='x', pady=(6,4))
            img_frame.pack_propagate(False)
            placeholder = tk.Label(img_frame, text='⏳ chargement image...',
                                   bg='#12121a', fg=MUTED, font=('Segoe UI', 8))
            placeholder.pack(expand=True)
            def set_img(photo, lbl=placeholder, frm=img_frame):
                self._image_refs.append(photo)  # Garder la référence
                lbl.config(image=photo, text='', bg='#12121a')
            load_image_async(d['img'], set_img, size=(440, 155))
        elif not PIL_OK and d.get('img'):
            tk.Label(body, text='📷 Image disponible (install Pillow pour afficher)',
                     bg='#12121a', fg=MUTED, font=('Segoe UI', 8), pady=4).pack(fill='x')

        # Lot badge
        if d['is_lot']:
            tk.Label(body, text='📦 LOT — objet de valeur détecté à l\'intérieur',
                     bg='#2d2a00', fg=ORANGE,
                     font=('Segoe UI', 8, 'bold')).pack(anchor='w', pady=(4,0))

        # Titre
        title_txt = d['title'][:72] + '...' if len(d['title']) > 72 else d['title']
        tk.Label(body, text=title_txt, bg=SURF2, fg=TEXT,
                 font=('Segoe UI', 10, 'bold'),
                 wraplength=360, justify='left').pack(anchor='w', pady=(6,2))

        # Objets détectés
        objs_txt = ', '.join(o[0] for o in d['objects'][:3])
        tk.Label(body, text=f'🎯 Détecté : {objs_txt}',
                 bg=SURF2, fg=PRI, font=('Segoe UI', 9)).pack(anchor='w')
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
        tk.Label(rp, text=f"Réf : {d['ref']} €", bg=SURF2, fg=MUTED, font=('Segoe UI', 8)).pack(anchor='e')
        tk.Label(rp, text=f"Économie ~{d['savings']} €", bg=SURF2, fg=GREEN, font=('Segoe UI', 9, 'bold')).pack(anchor='e')

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
