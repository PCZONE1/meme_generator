import os
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from PIL import Image, ImageDraw, ImageFont
import tempfile

# ─── Configuration ─────────────────────────────────────────────────
app = Flask(__name__)
TMP = tempfile.gettempdir()
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MEME_FOLDER']   = 'static/memes'
ALLOWED_EXT = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['MEME_FOLDER'], exist_ok=True)

# ─── Helper Functions ────────────────────────────────────────────────
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


def wrap_text(text, draw, font, max_width):
    words = text.split()
    if not words:
        return []
    lines = []
    line = words[0]
    for word in words[1:]:
        test_line = f"{line} {word}"
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    lines.append(line)
    return lines


def draw_wrapped_text(draw, img, lines, font, y_start):
    outline = max(int(font.size / 15), 1)
    y = y_start
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (img.width - w) // 2
        # draw outline
        for dx in range(-outline, outline + 1):
            for dy in range(-outline, outline + 1):
                draw.text((x + dx, y + dy), line, font=font, fill='black')
        draw.text((x, y), line, font=font, fill='white')
        y += h + 5
    return y - y_start

# ─── Routes ─────────────────────────────────────────────────────────
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    # Retrieve form data
    img_file = request.files.get('image')
    top_text = request.form.get('top_text', '').upper()
    bottom_text = request.form.get('bottom_text', '').upper()

    # Validate upload
    if not img_file or not allowed_file(img_file.filename):
        return redirect(url_for('index'))

    # Save uploaded image
    filename = secure_filename(img_file.filename)
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    img_file.save(input_path)

    # Open and draw text
    img = Image.open(input_path)
    draw = ImageDraw.Draw(img)
    font_size = max(int(img.width / 12), 24)
    font = ImageFont.truetype('static/fonts/Impact.ttf', font_size)
    max_width = img.width - 20

    # Top text
    top_lines = wrap_text(top_text, draw, font, max_width)
    draw_wrapped_text(draw, img, top_lines, font, y_start=10)

    # Bottom text
    bottom_lines = wrap_text(bottom_text, draw, font, max_width)
    block_height = sum(
        (draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] + 5)
        for line in bottom_lines
    ) - 5
    y_bottom = img.height - block_height - 10
    draw_wrapped_text(draw, img, bottom_lines, font, y_start=y_bottom)

    # Save result
    meme_filename = f"meme_{filename}"
    output_path = os.path.join(app.config['MEME_FOLDER'], meme_filename)
    img.save(output_path)

    # Render result page
    return render_template('result.html', meme_file=meme_filename)

if __name__ == '__main__':
    app.run(debug=True)
