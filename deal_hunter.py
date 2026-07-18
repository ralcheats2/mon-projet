import tkinter as tk
from tkinter import ttk, font
import threading
import requests
from bs4 import BeautifulSoup
import re
import time
import random
import webbrowser
import urllib.parse

# ─── Supprime les anciens fichiers Flask si present ───
import os, sys

try:
    from thefuzz import fuzz
    FUZZY_OK = True
except ImportError:
    FUZZY_OK = False

# ══════════════════════════════════════════════
#  BASE DE DONNEES DES OBJETS DE VALEUR
# ══════════════════════════════════════════════
VALUE_OBJECTS = {
    'iphone 15 pro': {'ref': 1100, 'kw': ['iphone','15 pro','apple'], 'cat': 'Téléphones'},
    'iphone 14':     {'ref': 650,  'kw': ['iphone','14','apple'],     'cat': 'Téléphones'},
    'iphone 13':     {'ref': 480,  'kw': ['iphone','13','apple'],     'cat': 'Téléphones'},
    'iphone 12':     {'ref': 320,  'kw': ['iphone','12','apple'],     'cat': 'Téléphones'},
    'samsung s24':   {'ref': 850,  'kw': ['samsung','s24','galaxy'],  'cat': 'Téléphones'},
    'samsung s23':   {'ref': 600,  'kw': ['samsung','s23','galaxy'],  'cat': 'Téléphones'},
    'macbook pro':   {'ref': 1800, 'kw': ['macbook','pro','apple'],   'cat': 'Ordinateurs'},
    'macbook air':   {'ref': 1100, 'kw': ['macbook','air','apple'],   'cat': 'Ordinateurs'},
    'ps5':           {'ref': 500,  'kw': ['ps5','playstation','sony'],'cat': 'Gaming'},
    'xbox series':   {'ref': 480,  'kw': ['xbox','series','microsoft'],'cat': 'Gaming'},
    'switch oled':   {'ref': 320,  'kw': ['switch','nintendo','oled'],'cat': 'Gaming'},
    'airpods pro':   {'ref': 230,  'kw': ['airpods','pro','apple'],   'cat': 'Audio'},
    'sony xm5':      {'ref': 330,  'kw': ['sony','xm5','casque'],     'cat': 'Audio'},
    'gopro':         {'ref': 350,  'kw': ['gopro','hero','action'],   'cat': 'Photo'},
    'dyson v15':     {'ref': 650,  'kw': ['dyson','v15','aspirateur'],'cat': 'Electroménager'},
    'dyson airwrap': {'ref': 500,  'kw': ['dyson','airwrap'],         'cat': 'Electroménager'},
    'thermomix':     {'ref': 1200, 'kw': ['thermomix','vorwerk','tm6'],'cat': 'Electroménager'},
    'rolex':         {'ref': 8000, 'kw': ['rolex','montre','oyster','submariner','datejust'], 'cat': 'Montres'},
    'omega':         {'ref': 3000, 'kw': ['omega','seamaster','speedmaster'], 'cat': 'Montres'},
    'tag heuer':     {'ref': 1500, 'kw': ['tag','heuer','carrera'],   'cat': 'Montres'},
    'casio gshock':  {'ref': 120,  'kw': ['casio','gshock','g-shock'],'cat': 'Montres'},
    'louis vuitton': {'ref': 900,  'kw': ['louis','vuitton','lv'],    'cat': 'Luxe'},
    'chanel sac':    {'ref': 2000, 'kw': ['chanel','sac','cc'],       'cat': 'Luxe'},
    'hermes':        {'ref': 4000, 'kw': ['hermes','birkin','kelly'], 'cat': 'Luxe'},
    'yeezy':         {'ref': 320,  'kw': ['yeezy','adidas','boost'],  'cat': 'Sneakers'},
    'jordan 1':      {'ref': 180,  'kw': ['jordan','aj1','air jordan'],'cat': 'Sneakers'},
    'nike dunk':     {'ref': 140,  'kw': ['nike','dunk','sb'],        'cat': 'Sneakers'},
    'pokemon':       {'ref': 80,   'kw': ['pokemon','carte','pikachu','charizard'], 'cat': 'Cartes'},
    'lego':          {'ref': 180,  'kw': ['lego','technic','star wars','creator'],  'cat': 'LEGO'},
    'canon eos':     {'ref': 1400, 'kw': ['canon','eos','reflex','hybride'],        'cat': 'Photo'},
    'sony alpha':    {'ref': 1800, 'kw': ['sony','alpha','a7','mirrorless'],        'cat': 'Photo'},
    'ipad pro':      {'ref': 850,  'kw': ['ipad','pro','apple','tablette'],         'cat': 'Tablettes'},
    'leica':         {'ref': 3000, 'kw': ['leica','m10','q2','telemetrique'],       'cat': 'Photo'},
    'vinyle':        {'ref': 40,   'kw': ['vinyle','vinyl','33t','45t','disque'],   'cat': 'Vinyles'},
}

