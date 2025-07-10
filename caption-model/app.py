import os
os.environ["TRANSFORMERS_NO_TF"] = "1"  # Avoid TensorFlow/Keras errors

from flask import Flask, request, send_from_directory
from datetime import datetime
from werkzeug.utils import secure_filename
from transformers import pipeline
import schedule
import time
import threading

# === SETUP ===
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load the caption model (BLIP)
caption_generator = pipeline(
    "image-to-text",
    model="Salesforce/blip-image-captioning-base",
    device=0  # use -1 if you want to run on CPU
)

# === ROUTES ===
@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        photo = request.files['photo']
        max_length = int(request.form.get('length', 80))

        if photo:
            filename = secure_filename(photo.filename)
            path = os.path.join(UPLOAD_FOLDER, filename)
            photo.save(path)

            caption, hashtags = generate_caption_and_hashtags(path, max_length)
            full_caption = f"{caption}\n\n{' '.join(hashtags)}"
            schedule_post(full_caption, path)

            return f"""
            <!DOCTYPE html>
            <html>
            <head>
              <title>Caption Generated</title>
              <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
              <style>
                body {{ background-color: #f0f0f0; padding-top: 30px; }}
                .container {{ max-width: 600px; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
                img {{ max-width: 100%; height: auto; border-radius: 10px; }}
              </style>
            </head>
            <body>
              <div class="container">
                <h2 class="mb-4 text-center">✅ Uploaded & Scheduled!</h2>
                <img src="/uploads/{filename}" class="mb-3" alt="Uploaded Image">
                <h5>📝 Generated Caption:</h5>
                <p>{caption}</p>
                <h5>🏷 Hashtags:</h5>
                <p>{' '.join(hashtags)}</p>
                <a href="/" class="btn btn-secondary mt-3">Upload Another</a>
              </div>
            </body>
            </html>
            """

    # GET request – show upload form
    return '''
    <!DOCTYPE html>
    <html>
    <head>
      <title>Auto Caption Generator</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
      <style>
        body { background-color: #f8f9fa; padding-top: 40px; }
        .container { max-width: 500px; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
        .btn-primary { width: 100%; }
      </style>
    </head>
    <body>
      <div class="container">
        <h2 class="mb-4 text-center">Upload a Photo</h2>
        <form method="post" enctype="multipart/form-data">
          <div class="mb-3">
            <label for="photo" class="form-label">Select Photo:</label>
            <input type="file" class="form-control" name="photo" required>
          </div>
          <div class="mb-3">
            <label for="length" class="form-label">Caption Length (10–200 tokens):</label>
            <input type="number" class="form-control" name="length" min="10" max="200" value="80" required>
          </div>
          <button type="submit" class="btn btn-primary">Upload & Generate</button>
        </form>
      </div>
    </body>
    </html>
    '''

# === SERVE IMAGES ===
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# === CAPTION + HASHTAG GENERATION ===
def generate_caption_and_hashtags(image_path, max_tokens):
    result = caption_generator(image_path, max_new_tokens=max_tokens)
    caption = result[0]['generated_text']
    keywords = caption.lower().split()
    hashtags = ['#' + word.strip('.,') for word in keywords if len(word) > 4][:6]
    return caption, hashtags

# === FAKE POSTING FUNCTION ===
def post_to_social(caption, image_path):
    print(f"\n[POSTED at {datetime.now()}]")
    print(f"Caption:\n{caption}")
    print(f"Image Path: {image_path}")

def schedule_post(caption, image_path, delay_minutes=1):
    def job():
        post_to_social(caption, image_path)
    schedule.every(delay_minutes).minutes.do(job)
    threading.Thread(target=run_schedule, daemon=True).start()

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

# === RUN FLASK APP (FOR SAME NETWORK USE) ===
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
