# -*- coding: utf-8 -*-
from __future__ import absolute_import
from datetime import datetime
import logging
import sys
from volttron.platform.vip.agent import Agent, Core, PubSub
from volttron.platform.agent import utils
import importlib
import json
import socket
import pyrebase
import settings
import time
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import psycopg2
import psycopg2.extras


utils.setup_logging()
_log = logging.getLogger(__name__)
__version__ = '3.2'
DEFAULT_HEARTBEAT_PERIOD = 20
DEFAULT_MONITORING_TIME = 20
DEFAULT_MESSAGE = 'HELLO'

apiKeyconfig = settings.CHANGE['change']['apiKeyLight']
authDomainconfig = settings.CHANGE['change']['authLight']
dataBaseconfig = settings.CHANGE['change']['databaseLight']
stoRageconfig = settings.CHANGE['change']['storageLight']

db_host = settings.DATABASES['default']['HOST']
db_port = settings.DATABASES['default']['PORT']
db_database = settings.DATABASES['default']['NAME']
db_user = settings.DATABASES['default']['USER']
db_password = settings.DATABASES['default']['PASSWORD']

try:
    config = {
      "apiKey": apiKeyconfig,
      "authDomain": authDomainconfig,
      "databaseURL": dataBaseconfig,
      "storageBucket": stoRageconfig,
    }
    firebase = pyrebase.initialize_app(config)
    db = firebase.database()
except Exception as er:
    print er

