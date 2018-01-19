# -*- coding: utf-8 -*-
'''
Copyright (c) 2016, Virginia Tech
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
 following conditions are met:
1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those of the authors and should not be
interpreted as representing official policies, either expressed or implied, of the FreeBSD Project.

This material was prepared as an account of work sponsored by an agency of the United States Government. Neither the
United States Government nor the United States Department of Energy, nor Virginia Tech, nor any of their employees,
nor any jurisdiction or organization that has cooperated in the development of these materials, makes any warranty,
express or implied, or assumes any legal liability or responsibility for the accuracy, completeness, or usefulness or
any information, apparatus, product, software, or process disclosed, or represents that its use would not infringe
privately owned rights.

Reference herein to any specific commercial product, process, or service by trade name, trademark, manufacturer, or
otherwise does not necessarily constitute or imply its endorsement, recommendation, favoring by the United States
Government or any agency thereof, or Virginia Tech - Advanced Research Institute. The views and opinions of authors
expressed herein do not necessarily state or reflect those of the United States Government or any agency thereof.

VIRGINIA TECH – ADVANCED RESEARCH INSTITUTE
under Contract DE-EE0006352

#__author__ = "BEMOSS Team"
#__credits__ = ""
#__version__ = "2.0"
#__maintainer__ = "BEMOSS Team"
#__email__ = "aribemoss@gmail.com"
#__website__ = "www.bemoss.org"
#__created__ = "2014-09-12 12:04:50"
#__lastUpdated__ = "2016-03-14 11:23:33"
'''

import logging
import sys
import datetime
import json
import os
from volttron.platform.agent import BaseAgent, PublishMixin, periodic
from volttron.platform.agent import utils, matching
from volttron.platform.messaging import headers as headers_mod
import settings
import psycopg2  # PostgresQL database adapter
import re

utils.setup_logging()
_log = logging.getLogger(__name__)
app_name = "appLauncher"
debug_agent = False
clock_time = 1
time_to_start_previous_apps = 30  # sec

# @params agent & DB interfaces
db_host = "localhost"
db_port = "5432"
db_database = "bemossdb"
db_user = "admin"
db_password = "admin"
db_table_application_registered = "application_registered"
db_table_application_running = "application_running"

