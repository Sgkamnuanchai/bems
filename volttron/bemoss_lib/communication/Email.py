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

# This Email class is for an agent wishing to send an email to any mail server

import smtplib  # simple mail transfer protocol library
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import datetime

class EmailService:
    # method1: GET a model number of a device by XML read
    def sendEmail(self, fromaddr, recipients, username, password, subject, text, mailServer):
        try:
            # agent snippet to send notification to a building operator
            self.fromaddr = fromaddr
            self.recipients = recipients
            self.username = username
            self.password = password
            self.msg = MIMEMultipart()
            self.msg['From'] = self.fromaddr
            self.msg['To'] = ",".join(self.recipients)
            self.msg['Subject'] = subject
            self.text = text
            self.msg.attach(MIMEText(self.text))
            self.server = smtplib.SMTP(mailServer)
            self.server.ehlo()
            self.server.starttls()
            self.server.ehlo()
            self.server.login(self.username, self.password)
            self.server.sendmail(self.fromaddr, self.recipients, self.msg.as_string())
            self.server.quit()
            print("Email is sent successfully")
        except:
            EmailService
            print('Error: Connection with SMTP server failed')

# This main method will not be executed when this class is used as a module
def main():
    # create an object with initialized data from DeviceDiscovery Agent
    # requirements for instantiation1. model, 2.type, 3.api, 4. address
    params = {"grid_energy_import": 10, "grid_electricity_bill": 40, "grid_avg_power":300, "solar_energy_generation": 20,
              "solar_electricity_bill": 80, "solar_avg_power": 1200, "load_energy_consumption": 30,
              "load_electricity_bill": 120, "load_avg_power": 1300}
    sendText = "Dear Sisaengtham School,\n " \
               "\n" \
               "\tHere is your energy report for {date},\n" \
               "\n" \
               "\t1. Grid: Energy Imported={grid_energy_import} kWh, Electricity Bill={grid_electricity_bill} Baht, Average Power={grid_avg_power} W\n" \
               "\t2. Solar: Energy Generated={solar_energy_generation} kWh, Bill Saving from Solar={solar_electricity_bill} Baht, Average Power={solar_avg_power} W\n"\
               "\t3. Load: Energy Consumed={load_energy_consumption} kWh, Actual Bill if Without Solar={load_electricity_bill} Baht, Average Power={load_avg_power} W\n"\
               "\n" \
               "Best Regard,\n" \
               "PEA HiVE Development Team,\n" \
               "email: peahive@gmail.com,\n" \
               "FB: facebook.som/peahiveplatform,\n" \
               "Line: @peahive" \
        .format(date=datetime.datetime.now().date(), grid_energy_import=params['grid_energy_import'], grid_electricity_bill=params['grid_electricity_bill'],
                grid_avg_power=params['grid_avg_power'], solar_energy_generation=params['solar_energy_generation'],
                solar_electricity_bill=params['solar_electricity_bill'], solar_avg_power=params['solar_avg_power'],
                load_energy_consumption=params['load_energy_consumption'],
                load_electricity_bill=params['load_electricity_bill'], load_avg_power=params['load_avg_power'],)
    print(sendText)
    email = EmailService()
    email.sendEmail(fromaddr='peahive@gmail.com', recipients=['kwarodom@vt.edu', 'peahive@gmail.com', 'smarthome.pea@gmail.com'], username='peahive@gmail.com', password='nbumnmwtqbeqcocc',
                    subject='HiVE Report', text=sendText, mailServer='smtp.gmail.com:587')

if __name__ == "__main__": main()
