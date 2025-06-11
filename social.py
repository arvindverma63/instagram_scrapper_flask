from flask import Flask, request, jsonify
from flasgger import Swagger, swag_from
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import re
import time
import os
from datetime import datetime

app = Flask(__name__)
swagger = Swagger(app)

def parse_number(text):
    """Convert formatted number (e.g., '1.2M', '1,234') to integer."""
    text = text.replace(',', '')
    if 'M' in text:
        return int(float(text.replace('M', '')) * 1_000_000)
    elif 'K' in text:
        return int(float(text.replace('K', '')) * 1_000)
    return int(text)

def parse_date(date_str):
    """Convert date string (e.g., 'June 6, 2025') to YYYY-MM-DD format."""
    try:
        return datetime.strptime(date_str, "%B %d, %Y").strftime("%Y-%m-%d")
    except ValueError as e:
        print(f"Date parsing error: {e}")
        return None

def get_instagram_data(username, retries=2):
    """Scrape Instagram profile data (Followers, Following, Posts)."""
    url = f"https://www.instagram.com/{username}/"
    data = {"ID": username, "Followers": None, "Following": None, "Posts": None}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        stealth_sync(page)

        for attempt in range(retries):
            try:
                print(f"Attempt {attempt + 1}: Navigating to {url}")
                page.goto(url, timeout=60000)
                page.wait_for_load_state("networkidle", timeout=40000)
                print(f"Page loaded for {username}, searching for meta tags...")

                meta_tags = page.query_selector_all('meta[property="og:description"], meta[name="description"]')
                for meta in meta_tags:
                    content = meta.get_attribute("content")
                    if content:
                        match = re.search(r"(\d[\d,\.MK]*)\s*Followers,\s*(\d[\d,\.MK]*)\s*Following,\s*(\d[\d,\.MK]*)\s*Posts", content, re.IGNORECASE)
                        if match:
                            data["Followers"] = parse_number(match.group(1))
                            data["Following"] = parse_number(match.group(2))
                            data["Posts"] = parse_number(match.group(3))
                            print(f"Extracted for {username}: {data['Followers']:,} Followers, {data['Following']:,} Following, {data['Posts']:,} Posts")
                            browser.close()
                            return data, None

                print(f"Attempt {attempt + 1} failed for {username}: No valid meta tag data found.")
                if attempt < retries - 1:
                    print("Retrying...")
                    time.sleep(2)

            except Exception as e:
                print(f"Attempt {attempt + 1} error for {username}: {str(e)}")
                if attempt < retries - 1:
                    print("Retrying...")
                    time.sleep(2)

        error_msg = f"Failed to extract data for {username}. Check page_content_{username}.html."
        with open(f"page_content_{username}.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        browser.close()
        return data, error_msg

def get_reel_data(reel_url, retries=2):
    """Scrape Instagram reel data (Likes, Comments, Upload Date) from meta tags."""
    data = {"Reel_URL": reel_url, "Likes": None, "Comments": None, "Upload_Date": None}
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        stealth_sync(page)

        for attempt in range(retries):
            try:
                print(f"Attempt {attempt + 1}: Navigating to {reel_url}")
                page.goto(reel_url, timeout=60000)
                page.wait_for_load_state("networkidle", timeout=40000)
                print(f"Page loaded for {reel_url}, searching for meta tags...")

                meta_tag = page.query_selector('meta[property="og:description"]')
                if meta_tag:
                    content = meta_tag.get_attribute("content")
                    print(f"Meta description content: {content}")

                    match = re.search(r"([\d,.MK]+)\s*likes,\s*([\d,.MK]+)\s*comments\s*-\s*\w+\s*on\s*([A-Za-z]+\s*\d{1,2},\s*\d{4})", content, re.IGNORECASE)
                    if match:
                        data["Likes"] = parse_number(match.group(1))
                        data["Comments"] = parse_number(match.group(2))
                        data["Upload_Date"] = parse_date(match.group(3))
                        print(f"Extracted for {reel_url}: {data['Likes']:,} Likes, {data['Comments']:,} Comments, {data['Upload_Date']} Upload Date")
                        browser.close()
                        return data, None

                print(f"Attempt {attempt + 1} failed for {reel_url}: No valid meta tag data found.")
                if attempt < retries - 1:
                    print("Retrying...")
                    time.sleep(2)

            except Exception as e:
                print(f"Attempt {attempt + 1} error for {reel_url}: {str(e)}")
                if attempt < retries - 1:
                    print("Retrying...")
                    time.sleep(2)

        error_msg = f"Failed to extract reel data for {reel_url}. Check page_content_reel.html."
        with open(f"page_content_reel.html", "w", encoding="utf-8") as f:
            f.write(page.content())
        browser.close()
        return data, error_msg

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
