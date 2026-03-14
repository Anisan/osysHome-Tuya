from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, PasswordField
from wtforms.validators import DataRequired, Optional


class SettingsForm(FlaskForm):
    """Tuya plugin settings form"""
    
    access_id = StringField(
        'Access ID',
        validators=[DataRequired()],
        description='Tuya IoT Platform Access ID'
    )
    
    access_secret = PasswordField(
        'Access Secret',
        validators=[DataRequired()],
        description='Tuya IoT Platform Access Secret'
    )
    
    region = SelectField(
        'Region',
        choices=[
            ('eu', 'Europe'),
            ('us', 'United States'),
            ('cn', 'China'),
            ('in', 'India')
        ],
        validators=[DataRequired()],
        default='eu'
    )
    
    connection_mode = SelectField(
        'Connection Mode',
        choices=[
            ('cloud', 'Cloud only'),
            ('local', 'Local only'),
            ('both', 'Both (Cloud + Local)')
        ],
        validators=[DataRequired()],
        default='both'
    )
    
    poll_interval = IntegerField(
        'Poll Interval (seconds)',
        validators=[Optional()],
        default=30,
        description='How often to poll device status'
    )

    linked_uid = StringField(
        'Linked App User UID',
        validators=[Optional()],
        description='UID of the Tuya/Smart Life app user linked to the project. Use if Discover returns 0 devices.'
    )


class AddDeviceForm(FlaskForm):
    """Form for manually adding a device"""
    
    device_id = StringField(
        'Device ID',
        validators=[DataRequired()],
        description='Tuya device ID'
    )
    
    device_name = StringField(
        'Device Name',
        validators=[DataRequired()],
        description='Friendly name for the device'
    )
    
    local_key = StringField(
        'Local Key',
        validators=[Optional()],
        description='Local key for LAN control (optional)'
    )
    
    ip_address = StringField(
        'IP Address',
        validators=[Optional()],
        description='Device IP address (optional, can be auto-discovered)'
    )
