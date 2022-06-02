from flaskapp import db

class Camera(db.Model):
    __tablename__ = 'cameras'
    #create columns
    cameraid = db.Column(db.Integer,primary_key=True)
    cameraname  = db.Column(db.String(20),nullable=False,unique=True)
    camerapurpose = db.Column(db.String(80),nullable=False)
    cameraurl = db.Column(db.String(80),nullable=False)