LOT_WORDS = ['lot','vrac','ensemble','collection','boite','caisse','assortiment','divers','melange']

HEADERS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0',
]

def rh():
    return {'User-Agent': random.choice(HEADERS), 'Accept-Language': 'fr-FR,fr;q=0.9'}

def parse_price(text):
    if not text: return None
    t = re.sub(r'[^\d.,]', '', text.replace('\xa0','').replace('\u202f',''))
    t = t.replace(',','.')
    m = re.search(r'\d+\.?\d*', t)
    try:
        v = float(m.group()) if m else None
        return v if v and 1 < v < 100000 else None
    except: return None

def detect_objects(text):
    tl = text.lower()
    found = []
    seen = set()
    for name, d in VALUE_OBJECTS.items():
        if name in seen: continue
        if FUZZY_OK:
            score = fuzz.partial_ratio(name, tl)
            if score >= 75:
                found.append((name, d['ref'], d['cat'], score))
                seen.add(name)
                continue
        matches = sum(1 for k in d['kw'] if k in tl)
        if matches >= 2:
            found.append((name, d['ref'], d['cat'], 60 + matches*8))
            seen.add(name)
    is_lot = any(w in tl for w in LOT_WORDS)
    return found, is_lot

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
    """eBay.fr - fonctionne bien sans JS"""
    results = []
    try:
        url = f'https://www.ebay.fr/sch/i.html?_nkw={urllib.parse.quote(query)}&_sop=10&LH_BIN=1&_ipg=48'
        r = requests.get(url, headers=rh(), timeout=15)
        soup = BeautifulSoup(r.text, 'html5lib')
        items = soup.select('.s-item')
        for item in items[:max_r]:
            try:
                title = item.select_one('.s-item__title')
                price = item.select_one('.s-item__price')
                link  = item.select_one('a.s-item__link')
                img   = item.select_one('.s-item__image-img, img')
                t = title.get_text(strip=True) if title else ''
                if not t or 'Shop on eBay' in t: continue
                p = parse_price(price.get_text() if price else '')
                if not p: continue
                results.append({
                    'title': t, 'price': p,
                    'link': link['href'] if link else '',
                    'img': img.get('src','') if img else '',
                    'platform': 'eBay', 'color': '#E53238'
                })
            except: continue
    except Exception as e:
        print(f'[eBay] {e}')
    return results

