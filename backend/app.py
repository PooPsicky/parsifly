from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
from apify_client import ApifyClient
import random
import openai
import json
from datetime import datetime
import requests
import logging # Import logging

app = Flask(__name__)
load_dotenv()

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# --- End Setup Logging ---

# API Keys
APIFY_API_KEY = os.getenv('APIFY_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Configure OpenAI client
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
else:
    print("Warning: OPENAI_API_KEY not found in environment variables.")

# Test endpoint
@app.route('/', methods=['GET'])
def hello_world():
    logging.info("Root endpoint '/' accessed.") # Add logging
    return jsonify({'message': 'Hello, Parsifly Backend is running!'})

@app.route('/scrape', methods=['POST'])
def scrape_profile():
    data = request.get_json()
    platform = data.get('platform')
    profile = data.get('profile')

    if not platform or not profile:
        return jsonify({'error': 'Platform and profile are required'}), 400

    try:
        # Initialize the Apify client
        apify_client = ApifyClient(APIFY_API_KEY)

        # Construct actor ID based on platform
        if platform == 'TikTok':
            actor_id = "clockworks~free-tiktok-scraper"
        elif platform == 'Instagram':
            actor_id = "apify~instagram-reel-scraper"
        elif platform == 'YouTube':
            actor_id = "streamers~youtube-shorts-scraper"
        else:
            return jsonify({'error': 'Unsupported platform'}), 400

        # Prepare actor input
        run_input = {
            "handle": profile,
            "resultsType": "posts",
            "maxPosts": 20,
        }

        # Run the actor and wait for it to finish
        run = apify_client.actor(actor_id).call(run_input=run_input)

        # Fetch results
        posts = []
        for item in apify_client.dataset(run["defaultDatasetId"]).iterate_items():
            # Extract relevant data based on platform
            timestamp_raw = None
            if platform == 'TikTok':
                account_url = f"https://www.tiktok.com/@{item.get('authorMeta', {}).get('name', '') or ''}"
                post_url = item.get('webVideoUrl', '') or ''
                timestamp_raw = item.get('createTime')
                caption = item.get('text', '') or ''
                views = item.get('playCount', 0) or 0
                likes = item.get('diggCount', 0) or 0
                comments = item.get('commentCount', 0) or 0
                shares = item.get('shareCount', 0) or 0
                duration = item.get('video', {}).get('duration', 0) or 0
                followers = item.get('authorMeta', {}).get('followerCount', 0) or 0

                caption_length = len(caption.split())

                er_followers = ((likes + comments) / followers * 100) if followers else 0
                er_likes_comments = ((likes + comments) / views * 100) if views else 0
                er_shares = (shares / views * 100) if views else 0

                post = {
                    'accountUrl': account_url,
                    'postUrl': post_url,
                    'timestamp': timestamp_raw,
                    'hook': caption.split('.')[0] if caption else '',
                    'caption': caption,
                    'captionLength': caption_length,
                    'followers': followers,
                    'views': views,
                    'likes': likes,
                    'comments': comments,
                    'shares': shares,
                    'duration': duration,
                    'erFollowers': er_followers,
                    'erLikesComments': er_likes_comments,
                    'erShares': er_shares,
                }
            elif platform == 'Instagram':
                account_url = f"https://www.instagram.com/{item.get('username', '') or ''}"
                post_url = item.get('postUrl', '') or ''
                timestamp_raw = item.get('timestamp')
                caption = item.get('text', '') or ''
                likes = item.get('likesCount', 0) or 0
                comments = item.get('commentsCount', 0) or 0
                followers = item.get('followersCount', 0) or 0

                caption_length = len(caption.split())

                er_followers = ((likes + comments) / followers * 100) if followers else 0
                er_likes_comments = ((likes + comments) / followers * 100) if followers else 0
                er_shares = 0

                post = {
                    'accountUrl': account_url,
                    'postUrl': post_url,
                    'timestamp': timestamp_raw,
                    'hook': caption.split('.')[0] if caption else '',
                    'caption': caption,
                    'captionLength': caption_length,
                    'followers': followers,
                    'views': 0,
                    'likes': likes,
                    'comments': comments,
                    'shares': 0,
                    'duration': 0,
                    'erFollowers': er_followers,
                    'erLikesComments': er_likes_comments,
                    'erShares': er_shares,
                }
            elif platform == 'YouTube':
                account_url = f"https://www.youtube.com/channel/{item.get('channelId', '') or ''}"
                post_url = f"https://www.youtube.com/watch?v={item.get('videoId', '') or ''}"
                timestamp_raw = item.get('publishedAt')
                caption = item.get('description', '') or ''
                views = item.get('viewCount', 0) or 0
                likes = item.get('likeCount', 0) or 0
                comments = item.get('commentCount', 0) or 0
                duration = item.get('duration', 0) or 0
                followers = item.get('subscriberCount', 0) or 0

                caption_length = len(caption.split())

                er_followers = ((likes + comments) / followers * 100) if followers else 0
                er_likes_comments = ((likes + comments) / views * 100) if views else 0
                er_shares = 0

                post = {
                    'accountUrl': account_url,
                    'postUrl': post_url,
                    'timestamp': timestamp_raw,
                    'hook': caption.split('.')[0] if caption else '',
                    'caption': caption,
                    'captionLength': caption_length,
                    'followers': followers,
                    'views': views,
                    'likes': likes,
                    'comments': comments,
                    'shares': 0,
                    'duration': duration,
                    'erFollowers': er_followers,
                    'erLikesComments': er_likes_comments,
                    'erShares': er_shares,
                }

            timestamp_iso = None
            if timestamp_raw:
                try:
                    if isinstance(timestamp_raw, (int, float)):
                        timestamp_iso = datetime.utcfromtimestamp(timestamp_raw).isoformat() + 'Z'
                    else:
                        timestamp_iso = datetime.fromisoformat(str(timestamp_raw).replace('Z', '+00:00')).isoformat() + 'Z'
                except (ValueError, TypeError) as ts_err:
                    print(f"Warning: Could not parse timestamp '{timestamp_raw}': {ts_err}")
                    timestamp_iso = str(timestamp_raw)

            if 'post' in locals():
                post['timestamp'] = timestamp_iso

            if 'post' in locals():
                posts.append(post)
                del post

        return jsonify({'posts': posts})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_openai_analysis(post):
    if not OPENAI_API_KEY:
        return {'error': 'OpenAI API key not configured'}

    caption_snippet = post.get('caption', '')[:1000]

    prompt = f"""
Analyze the following social media post data:

Caption: "{caption_snippet}"
Views: {post.get('views', 0)}
Likes: {post.get('likes', 0)}
Comments: {post.get('comments', 0)}
Shares: {post.get('shares', 0)}
Duration (s): {post.get('duration', 0)}
Followers at time of post: {post.get('followers', 0)}
Engagement Rate (vs Followers): {post.get('erFollowers', 0):.2f}%
Engagement Rate (vs Views): {post.get('erLikesComments', 0):.2f}%
Share Rate (vs Views): {post.get('erShares', 0):.2f}%

Based on this data, please provide the following in JSON format:
1.  category: A relevant category for the post (e.g., Education, Humor, Fitness, Lifestyle, Travel, Technology, News, etc.). Use "N/A" if unclear.
2.  theme: A specific theme or topic within the category (e.g., "Motivation", "Tutorials", "Comedy Sketch", "Healthy Recipe", "Travel Vlog", "Product Review"). Use "N/A" if unclear.
3.  viralityScore: An estimated virality score between 0.0 and 1.0, considering the engagement metrics relative to views and followers. Higher scores indicate stronger virality potential.
4.  erRating: A qualitative engagement rating (LOW, AVERAGE, GOOD, BEST) based on the metrics and virality score.
5.  reasoning: A brief explanation (1-2 sentences) for the assigned category, theme, score, and rating.

Return ONLY the JSON object. Example:
{{
  "category": "Fitness",
  "theme": "Workout Tutorial",
  "viralityScore": 0.65,
  "erRating": "GOOD",
  "reasoning": "High engagement relative to views suggests strong audience interest in the workout shown."
}}
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert social media analyst. Analyze the provided post data and return your analysis strictly in the requested JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=200,
            response_format={ "type": "json_object" }
        )

        content = response.choices[0].message.content
        analysis = json.loads(content)
        return analysis

    except json.JSONDecodeError as e:
        print(f"Error decoding OpenAI JSON response: {e}")
        print(f"Raw response content: {content}")
        return {'error': 'Failed to parse OpenAI response'}
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return {'error': f'OpenAI API error: {str(e)}'}

@app.route('/analyze', methods=['POST'])
def analyze_posts():
    data = request.get_json()
    posts = data.get('posts')

    if not posts:
        return jsonify({'error': 'Posts data is required'}), 400

    if not OPENAI_API_KEY:
         return jsonify({'error': 'OpenAI API key not configured on server'}), 500

    analyzed_posts = []
    for post in posts:
        try:
            analysis_result = get_openai_analysis(post)

            if 'error' in analysis_result:
                print(f"OpenAI analysis failed for post {post.get('postUrl')}: {analysis_result['error']}")
                post['category'] = 'N/A'
                post['theme'] = 'N/A'
                post['viralityScore'] = 0.0
                post['erRating'] = 'N/A'
                post['analysisReasoning'] = analysis_result['error']
            else:
                post['category'] = analysis_result.get('category', 'N/A')
                post['theme'] = analysis_result.get('theme', 'N/A')
                try:
                    post['viralityScore'] = float(analysis_result.get('viralityScore', 0.0))
                except (ValueError, TypeError):
                     post['viralityScore'] = 0.0
                post['erRating'] = analysis_result.get('erRating', 'N/A')
                post['analysisReasoning'] = analysis_result.get('reasoning', '')

            analyzed_posts.append(post)

        except Exception as e:
            print(f"Error processing post {post.get('postUrl')} during analysis: {e}")
            post['category'] = 'Error'
            post['theme'] = 'Error'
            post['viralityScore'] = 0.0
            post['erRating'] = 'Error'
            post['analysisReasoning'] = f"Processing error: {str(e)}"
            analyzed_posts.append(post)

    return jsonify({'analyzedPosts': analyzed_posts})

@app.route('/performance_data', methods=['POST'])
def get_performance_data():
    logging.info("'/performance_data' endpoint called.") # Log entry
    data = request.get_json()
    platform = data.get('platform')
    profile = data.get('profile')
    logging.info(f"Received request for platform: {platform}, profile: {profile}")

    if not platform or not profile:
        logging.warning("Missing platform or profile in request.") # Log warning
        return jsonify({'error': 'Platform and profile are required'}), 400

    try:
        scrape_url = request.url_root + 'scrape'
        logging.info(f"Making internal request to {scrape_url}")
        scrape_response = requests.post(url=scrape_url, json={'platform': platform, 'profile': profile}, timeout=60) # Add timeout
        logging.info(f"Internal scrape request status: {scrape_response.status_code}")
        scrape_response.raise_for_status()
        scraped_data = scrape_response.json()
        posts = scraped_data.get('posts')
        logging.info(f"Scrape successful, received {len(posts) if posts else 0} posts.")

        if not posts:
            logging.warning("No posts found after scraping.") # Log warning
            return jsonify({'error': 'No posts found'}), 404

        analyze_url = request.url_root + 'analyze'
        logging.info(f"Making internal request to {analyze_url}")
        analyze_response = requests.post(url=analyze_url, json={'posts': posts}, timeout=120) # Add timeout
        logging.info(f"Internal analyze request status: {analyze_response.status_code}")
        analyze_response.raise_for_status()
        analyzed_data = analyze_response.json()
        analyzed_posts = analyzed_data.get('analyzedPosts')
        logging.info(f"Analysis successful, received {len(analyzed_posts) if analyzed_posts else 0} analyzed posts.")


        if not analyzed_posts:
             logging.warning("No posts analyzed.") # Log warning
             return jsonify({'error': 'No posts analyzed'}), 404

        logging.info("Returning successful performance data.") # Log success
        return jsonify({'performanceData': analyzed_posts})

    except requests.exceptions.Timeout:
        logging.error("Internal request timed out.", exc_info=True)
        return jsonify({'error': 'Internal request timed out'}), 500
    except requests.exceptions.RequestException as e:
        logging.error(f"Internal request failed: {e}", exc_info=True) # Log request exception
        # Log response body if available and not JSON
        response_text = ""
        if e.response is not None:
            try:
                e.response.json() # Try to parse as JSON
            except json.JSONDecodeError:
                 response_text = e.response.text[:500] # Get first 500 chars if not JSON
                 logging.error(f"Internal request response body (non-JSON): {response_text}")

        return jsonify({'error': f'Internal request failed: {str(e)} {response_text}'}), 500
    except Exception as e:
        logging.error(f"An unexpected error occurred in /performance_data: {e}", exc_info=True) # Log general exception
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Use Gunicorn or another WSGI server in production instead of app.run(debug=True)
    # For local testing:
    app.run(host='0.0.0.0', port=8080, debug=True) # Match Procfile port if running locally like Railway
