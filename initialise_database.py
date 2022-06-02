from flaskapp.models import Camera,db

db.create_all()
camera1 = Camera(cameraname='CP Plus', camerapurpose='face_recognition', cameraurl='http://admin:admin@172.24.144.24:8083')
db.session.add(camera1)
db.session.commit()