def scrape_lbc_rss(query, max_r=30):
    """LeBonCoin via flux RSS - pas de JS nécessaire"""
    results = []
    try:
        url = f'https://www.leboncoin.fr/recherche?text={urllib.parse.quote(query)}&sort=time'
        r = requests.get(url, headers=rh(), timeout=15)
        soup = BeautifulSoup(r.text, 'html5lib')
        # Chercher les données JSON embarquées dans __NEXT_DATA__
        script = soup.find('script', id='__NEXT_DATA__')
        if script:
            import json
            data = json.loads(script.string)
            try:
                ads = data['props']['pageProps']['searchData']['ads']
                for ad in ads[:max_r]:
                    title = ad.get('subject','')
                    price = ad.get('price',[None])
                    price = price[0] if isinstance(price, list) and price else price
                    link  = 'https://www.leboncoin.fr' + ad.get('url','')
                    imgs  = ad.get('images',{}).get('urls',[])
                    img   = imgs[0] if imgs else ''
                    if title and price:
                        results.append({
                            'title': title, 'price': float(price),
                            'link': link, 'img': img,
                            'platform': 'LeBonCoin', 'color': '#F56B2A'
                        })
            except (KeyError, TypeError):
                pass
        # Fallback HTML classique
        if not results:
            for item in soup.select('li[data-qa-id="aditem_container"], article')[:max_r]:
                try:
                    t_el = item.select_one('[class*="title"], [class*="Title"], h2, h3')
                    p_el = item.select_one('[class*="price"], [class*="Price"]')
                    a_el = item.find('a')
                    i_el = item.find('img')
                    t = t_el.get_text(strip=True) if t_el else ''
                    p = parse_price(p_el.get_text() if p_el else '')
                    href = a_el.get('href','') if a_el else ''
                    link = ('https://www.leboncoin.fr'+href) if href.startswith('/') else href
                    if t and p:
                        results.append({'title':t,'price':p,'link':link,
                            'img': i_el.get('src','') if i_el else '',
                            'platform':'LeBonCoin','color':'#F56B2A'})
                except: continue
    except Exception as e:
        print(f'[LBC] {e}')
    return results

def scrape_vinted(query, max_r=30):
    """Vinted - tente l'API catalog"""
    results = []
    try:
        # API JSON publique Vinted
        api_url = f'https://www.vinted.fr/api/v2/catalog/items?search_text={urllib.parse.quote(query)}&order=newest_first&per_page=48'
        r = requests.get(api_url, headers={**rh(), 'Accept':'application/json'}, timeout=15)
        if r.status_code == 200:
            data = r.json()
            items = data.get('items', [])
            for item in items[:max_r]:
                t = item.get('title','')
                p = item.get('price',{}).get('amount') or item.get('price')
                link = item.get('url','') or f"https://www.vinted.fr/items/{item.get('id','')}"
                img  = item.get('photo',{}).get('url','') if isinstance(item.get('photo'),dict) else ''
                try: p = float(p)
                except: p = None
                if t and p:
                    results.append({'title':t,'price':p,'link':link,'img':img,
                        'platform':'Vinted','color':'#09B1BA'})
        else:
            # Fallback HTML
            url = f'https://www.vinted.fr/catalog?search_text={urllib.parse.quote(query)}'
            r2 = requests.get(url, headers=rh(), timeout=15)
            soup = BeautifulSoup(r2.text, 'html5lib')
            for item in soup.select('[data-testid*="item"], [class*="ItemBox"], [class*="item-box"]')[:max_r]:
                try:
                    t_el = item.select_one('[class*="title"],[class*="name"],[class*="Title"]')
                    p_el = item.select_one('[class*="price"],[class*="Price"]')
                    a_el = item.find('a')
                    i_el = item.find('img')
                    t = t_el.get_text(strip=True) if t_el else ''
                    p = parse_price(p_el.get_text() if p_el else '')
                    href = a_el.get('href','') if a_el else ''
                    link = ('https://www.vinted.fr'+href) if href.startswith('/') else href
                    if t and p:
                        results.append({'title':t,'price':p,'link':link,
                            'img': i_el.get('src','') if i_el else '',
                            'platform':'Vinted','color':'#09B1BA'})
                except: continue
    except Exception as e:
        print(f'[Vinted] {e}')
    return results

