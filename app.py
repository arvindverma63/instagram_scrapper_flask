from flask import Flask, request, jsonify
from flasgger import Swagger, swag_from
from scraper import get_instagram_data, get_reel_data

app = Flask(__name__)
swagger = Swagger(app)

@app.route('/api/profile', methods=['GET'])
@swag_from({
    'tags': ['Instagram Profile Scraper'],
    'parameters': [
        {
            'name': 'username',
            'in': 'query',
            'type': 'string',
            'required': True,
            'description': 'The Instagram username to scrape (e.g., sufitramp)'
        }
    ],
    'responses': {
        200: {
            'description': 'Successfully scraped profile data',
            'schema': {
                'type': 'object',
                'properties': {
                    'ID': {'type': 'string'},
                    'Followers': {'type': 'integer'},
                    'Following': {'type': 'integer'},
                    'Posts': {'type': 'integer'}
                }
            }
        },
        400: {
            'description': 'Missing username parameter'
        },
        500: {
            'description': 'Failed to scrape profile data'
        }
    }
})
def scrape_profile():
    """Scrape Instagram profile data (Followers, Following, Posts) for a given username."""
    username = request.args.get('username')
    if not username:
        return jsonify({'error': 'Missing username parameter'}), 400

    data, error = get_instagram_data(username)
    if error:
        return jsonify({'error': error}), 500

    return jsonify(data), 200

@app.route('/api/reel', methods=['GET'])
@swag_from({
    'tags': ['Instagram Reel Scraper'],
    'parameters': [
        {
            'name': 'reel_url',
            'in': 'query',
            'type': 'string',
            'required': True,
            'description': 'The URL of the Instagram reel to scrape (e.g., https://www.instagram.com/reel/DKjwPKyPo0d/)'
        }
    ],
    'responses': {
        200: {
            'description': 'Successfully scraped reel data',
            'schema': {
                'type': 'object',
                'properties': {
                    'Reel_URL': {'type': 'string'},
                    'Likes': {'type': 'integer'},
                    'Comments': {'type': 'integer'},
                    'Upload_Date': {'type': 'string', 'format': 'date'}
                }
            }
        },
        400: {
            'description': 'Missing reel_url parameter'
        },
        500: {
            'description': 'Failed to scrape reel data'
        }
    }
})
def scrape_reel():
    """Scrape Instagram reel data (Likes, Comments, Upload Date) for a given URL."""
    reel_url = request.args.get('reel_url')
    if not reel_url:
        return jsonify({'error': 'Missing reel_url parameter'}), 400

    data, error = get_reel_data(reel_url)
    if error:
        return jsonify({'error': error}), 500

    return jsonify(data), 200

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)