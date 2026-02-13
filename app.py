from flask import Flask, request, jsonify, render_template
import subprocess
import uuid
import zipfile
import os
import smtplib
from email.message import EmailMessage
import threading
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

job_status = {}
app = Flask(
    __name__,
    template_folder = "webpage",
    static_folder = "webpage"
)
PYTHON_SCRIPT = "102317012.py"
OUTPUT_FILE = "mashup.mp3"
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

# Check if email credentials are set
if not SENDER_EMAIL or not APP_PASSWORD:
    print("WARNING: SENDER_EMAIL and APP_PASSWORD environment variables are not set!")
    print("Email functionality will not work. Please set these variables:")
    print("  export SENDER_EMAIL='your_email@gmail.com'")
    print("  export APP_PASSWORD='your_app_password'")

def zip_results(zip_name, audio_file):
    zip_path = f"{zip_name}.zip" 
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(audio_file, arcname = audio_file)
    return zip_path

def send_email(receiver_email, zip_file):
    msg = EmailMessage()
    msg["Subject"] = "Your Mashup Song Files"
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver_email
    msg.set_content("Hi,\n\nYour mashup audio file is attached as a ZIP.\n\nEnjoy!")
    with open(zip_file, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype = "application",
            subtype = "zip",
            filename = os.path.basename(zip_file)
        )
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)

def process_request(data, job_id):
    try:
        singer = data["singer"]
        videos = str(data["videos"])
        duration = str(data["duration"])
        email = data["email"]
        zip_name = singer.replace(" ", "_") + "_mashup"

        print(f"\n{'='*50}")
        print(f"Starting mashup generation for job: {job_id}")
        print(f"Singer: {singer}, Videos: {videos}, Duration: {duration}s")
        print(f"{'='*50}\n")

        result = subprocess.run([
            "python",
            PYTHON_SCRIPT,
            singer,
            videos,
            duration,
            OUTPUT_FILE
        ])
        
        print(f"\nSubprocess completed with return code: {result.returncode}")
        print(f"Checking if {OUTPUT_FILE} exists...")
        
        if result.returncode != 0:
            print(f"ERROR: Subprocess failed with code {result.returncode}")
            job_status[job_id] = "error"
            return
            
        if not os.path.exists(OUTPUT_FILE):
            print(f"ERROR: Output file {OUTPUT_FILE} not found!")
            job_status[job_id] = "error"
            return
        
        file_size = os.path.getsize(OUTPUT_FILE) / (1024 * 1024)
        print(f"Mashup file created: {file_size:.2f} MB")
        
        print(f"Creating ZIP file: {zip_name}.zip")
        zip_file = zip_results(zip_name, OUTPUT_FILE)
        print(f"ZIP created: {zip_file}")
        
        print(f"Sending email to: {email}")
        send_email(email, zip_file)
        print(f"Email sent successfully!")
        
        if os.path.exists(zip_file):
            os.remove(zip_file)
            print(f"Cleaned up ZIP file")
        
        job_status[job_id] = "done"
        print(f"Job {job_id} completed successfully!\n")
        
    except Exception as e:
        print(f"Error in process_request: {e}")
        import traceback
        traceback.print_exc()
        job_status[job_id] = "error"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    job_id = str(uuid.uuid4())
    job_status[job_id] = "processing"
    thread = threading.Thread(target = process_request, args = (data, job_id))
    thread.start()
    return jsonify({
        "job_id": job_id,
        "message": "Mashup generation started. You will receive a ZIP file via email."
    })

@app.route("/status/<job_id>")
def status(job_id):
    return jsonify({
        "status": job_status.get(job_id, "unknown")
    })

if __name__ == "__main__":
    app.run(debug=True)