from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from scraper import DealScraper

app = Flask(__name__)
CORS(app)

scraper = DealScraper()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search():
    data = request.json
    keywords = data.get('keywords', '')
    min_discount = data.get('min_discount', 40)
    platforms = data.get('platforms', ['leboncoin', 'vinted', 'ebay'])
    results = scraper.search_deals(
        keywords=keywords,
        min_discount=min_discount,
        platforms=platforms
    )
    return jsonify(results)

@app.route('/api/auto_hunt', methods=['POST'])
def auto_hunt():
    data = request.json
    min_discount = data.get('min_discount', 50)
    platforms = data.get('platforms', ['leboncoin', 'vinted', 'ebay'])
    results = scraper.auto_hunt(min_discount=min_discount, platforms=platforms)
    return jsonify(results)

@app.route('/api/categories')
def get_categories():
    return jsonify(scraper.get_value_categories())

@app.route('/api/cache_status')
def cache_status():
    """Retourne les prix BackMarket actuellement en cache (source live)."""
    return jsonify(scraper.get_cache_status())

if __name__ == '__main__':
    print('\n🔍 Deal Hunter démarré sur http://localhost:5000')
    print('📊 Prix référence : BackMarket live (cache 6h) + fixes pour montres/luxe/sneakers\n')
    app.run(debug=False, port=5000, threaded=True)
