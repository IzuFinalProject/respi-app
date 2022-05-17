from flask import Flask, render_template,send_file, Response, request, make_response
import urllib.request
import numpy as np
import cv2
import io
import face_recognition
import os
import requests
from datetime import datetime
import json

app = Flask(__name__)

@app.route('/camera')
def camera():
    return render_template('camera.html')

@app.route('/video_feed')
def video_feed():
    return Response(video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

def findEncodings(images):
    encodeList = []
    for idx,img in enumerate(images):
        print("Encoding compleated! %d",idx)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList
def setupGPIO():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)

    GPIO.setup(18, GPIO.OUT)
    
def video_stream():
    path = 'images'
    CAMERA_URL = os.environ.get("CAMERA_URL")
    API_URL = os.environ.get("API_URL")
    images = []
    classNames = []
    images_list = os.listdir(path)
    for index,cl in enumerate(images_list):
        print("image {}  is being red.".format(index))
        curImg = cv2.imread(f'{path}/{cl}')
        images.append(curImg)
        classNames.append(os.path.splitext(cl)[0])
    encodeList = findEncodings(images)
    while True:
        imgPath=urllib.request.urlopen(CAMERA_URL+"/shot.jpg")
        print("Reading Image from Camera")
        read_image = imgPath.read()
        imgNp=np.array(bytearray(read_image),dtype=np.uint8)

        img=cv2.imdecode(imgNp,-1)
        small_frame = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        rgb_small_frame= cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
        for encodeFace, faceLoc in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(encodeList, encodeFace)
            faceDis = face_recognition.face_distance(encodeList, encodeFace)
            matchIndex = np.argmin(faceDis)
            if matches[matchIndex]:
                name = classNames[matchIndex].upper() 
                print(name)
                json_data = { 'title':'Person Detected Detected','message':'What the hell you doing in my home?','user_id':'1'}
                data = json.dumps(json_data)
                print(data)
                res = requests.post(API_URL+'/api/notification/', data=data ,headers={'Content-Type': 'application/json'})
                print(res.content)
            else:
                print("Unknown Person!")
        ret, buffer = cv2.imencode('.jpeg',img)
        frame = buffer.tobytes()
        yield (b' --frame\r\n' b'Content-type: imgae/jpeg\r\n\r\n' + frame +b'\r\n')


@app.route("/led",methods=["POST"])
def door_led():
    response = None
    if request.method == 'POST':
        data = request.get_json()
        print(data['led'])
        response = app.response_class(
        response=json.dumps({'status':'ok'}),
        status=200,
        mimetype='application/json'
        )
    else :
        response = app.response_class(
        response=json.dumps({'status':'bad'}),
        status=400,
        mimetype='application/json'
        ) 

    return response
