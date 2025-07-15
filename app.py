import os
import io
import logging
import base64
import requests
from flask import Flask, request, jsonify
from PIL import Image, ImageDraw
import qrcode
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default-secret-key")

# Monday.com configuration
MONDAY_API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJ0aWQiOjQxMDM1MDMyNiwiYWFpIjoxMSwidWlkIjo1NTIyMDQ0LCJpYWQiOiIyMDI0LTA5LTEzVDExOjUyOjQzLjAwMFoiLCJwZXIiOiJtZTp3cml0ZSIsImFjdGlkIjozNzk1MywicmduIjoidXNlMSJ9.hwTlwMwtbhKdZsYcGT7UoENBLZUAxnfUXchj5RZJBz4"
MONDAY_API_URL = "https://api.monday.com/v2"
BOARD_ID = "9241811459"

# Column mappings
COLUMN_MAPPINGS = {
    "qrguias": {
        "file_column": "file_mksww9yh",
        "url_column": "text_mkspdyty"
    },
    "qrclientes": {
        "file_column": "file_mksws2k3",
        "url_column": "text_mksvzfm1"
    },
    "qrfornecedores": {
        "file_column": "file_mkswpexs",
        "url_column": "text_mksw9b2r"
    }
}

# Color mappings (RGB values based on provided screenshots)
COLOR_MAPPINGS = {
    "qrguias": (64, 224, 208, 128),    # Turquoise with 50% opacity
    "qrclientes": (147, 112, 219, 128), # Purple with 50% opacity
    "qrfornecedores": (100, 149, 237, 128) # Blue with 50% opacity
}

def create_background_image():
    """Create a composite background image with travel landmarks"""
    try:
        # Load the travel background image
        background_path = "attached_assets/fundo (1)_1752581379817.png"
        background = Image.open(background_path)
        
        # Resize to 1000x1000 while maintaining aspect ratio
        background = background.resize((1000, 1000), Image.Resampling.LANCZOS)
        
        # Convert to RGB to ensure compatibility
        background = background.convert('RGB')
        
        logger.info("Successfully loaded travel background image")
        return background
        
    except Exception as e:
        logger.error(f"Error loading background image: {e}")
        # Fallback to gradient background
        background = Image.new('RGB', (1000, 1000), color=(135, 206, 235))
        draw = ImageDraw.Draw(background)
        for i in range(1000):
            color_value = int(135 + (i / 1000) * 50)
            draw.line([(0, i), (1000, i)], fill=(color_value, 206, 235))
        return background

