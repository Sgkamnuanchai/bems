# -*- coding: utf-8 -*-
from __future__ import absolute_import
from datetime import datetime
import logging
import sys
import settings
from pprint import pformat
from volttron.platform.messaging.health import STATUS_GOOD
from volttron.platform.vip.agent import Agent, Core, PubSub, compat
from volttron.platform.agent import utils
from volttron.platform.messaging import headers as headers_mod
import importlib
import random
import json
import socket
import psycopg2
import psycopg2.extras
import pyrebase

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
def netatmoing_agent(config_path, **kwargs):
    config = utils.load_config(config_path)
    def get_config(name):
        try:
            kwargs.pop(name)
        except KeyError:
            return config.get(name, '')

    # List of all keywords for a netatmoing agent
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
    username = get_config('username')
    device_type = get_config('grant_type')
    url = get_config('url')
    password = get_config('password')
    address = get_config('address')
    client_id = get_config('client_id')
    scope = get_config('scope')
    client_secret = get_config('client_secret')
    grant_type = get_config('grant_type')
    content = get_config('content')
    api = get_config('api')
    ipaddress = get_config('ipaddress')
    device_type = get_config('device_type')
    # _address = address.replace('http://', '')
    # _address = address.replace('https://', '')
    # try:  # validate whether or not address is an ip address
    #     socket.inet_aton(_address)
    #     ip_address = _address
    # except socket.error:
    #     ip_address = None
    identifiable = get_config('identifiable')

    # DATABASES
    # print settings.DEBUG
    # db_host = settings.DATABASES['default']['HOST']
    # db_port = settings.DATABASES['default']['PORT']
    # db_database = settings.DATABASES['default']['NAME']
    # db_user = settings.DATABASES['default']['USER']
    # db_password = settings.DATABASES['default']['PASSWORD']
    # db_table_netatmoing = settings.DATABASES['default']['TABLE_netatmoing']
    # db_table_active_alert = settings.DATABASES['default']['TABLE_active_alert']
    # db_table_bemoss_notify = settings.DATABASES['default']['TABLE_bemoss_notify']
    # db_table_alerts_notificationchanneladdress = settings.DATABASES['default']['TABLE_alerts_notificationchanneladdress']
    # db_table_temp_time_counter = settings.DATABASES['default']['TABLE_temp_time_counter']
    # db_table_priority = settings.DATABASES['default']['TABLE_priority']

    # construct _topic_Agent_UI based on data obtained from DB
    _topic_Agent_UI_tail = building_name + '/' + str(zone_id) + '/' + agent_id
    topic_device_control = '/ui/agent/update/'+_topic_Agent_UI_tail
    print(topic_device_control)
    gateway_id = 'hivecdf12345'

    # 5. @params notification_info
    send_notification = True
    # email_fromaddr = settings.NOTIFICATION['email']['fromaddr']
    # email_username = settings.NOTIFICATION['email']['username']
    # email_password = settings.NOTIFICATION['email']['password']
    # email_mailServer = settings.NOTIFICATION['email']['mailServer']
    # notify_heartbeat = settings.NOTIFICATION['heartbeat']

    class netatmoingAgent(Agent):
        """Listens to everything and publishes a heartbeat according to the
        heartbeat period specified in the settings module.
        """

        def __init__(self, config_path, **kwargs):
            super(netatmoingAgent, self).__init__(**kwargs)
            self.config = utils.load_config(config_path)
            self._agent_id = agent_id
            self._message = message
            self._heartbeat_period = heartbeat_period
            self.model = model
            self.url = url
            self.address = address
            self.client_id = client_id
            self.username = username
            self.password = password
            self.scope = scope
            self.client_secret = client_secret
            self.grant_type = grant_type
            self.content = content
            self.device_type = device_type

            # initialize device object
            self.apiLib = importlib.import_module("DeviceAPI.classAPI." + api)
            self.netatmo = self.apiLib.API(model=self.model, agent_id=self._agent_id,device_type = self.device_type,username=self.username, client_id = self.client_id,
                                        url=self.url, password=self.password, scope=self.scope, client_secret=self.client_secret ,grant_type=self.grant_type,content=self.content)

        @Core.receiver('onsetup')
        def onsetup(self, sender, **kwargs):
            # Demonstrate accessing a value from the config file
            _log.info(self.config.get('message', DEFAULT_MESSAGE))

            # setup connection with db -> Connect to local postgres
            # try:
            #     self.con = psycopg2.connect(host=db_host, port=db_port, database=db_database, user=db_user,
            #                                 password=db_password)
            #     self.cur = self.con.cursor()  # open a cursor to perfomm database operations
            #     _log.debug("{} connected to the db name {}".format(agent_id, db_database))
            # except:
            #     _log.error("ERROR: {} fails to connect to the database name {}".format(agent_id, db_database))
            # connect to Azure IoT hub
            self.iotmodul = importlib.import_module("hive_lib.azure-iot-sdk-python.device.samples.iothub_client_sample")

        @Core.receiver('onstart')
        def onstart(self, sender, **kwargs):
            _log.debug("VERSION IS: {}".format(self.core.version()))

        @Core.periodic(device_monitor_time)
        def deviceMonitorBehavior(self):

            self.netatmo.getDeviceStatus()

            self.StatusPublish(self.netatmo.variables)

            # TODO update local postgres
            # self.publish_local_postgres()

            # update firebase
            self.publish_firebase()

            # update Azure IoT Hub
            # self.publish_azure_iot_hub()

        def publish_firebase(self):
            try:
                db.child(gateway_id).child('devices').child(agent_id).child("dt").set(datetime.now().replace(microsecond=0).isoformat())
                # db.child(gateway_id).child('devices').child(agent_id).child("device_status").set(self.netatmo.variables['device_status'])
                db.child(gateway_id).child('devices').child(agent_id).child("noise").set(self.netatmo.variables['noise'])
                db.child(gateway_id).child('devices').child(agent_id).child("temperature").set(self.netatmo.variables['temperature'])
                db.child(gateway_id).child('devices').child(agent_id).child("pressure").set(self.netatmo.variables['pressure'])
                db.child(gateway_id).child('devices').child(agent_id).child("co2").set(self.netatmo.variables['co2'])
                db.child(gateway_id).child('devices').child(agent_id).child("date_max_temp").set(self.netatmo.variables['date_max_temp'])
                db.child(gateway_id).child('devices').child(agent_id).child("humidity").set(self.netatmo.variables['humidity'])
                db.child(gateway_id).child('devices').child(agent_id).child("date_min_temp").set(self.netatmo.variables['date_min_temp'])
                db.child(gateway_id).child('devices').child(agent_id).child("max_temp").set(self.netatmo.variables['max_temp'])
                db.child(gateway_id).child('devices').child(agent_id).child("min_temp").set(self.netatmo.variables['min_temp'])
                db.child(gateway_id).child('devices').child(agent_id).child("outdoor_temperature").set(self.netatmo.variables['outdoor_temperature'])
                db.child(gateway_id).child('devices').child(agent_id).child("outdoor_humidity").set(self.netatmo.variables['outdoor_humidity'])
                db.child(gateway_id).child('devices').child(agent_id).child("outdoor_date_max_temp").set(self.netatmo.variables['outdoor_date_max_temp'])
                db.child(gateway_id).child('devices').child(agent_id).child("outdoor_date_min_temp").set(self.netatmo.variables['outdoor_date_min_temp'])
                db.child(gateway_id).child('devices').child(agent_id).child("outdoor_max_temp").set(self.netatmo.variables['outdoor_max_temp'])
                db.child(gateway_id).child('devices').child(agent_id).child("outdoor_min_temp").set(self.netatmo.variables['outdoor_min_temp'])
                db.child(gateway_id).child('devices').child(agent_id).child("device_type").set(self.netatmo.variables['device_type'])


            except Exception as er:
                print er

        def publish_azure_iot_hub(self):
            # TODO publish to Azure IoT Hub u
            '''
            here we need to use code from /home/kwarodom/workspace/hive_os/volttron/
            hive_lib/azure-iot-sdk-python/device/samples/simulateddevices.py
            def iothub_client_telemetry_sample_run():
            '''
            print(self.netatmo.variables)
            x = {}
            x["agent_id"] = self.netatmo.variables['agent_id']
            x["dt"] = datetime.now().replace(microsecond=0).isoformat()
            x["device_status"] = self.netatmo.variables['device_status']
            x["device_type"] = self.netatmo.variables['device_type']
            discovered_address = self.iotmodul.iothub_client_sample_run(bytearray(str(x), 'utf8'))

        def StatusPublish(self, commsg):
            # TODO this is example how to write an app to control AC
            topic = str('/agent/zmq/update/hive/999/' + str(self.netatmo.variables['agent_id']))
            message = json.dumps(commsg)
            print ("topic {}".format(topic))
            print ("message {}".format(message))

            self.vip.pubsub.publish(
                'pubsub', topic,
                {'Type': 'pub device status to ZMQ'}, message)
        
        @PubSub.subscribe('pubsub', topic_device_control)
        def match_device_control(self, peer, sender, bus, topic, headers, message):
            print "Topic: {topic}".format(topic=topic)
            print "Headers: {headers}".format(headers=headers)
            print "Message: {message}\n".format(message=message)
            self.netatmo.setDeviceStatus(json.loads(message))

    Agent.__name__ = 'netatmoingAgent'
    return netatmoingAgent(config_path, **kwargs)

def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    try:
        utils.vip_main(netatmoing_agent, version=__version__)
    except Exception as e:
        _log.exception('unhandled exception')

if __name__ == '__main__':
    # Entry point for script
    sys.exit(main())
