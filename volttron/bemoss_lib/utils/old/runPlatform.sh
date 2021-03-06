#!/bin/bash

#Copyright (c) 2016, Virginia Tech
#All rights reserved.
#
#Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
#disclaimer.
#2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
#disclaimer in the documentation and/or other materials provided with the distribution.
#
#THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
#INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
#SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
#WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#The views and conclusions contained in the software and documentation are those of the authors and should not be
#interpreted as representing official policies, either expressed or implied, of the FreeBSD Project.
#
#This material was prepared as an account of work sponsored by an agency of the United States Government. Neither the
#United States Government nor the United States Department of Energy, nor Virginia Tech, nor any of their employees,
#nor any jurisdiction or organization that has cooperated in the development of these materials, makes any warranty,
#express or implied, or assumes any legal liability or responsibility for the accuracy, completeness, or usefulness or
#any information, apparatus, product, software, or process disclosed, or represents that its use would not infringe
#privately owned rights.
#
#Reference herein to any specific commercial product, process, or service by trade name, trademark, manufacturer, or
#otherwise does not necessarily constitute or imply its endorsement, recommendation, favoring by the United States
#Government or any agency thereof, or Virginia Tech - Advanced Research Institute. The views and opinions of authors
#expressed herein do not necessarily state or reflect those of the United States Government or any agency thereof.
#
#VIRGINIA TECH – ADVANCED RESEARCH INSTITUTE
#under Contract DE-EE0006352
#
#__author__ = "BEMOSS Team"
#__credits__ = ""
#__version__ = "2.0"
#__maintainer__ = "BEMOSS Team"
#__email__ = "aribemoss@gmail.com"
#__website__ = "www.bemoss.org"
#__created__ = "2014-09-12 12:04:50"
#__lastUpdated__ = "2016-03-14 11:23:33"



cd ~/workspace/bemoss_os/
. env/bin/activate
volttron -vv 2>&1 | tee ~/workspace/bemoss_os/log/volttron.log &
echo $i > ~/workspace/bemoss_os/.temp/BEMOSS.pid

#volttron-ctl start --tag devicediscoveryagent
#sleep 2
volttron-ctl start --tag applauncheragent
sleep 2
volttron-ctl start --tag approvalhelperagent
sleep 2

#volttron-ctl start --tag multibuildingagent
#sleep 2
#volttron-ctl start --tag networkagent
#sleep 2
volttron-ctl start --tag gridappagent
sleep 2

#volttron-ctl start --tag NETPIEButton
#sleep 2
#volttron-ctl start --tag DemandResponseAgent
#sleep 2

volttron-ctl start --tag gridappagent
sleep 2
volttron-ctl start --tag powermeteragent
sleep 2
volttron-ctl start --tag modeappagent
sleep 2
volttron-ctl start --tag devicestatusappagent
sleep 2
#volttron-ctl start --tag ACAPP
#sleep 2
#volttron-ctl start --tag LightingApp
#sleep 2
#volttron-ctl start --tag PlugloadApp
#sleep 2
#volttron-ctl start --tag evappagent
#sleep 2
volttron-ctl start --tag EnergyBillAppAgent
sleep 2
volttron-ctl start --tag GridAppAgent
sleep 2
volttron-ctl start --tag 1WE221445K1200132  #weatheragent
sleep 2

#volttron-ctl start --tag LivingroomAir1
#sleep 2
#volttron-ctl start --tag LivingroomAir2
#sleep 2
#volttron-ctl start --tag BedroomAir
#sleep 2
#volttron-ctl start --tag 1FR221445K1200111
#sleep 2
volttron-ctl start --tag 1MS221445K1200132
sleep 2
volttron-ctl start --tag 1LG221445K1200137

sleep 2
volttron-ctl start --tag Daikinagent
sleep 2
volttron-ctl start --tag Netatmoagent
#sleep 2
#volttron-ctl start --tag PVInverterAgent
sleep 2
volttron-ctl start --tag KitchenLight
sleep 2
volttron-ctl start --tag LivingLight
sleep 2
volttron-ctl start --tag PEASmartHomeHue
sleep 2
volttron-ctl start --tag PEASmartHomeWemo
sleep 2
volttron-ctl start --tag HomeSceneApp

sleep 2
volttron-ctl start --tag doorlock
#sleep 2

sleep 2
volttron-ctl start --tag curtain

sleep 2
volttron-ctl start --tag openclose
#volttron-ctl start --tag CreativePowerAgent

sleep 2
volttron-ctl start --tag openclosedoor

sleep 2
volttron-ctl start --tag EnergyReportSchedulerApp

volttron-ctl status
deactivate
sudo chmod 777 ~/.volttron/run/publish
sudo chmod 777 ~/.volttron/run/subscribe