# Step1: Agent Initialization
def lighting_agent(config_path, **kwargs):
    config = utils.load_config(config_path)
    def get_config(name):
        try:
            kwargs.pop(name)
        except KeyError:
            return config.get(name, '')

    # List of all keywords for a ac agent
    agentAPImapping = dict(status=[], brightness=[], color=[], saturation=[], power=[])
    log_variables = dict(status='text', brightness='double', hexcolor='text', power='double', offline_count='int')

    agent_id = get_config('agent_id')
    message = get_config('message')
    heartbeat_period = get_config('heartbeat_period')
    device_monitor_time = config.get('device_monitor_time', DEFAULT_MONITORING_TIME)
    building_name = get_config('building_name')
    zone_id = get_config('zone_id')
    model = get_config('model')
    if model == "Philips hue bridge":
        hue_username = get_config('username')
    else:
        hue_username = ''
    device_type = get_config('type')
    device = get_config('device')
    bearer = get_config('bearer')
    url = get_config('url')
    api = get_config('api')
    address = get_config('ipaddress')
    _address = address.replace('http://', '')
    _address = address.replace('https://', '')
    try:  # validate whether or not address is an ip address
        socket.inet_aton(_address)
        ip_address = _address
    except socket.error:
        ip_address = None
    identifiable = get_config('identifiable')

    # construct _topic_Agent_UI based on data obtained from DB
    _topic_Agent_UI_tail = building_name + '/' + str(zone_id) + '/' + agent_id
    topic_device_control = '/ui/agent/update/'+_topic_Agent_UI_tail
    print(topic_device_control)
    gateway_id = settings.gateway_id

    # 5. @params notification_info
    send_notification = True
    # email_fromaddr = settings.NOTIFICATION['email']['fromaddr']
    # email_username = settings.NOTIFICATION['email']['username']
    # email_password = settings.NOTIFICATION['email']['password']
    # email_mailServer = settings.NOTIFICATION['email']['mailServer']
    # notify_heartbeat = settings.NOTIFICATION['heartbeat']

    class LightingAgent(Agent):
        """Listens to everything and publishes a heartbeat according to the
        heartbeat period specified in the settings module.
        """

        def __init__(self, config_path, **kwargs):
            super(LightingAgent, self).__init__(**kwargs)
            self.config = utils.load_config(config_path)
            self._agent_id = agent_id
            self._message = message
            self._heartbeat_period = heartbeat_period
            self.model = model
            self.device_type = device_type
            self.url = url
            self.device = device
            self.bearer = bearer
            # initialize device object
            self.apiLib = importlib.import_module("DeviceAPI.classAPI." + api)
            self.Light = self.apiLib.API(model=self.model, device_type=self.device_type, agent_id=self._agent_id,
                                         bearer=self.bearer, device=self.device, url=self.url)

        @Core.receiver('onsetup')
        def onsetup(self, sender, **kwargs):
            # Demonstrate accessing a value from the config file
            _log.info(self.config.get('message', DEFAULT_MESSAGE))
            self.iotmodul = importlib.import_module("hive_lib.azure-iot-sdk-python.device.samples.iothub_client_sample")

        @Core.receiver('onstart')
        def onstart(self, sender, **kwargs):
            _log.debug("VERSION IS: {}".format(self.core.version()))
            self.gettoken()
            self.status_old = ""

        @Core.periodic(device_monitor_time)
        def deviceMonitorBehavior(self):

            self.Light.getDeviceStatus()

            # update firebase , posgres , azure
            if(self.Light.variables['device_status'] ==  self.status_old):
                pass
            else:
                self.publish_firebase()
                self.publish_postgres()
                self.StatusPublish(self.Light.variables)
                self.publish_azure_iot_hub(activity_type='devicemonitor', username=agent_id)

            self.status_old = self.Light.variables['device_status']
            print(self.status_old)

        def publish_firebase(self):

            try:

                db.child(gateway_id).child('devices').child(agent_id).child("dt").set(
                    datetime.now().replace(microsecond=0).isoformat())
                db.child(gateway_id).child('devices').child(agent_id).child("STATUS").set(
                    self.Light.variables['device_status'])
                db.child(gateway_id).child('devices').child(agent_id).child("TYPE").set(
                    self.Light.variables['device_type'])
                print('------------------update firebase--------------------')
            except Exception as er:
                print er

        def publish_azure_iot_hub(self, activity_type, username):
            # TODO publish to Azure IoT Hub u
            '''
            here we need to use code from /home/kwarodom/workspace/hive_os/volttron/
            hive_lib/azure-iot-sdk-python/device/samples/simulateddevices.py
            def iothub_client_telemetry_sample_run():
            '''
            print(self.Light.variables)
            x = {}
            x["device_id"] = self.Light.variables['agent_id']
            x["date_time"] = datetime.now().replace(microsecond=0).isoformat()
            x["unixtime"] = int(time.time())
            x["device_status"] = self.Light.variables['device_status']
            x["activity_type"] = activity_type
            x["username"] = username
            x["device_name"] = 'In-wall'
            x["device_type"] = "lightinglogging"
            print x
            discovered_address = self.iotmodul.iothub_client_sample_run(bytearray(str(x), 'utf8'))
            print('--------------update azure--------------')

        def publish_postgres(self):

            postgres_url = 'https://peahivemobilebackends.azurewebsites.net/api/v2.0/devices/'
            postgres_Authorization = 'Token '+self.api_token

            print str(self.Light.variables['device_status'])
            print str(self.Light.variables['agent_id'])

            print postgres_Authorization
            print postgres_Authorization
            print postgres_Authorization

            m = MultipartEncoder(
                fields={
                    "status": str(self.Light.variables['device_status']),
                    "device_id": str(self.Light.variables['agent_id']),
                    "device_type": "lightinglogging",
                    "last_scanned_time": datetime.now().replace(microsecond=0).isoformat(),
                }
            )

            r = requests.put(postgres_url,
                             data=m,
                             headers={'Content-Type': m.content_type,
                                      "Authorization": postgres_Authorization,
                                      })
            print r.status_code
            print('-------------------update postgres---------------')

        def StatusPublish(self, commsg):
            # TODO this is example how to write an app to control AC
            topic = str('/agent/zmq/update/hive/999/' + str(self.Light.variables['agent_id']))
            message = json.dumps(commsg)
            print ("topic {}".format(topic))
            print ("message {}".format(message))

            self.vip.pubsub.publish(
                'pubsub', topic,
                {'Type': 'pub device status to ZMQ'}, message)

        def gettoken(self):
            
            self.api_token = '89eff42e99c895fe1e1083e04af3bda412e685d7'
            conn = psycopg2.connect(host=db_host, port=db_port, database=db_database, user=db_user,
                                    password=db_password)
            self.conn = conn
            self.cur = self.conn.cursor()
            self.cur.execute("""SELECT * FROM token """)
            rows = self.cur.fetchall()
            for row in rows:
                if row[0] == gateway_id:
                    self.api_token =  row[1]
            self.conn.close()

        @PubSub.subscribe('pubsub', topic_device_control)
        def match_device_control(self, peer, sender, bus, topic, headers, message):
            print "Topic: {topic}".format(topic=topic)
            print "Headers: {headers}".format(headers=headers)
            print "Message: {message}\n".format(message=message)

            message = json.loads(message)
            if 'device_status' in message:
                self.Light.variables['device_status'] = str(message['device_status'])
            self.Light.setDeviceStatus(message)

            #step request status if change update firebase
            # or status not change delay time for update firebase
            print self.status_old
            time.sleep(1)
            print "1"
            self.Light.getDeviceStatus()
            # update firebase , posgres , azure
            if(self.Light.variables['device_status'] ==  self.status_old):
                time.sleep(1)
                print "2"
                self.Light.getDeviceStatus()
                if (self.Light.variables['device_status'] == self.status_old):
                    time.sleep(1)
                    print "3"
                    self.Light.getDeviceStatus()
                    if (self.Light.variables['device_status'] == self.status_old):
                        print "4"
                        time.sleep(2)
                    else:
                        self.publish_firebase()
                        self.publish_postgres()
                else:
                    self.publish_firebase()
                    self.publish_postgres()
            else:
                self.publish_firebase()
                self.publish_postgres()

            self.status_old = self.Light.variables['device_status']
            print "status old____________________________"
            print self.status_old
            print "status old____________________________"

    Agent.__name__ = '02ORV_InwallLightingAgent'
    return LightingAgent(config_path, **kwargs)

def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    try:
        utils.vip_main(lighting_agent, version=__version__)
    except Exception as e:
        _log.exception('unhandled exception')

if __name__ == '__main__':
    # Entry point for script
    sys.exit(main())