def analyze(listings, min_disc):
    deals = []
    for item in listings:
        objs, is_lot = detect_objects(item['title'])
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
    'jordan sneakers', 'dyson occasion', 'macbook'
]

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
        self.geometry('1200x750')
        self.minsize(900, 600)
        self.configure(bg=BG)
        self.deals = []
        self._build_ui()
        self._style_ttk()

    def _style_ttk(self):
        s = ttk.Style(self)
        s.theme_use('clam')
        s.configure('TFrame', background=BG)
        s.configure('Sidebar.TFrame', background=SURF)
        s.configure('Card.TFrame', background=SURF2)
        s.configure('TLabel', background=BG, foreground=TEXT, font=('Segoe UI', 10))
        s.configure('Muted.TLabel', background=SURF, foreground=MUTED, font=('Segoe UI', 9))
        s.configure('Title.TLabel', background=SURF, foreground=TEXT, font=('Segoe UI', 11, 'bold'))
        s.configure('Big.TLabel', background=SURF2, foreground=GREEN, font=('Segoe UI', 16, 'bold'))
        s.configure('Ref.TLabel', background=SURF2, foreground=MUTED, font=('Segoe UI', 9))
        s.configure('Pct.TLabel', background=RED, foreground='white', font=('Segoe UI', 10, 'bold'))
        s.configure('Score.TLabel', background=SURF2, foreground=ORANGE, font=('Segoe UI', 9))
        s.configure('Plat.TLabel', background=SURF2, foreground=MUTED, font=('Segoe UI', 9, 'bold'))
        s.configure('Savings.TLabel', background=SURF2, foreground=GREEN, font=('Segoe UI', 9, 'bold'))
        s.configure('Vertical.TScrollbar', background=SURF2, troughcolor=BG, arrowcolor=MUTED)
        s.configure('TEntry', fieldbackground=SURF2, foreground=TEXT,
                    insertcolor=TEXT, borderwidth=1, relief='flat')
        s.configure('Search.TButton', background=PRI, foreground='white',
                    font=('Segoe UI', 10, 'bold'), relief='flat', borderwidth=0)
        s.map('Search.TButton', background=[('active', '#6b58f0')])
        s.configure('Auto.TButton', background='#d97706', foreground='white',
                    font=('Segoe UI', 10, 'bold'), relief='flat', borderwidth=0)
        s.map('Auto.TButton', background=[('active', '#b45309')])
        s.configure('Link.TButton', background=SURF2, foreground=PRI,
                    font=('Segoe UI', 9), relief='flat', borderwidth=0)
        s.map('Link.TButton', foreground=[('active', '#a78bfa')])
        s.configure('Cat.TButton', background=SURF, foreground=MUTED,
                    font=('Segoe UI', 9), relief='flat', borderwidth=0)
        s.map('Cat.TButton', background=[('active', SURF2)])
        s.configure('Horizontal.TProgressbar', troughcolor=SURF, background=PRI, thickness=4)

    def _build_ui(self):
        # ── Layout principal
        self.sidebar = ttk.Frame(self, style='Sidebar.TFrame', width=260)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)

        self.content = ttk.Frame(self, style='TFrame')
        self.content.pack(side='left', fill='both', expand=True)

        self._build_sidebar()
        self._build_content()

    def _build_sidebar(self):
        sb = self.sidebar
        pad = {'padx': 14, 'pady': 6}

        # Logo
        logo_frame = tk.Frame(sb, bg=SURF, pady=14)
        logo_frame.pack(fill='x')
        tk.Label(logo_frame, text='🔍 Deal Hunter', bg=SURF, fg=PRI,
                 font=('Segoe UI', 15, 'bold')).pack(padx=14)
        tk.Label(logo_frame, text='Chasseur de bonnes affaires', bg=SURF, fg=MUTED,
                 font=('Segoe UI', 9)).pack()
        tk.Frame(sb, bg=BORD, height=1).pack(fill='x')

        # Recherche
        tk.Frame(sb, bg=SURF, height=8).pack(fill='x')
        tk.Label(sb, text='RECHERCHE', bg=SURF, fg=MUTED,
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', **pad)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(sb, textvariable=self.search_var, font=('Segoe UI', 10))
        search_entry.pack(fill='x', padx=14, pady=(0,4))
        search_entry.bind('<Return>', lambda e: self.do_search())

        # Tags rapides
        tags_frame = tk.Frame(sb, bg=SURF)
        tags_frame.pack(fill='x', padx=10, pady=(0,8))
        tags = [('📦 Lots élec','lot electronique'),('📱 iPhone','iphone'),
                ('🎮 PS5','ps5'),('⌚ Montres','rolex omega montre'),
                ('🃏 Pokémon','pokemon carte'),('👟 Sneakers','jordan yeezy'),
                ('🖥 Mac','macbook'),('🌀 Dyson','dyson')]
        for i,(label,val) in enumerate(tags):
            btn = tk.Button(tags_frame, text=label, bg=SURF2, fg=MUTED,
                            font=('Segoe UI', 8), relief='flat', bd=0,
                            cursor='hand2', pady=3, padx=6,
                            command=lambda v=val: self._quick_search(v))
            btn.grid(row=i//2, column=i%2, sticky='ew', padx=2, pady=2)
        tags_frame.columnconfigure(0, weight=1)
        tags_frame.columnconfigure(1, weight=1)

        tk.Frame(sb, bg=BORD, height=1).pack(fill='x')

        # Remise minimale
        tk.Frame(sb, bg=SURF, height=4).pack(fill='x')
        tk.Label(sb, text='REMISE MINIMALE', bg=SURF, fg=MUTED,
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', **pad)
        disc_frame = tk.Frame(sb, bg=SURF)
        disc_frame.pack(fill='x', padx=14)
        self.disc_var = tk.IntVar(value=40)
        self.disc_lbl = tk.Label(disc_frame, text='40%', bg=SURF, fg=PRI,
                                  font=('Segoe UI', 12, 'bold'), width=5)
        self.disc_lbl.pack(side='right')
        disc_slider = tk.Scale(disc_frame, from_=10, to=90, orient='horizontal',
                               variable=self.disc_var, bg=SURF, fg=TEXT,
                               highlightthickness=0, troughcolor=SURF2,
                               activebackground=PRI, sliderrelief='flat',
                               command=lambda v: self.disc_lbl.config(text=f'{v}%'))
        disc_slider.pack(side='left', fill='x', expand=True)

        tk.Frame(sb, bg=BORD, height=1).pack(fill='x', pady=4)

        # Plateformes
        tk.Label(sb, text='PLATEFORMES', bg=SURF, fg=MUTED,
                 font=('Segoe UI', 8, 'bold')).pack(anchor='w', **pad)
        self.plat_lbc    = tk.BooleanVar(value=True)
        self.plat_vinted = tk.BooleanVar(value=True)
        self.plat_ebay   = tk.BooleanVar(value=True)
        for var, label, color in [
            (self.plat_lbc,    '🟠 LeBonCoin', '#F56B2A'),
            (self.plat_vinted, '🔵 Vinted',    '#09B1BA'),
            (self.plat_ebay,   '🔴 eBay',      '#E53238'),
        ]:
            cb = tk.Checkbutton(sb, text=label, variable=var,
                                bg=SURF, fg=TEXT, selectcolor=SURF2,
                                activebackground=SURF, font=('Segoe UI', 10),
                                cursor='hand2')
            cb.pack(anchor='w', padx=14, pady=2)

        tk.Frame(sb, bg=BORD, height=1).pack(fill='x', pady=6)

        # Boutons
        tk.Button(sb, text='🔍  Rechercher les deals',
                  bg=PRI, fg='white', font=('Segoe UI', 10, 'bold'),
                  relief='flat', bd=0, pady=10, cursor='hand2',
                  command=self.do_search).pack(fill='x', padx=14, pady=(0,6))
        tk.Button(sb, text='🎯  Auto-Hunt (toutes catégories)',
                  bg='#d97706', fg='white', font=('Segoe UI', 10, 'bold'),
                  relief='flat', bd=0, pady=10, cursor='hand2',
                  command=self.do_auto).pack(fill='x', padx=14, pady=(0,10))

        # Info bas
        tk.Frame(sb, bg=BORD, height=1).pack(fill='x')
        tk.Label(sb, text='Détecte les objets de valeur\nmême dans des lots vrac.\nFuzzy matching inclus.',
                 bg=SURF, fg=MUTED, font=('Segoe UI', 8),
                 justify='center').pack(pady=12)

    def _build_content(self):
        top = tk.Frame(self.content, bg=BG)
        top.pack(fill='x', padx=20, pady=(16,8))

        self.title_lbl = tk.Label(top, text='Prêt à chasser les deals 🎯',
                                   bg=BG, fg=TEXT, font=('Segoe UI', 14, 'bold'))
        self.title_lbl.pack(side='left')

        # Stats
        self.stats_frame = tk.Frame(self.content, bg=BG)
        self.stats_frame.pack(fill='x', padx=20, pady=(0,8))
        self.stat_scanned = self._stat_card('0', 'Annonces analysées')
        self.stat_deals   = self._stat_card('0', 'Deals trouvés')
        self.stat_best    = self._stat_card('-', 'Meilleure remise')
        for w in [self.stat_scanned[0], self.stat_deals[0], self.stat_best[0]]:
            w.pack(side='left', padx=(0,10))

        # Progress
        self.progress = ttk.Progressbar(self.content, mode='indeterminate')
        self.status_lbl = tk.Label(self.content, text='', bg=BG, fg=MUTED,
                                    font=('Segoe UI', 9))

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
        v_lbl = tk.Label(f, text=val, bg=SURF, fg=GREEN,
                         font=('Segoe UI', 18, 'bold'))
        v_lbl.pack()
        tk.Label(f, text=label, bg=SURF, fg=MUTED,
                 font=('Segoe UI', 8)).pack()
        return f, v_lbl

    def _show_empty(self):
        for w in self.scroll_frame.winfo_children(): w.destroy()
        tk.Label(self.scroll_frame, text='🎯', bg=BG,
                 font=('Segoe UI', 48)).pack(pady=(60,10))
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
        self._set_loading(f'Scraping "{kw}" sur {len(plats)} plateforme(s)...')
        threading.Thread(target=self._run_search, args=(kw, disc, plats), daemon=True).start()

    def do_auto(self):
        plats = self._get_platforms()
        disc  = self.disc_var.get()
        self._set_loading('Auto-Hunt : scan de toutes les catégories rentables...')
        threading.Thread(target=self._run_auto, args=(disc, plats), daemon=True).start()

    def _run_search(self, kw, disc, plats):
        listings = []
        if 'lbc'    in plats: listings += scrape_lbc_rss(kw)
        if 'vinted' in plats: listings += scrape_vinted(kw)
        if 'ebay'   in plats: listings += scrape_ebay(kw)
        deals = analyze(listings, disc)
        self.after(0, self._show_results, deals, len(listings),
                   f'Résultats : "{kw}"')

    def _run_auto(self, disc, plats):
        listings = []
        for q in AUTO_QUERIES:
            if 'lbc'  in plats: listings += scrape_lbc_rss(q, max_r=15)
            if 'ebay' in plats: listings += scrape_ebay(q, max_r=15)
            time.sleep(random.uniform(0.3, 0.8))
        # Déduplique
        seen, uniq = set(), []
        for i in listings:
            if i['link'] not in seen:
                seen.add(i['link']); uniq.append(i)
        deals = analyze(uniq, disc)
        self.after(0, self._show_results, deals, len(uniq), 'Auto-Hunt IA')

    def _show_results(self, deals, scanned, title):
        self._set_done()
        self.deals = deals
        self.title_lbl.config(text=title)
        # Update stats
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

        # Grille de cartes (2 colonnes)
        grid = tk.Frame(self.scroll_frame, bg=BG)
        grid.pack(fill='both', expand=True)
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        for i, deal in enumerate(deals):
            self._make_card(grid, deal, row=i//2, col=i%2)

    def _make_card(self, parent, d, row, col):
        outer = tk.Frame(parent, bg=BG, padx=6, pady=6)
        outer.grid(row=row, column=col, sticky='nsew')

        card = tk.Frame(outer, bg=SURF2,
                        highlightbackground=BORD, highlightthickness=1)
        card.pack(fill='both', expand=True)

        # Header coloré plateforme
        hdr = tk.Frame(card, bg=d['color'], height=4)
        hdr.pack(fill='x')

        body = tk.Frame(card, bg=SURF2, padx=12, pady=10)
        body.pack(fill='both', expand=True)

        # Ligne 1 : plateforme + badge remise
        top_row = tk.Frame(body, bg=SURF2)
        top_row.pack(fill='x')
        tk.Label(top_row, text=d['platform'], bg=SURF2, fg=d['color'],
                 font=('Segoe UI', 9, 'bold')).pack(side='left')
        badge_bg = RED if d['score'] < 70 else '#7c3aed'
        tk.Label(top_row, text=f"  -{d['pct']}%  ",
                 bg=badge_bg, fg='white',
                 font=('Segoe UI', 10, 'bold')).pack(side='right')

        # Lot badge
        if d['is_lot']:
            tk.Label(body, text='📦 LOT — objet de valeur détecté à l\'intérieur',
                     bg='#2d2a00', fg=ORANGE,
                     font=('Segoe UI', 8, 'bold')).pack(anchor='w', pady=(4,0))

        # Titre
        title_txt = d['title'] if len(d['title']) <= 70 else d['title'][:67]+'...'
        tk.Label(body, text=title_txt, bg=SURF2, fg=TEXT,
                 font=('Segoe UI', 10, 'bold'),
                 wraplength=340, justify='left').pack(anchor='w', pady=(6,2))

        # Détection
        objs_txt = ', '.join(o[0] for o in d['objects'][:3])
        tk.Label(body, text=f'🎯 Détecté : {objs_txt}',
                 bg=SURF2, fg=PRI, font=('Segoe UI', 9)).pack(anchor='w')

        # Catégorie
        tk.Label(body, text=f"📂 {d['cat']}",
                 bg=SURF2, fg=MUTED, font=('Segoe UI', 8)).pack(anchor='w', pady=(2,6))

        tk.Frame(body, bg=BORD, height=1).pack(fill='x')

        # Prix
        price_row = tk.Frame(body, bg=SURF2)
        price_row.pack(fill='x', pady=8)
        tk.Label(price_row, text=f"{d['price']} €",
                 bg=SURF2, fg=GREEN, font=('Segoe UI', 18, 'bold')).pack(side='left')
        right_prices = tk.Frame(price_row, bg=SURF2)
        right_prices.pack(side='right', anchor='e')
        tk.Label(right_prices, text=f"Réf : {d['ref']} €",
                 bg=SURF2, fg=MUTED, font=('Segoe UI', 8)).pack(anchor='e')
        tk.Label(right_prices, text=f"Économie ~{d['savings']} €",
                 bg=SURF2, fg=GREEN, font=('Segoe UI', 9, 'bold')).pack(anchor='e')

        # Barre de score
        score_pct = d['score']
        bar_color = RED if score_pct >= 80 else (ORANGE if score_pct >= 60 else GREEN)
        bar_frame = tk.Frame(body, bg=SURF, height=5)
        bar_frame.pack(fill='x')
        tk.Frame(bar_frame, bg=bar_color,
                 height=5, width=int(3.4*score_pct)).place(x=0, y=0)

        tk.Label(body, text=f'Score deal : {score_pct}/100',
                 bg=SURF2, fg=MUTED, font=('Segoe UI', 8)).pack(anchor='w', pady=(4,6))

        # Bouton lien
        if d['link']:
            tk.Button(body, text='🔗  Voir l\'annonce →',
                      bg=PRI, fg='white', font=('Segoe UI', 9, 'bold'),
                      relief='flat', bd=0, pady=7, cursor='hand2',
                      command=lambda url=d['link']: webbrowser.open(url)
                      ).pack(fill='x')


if __name__ == '__main__':
    app = DealHunter()
    app.mainloop()
