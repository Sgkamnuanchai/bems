from azure.servicebus import ServiceBusService, Message, Topic, Rule, DEFAULT_RULE_NAME
import time

'''
The following code creates a ServiceBusService object.
 Replace mynamespace, sharedaccesskeyname, and sharedaccesskey
 with your namespace, shared access signature (SAS) key name, and value.
 The values for the SAS key name and value can be found in the Azure portal
connection information, or in the Visual Studio Properties pane
when selecting the Service Bus namespace in Server Explorer
(as shown in the previous section).
'''
# service_namespace='homespace',


bus_service = ServiceBusService(
    service_namespace='hive03',
    shared_access_key_name='RootManageSharedAccessKey',
    shared_access_key_value='Ijidj1JCQ5unGXTpuCPahIZQl5KVhswqlZdND+AS8Eg=')

'''
create_queue also supports additional options,
which enable you to override default queue settings such as message time
to live (TTL) or maximum queue size. The following example sets t
he maximum queue size to 5 GB, and the TTL value to 1 minute
'''

bus_service.create_subscription('home03', 'AllMessages')
while True:
    msg = bus_service.receive_subscription_message('home03', 'AllMessages', peek_lock=False)
    print("message received!!!")
    print(msg.body)
    time.sleep(2)
