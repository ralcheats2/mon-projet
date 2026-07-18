import requests
from bs4 import BeautifulSoup
import re
import time
import random
import threading

# ─────────────────────────────────────────────────────────────────────────────
# MATCHING : règles strictes
# Chaque entrée définit :
#   anchor   : mot(s) OBLIGATOIRE(S) dans le texte (brand ou terme unique)
#   required : au moins N de ces mots doivent être présents
#   bonus    : mots qui affinent (modèle précis)
#   exclude  : si l'un de ces mots est présent, on annule le match
#   min_hits : nombre de mots "required" min pour valider
# ─────────────────────────────────────────────────────────────────────────────

# Ordre important : les entrées plus spécifiques DOIVENT être avant les génériques
# (rolex submariner avant rolex, etc.)

CATALOG = [
    # ──────────── SAMSUNG ────────────
    {'name': 'samsung galaxy s24 ultra', 'anchor': ['samsung'], 'required': ['s24', 'ultra'], 'min_hits': 2,
     'ref_price': 0, 'category': '📱 Téléphones', 'bm_key': 'samsung galaxy s24 ultra'},
    {'name': 'samsung galaxy s24',       'anchor': ['samsung'], 'required': ['s24'], 'min_hits': 1, 'exclude': ['ultra'],
     'ref_price': 0, 'category': '📱 Téléphones', 'bm_key': 'samsung galaxy s24'},
    {'name': 'samsung galaxy s23',       'anchor': ['samsung'], 'required': ['s23'], 'min_hits': 1,
     'ref_price': 380, 'category': '📱 Téléphones'},
    {'name': 'samsung galaxy s22',       'anchor': ['samsung'], 'required': ['s22'], 'min_hits': 1,
     'ref_price': 280, 'category': '📱 Téléphones'},

    # ──────────── MACBOOK ────────────
    {'name': 'macbook pro m3',  'anchor': ['macbook'], 'required': ['pro', 'm3'], 'min_hits': 2,
     'ref_price': 0, 'category': '💻 Ordinateurs', 'bm_key': 'macbook pro m3'},
    {'name': 'macbook pro m2',  'anchor': ['macbook'], 'required': ['pro', 'm2'], 'min_hits': 2,
     'ref_price': 0, 'category': '💻 Ordinateurs', 'bm_key': 'macbook pro m2'},
    {'name': 'macbook pro m1',  'anchor': ['macbook'], 'required': ['pro', 'm1'], 'min_hits': 2,
     'ref_price': 0, 'category': '💻 Ordinateurs', 'bm_key': 'macbook pro m1'},
    {'name': 'macbook air m2',  'anchor': ['macbook'], 'required': ['air', 'm2'], 'min_hits': 2,
     'ref_price': 0, 'category': '💻 Ordinateurs', 'bm_key': 'macbook air m2'},
    {'name': 'macbook air m1',  'anchor': ['macbook'], 'required': ['air', 'm1'], 'min_hits': 2,
     'ref_price': 0, 'category': '💻 Ordinateurs', 'bm_key': 'macbook air m1'},
    {'name': 'macbook',         'anchor': ['macbook'], 'required': [],           'min_hits': 0,
     'ref_price': 500, 'category': '💻 Ordinateurs'},

    # ──────────── iPad ────────────
    {'name': 'ipad pro',   'anchor': ['ipad'], 'required': ['pro'],      'min_hits': 1, 'ref_price': 0, 'category': '📱 Tablettes', 'bm_key': 'ipad pro'},
    {'name': 'ipad air',   'anchor': ['ipad'], 'required': ['air'],      'min_hits': 1, 'ref_price': 0, 'category': '📱 Tablettes', 'bm_key': 'ipad air'},
    {'name': 'ipad',       'anchor': ['ipad'], 'required': [],           'min_hits': 0, 'ref_price': 250, 'category': '📱 Tablettes'},

    # ──────────── GAMING ────────────
    {'name': 'ps5',               'anchor': ['ps5'],          'required': [],           'min_hits': 0, 'ref_price': 0, 'category': '🎮 Gaming', 'bm_key': 'ps5'},
    {'name': 'playstation 5',     'anchor': ['playstation 5'],'required': [],           'min_hits': 0, 'ref_price': 0, 'category': '🎮 Gaming', 'bm_key': 'ps5'},
    {'name': 'ps4 pro',           'anchor': ['ps4'],          'required': ['pro'],      'min_hits': 1, 'ref_price': 120, 'category': '🎮 Gaming'},
    {'name': 'xbox series x',     'anchor': ['xbox'],         'required': ['series x'], 'min_hits': 1, 'ref_price': 0, 'category': '🎮 Gaming', 'bm_key': 'xbox series x'},
    {'name': 'nintendo switch oled','anchor': ['nintendo','switch oled'], 'required': ['oled'], 'min_hits': 1, 'ref_price': 0, 'category': '🎮 Gaming', 'bm_key': 'nintendo switch oled'},
    {'name': 'nintendo switch',   'anchor': ['nintendo switch'],'required': [],         'min_hits': 0, 'exclude': ['oled'], 'ref_price': 180, 'category': '🎮 Gaming'},
    {'name': 'steam deck',        'anchor': ['steam deck'],   'required': [],           'min_hits': 0, 'ref_price': 0, 'category': '🎮 Gaming', 'bm_key': 'steam deck'},

    # ──────────── AUDIO APPLE ────────────
    {'name': 'airpods pro',  'anchor': ['airpods'], 'required': ['pro'],     'min_hits': 1, 'ref_price': 180, 'category': '🎧 Audio'},
    {'name': 'sony xm5',     'anchor': ['sony'],    'required': ['xm5'],    'min_hits': 1, 'ref_price': 230, 'category': '🎧 Audio'},
    {'name': 'sony xm4',     'anchor': ['sony'],    'required': ['xm4'],    'min_hits': 1, 'ref_price': 160, 'category': '🎧 Audio'},

    # ──────────── ÉLECTROMÉNAGER ────────────
    {'name': 'dyson v15',     'anchor': ['dyson'], 'required': ['v15'],     'min_hits': 1, 'ref_price': 0, 'category': '🏠 Électroménager', 'bm_key': 'dyson v15'},
    {'name': 'dyson v12',     'anchor': ['dyson'], 'required': ['v12'],     'min_hits': 1, 'ref_price': 0, 'category': '🏠 Électroménager', 'bm_key': 'dyson v12'},
    {'name': 'dyson v11',     'anchor': ['dyson'], 'required': ['v11'],     'min_hits': 1, 'ref_price': 300, 'category': '🏠 Électroménager'},
    {'name': 'dyson airwrap', 'anchor': ['dyson'], 'required': ['airwrap'], 'min_hits': 1, 'ref_price': 0, 'category': '🏠 Électroménager', 'bm_key': 'dyson airwrap'},
    {'name': 'thermomix tm6', 'anchor': ['thermomix'], 'required': ['tm6'], 'min_hits': 1, 'ref_price': 900, 'category': '🏠 Électroménager'},
    {'name': 'thermomix',     'anchor': ['thermomix'], 'required': [],      'min_hits': 0, 'exclude': ['tm6'], 'ref_price': 600, 'category': '🏠 Électroménager'},

    # ──────────── MONTRES ────────────
    {'name': 'rolex submariner', 'anchor': ['rolex'], 'required': ['submariner'], 'min_hits': 1, 'ref_price': 9000,  'category': '⌚ Montres'},
    {'name': 'rolex datejust',   'anchor': ['rolex'], 'required': ['datejust'],   'min_hits': 1, 'ref_price': 6500,  'category': '⌚ Montres'},
    {'name': 'rolex daytona',    'anchor': ['rolex'], 'required': ['daytona'],    'min_hits': 1, 'ref_price': 15000, 'category': '⌚ Montres'},
    {'name': 'rolex',            'anchor': ['rolex'], 'required': [],             'min_hits': 0, 'ref_price': 7000,  'category': '⌚ Montres'},
    {'name': 'omega seamaster',  'anchor': ['omega'], 'required': ['seamaster'],  'min_hits': 1, 'ref_price': 2800,  'category': '⌚ Montres'},
    {'name': 'omega speedmaster','anchor': ['omega'], 'required': ['speedmaster'],'min_hits': 1, 'ref_price': 3500,  'category': '⌚ Montres'},
    {'name': 'omega',            'anchor': ['omega'], 'required': ['montre'],     'min_hits': 1, 'ref_price': 2000,  'category': '⌚ Montres'},
    {'name': 'tag heuer carrera','anchor': ['tag heuer'], 'required': ['carrera'],'min_hits': 1, 'ref_price': 1500,  'category': '⌚ Montres'},
    {'name': 'tag heuer',        'anchor': ['tag heuer'], 'required': [],         'min_hits': 0, 'ref_price': 1200,  'category': '⌚ Montres'},
    {'name': 'breitling',        'anchor': ['breitling'], 'required': [],         'min_hits': 0, 'ref_price': 2500,  'category': '⌚ Montres'},
    {'name': 'seiko',            'anchor': ['seiko'], 'required': ['srpd','skx','presage','prospex','montre'], 'min_hits': 1, 'ref_price': 150, 'category': '⌚ Montres'},
    {'name': 'casio g-shock',    'anchor': ['g-shock','gshock'], 'required': [],  'min_hits': 0, 'ref_price': 80,   'category': '⌚ Montres'},
    {'name': 'apple watch ultra','anchor': ['apple watch'], 'required': ['ultra'],'min_hits': 1, 'ref_price': 650,  'category': '⌚ Montres'},
    {'name': 'apple watch',      'anchor': ['apple watch'], 'required': [],       'min_hits': 0, 'exclude': ['ultra'], 'ref_price': 280, 'category': '⌚ Montres'},

    # ──────────── PHOTO NICHE ────────────
    {'name': 'leica m6',  'anchor': ['leica'], 'required': ['m6'],  'min_hits': 1, 'ref_price': 2800, 'category': '📷 Photo Niche'},
    {'name': 'leica m3',  'anchor': ['leica'], 'required': ['m3'],  'min_hits': 1, 'ref_price': 1800, 'category': '📷 Photo Niche'},
    {'name': 'leica m4',  'anchor': ['leica'], 'required': ['m4'],  'min_hits': 1, 'ref_price': 1500, 'category': '📷 Photo Niche'},
    {'name': 'leica m2',  'anchor': ['leica'], 'required': ['m2'],  'min_hits': 1, 'ref_price': 1200, 'category': '📷 Photo Niche'},
    {'name': 'leica',     'anchor': ['leica'], 'required': [],      'min_hits': 0, 'ref_price': 1500, 'category': '📷 Photo Niche'},
    {'name': 'hasselblad','anchor': ['hasselblad'], 'required': [], 'min_hits': 0, 'ref_price': 2000, 'category': '📷 Photo Niche'},
    {'name': 'rolleiflex','anchor': ['rolleiflex'], 'required': [], 'min_hits': 0, 'ref_price': 600,  'category': '📷 Photo Niche'},
    {'name': 'rolleicord','anchor': ['rolleicord'], 'required': [], 'min_hits': 0, 'ref_price': 280,  'category': '📷 Photo Niche'},
    {'name': 'contax',    'anchor': ['contax'], 'required': ['zeiss','t2','g2','rts'], 'min_hits': 1, 'ref_price': 400, 'category': '📷 Photo Niche'},
    {'name': 'mamiya',    'anchor': ['mamiya'], 'required': ['rb67','rz67','645'], 'min_hits': 1, 'ref_price': 500, 'category': '📷 Photo Niche'},
    {'name': 'nikon f2',  'anchor': ['nikon'], 'required': ['f2', 'argentique'], 'min_hits': 2, 'ref_price': 350, 'category': '📷 Photo Niche'},
    {'name': 'canon ae-1','anchor': ['canon'], 'required': ['ae-1','ae1'], 'min_hits': 1, 'ref_price': 180, 'category': '📷 Photo Niche'},

    # ──────────── HIFI VINTAGE ────────────
    {'name': 'bang & olufsen beolab', 'anchor': ['beolab'],   'required': [],         'min_hits': 0, 'ref_price': 1200, 'category': '🔊 Audio Vintage'},
    {'name': 'bang & olufsen beoplay','anchor': ['beoplay'],  'required': [],         'min_hits': 0, 'ref_price': 300,  'category': '🔊 Audio Vintage'},
    {'name': 'bang & olufsen beosound','anchor': ['beosound'],'required': [],         'min_hits': 0, 'ref_price': 500,  'category': '🔊 Audio Vintage'},
    {'name': 'bang & olufsen',        'anchor': ['bang olufsen','bang & olufsen'], 'required': [], 'min_hits': 0, 'ref_price': 800, 'category': '🔊 Audio Vintage'},
    {'name': 'marantz',  'anchor': ['marantz'], 'required': ['ampli','receiver','hifi','platine','cd'], 'min_hits': 1, 'ref_price': 400, 'category': '🔊 Audio Vintage'},
    {'name': 'mcintosh', 'anchor': ['mcintosh'],'required': [],         'min_hits': 0, 'ref_price': 2000, 'category': '🔊 Audio Vintage'},
    {'name': 'technics sl-1200', 'anchor': ['technics'], 'required': ['sl-1200','sl1200'], 'min_hits': 1, 'ref_price': 900, 'category': '🔊 Audio Vintage'},
    {'name': 'technics',         'anchor': ['technics'], 'required': ['platine', 'turntable'], 'min_hits': 1, 'ref_price': 300, 'category': '🔊 Audio Vintage'},
    {'name': 'sansui',   'anchor': ['sansui'],   'required': ['ampli','tuner','receiver'], 'min_hits': 1, 'ref_price': 350, 'category': '🔊 Audio Vintage'},
    {'name': 'yamaha hifi', 'anchor': ['yamaha'], 'required': ['ampli','receiver','hifi'], 'min_hits': 2, 'ref_price': 250, 'category': '🔊 Audio Vintage', 'exclude': ['voiture','moto','scooter','deux roues']},
    {'name': 'naim audio',  'anchor': ['naim'],   'required': ['nait','cd','ampli','streamer'], 'min_hits': 1, 'ref_price': 1200, 'category': '🔊 Audio Vintage'},
    {'name': 'linn sondek', 'anchor': ['linn'],   'required': ['sondek','lp12'],              'min_hits': 1, 'ref_price': 1500, 'category': '🔊 Audio Vintage'},

    # ──────────── INSTRUMENTS ────────────
    {'name': 'gibson les paul', 'anchor': ['gibson'],  'required': ['les paul'],     'min_hits': 1, 'ref_price': 2500, 'category': '🎸 Instruments'},
    {'name': 'gibson sg',       'anchor': ['gibson'],  'required': ['sg'],            'min_hits': 1, 'ref_price': 1500, 'category': '🎸 Instruments'},
    {'name': 'gibson es',       'anchor': ['gibson'],  'required': ['es-335','es335','es-175'], 'min_hits': 1, 'ref_price': 2000, 'category': '🎸 Instruments'},
    {'name': 'gibson',          'anchor': ['gibson'],  'required': ['guitare','guitar'], 'min_hits': 1, 'ref_price': 1800, 'category': '🎸 Instruments'},
    {'name': 'fender stratocaster','anchor': ['fender'],'required': ['stratocaster','strat'], 'min_hits': 1, 'ref_price': 1200, 'category': '🎸 Instruments'},
    {'name': 'fender telecaster',  'anchor': ['fender'],'required': ['telecaster','tele'],    'min_hits': 1, 'ref_price': 1000, 'category': '🎸 Instruments'},
    {'name': 'martin guitar',      'anchor': ['martin'],'required': ['guitare','guitar','acoustique','d-28','d28'], 'min_hits': 1, 'ref_price': 1500, 'category': '🎸 Instruments'},
    {'name': 'selmer saxophone',   'anchor': ['selmer'],'required': ['saxophone','sax'],      'min_hits': 1, 'ref_price': 3000, 'category': '🎸 Instruments'},
    {'name': 'yamaha dx7',  'anchor': ['yamaha'], 'required': ['dx7'],               'min_hits': 1, 'ref_price': 600,  'category': '🎸 Instruments'},
    {'name': 'roland juno',  'anchor': ['roland'], 'required': ['juno'],             'min_hits': 1, 'ref_price': 800,  'category': '🎸 Instruments'},
    {'name': 'roland jupiter','anchor': ['roland'], 'required': ['jupiter'],         'min_hits': 1, 'ref_price': 1200, 'category': '🎸 Instruments'},

    # ──────────── DESIGN NICHE ────────────
    {'name': 'braun dieter rams','anchor': ['braun'], 'required': ['dieter rams','calculator','calculatrice','rasoir vintage','radio vintage'], 'min_hits': 1, 'ref_price': 600, 'category': '🎨 Design Niche'},
    {'name': 'braun vintage',    'anchor': ['braun'], 'required': ['vintage'],         'min_hits': 1, 'ref_price': 150, 'category': '🎨 Design Niche'},
    {'name': 'usm haller',       'anchor': ['usm haller','usm modulaire'], 'required': [], 'min_hits': 0, 'ref_price': 1500, 'category': '🎨 Design Niche'},
    {'name': 'knoll saarinen',   'anchor': ['saarinen','knoll tulip'],     'required': [], 'min_hits': 0, 'ref_price': 600, 'category': '🎨 Design Niche'},
    {'name': 'artek aalto',      'anchor': ['artek','alvar aalto'],        'required': [], 'min_hits': 0, 'ref_price': 800, 'category': '🎨 Design Niche'},
    {'name': 'charlotte perriand','anchor': ['charlotte perriand'],        'required': [], 'min_hits': 0, 'ref_price': 1200,'category': '🎨 Design Niche'},

    # ──────────── OUTDOOR PREMIUM ────────────
    {'name': "arc'teryx alpha", 'anchor': ['arcteryx','arc teryx'], 'required': ['alpha','beta','atom','zeta'], 'min_hits': 1, 'ref_price': 600, 'category': '🧥 Outdoor Premium'},
    {'name': "arc'teryx",       'anchor': ['arcteryx','arc teryx'], 'required': [],  'min_hits': 0, 'ref_price': 400, 'category': '🧥 Outdoor Premium'},
    {'name': 'patagonia nano puff', 'anchor': ['patagonia'], 'required': ['nano puff','nano-puff'], 'min_hits': 1, 'ref_price': 200, 'category': '🧥 Outdoor Premium'},
    {'name': 'patagonia retro x',   'anchor': ['patagonia'], 'required': ['retro x','retro-x'],     'min_hits': 1, 'ref_price': 250, 'category': '🧥 Outdoor Premium'},
    {'name': 'patagonia',           'anchor': ['patagonia'], 'required': ['veste','doudoune','gilet','polaire','jacket'], 'min_hits': 1, 'ref_price': 180, 'category': '🧥 Outdoor Premium'},
    {'name': 'stone island',    'anchor': ['stone island'], 'required': [],  'min_hits': 0, 'ref_price': 400, 'category': '🧥 Outdoor Premium'},
    {'name': 'canada goose',    'anchor': ['canada goose'], 'required': [],  'min_hits': 0, 'ref_price': 700, 'category': '🧥 Outdoor Premium'},
    {'name': 'moncler',         'anchor': ['moncler'],      'required': ['doudoune','veste','gilet'], 'min_hits': 1, 'ref_price': 900, 'category': '🧥 Outdoor Premium'},

    # ──────────── LUXE / MAROQUINERIE ────────────
    {'name': 'hermes birkin',    'anchor': ['hermes','hermès'], 'required': ['birkin'],       'min_hits': 1, 'ref_price': 8000, 'category': '👜 Luxe/Mode'},
    {'name': 'hermes kelly',     'anchor': ['hermes','hermès'], 'required': ['kelly'],        'min_hits': 1, 'ref_price': 6000, 'category': '👜 Luxe/Mode'},
    {'name': 'hermes',           'anchor': ['hermes','hermès'], 'required': ['sac','pochette','ceinture','foulard'], 'min_hits': 1, 'ref_price': 3000, 'category': '👜 Luxe/Mode'},
    {'name': 'chanel classic',   'anchor': ['chanel'],  'required': ['classic flap','2.55'], 'min_hits': 1, 'ref_price': 5000, 'category': '👜 Luxe/Mode'},
    {'name': 'chanel',           'anchor': ['chanel'],  'required': ['sac','pochette'],      'min_hits': 1, 'ref_price': 2000, 'category': '👜 Luxe/Mode'},
    {'name': 'louis vuitton neverfull','anchor': ['louis vuitton','vuitton'], 'required': ['neverfull'], 'min_hits': 1, 'ref_price': 900, 'category': '👜 Luxe/Mode'},
    {'name': 'louis vuitton',    'anchor': ['louis vuitton','vuitton'], 'required': ['sac','pochette','portefeuille'], 'min_hits': 1, 'ref_price': 700, 'category': '👜 Luxe/Mode'},
    {'name': 'dior',             'anchor': ['dior'],    'required': ['sac','pochette'],      'min_hits': 1, 'ref_price': 800, 'category': '👜 Luxe/Mode'},
    {'name': 'gucci',            'anchor': ['gucci'],   'required': ['sac','pochette','ceinture'], 'min_hits': 1, 'ref_price': 500, 'category': '👜 Luxe/Mode'},

    # ──────────── SNEAKERS ────────────
    {'name': 'yeezy 350',      'anchor': ['yeezy'],   'required': ['350'],              'min_hits': 1, 'ref_price': 220, 'category': '👟 Sneakers'},
    {'name': 'jordan 1',       'anchor': ['jordan 1','air jordan 1','aj1'], 'required': [], 'min_hits': 0, 'ref_price': 170, 'category': '👟 Sneakers'},
    {'name': 'jordan 4',       'anchor': ['jordan 4','air jordan 4','aj4'], 'required': [], 'min_hits': 0, 'ref_price': 200, 'category': '👟 Sneakers'},
    {'name': 'nike dunk',      'anchor': ['nike dunk'],   'required': [],               'min_hits': 0, 'ref_price': 110, 'category': '👟 Sneakers'},

    # ──────────── LEGO ────────────
    {'name': 'lego technic',   'anchor': ['lego'], 'required': ['technic'],    'min_hits': 1, 'ref_price': 180, 'category': '🧱 LEGO'},
    {'name': 'lego star wars', 'anchor': ['lego'], 'required': ['star wars'],  'min_hits': 1, 'ref_price': 200, 'category': '🧱 LEGO'},
    {'name': 'lego creator',   'anchor': ['lego'], 'required': ['creator'],    'min_hits': 1, 'ref_price': 150, 'category': '🧱 LEGO'},
    {'name': 'lego',           'anchor': ['lego'], 'required': ['boite','set','complet'], 'min_hits': 1, 'ref_price': 80, 'category': '🧱 LEGO'},
]

# Index BackMarket pour les produits à prix live
BM_KEYS = {e['name']: e['bm_key'] for e in CATALOG if 'bm_key' in e}

LOT_TRIGGER_WORDS = ['lot', 'ensemble', 'vrac', 'collection', 'caisse', 'divers',
                     'melange', 'assortiment', 'carton', 'palette']

HEADERS_POOL = [
    {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'},
    {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0'},
    {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15'},
]

_bm_price_cache = {}
_bm_cache_ts    = {}
_bm_cache_lock  = threading.Lock()
BM_CACHE_TTL    = 6 * 3600


# ─────────────────────────────────────────────────────────────────────────────
# MOBILIER PREMIUM MÉCONNU
# ─────────────────────────────────────────────────────────────────────────────

GENERIC_TITLES = [
    'chaise bureau', 'fauteuil bureau', 'siege bureau', 'chaise ergonomique',
    'chaise filet', 'chaise mesh', 'siege ergonomique', 'chaise gaming'
]
UNCERTAIN_PHRASES = [
    'je ne connais pas la marque', 'sans marque', 'recuperation', 'debarras',
    'vide bureau', 'ancien materiel', 'lot mobilier', 'succession',
    'marque inconnue', 'open space', 'liquidation', 'vide local'
]

PREMIUM_FURNITURE = {
    'herman miller aeron': {
        'brand': 'herman miller', 'category': '🪑 Mobilier Premium', 'market_price': 600,
        'strong_features': ['posturefit', 'pellicle', 'aeron', '8z pellicle', 'posturefit sl'],
        'shape_features': ['maille', 'mesh', 'filet', 'molette inclinaison', 'accoudoirs reglables']
    },
    'herman miller embody': {
        'brand': 'herman miller', 'category': '🪑 Mobilier Premium', 'market_price': 900,
        'strong_features': ['embody', 'backfit', 'herman miller'],
        'shape_features': ['colonne centrale', 'ribs', 'assise multicouche']
    },
    'herman miller mirra': {
        'brand': 'herman miller', 'category': '🪑 Mobilier Premium', 'market_price': 300,
        'strong_features': ['mirra', 'herman miller'],
        'shape_features': ['dossier plastique perfore', 'dossier ventile']
    },
    'steelcase leap': {
        'brand': 'steelcase', 'category': '🪑 Mobilier Premium', 'market_price': 500,
        'strong_features': ['steelcase', 'leap', 'liveback', 'natural glide'],
        'shape_features': ['dossier flexible', 'accoudoirs 4d']
    },
    'steelcase gesture': {
        'brand': 'steelcase', 'category': '🪑 Mobilier Premium', 'market_price': 600,
        'strong_features': ['steelcase', 'gesture'],
        'shape_features': ['accoudoirs 360', 'accoudoirs pivotants']
    },
    'humanscale freedom': {
        'brand': 'humanscale', 'category': '🪑 Mobilier Premium', 'market_price': 650,
        'strong_features': ['humanscale', 'freedom'],
        'shape_features': ['appuie-tete integre', 'inclinaison automatique']
    },
    'vitra eames': {
        'brand': 'vitra', 'category': '🪑 Mobilier Premium', 'market_price': 900,
        'strong_features': ['vitra', 'eames', 'lounge chair', 'daw', 'dsx'],
        'shape_features': ['coque plastique', 'pied tour eiffel']
    },
}


def _tokenize(text):
    """Retourne le texte minuscule normalisé (accents basiques retirés)."""
    t = text.lower()
    for a, b in [('é','é'),('à','a'),('è','e'),('ê','e'),('ô','o'),('û','u'),('ü','u')]:
        t = t.replace(a, b)
    return t


def _anchor_present(text, anchors):
    """Vérifie qu'AU MOINS UN anchor est présent dans le texte."""
    return any(a in text for a in anchors)


def _count_required(text, required):
    return sum(1 for r in required if r in text)


def _exclude_hit(text, excludes):
    return any(e in text for e in (excludes or []))


def match_catalog(title, description=''):
    """
    Retourne la liste des objets détectés avec leur prix de référence.
    Logique :
      1. Pour chaque entrée CATALOG (ordre = spécifique → générique) :
         - anchor obligatoire présent
         - required count >= min_hits
         - aucun mot d'exclusion
      2. Dès qu'un match plus spécifique est trouvé pour une famille,
         on ne remonte pas le fallback générique (flag seen_anchor).
    """
    text = _tokenize(title + ' ' + description)
    detected = []
    seen_anchors = set()

    for entry in CATALOG:
        anchors = entry['anchor']
        anchor_key = anchors[0]
        if anchor_key in seen_anchors:
            continue
        if not _anchor_present(text, anchors):
            continue
        required = entry.get('required', [])
        min_hits = entry.get('min_hits', 0)
        excludes = entry.get('exclude', [])
        if _exclude_hit(text, excludes):
            continue
        hits = _count_required(text, required)
        if hits < min_hits:
            continue
        ref_price = entry.get('ref_price', 0)
        bm_key = entry.get('bm_key')
        if bm_key:
            live = scrape_backmarket_price(bm_key)
            if live:
                ref_price = live
            elif ref_price == 0:
                ref_price = EMERGENCY_PRICES.get(bm_key, 0)
        if ref_price <= 0:
            continue
        detected.append({
            'name': entry['name'],
            'ref_price': ref_price,
            'category': entry['category'],
            'confidence': 90 if hits >= min_hits and min_hits > 0 else 70,
        })
        seen_anchors.add(anchor_key)
    is_lot = any(w in text for w in LOT_TRIGGER_WORDS)
    return detected, is_lot


EMERGENCY_PRICES = {
    'samsung galaxy s24 ultra': 750, 'samsung galaxy s24': 580,
    'ps5': 380, 'xbox series x': 350, 'nintendo switch oled': 230, 'steam deck': 360,
    'macbook pro m3': 1600, 'macbook pro m2': 1200, 'macbook pro m1': 900,
    'macbook air m2': 850, 'macbook air m1': 620,
    'ipad pro': 600, 'ipad air': 450,
    'dyson v15': 420, 'dyson v12': 340, 'dyson airwrap': 380,
}


# ─────────────────────────────────────────────────────────────────────────────
# MOBILIER : détection sémantème visuel
# ─────────────────────────────────────────────────────────────────────────────

def detect_premium_furniture(title, description=''):
    text = _tokenize(title + ' ' + description)
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
    text = _tokenize(title + ' ' + description)
    t = _tokenize(title)
    score = 0
    if any(g in t for g in GENERIC_TITLES):
        score += 20
    if any(p in text for p in UNCERTAIN_PHRASES):
        score += 25
    if detected_model and detected_model in PREMIUM_FURNITURE:
        brand = PREMIUM_FURNITURE[detected_model]['brand']
        if brand not in t:
            score += 20
        model_short = detected_model.split()[-1]
        if model_short not in t:
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
    text = text.replace('\xa0','').replace('\u202f','').replace('\u00a0','').replace(' ','').replace(',','.')
    m = re.search(r'([\d]+\.?[\d]*)', text)
    if m:
        try:
            v = float(m.group(1))
            return v if v > 0 else None
        except Exception:
            return None
    return None


def scrape_backmarket_price(product_name):
    now = time.time()
    with _bm_cache_lock:
        if now - _bm_cache_ts.get(product_name, 0) < BM_CACHE_TTL and product_name in _bm_price_cache:
            return _bm_price_cache[product_name]
    try:
        url = f'https://www.backmarket.fr/fr-fr/search?q={requests.utils.quote(product_name)}&grade=9'
        h = get_headers()
        h.update({'Accept-Language': 'fr-FR,fr;q=0.9', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'})
        resp = requests.get(url, headers=h, timeout=15)
        delay(short=True)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, 'html5lib')
        candidates = []
        for el in soup.select('[data-qa="product-price"],[class*="price"],[class*="Price"]'):
            p = extract_price(el.get_text(strip=True))
            if p and 10 < p < 20000:
                candidates.append(p)
        if not candidates:
            script = soup.find('script', {'id': '__NEXT_DATA__'})
            if script and script.string:
                for m in re.findall(r'"price"\s*:\s*"?([\d]+\.?[\d]*)"?', script.string):
                    try:
                        p = float(m)
                        if 10 < p < 20000: candidates.append(p)
                    except Exception: pass
        if candidates:
            best = min(candidates)
            with _bm_cache_lock:
                _bm_price_cache[product_name] = best
                _bm_cache_ts[product_name] = now
            print(f'[BM] {product_name} → {best}€')
            return best
    except Exception as e:
        print(f'[BM] Erreur {product_name}: {e}')
    return None


def prefetch_backmarket_prices():
    keys = list({e['bm_key'] for e in CATALOG if 'bm_key' in e})
    def _run():
        for k in keys[:20]:
            now = time.time()
            with _bm_cache_lock:
                fresh = now - _bm_cache_ts.get(k, 0) < BM_CACHE_TTL and k in _bm_price_cache
            if not fresh:
                scrape_backmarket_price(k)
                time.sleep(random.uniform(1.0, 2.0))
    threading.Thread(target=_run, daemon=True).start()


def calculate_deal_score(price, ref_price, is_lot=False, nb_detected=0):
    if not price or not ref_price or price <= 0:
        return 0, 0
    eff = ref_price * min(nb_detected, 3) * 0.6 if is_lot and nb_detected > 1 else ref_price
    disc = ((eff - price) / eff) * 100
    if disc <= 0: score = 0
    elif disc < 20: score = disc * 1.5
    elif disc < 40: score = 30 + (disc - 20) * 2
    elif disc < 60: score = 70 + (disc - 40)
    else: score = min(90 + (disc - 60) * 0.5, 100)
    return round(disc, 1), round(score)


# ─────────────────────────────────────────────────────────────────────────────
# SCRAPER
# ─────────────────────────────────────────────────────────────────────────────

class DealScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(get_headers())
        print('[BM] Pré-chargement des prix BackMarket...')
        prefetch_backmarket_prices()

    def _parse_listing(self, item, platform, color):
        try:
            title_el = item.select_one('[class*="title"],[class*="Title"]') or item.find(['h2','h3','p'])
            price_el = item.select_one('[class*="price"],[class*="Price"]') or item.find(string=re.compile(r'\d+\s*€'))
            link_el  = item if item.name == 'a' else item.find('a')
            img_el   = item.find('img')
            title = title_el.get_text(strip=True) if title_el else ''
            price_text = price_el.get_text(strip=True) if hasattr(price_el, 'get_text') else str(price_el or '')
            price = extract_price(price_text)
            href = link_el.get('href', '') if link_el else ''
            if href.startswith('http'): link = href
            elif href.startswith('/'): link = ('https://www.leboncoin.fr' if platform == 'LeBonCoin' else 'https://www.vinted.fr') + href
            else: link = ''
            img = (img_el.get('src') or img_el.get('data-src', '')) if img_el else ''
            if title and price and 1 < price < 50000:
                return {'title': title, 'price': price, 'link': link, 'image': img, 'platform': platform, 'platform_color': color}
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
            items = (soup.select('[data-test-id="ad"]') or soup.select('article[class*="styles_adCard"]')
                     or soup.select('article') or soup.select('li[class*="aditem"]'))
            for item in items[:max_results]:
                r = self._parse_listing(item, 'LeBonCoin', '#F56B2A')
                if r: results.append(r)
        except Exception as e:
            print(f'[LBC] {e}')
        return results

    def scrape_vinted(self, query, max_results=30):
        results = []
        try:
            url = f'https://www.vinted.fr/catalog?search_text={requests.utils.quote(query)}&order=newest_first'
            resp = self.session.get(url, headers=get_headers(), timeout=15)
            delay()
            soup = BeautifulSoup(resp.text, 'html5lib')
            items = (soup.select('[data-testid="grid-item"]') or soup.select('.feed-grid__item')
                     or soup.select('[class*="ItemBox"]'))
            for item in items[:max_results]:
                r = self._parse_listing(item, 'Vinted', '#09B1BA')
                if r: results.append(r)
        except Exception as e:
            print(f'[Vinted] {e}')
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
                    te = item.select_one('.s-item__title')
                    pe = item.select_one('.s-item__price')
                    le = item.select_one('a.s-item__link') or item.find('a')
                    ie = item.find('img')
                    title = te.get_text(strip=True) if te else ''
                    if 'Shop on eBay' in title or not title: continue
                    price = extract_price(pe.get_text(strip=True) if pe else '')
                    if price and 1 < price < 50000:
                        results.append({'title': title, 'price': price, 'link': le.get('href','') if le else '',
                                        'image': ie.get('src','') if ie else '', 'platform': 'eBay', 'platform_color': '#E53238'})
                except Exception: continue
        except Exception as e:
            print(f'[eBay] {e}')
        return results

    def analyze_listings(self, listings, min_discount=40):
        deals = []
        for item in listings:
            title = item.get('title', '')
            description = item.get('description', '')
            price = item.get('price')
            if not price:
                continue

            detected_objects, is_lot = match_catalog(title, description)

            furniture_model, furniture_conf = detect_premium_furniture(title, description)
            kg_score = knowledge_gap_score(title, description, furniture_model)
            if furniture_model and furniture_conf >= 30:
                fd = PREMIUM_FURNITURE[furniture_model]
                detected_objects.append({
                    'name': furniture_model, 'ref_price': fd['market_price'],
                    'category': fd['category'], 'confidence': furniture_conf
                })

            if not detected_objects:
                continue

            best_obj = max(detected_objects, key=lambda x: x['ref_price'])
            disc, base_score = calculate_deal_score(price, best_obj['ref_price'], is_lot, len(detected_objects))
            final_score = round(base_score * 0.55 + kg_score * 0.45)

            if disc >= min_discount or (furniture_model and kg_score >= 50):
                result = {
                    **item,
                    'detected_objects': detected_objects,
                    'best_match': best_obj['name'],
                    'ref_price': best_obj['ref_price'],
                    'category': best_obj['category'],
                    'discount_pct': disc,
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
        if platforms is None: platforms = ['leboncoin', 'vinted', 'ebay']
        listings = []
        if 'leboncoin' in platforms: listings += self.scrape_leboncoin(keywords)
        if 'vinted'    in platforms: listings += self.scrape_vinted(keywords)
        if 'ebay'      in platforms: listings += self.scrape_ebay(keywords)
        deals = self.analyze_listings(listings, min_discount)
        return {'deals': deals, 'total_scanned': len(listings), 'total_deals': len(deals), 'query': keywords}

    def auto_hunt(self, min_discount=50, platforms=None):
        if platforms is None: platforms = ['leboncoin', 'vinted', 'ebay']
        queries = [
            'lot electronique', 'montre collection',
            'ampli hifi vintage', 'guitare electrique occasion',
            'leica appareil photo', 'chaise bureau ergonomique',
            'fauteuil ergonomique bureau', 'dyson aspirateur',
            'veste patagonia', 'arc teryx veste', 'platine vinyle'
        ]
        listings = []
        for q in queries:
            if 'leboncoin' in platforms: listings += self.scrape_leboncoin(q, max_results=15)
            if 'ebay'      in platforms: listings += self.scrape_ebay(q, max_results=15)
            time.sleep(random.uniform(0.8, 1.5))
        seen = set()
        unique = [i for i in listings if i.get('link') and i['link'] not in seen and not seen.add(i['link'])]
        deals = self.analyze_listings(unique, min_discount)
        return {'deals': deals, 'total_scanned': len(unique), 'total_deals': len(deals), 'query': 'Auto Hunt'}
