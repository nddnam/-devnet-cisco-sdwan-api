import requests
import json
import os
import sys
import csv
import random
from datetime import datetime
import socket
#optional
import urllib3
urllib3.disable_warnings()

def TCP_CONNECTION_CHECK(vmanage_host, vmanage_port=443):
    timeout_seconds=2
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout_seconds)
    result = sock.connect_ex((vmanage_host,int(vmanage_port)))
    if result == 0:
        return True
    else:
        return False
    sock.close()

def CSV_EXPORT(list_of_dict, file_name='output_'+''.join((random.choice('random_filename_if_blank') for i in range(20)))):
#Write to csv
    if (file_name.split("."))[-1] == 'csv':
        csv_filename = file_name
    else:
        csv_filename = f"{file_name}.csv"

    csv_header = [key for key in list_of_dict[0]]
    with open(csv_filename, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames = csv_header)
        writer.writeheader()
        writer.writerows(list_of_dict)
    csvfile.close()
    return os.path.join(os.getcwd(), csv_filename)

class VMANAGE_AUTHENTICATION:
#Authentication with vManage and return the header
    def __init__(self, vmanage_host, vmanage_port, vmanage_username, vmanage_password):
        self.vmanage_host = vmanage_host
        self.vmanage_port = vmanage_port
        self.vmanage_username = vmanage_username
        self.vmanage_password = vmanage_password
        self.base_url = f"https://{self.vmanage_host}:{self.vmanage_port}"

    def get_header(self):
    #get jsessionid
        api = "/j_security_check"
        #base_url = "https://%s:%s"%(self.vmanage_host, self.vmanage_port)
        url = self.base_url + api
        payload = {'j_username' : self.vmanage_username, 'j_password' : self.vmanage_password}
        response = requests.post(url=url, data=payload, verify=False)
        try:
            cookies = response.headers["Set-Cookie"]
            jsessionid = cookies.split(";")[0]
            #return(jsessionid[0])
        except:
            print("No valid JSESSION ID returned\n")
            exit()
    #get token
        headers = {'Cookie': jsessionid}
        api = "/dataservice/client/token"
        url = self.base_url + api   
        response = requests.get(url=url, headers=headers, verify=False)
        if response.status_code == 200:
            token = response.text
        else:
            print(f"Failed to get Token: {response.text}")
    #get header
        header = {'Content-Type': "application/json",'Cookie': jsessionid, 'X-XSRF-TOKEN': token}
    #combine header + baseurl
        return {'header': header, 'base_url': self.base_url}

    def get_baseurl(self):
        return self.base_url

class DEVICES:
#Cisco SD-WAN Fabric Device Adminitration
    def __init__(self, header):
        self.header = header['header']
        self.base_url = header['base_url']

    def get_device_list(self):
    #get all device list
        api = "/dataservice/device"
        url = self.base_url + api
        response = requests.get(url=url, headers=self.header, verify=False)

        if response.status_code == 200:
            items = response.json()['data']
        else:
            print(f"Failed >> {response.status_code} >> {response.text}")
            exit()
    
        #categorize neccesary information
        neccessary_info = ['system-ip', 'host-name', 'site-id', 'status', 'version']
        output_data = []
        for item in items:
            data = {key: item[key] for key in neccessary_info}
            output_data.append(data)

        return(output_data)

    def control_check(self, system_ip):
    #get all control connections status from given device
        api = "/dataservice/device/control/connections"
        url = f"{self.base_url}{api}?deviceId={system_ip}"
        response = requests.get(url=url, headers=self.header, verify=False)

        if response.status_code == 200:
            items = response.json()['data']
        else:
            print(f"Failed >> {response.status_code} >> {response.text}")
            exit()

        neccessary_info = ['peer-type', 'system-ip', 'local-color', 'remote-color', 'uptime', 'site-id', 'protocol', 'state']
        output_data = []
        for item in items:
            data = {key: item[key] for key in neccessary_info}
            output_data.append(data)

        return output_data

class TEMPLATE:
#Cisco SD-WAN CLI Template Administration
    def __init__(self, header):
        self.header = header['header']
        self.base_url = header['base_url']

    def check_attached(self, template_name):
    #Check if the given Template is being used by any devices.
        api = "/dataservice/template/device"
        url = self.base_url + api
        response = requests.get(url=url, headers=self.header, verify=False)

        if response.status_code == 200:
            items = response.json()['data']
        else:
            print(f"Failed >> {response.status_code} >> {response.text}")
            exit()
        #filter by given Template Name
        #for item in items:
        #    if item['templateName'] == template_name:
        #        template_attached_check = item['devicesAttached']
        #        break
        template_attached_check = [item['devicesAttached'] for item in items if item['templateName'] == template_name]
        if template_attached_check[0] != 0:
            return "Template In Used"
        else:
            return "Template Not In Used"

    def get_device_template(self):
    #List all of non-Default Device Templates
        api = "/dataservice/template/device"
        url = self.base_url + api
        response = requests.get(url=url, headers=self.header, verify=False)

        if response.status_code == 200:
            items = response.json()['data']
        else:
            print(f"Failed >> {response.status_code} >> {response.text}")
            exit()
        #categorize neccesary information
        neccessary_info = ['deviceType', 'templateName', 'templateClass', 'devicesAttached', 'lastUpdatedOn']    
        output_data = []
        for item in items:
            data = {}
            if item['factoryDefault'] == False:
                for key in neccessary_info:
                    data[key] = item[key]
                #convert date time format
                data['lastUpdatedOn'] = datetime.fromtimestamp(int(data['lastUpdatedOn']) / 1e3)
                output_data.append(data)
            #data = {key: item[key] for key in neccessary_info if item['factoryDefault'] == False}
            #output_data.append(data)

        return output_data
            
if __name__ == "__main__":
    vmanage_host = os.environ['vmanage_host']
    vmanage_port = os.environ['vmanage_port']
    vmanage_username = os.environ['vmanage_username']
    vmanage_password = os.environ['vmanage_password']

    if (vmanage_host == None) or (vmanage_port == None) or (vmanage_username == None) or (vmanage_password == None):
        print(
            "Please export the envirionment variables which content the credential information:"
            "\[Linux\]"
            " export vmanage_host='your vmanage host'"
            " export vmanage_port='443'"
            " export vmanage_username='your username'"
            " export vmanage_password='your password'"
            "\[Windows\]"
            "[System.Environment]::SetEnvironmentVariable('vmanage_host','your vmanage host')"
            "[System.Environment]::SetEnvironmentVariable('vmanage_port','443')"
            "[System.Environment]::SetEnvironmentVariable('vmanage_username','your username')"
            "[System.Environment]::SetEnvironmentVariable('vmanage_password','your password')"
        )
        exit()
    
    #AUTHENTICATION &  GETTING header
    Auth = VMANAGE_AUTHENTICATION(vmanage_host,vmanage_port,vmanage_username,vmanage_password)
    header = Auth.get_header()

    #GET START USING

    #dev = DEVICES(header)
    #result = CSV_EXPORT(dev.control_check('10.10.10.12'), 'control_check.csv')
    #print(result)
    #result = CSV_EXPORT(dev.get_device_list(), 'device_list.csv')
    #print(result)

    template = TEMPLATE(header)
    #template_name1 = 'C8000v-DUAL-WAN'
    #template_name2 = '[Custom]_cEdge-12'

    #print(template.check_attached(template_name1))
    #print(template.device_template_list())
    result = CSV_EXPORT(template.get_device_template(), 'device_template_list.csv')





