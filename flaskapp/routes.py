from flask import render_template, flash,request,Response
from flaskapp import app, db
from flaskapp.forms import CameraForm
from flaskapp.models import Camera
import re
import threading
from vidgear.gears import VideoGear
import os
import cv2
import face_recognition
import numpy as np


Names = []
Images = []
ActiveThread = []
data_list = []
camera_list = []
URL_LIST = []
path = './Images'
dir = os.listdir(path)

for img in dir:
    getImage = cv2.imread(f'{path}/{img}')
    Images.append(getImage)
    Names.append(os.path.splitext(img)[0])

def find_camera(list_id):
    cam = Camera.query.filter_by(cameraid=list_id).first()
    return (cam.cameraurl)

def findEncodings(images):
    encodeList = []
    for img in images:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encode = face_recognition.face_encodings(img)[0]
        encodeList.append(encode)
    return encodeList

encodedListKnown = findEncodings(Images)

def render_camera_feed(url):
    cam = VideoGear(source=url, logging=True)
    if len(URL_LIST) == 0:
        print('Starting Camera',url)
        cap = cam.start()
        URL_LIST.append(url)
        return cap
    if len(URL_LIST) == 1 :
        if URL_LIST != [url]:
            print('True')
            URL_LIST.append(url)
            print('Starting Camera', url)
            cap = cam.start()
            return cap
        if URL_LIST == [url]:
            print('Camera is Running')
            return cam
    if len(URL_LIST) > 1:
        res = [existing_url for existing_url in URL_LIST if (existing_url in url)]
        if str(bool(res)) == 'False':
            print('Starting Camera', url)
            cap = cam.start()
            URL_LIST.append(url)
            return cap
        else:
            print('Camera is Running')
            return cam


@app.route('/camera',methods=['GET', 'POST'])
def camera():
    form = CameraForm()
    if request.method == 'POST':
        if form.submit():
            camera = Camera(cameraname=form.cameraname.data,
                            camerapurpose=form.camerapurpose.data, cameraurl=form.cameraurl.data)
            db.session.add(camera)
            db.session.commit()
            flash('Registration Successful!!')
    return render_template('camera.html', form=form)

@app.route('/all_cameras', methods=['GET','POST'])
def retrievecameralist():
    cameras = Camera.query.all()
    return render_template('list_cameras.html', cameras=cameras)

@app.route('/view', methods=['GET','POST'])
def view():
    global new_list
    if request.method == 'POST':
       data = str(request.data)
       data = re.findall('"([^"]*)"', data)
       new_list = [x for xs in data for x in xs.split(',')]
       new_list = [i for i in new_list if i]
       if len(new_list) > 1:
           for ele in new_list:
               cam = Camera.query.filter_by(cameraid=ele).first()
               data_list.append(cam.camerapurpose+'/'+ele)
       if len(new_list) == 1:
           for ele in new_list:
               cam = Camera.query.filter_by(cameraid=ele).first()
               data_list.append(cam.camerapurpose + '/' + ele)
    return render_template('view_all.html',datas=data_list)


def gen_frames(camera_id):
    cam = find_camera(camera_id)
    print("Cam",cam)
    cap = render_camera_feed(cam)
    while True:
        frame = cap.read()
        frame = cv2.rotate(frame, cv2.cv2.ROTATE_90_COUNTERCLOCKWISE)
        frame = cv2.resize(frame,(420,236))
        if frame is None:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            data_encode = np.array(buffer)
            frame = data_encode.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/video_feed/<string:purpose>/<string:list_id>/', methods=["GET","POST"])
def video_feed(list_id,purpose):
    print("Purpose",purpose)
    return Response(gen_frames(list_id),
                          mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/enable_cam', methods=["GET","POST"])
def enable_cam():
    global new_list
    cameras = Camera.query.all()
    if request.method == 'POST':
        data = str(request.data)
        data = re.findall('"([^"]*)"', data)
        new_list = [x for xs in data for x in xs.split(',')]
        new_list = [i for i in new_list if i]
        if len(new_list) > 1:
            for ele in new_list:
                camera_list.append(ele)
        if len(new_list) == 1:
            for ele in new_list:
                camera_list.append(ele)
    camera_threading(camera_list)
    return render_template('list_cameras.html',cameras=cameras)

def camera_threading(camera_list):
    if len(camera_list) > 1:
        for list_id in camera_list:
            cam=Camera.query.filter_by(cameraid=list_id).first()
            purpose = cam.camerapurpose
            incoming_thread = purpose+list_id
            if len(ActiveThread) == 0:
                ActiveThread.append(invoke_Thread(list_id,purpose))
            else:
                if len(ActiveThread) == 1:
                    if [incoming_thread] != ActiveThread:
                        ActiveThread.append(invoke_Thread(list_id,purpose))
                    else:
                        print('Thread is Active')
                if len(ActiveThread) > 1:
                    res = [thread_name for thread_name in ActiveThread if (thread_name in incoming_thread)]
                    if str(bool(res)) == 'False':
                        ActiveThread.append(invoke_Thread(list_id, purpose))
                    else:
                        print('Thread is Active')
    if len(camera_list) ==1:
        for list_id in camera_list:
            cam = Camera.query.filter_by(cameraid=list_id).first()
            purpose = cam.camerapurpose
            incoming_thread = purpose + list_id
            if len(ActiveThread) == 0:
                ActiveThread.append(invoke_Thread(list_id, purpose))
            else:
                if len(ActiveThread) == 1:
                    if [incoming_thread] != ActiveThread:
                        ActiveThread.append(invoke_Thread(list_id, purpose))
                    else:
                        print('Thread is Active')
                if len(ActiveThread) > 1:
                    res = [thread_name for thread_name in ActiveThread if (thread_name in incoming_thread)]
                    if str(bool(res)) == 'False':
                        ActiveThread.append(invoke_Thread(list_id, purpose))
                    else:
                        print('Thread is Active')

def invoke_Thread(list_id,purpose):
    print('Thread Invoked = ',purpose+list_id)
    thread = threading.Thread(target=camera_analysis, args=(list_id, purpose,), name=purpose)
    thread.start()
    current_thread_name = thread.name+list_id

    return current_thread_name

def camera_analysis(camera_id,camera_purpose):
    global count
    count = 0
    cam = find_camera(camera_id)
    print("INCOMING CAM URL ",cam)
    cap = render_camera_feed(cam)
    if camera_purpose == 'face_recognition':
        while True:
            frame = cap.read()
            rgb_frame = frame[:, :, ::-1]
            image = cv2.rotate(rgb_frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
            if rgb_frame is not None:
                facesCurFrame = face_recognition.face_locations(image)
                encodesCurFrame = face_recognition.face_encodings(image, facesCurFrame)
                for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
                    matches = face_recognition.compare_faces(encodedListKnown, encodeFace)
                    faceDis = face_recognition.face_distance(encodedListKnown, encodeFace)
                    matchIndex = np.argmin(faceDis)
                    if matches[matchIndex]:
                        name = Names[matchIndex].upper()
                        print('Matched',name)
                        count = count+1
                        print(count)
            else:
                print("Not Matched")
    if camera_purpose == 'vehicle_detection':
        pass
