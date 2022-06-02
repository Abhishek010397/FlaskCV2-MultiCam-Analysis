from flask_wtf import FlaskForm
from wtforms import StringField,SubmitField
from wtforms.validators import InputRequired, Length

class CameraForm(FlaskForm):
    cameraname=StringField(validators=[InputRequired(),Length(min=4, max=90)])
    camerapurpose = StringField(validators=[InputRequired(), Length(min=4, max=90)])
    cameraurl= StringField(validators=[InputRequired(),Length(min=4, max=90)])
    submit=SubmitField("Submit")