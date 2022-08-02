import os
from flask import Flask, render_template, request, redirect, flash, session
import base64
import folium
from exif import Image
from datetime import datetime
import hashlib
from PIL import Image as PILImage
import io

app = Flask(__name__)
app.secret_key = "good-secret_key"

users = []
class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.id = base64.b64encode((username+password).encode("ascii"))
    def __eq__(self, other):
        return self.username == other.username

image = {}

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User(username, password)
        if user in users:
            return user.id
        else:
            users.append(user)
            session["user_name"] = user.username
            session["user_id"] = user.id
            return redirect("/")
    else:
        return render_template("register.html")
    
@app.route('/logout')
def logout():
    session.clear()
    return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        login = User(username, password)
        for user in users:
            if user.id == login.id:
                session["user_name"] = user.username
                session["user_id"] = user.id   
                return redirect("/")
        return "wrong"
    else:
        return render_template("login.html")

@app.route('/')
def index():
    images = []
    for file in os.listdir("./fish/static/images"):
        if file != ".gitkeep":
            images.append("/static/images/" + file)
    return render_template("index.html", images=images)

def extract_exif(path, filename):
    pos = []
    with open(path, "rb") as img_file:
        img = Image(img_file)
        for x in range(0, 2):
            ref = (img.gps_longitude_ref if x else img.gps_latitude_ref)
            new = (img.gps_longitude if x else img.gps_latitude)
            new = str(new).strip("()").split(",")
            new = [float(x) for x in new]
            new = (new[0]+new[1]/60.0+new[2]/3600.0) * (-1 if ref in ["S","W"] else 1)
            pos.append(new)
    image[filename] = {
        "pos": pos,
        "date": datetime.now()
    }

@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        # hash
        file = request.files["file"]
        bytes = file.read()
        hash = hashlib.sha256(bytes).hexdigest()

        # save as webp
        name = hash + ".png"
        path = os.path.join("./fish/static/images", name)
        image = PILImage.open(io.BytesIO(bytes))
        image.save(path, format="png")
        return redirect("/")
    else:
        return render_template('upload.html')

@app.route("/map")
def map():
    map = folium.Map(location=[50.5, 8], zoom_start=2)
    for file in os.listdir("./fish/static/images"):
        path = os.path.join("./fish/static/images", file)
        if file != ".gitkeep":
            extract_exif(path, file)
            folium.Marker(image[file]["pos"]).add_to(map)
    return render_template('map.html', map=map._repr_html_())
