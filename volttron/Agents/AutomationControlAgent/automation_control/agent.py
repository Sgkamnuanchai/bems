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
import requests
import socket
import psycopg2
import psycopg2.extras
import pyrebase
import pprint
import psycopg2
import sys

utils.setup_logging()
_log = logging.getLogger(__name__)
__version__ = '3.2'
DEFAULT_HEARTBEAT_PERIOD = 20
DEFAULT_MONITORING_TIME = 20
DEFAULT_MESSAGE = 'HELLO'

# Step1: Agent Initialization
def scenecontrol_agent(config_path, **kwargs):
    config = utils.load_config(config_path)

    def get_config(name):
        try:
            kwargs.pop(name)
        except KeyError:
            return config.get(name, '')

    agent_id = get_config('agent_id')


    # DATABASES
    automation_id = get_config('automation_id')
    db_host = settings.DATABASES['default']['HOST']
    db_port = settings.DATABASES['default']['PORT']
    db_database = settings.DATABASES['default']['NAME']
    db_user = settings.DATABASES['default']['USER']
    db_password = settings.DATABASES['default']['PASSWORD']
    topic_tricker = ''
    conn = psycopg2.connect(host=db_host, port=db_port, database=db_database, user=db_user,
                            password=db_password)
    cur = conn.cursor()
    cur.execute("""SELECT * FROM automation """)
    rows = cur.fetchall()
    for row in rows:
        if int(automation_id) == int(row[0]):
            triger_device = row[2]
            triger_device_str = ((triger_device).replace("['", '', 1)).replace("']", '', 1)
            topic_tricker = '/agent/zmq/update/hive/999/' + triger_device_str
            print "<<<< subscribe topic >>>>>"
            print topic_tricker

    conn.close()


    class SceneControlAgent(Agent):
        def __init__(self, config_path, **kwargs):
            super(SceneControlAgent, self).__init__(**kwargs)
            self.config = utils.load_config(config_path)
            self._agent_id = agent_id
            self.conn = None
            self.cur = None
            self.sceneconf = None
            self.num_of_scene = None
            self.token = None
            self.url = None
            self.automation_id = automation_id
            # self.reload_config()  # Reload Scene when Agent Start

            _log.info("init attribute to Agent")

        @Core.receiver('onsetup')
        def onsetup(self, sender, **kwargs):
            # Demonstrate accessing a value from the config file
            _log.info(self.config.get('message', DEFAULT_MESSAGE))
            # self._agent_id = self.config.get('agentid')
            # self.url = self.config.get('backend_url') + self.config.get('scene_api')
            # self.token = self.config.get('token')

        @Core.receiver('onstart')
        def onstart(self, sender, **kwargs):
            _log.debug("VERSION IS: {}".format(self.core.version()))
            self.load_config()

        @PubSub.subscribe('pubsub', topic_tricker)
        def match_agent_reload(self, peer, sender, bus, topic, headers, message):
            print ">>"
            print ">>"
            print "<<<<<< step 1 subscribe triger >>>>>>>>"
            print "--------------------"
            print(" Automation set device = {}".format(self.triger_device))
            print(" Automation set event = {}".format(self.triger_event))
            print(" Automation set value = {}".format(self.triger_value))
            convert_msg = json.loads(message)
            triger_event_now = convert_msg[self.triger_event]
            print(" value reading now is value = {}".format(convert_msg[self.triger_event]))

            if triger_event_now == self.triger_value:
                print(" Automation set value == value reading now ")
                print(" go to step [[[  2  ]]] check condition event ")
                self.conditionevent()



        def load_config(self): # reload scene configuration to Agent Variable

            conn = psycopg2.connect(host=db_host, port=db_port, database=db_database, user=db_user,
                                    password=db_password)
            self.conn = conn
            self.cur = self.conn.cursor()
            self.cur.execute("""SELECT * FROM automation """)
            rows = self.cur.fetchall()

            for row in rows :
                if int(self.automation_id) == int(row[0]):
                    self.triger_device = row[2]
                    self.triger_event = row[3]
                    self.triger_value = row[4]
                    self.condition_event = row[5]
                    self.condition_value = row[6]
                    self.devicecontrols = (json.loads((row[7])))
                    print(" triger_device = {}".format(self.triger_device))
                    print(" triger_event = {}".format(self.triger_event))
                    print(" triger_value = {}".format(self.triger_value))
                    print(" condition_event  = {}".format(self.condition_event))
                    print(" condition_value = {}".format(self.condition_value))
                    print(" devicecontrols = {}".format(self.devicecontrols))

            self.conn.close()

        def conditionevent(self):
            print ">>"
            print ">>"
            print "<<<<<< step 2 check condition event>>>>>>>>"

            conn = psycopg2.connect(host=db_host, port=db_port, database=db_database, user=db_user,
                                    password=db_password)

            if self.condition_event == 'SCENE':
                self.conn = conn
                self.cur = self.conn.cursor()
                self.cur.execute("""SELECT * FROM active_scene """)
                rows = self.cur.fetchall()
                for row in rows :
                    self.scene_id_now = row[0]
                    self.scene_name_now = row[1]
                    print(" condition now = {}".format(self.scene_name_now))
                    print(" condition in automation seting  = {}".format(self.scene_name_now))

                    if str(self.condition_value) == str(self.scene_name_now):
                        print '>> condition value == condition now'
                        print(" go to step [[[  3  ]]] device control ")
                        self.devicecontrol()
                    else:
                        print '>> condition value != condition now'
                        print ""
                        print(" go to step [[[  1  ]]] for subscribe triger")
                        print ""

            self.conn.close()


        def devicecontrol(self):
            print ">>"
            print ">>"
            print "<<<<<<step 3 device control >>>>>>>>"
            try:
                for task in self.devicecontrols:
                    topic = str('/ui/agent/update/hive/999/') + str(task['device_id'])
                    print topic
                    message = json.dumps(task['command'])
                    print ("topic {}".format(topic))
                    print ("message {} \n".format(message))
                    self.vip.pubsub.publish(
                        'pubsub', topic,
                        {'Type': 'HiVE Scene Control'}, message)
            except Exception as Error:
                print('Reload Config to Agent')


    Agent.__name__ = 'scenecontrolAgent'
    return SceneControlAgent(config_path, **kwargs)


def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    try:
        utils.vip_main(scenecontrol_agent, version=__version__)

    except Exception as e:
        _log.exception('unhandled exception')


if __name__ == '__main__':
    # Entry point for script
    sys.exit(main())