def get_url_from_monday(item_id, url_column_id):
    """Query Monday.com to get URL from specific column"""
    try:
        query = '''
        query ($itemId: [ID!]) {
            items (ids: $itemId) {
                id
                column_values {
                    id
                    text
                }
            }
        }
        '''
        
        variables = {
            "itemId": [str(item_id)]
        }
        
        headers = {
            'Authorization': f'Bearer {MONDAY_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'query': query,
            'variables': variables
        }
        
        response = requests.post(MONDAY_API_URL, headers=headers, json=data)
        logger.debug(f"Monday.com query response: {response.status_code}, {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if 'data' in result and 'items' in result['data'] and result['data']['items']:
                item = result['data']['items'][0]
                for column in item['column_values']:
                    if column['id'] == url_column_id and column['text']:
                        logger.info(f"Found URL in column {url_column_id}: {column['text']}")
                        return column['text']
        
        logger.error(f"No URL found in column {url_column_id} for item {item_id}")
        return None
        
    except Exception as e:
        logger.error(f"Error querying Monday.com for URL: {e}")
        return None

def generate_qr_code(url):
    """Generate QR code for given URL"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        qr_image = qr.make_image(fill_color="black", back_color="white")
        return qr_image
    except Exception as e:
        logger.error(f"Error generating QR code: {e}")
        return None

def create_composite_image(qr_image, overlay_color):
    """Create composite image with background, overlay, and QR code"""
    try:
        # Create background
        background = create_background_image()
        
        # Convert background to RGBA for transparency support
        background_rgba = background.convert('RGBA')
        
        # Create semi-transparent overlay with specified color
        overlay = Image.new('RGBA', (1000, 1000), overlay_color)
        
        # Composite background with semi-transparent overlay
        composite = Image.alpha_composite(background_rgba, overlay)
        
        # Resize QR code to 75% of image size (750x750)
        qr_size = 750
        qr_resized = qr_image.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        
        # Convert QR to RGBA for compositing
        qr_rgba = qr_resized.convert('RGBA')
        
        # Calculate position to center QR code
        qr_x = (1000 - qr_size) // 2
        qr_y = (1000 - qr_size) // 2
        
        # Paste QR code onto composite (QR code should be opaque)
        composite.paste(qr_rgba, (qr_x, qr_y), qr_rgba)
        
        # Convert back to RGB for final output
        return composite.convert('RGB')
    except Exception as e:
        logger.error(f"Error creating composite image: {e}")
        return None

def upload_to_monday(item_id, column_id, image):
    """Upload image to Monday.com column"""
    try:
        # Convert image to bytes
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # GraphQL mutation for file upload (correct format from Monday.com docs)
        query = 'mutation ($file: File!) { add_file_to_column (item_id: %s, column_id: "%s", file: $file) { id } }' % (item_id, column_id)
        
        # Prepare multipart form data with correct format
        data = {
            'query': query,
            'map': '{"image":"variables.file"}'
        }
        
        files = {
            'image': ('qr_code.png', img_buffer, 'image/png')
        }
        
        headers = {
            'Authorization': MONDAY_API_TOKEN
        }
        
        logger.debug(f"Uploading to Monday.com - Item ID: {item_id}, Column ID: {column_id}")
        logger.debug(f"Query: {query}")
        
        response = requests.post(
            'https://api.monday.com/v2/file',
            headers=headers,
            data=data,
            files=files
        )
        
        logger.debug(f"Monday.com upload response: {response.status_code}")
        logger.debug(f"Monday.com upload response body: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if 'errors' in result:
                logger.error(f"GraphQL errors in upload response: {result['errors']}")
                return False
            else:
                logger.info(f"Successfully uploaded QR code to Monday.com")
                return True
        else:
            logger.error(f"Failed to upload to Monday.com: HTTP {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error uploading to Monday.com: {e}")
        return False

def process_webhook(endpoint_type, payload):
    """Process webhook and generate QR code"""
    try:
        # Get item ID from webhook
        item_id = None
        if 'event' in payload and 'pulseId' in payload['event']:
            item_id = payload['event']['pulseId']
        
        if not item_id:
            logger.error("No item ID found in webhook payload")
            return False, "No item ID found in webhook payload"
        
        logger.info(f"Processing item ID: {item_id} for {endpoint_type}")
        
        # Query Monday.com to get URL from specific column
        url_column_id = COLUMN_MAPPINGS[endpoint_type]["url_column"]
        url = get_url_from_monday(item_id, url_column_id)
        
        if not url:
            logger.error(f"No URL found in column {url_column_id} for item {item_id}")
            return False, f"No URL found in column {url_column_id}"
        
        logger.info(f"Processing URL: {url}")
        
        # Generate QR code
        qr_image = generate_qr_code(url)
        if not qr_image:
            logger.error("Failed to generate QR code")
            return False, "Failed to generate QR code"
        
        # Create composite image with appropriate overlay
        overlay_color = COLOR_MAPPINGS[endpoint_type]
        composite_image = create_composite_image(qr_image, overlay_color)
        if not composite_image:
            logger.error("Failed to create composite image")
            return False, "Failed to create composite image"
        
        # Upload to Monday.com
        file_column_id = COLUMN_MAPPINGS[endpoint_type]["file_column"]
        success = upload_to_monday(item_id, file_column_id, composite_image)
        
        if success:
            logger.info(f"Successfully processed webhook for {endpoint_type}")
            return True, "QR code generated and uploaded successfully"
        else:
            logger.error(f"Failed to upload to Monday.com for {endpoint_type}")
            return False, "Failed to upload to Monday.com"
            
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return False, f"Error processing webhook: {str(e)}"

@app.route('/qrguias', methods=['POST'])
def qrguias():
    """Webhook endpoint for guides QR codes"""
    try:
        data = request.get_json()
        
        # Handle Monday.com webhook challenge validation
        if 'challenge' in data:
            challenge = data['challenge']
            logger.info(f"Responding to Monday.com challenge for qrguias: {challenge}")
            return jsonify({'challenge': challenge})
        
        logger.debug(f"Received webhook for qrguias: {data}")
        
        success, message = process_webhook('qrguias', data)
        
        if success:
            return jsonify({'status': 'success', 'message': message}), 200
        else:
            return jsonify({'status': 'error', 'message': message}), 400
            
    except Exception as e:
        logger.error(f"Error in qrguias endpoint: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/qrclientes', methods=['POST'])
def qrclientes():
    """Webhook endpoint for clients QR codes"""
    try:
        data = request.get_json()
        
        # Handle Monday.com webhook challenge validation
        if 'challenge' in data:
            challenge = data['challenge']
            logger.info(f"Responding to Monday.com challenge for qrclientes: {challenge}")
            return jsonify({'challenge': challenge})
        
        logger.debug(f"Received webhook for qrclientes: {data}")
        
        success, message = process_webhook('qrclientes', data)
        
        if success:
            return jsonify({'status': 'success', 'message': message}), 200
        else:
            return jsonify({'status': 'error', 'message': message}), 400
            
    except Exception as e:
        logger.error(f"Error in qrclientes endpoint: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/qrfornecedores', methods=['POST'])
def qrfornecedores():
    """Webhook endpoint for suppliers QR codes"""
    try:
        data = request.get_json()
        
        # Handle Monday.com webhook challenge validation
        if 'challenge' in data:
            challenge = data['challenge']
            logger.info(f"Responding to Monday.com challenge for qrfornecedores: {challenge}")
            return jsonify({'challenge': challenge})
        
        logger.debug(f"Received webhook for qrfornecedores: {data}")
        
        success, message = process_webhook('qrfornecedores', data)
        
        if success:
            return jsonify({'status': 'success', 'message': message}), 200
        else:
            return jsonify({'status': 'error', 'message': message}), 400
            
    except Exception as e:
        logger.error(f"Error in qrfornecedores endpoint: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({
        'message': 'QR Code Generator API',
        'endpoints': ['/qrguias', '/qrclientes', '/qrfornecedores'],
        'status': 'running'
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
