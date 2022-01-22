VERSION_CODE = 0
try:
    with open('VERSION', 'r') as f:
        VERSION_CODE = int(f.read())
except:
    pass    

HW_MODEL = 'v1'
try:
    with open('/HW_MODEL', 'r') as f:
        HW_MODEL = f.read()
except:
    pass

VERSION = 'v%s' % VERSION_CODE

BASE_PATH = '/opt/shell/'
CONFIG_PATH = '/opt/shell/config.json'

DEFAULT_CONFIG = {
            'DefaultVideoDelay':0,
            'DefaultVideoDelayBluetooth':-600,
            'DefaultVolume':-12,
            'AlsaVolume':70,
            'DistortionUpDown': 30,
            'DistortionLeftRight': 30
        }

PROJECTOR_ARGS = [
    ('Brightness', -31, 10, 41),
    ('Contrast', -15, 15, 43),
    ('Sharpness', 0, 6, 49),
    ('DistortionUpDown', -20, 30, 53),
    ('DistortionLeftRight', -30, 30, 51),
    ('HueU', -15, 15, 45),
    ('HueV', -15, 15, 45),
    ('SaturationU', -15, 15, 47),
    ('SaturationV', -15, 15, 47),
]
