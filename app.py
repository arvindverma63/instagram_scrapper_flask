from flask import Flask, request, jsonify
from flasgger import Swagger, swag_from
from flask_cors import CORS
import asyncio
import logging

from scraper import get_instagram_data, get_reel_data
from tiktok_scraper import scrape_tiktok_profile

app = Flask(__name__)
swagger = Swagger(app)
CORS(app)  # Enable CORS for frontend API calls

# Setup basic logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


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
def scrape_instagram_profile():
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
def scrape_instagram_reel():
    """Scrape Instagram reel data (Likes, Comments, Upload Date) for a given URL."""
    reel_url = request.args.get('reel_url')
    if not reel_url:
        return jsonify({'error': 'Missing reel_url parameter'}), 400

    data, error = get_reel_data(reel_url)
    if error:
        return jsonify({'error': error}), 500

    return jsonify(data), 200


@app.route('/api/tiktok_profile', methods=['GET'])
@swag_from({
    'tags': ['TikTok Profile Scraper'],
    'parameters': [
        {
            'name': 'username',
            'in': 'query',
            'type': 'string',
            'required': True,
            'description': 'The TikTok username to scrape (e.g., marylou.sidibe)'
        }
    ],
    'responses': {
        200: {
            'description': 'Successfully scraped profile data',
            'schema': {
                'type': 'object',
                'properties': {
                    'name': {'type': 'string', 'description': 'Full name of the profile'},
                    'followers': {'type': 'integer', 'description': 'Number of followers'},
                    'following': {'type': 'integer', 'description': 'Number of accounts followed'},
                    'likes': {'type': 'integer', 'description': 'Total likes on posts'},
                    'bio': {'type': 'string', 'description': 'Profile biography'},
                    'link': {'type': 'string', 'description': 'External link in bio'}
                }
            }
        },
        400: {
            'description': 'Missing username parameter',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        },
        500: {
            'description': 'Failed to scrape profile data',
            'schema': {
                'type': 'object',
                'properties': {
                    'error': {'type': 'string'}
                }
            }
        }
    }
})
def scrape_tiktok_profile_data():
    """Scrape TikTok profile data (name, followers, following, likes, bio, link) for a given username."""
    username = request.args.get('username')
    if not username:
        logger.error("Missing username parameter")
        return jsonify({'error': 'Missing username parameter'}), 400

    try:
        logger.info(f"Scraping TikTok profile for username: {username}")
        data = asyncio.run(scrape_tiktok_profile(username))
        if 'error' in data:
            logger.error(f"Scraper error: {data['error']}")
            return jsonify({'error': data['error']}), 500
        return jsonify(data), 200
    except Exception as e:
        logger.error(f"API error: {str(e)}")
        return jsonify({'error': f"Failed to scrape profile: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=False, host='0.0.0.0', port=5000)