class AppLauncherAgent(PublishMixin, BaseAgent):
    '''Listens to UI to launch new APP in the BEMOSS APP Store'''
    def __init__(self, config_path, **kwargs):
        super(AppLauncherAgent, self).__init__(**kwargs)
        self.config = utils.load_config(config_path)
        # self.app_number = 0
        #connect to the database
        try:
            self.con = psycopg2.connect(host=db_host, port=db_port, database=db_database, user=db_user,
                                        password=db_password)
            self.cur = self.con.cursor()  # open a cursor to perform database operations
            print("AppLauncher Agent connects to the database name {} successfully".format(db_database))
        except:
            print("ERROR: {} fails to connect to the database name {}".format(app_name, db_database))

        self.time_applauncher_start = datetime.datetime.now()
        self.already_started_previous_apps = False

    def setup(self):
        # Demonstrate accessing a value from the config file
        _log.info(self.config['message'])
        self._agent_id = self.config['agent_id']
        # Always call the base class setup()
        super(AppLauncherAgent, self).setup()
        # self.appLauncherInitiator()
        print "AppLauncher Agent is waiting for UI to activate/disable APPs"

    # clockBehavior (CyclicBehavior)
    @periodic(clock_time)
    def clockBehavior(self):
        #1. check current time
        self.time_applauncher_now = datetime.datetime.now()
        if self.already_started_previous_apps:
            # print "AppLauncher Agent >> appLauncherInitiator has already run"
            pass
        else:
            # print "AppLauncher Agent >> appLauncherInitiator has not run yet"
            if (self.time_applauncher_now - self.time_applauncher_start).seconds > time_to_start_previous_apps:
                print "AppLauncher Agent is starting previously running Apps"
                self.appLauncherInitiator()
                self.already_started_previous_apps = True
            else:
                pass

    # Add Cyclic behavior to track current status of app then update DB
    def appLauncherInitiator(self):
        try:
            self.cur.execute("SELECT * FROM "+db_table_application_running)
            # self.cur.execute("SELECT status FROM applications_running WHERE app_name=%s", (ui_app_name,))
            print self.cur.rowcount
            if self.cur.rowcount != 0:
                all_row = self.cur.fetchall()
                for row in all_row:
                    if row[3] == 'running':  # rerun app for the agent
                        # To launch agent: 1.get app_name, 2.get agent_id, 3.get auth_token
                        print "This {} is {}".format(row[1], row[3])
                        _temp_app_agent_id = str(row[1]).split('_')
                        app_name = _temp_app_agent_id[0]+'_'+_temp_app_agent_id[1]
                        agent_id = _temp_app_agent_id[2]
                        self.cur.execute("SELECT auth_token FROM "+db_table_application_registered+" WHERE app_name=%s",
                                         (app_name,))
                        if self.cur.rowcount != 0:
                            auth_token = str(self.cur.fetchone()[0])
                        app_setting = row[4]
                        print "AppLauncher >> is trying the previous run App {} for agent {} with auth_token {} and " \
                              "app_setting {}".format(app_name, agent_id, auth_token, app_setting)
                        self.app_has_already_launched = False
                        self.launch_app(app_name, agent_id, auth_token)
                    else:  # do nothing
                        print "This {} is {}".format(row[1], row[3])
            else:
                print "AppLauncher >> no App was running"
        except:
            "AppLauncher >> failed to launch the previous run Apps"

    # on_match (Cyclic Behavior) to filter message from the UI to launch new APP
    @matching.match_start('/ui/appLauncher/')
    def on_match(self, topic, headers, message, match):
        print "AppLauncher Agent got Topic: {topic}".format(topic=topic)
        _sub_topic = str(topic).split('/')
        app_name = _sub_topic[3]
        agent_id = _sub_topic[4]
        _data = json.dumps(message[0])
        _data = json.loads(message[0])
        auth_token = _data.get('auth_token')
        if _sub_topic[5] == 'launch':
            self.app_has_already_launched = False
            self.launch_app(app_name, agent_id, auth_token)
        elif _sub_topic[5] == 'disable':
            self.app_has_already_launched = False
            self.disable_app(app_name, agent_id, auth_token)
        else:
            "AppLauncher Agent does not understand this message"

    def launch_app(self, ui_app_name, ui_agent_id, ui_auth_token):
        # 1. query database whether the app_name is verified and registered
        # if app_name is in database with the valid authorization_token, then launch agent
        self.cur.execute("SELECT auth_token FROM "+db_table_application_registered+" WHERE app_name=%s", (ui_app_name))
        if self.cur.rowcount != 0:
            app_auth_token = self.cur.fetchone()[0]
            if ui_auth_token == app_auth_token:
                # 1. launch app
                PROJECT_DIR = settings.PROJECT_DIR
                sys.path.append(PROJECT_DIR)
                os.system("volttron-ctl status > app_running_agent.txt")
                # os.system("bin/volttron-ctrl list-agent > app_running_agent.txt")
                infile = open('app_running_agent.txt', 'r')
                for line in infile:
                    # print(line, end='') #write to a next file name outfile
                    match = re.search(ui_app_name+'_'+ui_agent_id, line) \
                            and re.search('running', line)  # have results in match
                    if match:  # The app that ui requested has already launched
                        self.app_has_already_launched = True
                        print "AppLauncher failed to launch APP: {}, APP has actually been launched"\
                            .format(ui_app_name)
                        print "AppLauncher >> {}".format(line)

                if self.app_has_already_launched:
                    _launch_file_to_check = str(ui_app_name) + "_" + str(ui_agent_id)
                    self.cur.execute("SELECT status FROM "+db_table_application_running+" WHERE app_agent_id=%s",
                                     (_launch_file_to_check,))
                    if self.cur.rowcount != 0:  # this APP used to be launched before
                        _app_status = str(self.cur.fetchone()[0])
                        if _app_status == "running":  # no need to launch new app
                            pass
                        else:
                            self.cur.execute("UPDATE application_running SET status=%s WHERE app_agent_id=%s",
                                     ("running", _launch_file_to_check,))
                            self.con.commit()
                    else:
                        # 2. log app that has been launched to the database
                        _launch_file_name = str(ui_app_name) + "_" + str(ui_agent_id)
                        _start_time = str(datetime.datetime.now())
                        _app_status = "running"
                        self.cur.execute("SELECT application_id FROM "+db_table_application_running)
                        if self.cur.rowcount != 0:
                            # print 'cur.fetchall()' + str(max(cur.fetchall())[0])
                            app_no = max(self.cur.fetchall())[0] + 1
                        else: #default no_app
                            app_no = 1
                        self.cur.execute("INSERT INTO application_running(application_id, app_agent_id, start_time, status) "
                             "VALUES(%s,%s,%s,%s)",
                             (app_no, _launch_file_name, _start_time, _app_status))
                        self.con.commit()
                        print "AppLauncher >> the requested APP {} for {} is running but not in db, " \
                              "now it is added to db".format(ui_app_name, ui_agent_id)
                        print "AppLauncher >> NOTE Date and Time launch APP is the current time not actual time"

                    _topic_appLauncher_ui = '/appLauncher/ui/' + ui_app_name + '/' + ui_agent_id + '/' \
                                            + 'launch/response'
                    _headers = {
                        headers_mod.FROM: app_name,
                        headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
                    }
                    _message = "failure"
                    self.publish(_topic_appLauncher_ui, _headers, _message)
                else: # APP has not launched yet
                    _launch_file_to_check = str(ui_app_name) + "_" + str(ui_agent_id)
                    self.cur.execute("SELECT status FROM "+db_table_application_running+" WHERE app_agent_id=%s",
                                     (_launch_file_to_check,))
                    if self.cur.rowcount != 0: # delete existing row from the table before launching new app
                        # self.cur.execute("DELETE FROM "+db_table_application_running+" WHERE app_agent_id=%s",
                        #                  (_launch_file_to_check,))
                        # self.con.commit()
                        self.launch_existing_app(ui_app_name, ui_agent_id)
                    else: #this APP has never been launched and not in db launch new app
                        self.launch_new_app(ui_app_name, ui_agent_id)
            else:
                print "UI failed to authorize with AppLauncher Agent before launching the requested APP"
        else:
            print "The APP that UI requested is neither REGISTERED nor AVAILABLE"

    def launch_existing_app(self, ui_app_name, ui_agent_id):
        print "launch existing app: start"
        self.cur.execute("SELECT executable FROM "+db_table_application_registered+" WHERE app_name=%s", (ui_app_name,))
        # 1. launch app for an agent based on the exec file and agent_id
        if self.cur.rowcount != 0:
            _exec_name = str(self.cur.fetchone()[0])
            _exec = _exec_name+"-0.1-py2.7.egg --config \"%c\" --sub \"%s\" --pub \"%p\""
            data = {
                "agent": {
                    "exec": _exec
                },
                "agent_id": ui_agent_id,
                "message": "hello my name is "+ui_agent_id
            }
            PROJECT_DIR = settings.PROJECT_DIR
            _launch_file = os.path.join(PROJECT_DIR, "Applications/launch/"
                                        + str(ui_app_name) + "_" + str(ui_agent_id)+".launch.json")
            if debug_agent: print(_launch_file)
            with open(_launch_file, 'w') as outfile:
                json.dump(data, outfile, indent=4, sort_keys=True)
            if debug_agent: print(os.path.basename(_launch_file))
            #os.system(#". env/bin/activate"
            #       # ";volttron-ctl stop --tag " + agent_id+
            #       "volttron-pkg configure /tmp/volttron_wheels/"+agentname+"agent-0.1-py2-none-any.whl "+ _launch_file+
            #       ";volttron-ctl install "+agent_id+"=/tmp/volttron_wheels/"+agentname+"agent-0.1-py2-none-any.whl"
            #       ";volttron-ctl start --tag " + agent_id+
            #       ";volttron-
            os.system("volttron-ctl status > app_running_agent.txt")
            # os.system("bin/volttron-ctrl list-agent > app_running_agent.txt")
            infile = open('app_running_agent.txt', 'r')
            installed = False
            for line in infile:
                # print(line, end='') #write to a next file name outfile
                match = re.search(ui_app_name+'_'+ui_agent_id, line)
                if match:  # The app that ui requested has not been installed.
                    print "APP: {}, APP has actually been installed. Just starting"\
                        .format(ui_app_name)
                    installed = True

            if not installed:
                os.system("volttron-pkg configure /tmp/volttron_wheels/"+ui_app_name+"agent-0.1-py2-none-any.whl "+ _launch_file)
                os.system("volttron-ctl install " + ui_app_name + "_" + ui_agent_id +"=/tmp/volttron_wheels/" + ui_app_name + "agent-0.1-py2-none-any.whl")

            print("OK")
            # os.system("volttron-ctl start --tag "+os.path.basename(_launch_file))
            os.system("volttron-ctl start --tag "+ui_app_name+"_"+ui_agent_id)
            os.system("volttron-ctl status")
            # os.system("bin/volttron-ctrl load-agent "+_launch_file)
            # os.system("bin/volttron-ctrl start-agent "+os.path.basename(_launch_file))
            # os.system("bin/volttron-ctrl list-agent")
            print "AppLauncher has successfully launched APP: {} for Agent: {}"\
                .format(ui_app_name, ui_agent_id)
            # send reply back to UI
            _topic_appLauncher_ui = '/appLauncher/ui/' + ui_app_name + '/' + ui_agent_id + '/' + 'launch/response'
            _headers = {
                headers_mod.FROM: app_name,
                headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
            }
            _message = "success"
            self.publish(_topic_appLauncher_ui, _headers, _message)

    def launch_new_app(self, ui_app_name, ui_agent_id):
        print "launch new app: start"
        self.cur.execute("SELECT executable FROM "+db_table_application_registered+" WHERE app_name=%s", (ui_app_name,))
        # 1. launch app for an agent based on the exec file and agent_id
        if self.cur.rowcount != 0:
            _exec_name = str(self.cur.fetchone()[0])
            _exec = _exec_name+"-0.1-py2.7.egg --config \"%c\" --sub \"%s\" --pub \"%p\""
            data = {
                "agent": {
                    "exec": _exec
                },
                "agent_id": ui_agent_id,
                "message": "hello my name is " + ui_agent_id
            }
            PROJECT_DIR = settings.PROJECT_DIR
            _launch_file = os.path.join(PROJECT_DIR, "Applications/launch/"
                                        + str(ui_app_name) + "_" + str(ui_agent_id)+".launch.json")
            if debug_agent: print(_launch_file)
            with open(_launch_file, 'w') as outfile:
                json.dump(data, outfile, indent=4, sort_keys=True)
            if debug_agent: print(os.path.basename(_launch_file))

            os.system("volttron-ctl status > app_running_agent.txt")
            # os.system("bin/volttron-ctrl list-agent > app_running_agent.txt")
            infile = open('app_running_agent.txt', 'r')
            installed = False
            for line in infile:
                # print(line, end='') #write to a next file name outfile
                match = re.search(ui_app_name+'_'+ui_agent_id, line)
                if match:  # The app that ui requested has not been installed.
                    print "APP: {}, APP has actually been installed. Just starting"\
                        .format(ui_app_name)
                    installed = True

            if not installed:
                os.system("volttron-pkg configure /tmp/volttron_wheels/" + ui_app_name + "agent-0.1-py2-none-any.whl " + _launch_file)
                os.system("volttron-ctl install " + ui_app_name + "_" + ui_agent_id +"=/tmp/volttron_wheels/" + ui_app_name + "agent-0.1-py2-none-any.whl")

            # os.system("volttron-ctl start --tag "+os.path.basename(_launch_file))
            os.system("volttron-ctl start --tag " + ui_app_name + "_" + ui_agent_id)
            os.system("volttron-ctl status")

            print "AppLauncher has successfully launched APP: {} for Agent: {}"\
                .format(ui_app_name, ui_agent_id)
            # send reply back to UI
            _topic_appLauncher_ui = '/appLauncher/ui/' + ui_app_name + '/' + ui_agent_id + '/' + 'launch/response'
            _headers = {
                headers_mod.FROM: app_name,
                headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
            }
            _message = "success"
            self.publish(_topic_appLauncher_ui, _headers, _message)
            # self.app_number += 1
            self.cur.execute("SELECT description FROM "+db_table_application_registered+" WHERE app_name=%s", (ui_app_name,))
            if self.cur.rowcount != 0:
                _app_description = str(self.cur.fetchone()[0])
                print "The description of APP: {} is {}".format(ui_app_name, _app_description)
            else:
                print "AppLauncher failed to get APP: {} description".format(ui_app_name)

            # 2. log app that has been launched to the database
            _launch_file_name = str(ui_app_name) + "_" + str(ui_agent_id)
            _start_time = str(datetime.datetime.now())
            _app_status = "running"
            self.cur.execute("SELECT application_id FROM "+db_table_application_running)
            if self.cur.rowcount != 0:
                # print 'cur.fetchall()' + str(max(cur.fetchall())[0])
                app_no = max(self.cur.fetchall())[0] + 1
            else: #default no_app
                app_no = 1
            self.cur.execute("INSERT INTO application_running(application_id, app_agent_id, start_time, status) "
                             "VALUES(%s,%s,%s,%s)",
                             (app_no, _launch_file_name, _start_time, _app_status))
            self.con.commit()
            print "AppLauncher finished update table applications_running of APP: {}".format(ui_app_name)
            print "with launch_file: {}, at timestamp {}".format(_launch_file, _start_time)
        else:
            print "AppLauncher failed to launch APP: {} for Agent: {}".format(ui_app_name, ui_agent_id)

    def disable_app(self, ui_app_name, ui_agent_id, ui_auth_token):
        print "disable app: start"
        #1. query database whether the ui_app_name is verified and registered
        self.cur.execute("SELECT auth_token FROM "+db_table_application_registered+" WHERE app_name=%s", (ui_app_name,))
        if self.cur.rowcount != 0:
            app_auth_token = self.cur.fetchone()[0]
            if ui_auth_token == app_auth_token:
                #check whether the ui_app_name and ui_agent_id is actually running
                PROJECT_DIR = settings.PROJECT_DIR
                sys.path.append(PROJECT_DIR)
                os.system("volttron-ctl status > app_running_agent.txt")
                # os.system("bin/volttron-ctrl list-agent > app_running_agent.txt")
                infile = open('app_running_agent.txt', 'r')
                for line in infile:
                    #print(line, end='') #write to a next file name outfile
                    print(line)
                    match = re.search(ui_app_name+'_'+ui_agent_id, line) \
                            and re.search('running', line)  # have results in match
                    if match: # The app that ui requested has already launched
                        self.app_has_already_launched = True
                    else:
                        pass

                if self.app_has_already_launched:
                    _launch_file_to_check = str(ui_app_name) + "_" + str(ui_agent_id)
                    self.cur.execute("SELECT status FROM "+db_table_application_running+" WHERE app_agent_id=%s",
                                     (_launch_file_to_check,))
                    if self.cur.rowcount != 0:
                        _app_status = str(self.cur.fetchone()[0])
                        #if it's running disable app
                        if _app_status == "running":
                            _lauch_file_to_disable = _launch_file_to_check
                            os.system("volttron-ctl stop --tag "+_lauch_file_to_disable)
                            os.system("volttron-ctl status")
                            print "AppLauncher has successfully disabled APP: {} ".format(ui_app_name)
                            self.cur.execute("UPDATE application_running SET status=%s WHERE app_agent_id=%s"
                                             , ('disabled', _launch_file_to_check))
                            self.con.commit()
                            # send reply back to UI
                            topic_appLauncher_ui = '/appLauncher/ui/' + ui_app_name + '/' + ui_agent_id + '/' \
                                                   + 'disable/response'
                            headers = {
                                headers_mod.FROM: app_name,
                                headers_mod.CONTENT_TYPE: headers_mod.CONTENT_TYPE.JSON,
                            }
                            message = "success"
                            self.publish(topic_appLauncher_ui, headers, message)
                        elif _app_status == "disabled":
                            print "AppLauncher: the requested APP: {} for Agent: {} has already disabled"\
                                .format(ui_app_name, ui_agent_id)
                        else:
                            print "AppLauncher: the requested APP: {} for Agent: {} has unknown status"\
                                .format(ui_app_name, ui_agent_id)
                    else:
                        print "AppLauncher: APP {} for Agent: {} is not running".format(ui_app_name, ui_agent_id)
                else: # app is acutally not running no need to do action
                    "AppLauncher: discard request to disable APP: {} for Agent: {} since it's not running"\
                        .format(ui_app_name, ui_agent_id)
            else:
                print "UI failed to authorize with AppLauncher Agent before disabling the requested APP"
        else:
            print "The APP that UI requested is neither REGISTERED nor AVAILABLE"

def main(argv=sys.argv):
    '''Main method called by the eggsecutable.'''
    try:
        utils.default_main(AppLauncherAgent,
                           description='this is an AppLauncher agent',
                           argv=argv)
    except Exception as e:
        _log.exception('unhandled exception')

if __name__ == '__main__':
    # Entry point for script
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass