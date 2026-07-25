# 100% GRATUIT - aucune API, aucune cle, OCR local
# pip install easyocr  (tourne sur CPU, pas de GPU requis)

import re, io, requests

try:
    import easyocr
    _reader = None
    EASYOCR_OK = True
except ImportError:
    EASYOCR_OK = False

try:
    import pytesseract
    from PIL import Image as _PILImage
    TESSERACT_OK = True
except ImportError:
    TESSERACT_OK = False

try:
    from PIL import Image as _PILImage
    PIL_OK = True
except ImportError:
    PIL_OK = False

CHAIR_TRIGGER_WORDS = [
    'chaise bureau', 'fauteuil bureau', 'siege bureau',
    'chaise ergonomique', 'fauteuil ergonomique', 'siege ergonomique',
    'chaise filet', 'chaise mesh', 'chaise gaming',
    'fauteuil gaming', 'chaise pivotante', 'siege pivotant',
    'chaise direction', 'fauteuil direction',
]

PREMIUM_CHAIR_CATALOG = {
    'herman miller aeron':  {'market_price': 600,  'brand': 'Herman Miller'},
    'herman miller embody': {'market_price': 900,  'brand': 'Herman Miller'},
    'herman miller mirra':  {'market_price': 300,  'brand': 'Herman Miller'},
    'herman miller cosm':   {'market_price': 800,  'brand': 'Herman Miller'},
    'herman miller sayl':   {'market_price': 350,  'brand': 'Herman Miller'},
    'steelcase leap':       {'market_price': 500,  'brand': 'Steelcase'},
    'steelcase gesture':    {'market_price': 600,  'brand': 'Steelcase'},
    'steelcase think':      {'market_price': 400,  'brand': 'Steelcase'},
    'steelcase amia':       {'market_price': 350,  'brand': 'Steelcase'},
    'vitra eames daw':      {'market_price': 700,  'brand': 'Vitra'},
    'vitra eames dsw':      {'market_price': 600,  'brand': 'Vitra'},
    'vitra hal':            {'market_price': 450,  'brand': 'Vitra'},
    'humanscale freedom':   {'market_price': 650,  'brand': 'Humanscale'},
    'knoll barcelona':      {'market_price': 2000, 'brand': 'Knoll'},
    'okamura contessa':     {'market_price': 700,  'brand': 'Okamura'},
    'haworth fern':         {'market_price': 700,  'brand': 'Haworth'},
}

OCR_KEYWORD_MAP = {
    'aeron':         'herman miller aeron',
    'embody':        'herman miller embody',
    'mirra':         'herman miller mirra',
    'cosm':          'herman miller cosm',
    'sayl':          'herman miller sayl',
    'herman miller': 'herman miller aeron',
    'hermanmiller':  'herman miller aeron',
    'steelcase':     'steelcase leap',
    'leap':          'steelcase leap',
    'gesture':       'steelcase gesture',
    'think':         'steelcase think',
    'amia':          'steelcase amia',
    'vitra':         'vitra eames daw',
    'eames':         'vitra eames daw',
    'humanscale':    'humanscale freedom',
    'freedom':       'humanscale freedom',
    'knoll':         'knoll barcelona',
    'barcelona':     'knoll barcelona',
    'okamura':       'okamura contessa',
    'contessa':      'okamura contessa',
    'haworth':       'haworth fern',
    'fern':          'haworth fern',
}


def is_chair_listing(title: str, description: str = '') -> bool:
    text = (title + ' ' + description).lower()
    return any(t in text for t in CHAIR_TRIGGER_WORDS)


def _download_image(img_url: str):
    if not PIL_OK or not img_url:
        return None
    try:
        r = requests.get(img_url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        r.raise_for_status()
        return _PILImage.open(io.BytesIO(r.content)).convert('RGB')
    except Exception:
        return None


def _ocr_text(img) -> str:
    global _reader
    if EASYOCR_OK:
        try:
            if _reader is None:
                _reader = easyocr.Reader(['fr', 'en'], gpu=False, verbose=False)
            import numpy as np
            return ' '.join(_reader.readtext(np.array(img), detail=0)).lower()
        except Exception:
            pass
    if TESSERACT_OK:
        try:
            return pytesseract.image_to_string(img, lang='fra+eng').lower()
        except Exception:
            pass
    return ''


def _match_ocr(ocr_text: str) -> tuple:
    found = {}
    for keyword, catalog_key in OCR_KEYWORD_MAP.items():
        if keyword in ocr_text:
            found[catalog_key] = found.get(catalog_key, 0) + 1
    if not found:
        return None, 0
    best = max(found, key=found.get)
    confidence = min(70 + found[best] * 10, 95)
    return best, confidence


def identify_chair_local(img_url: str) -> dict:
    empty = {'model': None, 'brand': None, 'confidence': 0, 'market_price': 0}
    if not (EASYOCR_OK or TESSERACT_OK):
        return empty
    img = _download_image(img_url)
    if img is None:
        return empty
    ocr_text = _ocr_text(img)
    if not ocr_text.strip():
        return empty
    model_key, confidence = _match_ocr(ocr_text)
    if not model_key:
        return empty
    entry = PREMIUM_CHAIR_CATALOG.get(model_key, {})
    return {
        'model':        model_key,
        'brand':        entry.get('brand'),
        'confidence':   confidence,
        'market_price': entry.get('market_price', 0),
    }


def analyze_chair_deal(item: dict, min_confidence: int = 65) -> dict | None:
    if not is_chair_listing(item.get('title', ''), item.get('desc', '')):
        return None
    if not item.get('img') or not item.get('price'):
        return None
    result = identify_chair_local(item['img'])
    if not result['model'] or result['confidence'] < min_confidence:
        return None
    if result['market_price'] <= 0:
        return None
    ref      = result['market_price']
    price    = item['price']
    disc_pct = round((ref - price) / ref * 100, 1)
    savings  = round(ref - price, 2)
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
        'vision_details':    '',
        'vision_confidence': result['confidence'],
        'vendor_unaware':    True,
    }


def ocr_available() -> bool:
    return EASYOCR_OK or TESSERACT_OK
