from wtforms import Form, StringField, SelectField
from wtforms.validators import DataRequired, URL

class ResultForm(Form):
    result_link = StringField('RESULT LINK', validators=[DataRequired(), URL()])
    college_code = SelectField('COLLEGE CODE', choices=[('1604', 'MJCET'), ('1603', 'DECCAN'), ('1605', 'ISL'), ('1610', 'NSAKCET'), ('2455', 'KMEC'), ('2453', 'NGIT')], validators=[DataRequired()])
    field_code = SelectField('BRANCH CODE', choices=[('748', 'AIML'), ('749', 'IOT'), ('750', 'DS'), ('736', 'MECH'), ('733', 'CSE'), ('732', 'CIVIL'), ('737', 'IT'), ('735', 'ECE'), ('734', 'EEE')], validators=[DataRequired()])
    year = StringField('YEAR OF ADMISSION', validators=[DataRequired()], render_kw={"placeholder": "If your hallticket is 1610'21'748031, enter 21."})
