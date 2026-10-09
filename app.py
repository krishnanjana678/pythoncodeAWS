import os
import uuid
from flask import Flask, render_template, request, redirect, url_for
import boto3
import pymysql

app = Flask(__name__)

BUCKET_NAME = "krishna-app-storage-2026"
REGION = "ap-south-1"

s3 = boto3.client("s3", region_name=REGION)

def get_db_connection():
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=3306,
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ.get("DB_NAME", "studentdb"),
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    email = request.form["email"]
    course = request.form["course"]
    photo = request.files.get("photo")

    if not photo or not photo.filename:
        return "Please select a photo.", 400

    filename = f"{uuid.uuid4().hex}_{os.path.basename(photo.filename)}"

    s3.upload_fileobj(photo, BUCKET_NAME, filename)

    photo_url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": BUCKET_NAME, "Key": filename},
        ExpiresIn=3600
    )

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """INSERT INTO students (name, email, course, photo_url)
                   VALUES (%s, %s, %s, %s)""",
                (name, email, course, photo_url)
            )
        connection.commit()
    finally:
        connection.close()

    return "Student Registered Successfully"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
