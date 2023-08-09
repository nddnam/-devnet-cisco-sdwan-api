import ciscosdwanapi as sapi
import os

vmanage_host = os.environ['vmanage_host']
vmanage_port = os.environ['vmanage_port']
vmanage_username = os.environ['vmanage_username']
vmanage_password = os.environ['vmanage_password']

#VMANAGE AUTHENTICATION
#CHECK CONNECTION
status = sapi.TCP_CONNECTION_CHECK(vmanage_host,vmanage_port)
if status == True:
    auth = sapi.VMANAGE_AUTHENTICATION(vmanage_host,vmanage_port,vmanage_username,vmanage_password)
    header = auth.get_header()
else:
    print(f"Connection Error to Host {vmanage_host} port {vmanage_port}")
    exit()

#DEVICE ADMIN
#device = sapi.DEVICES(header)
#
##DEVICE LIST
#dev_list = device.device_list()
#sapi.CSV_EXPORT(dev_list, "device-list.csv")
#
##CONTROL CONNECTION CHECK
#system_ip = '10.10.10.12'
#control_connections = device.control_check(system_ip)
#sapi.CSV_EXPORT(control_connections, "10.10.10.12-control-check.csv")

#TEMPLATE ADMIN
template = sapi.TEMPLATE(header)
#LIST ALL DEVICE TEMPLATES
sapi.CSV_EXPORT(template.get_device_template(),"device_template_list.csv")
sapi.TCP_CONNECTION_CHECK(vmanage_host,vmanage_port)
