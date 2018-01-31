#!/usr/bin/env python3
from lxml import etree
from lxml import objectify
import requests
import base64
from . import device
from . import exceptions

class EagleLocalHTTP():
   #Initializes this library and prepares for communication with the EAGLE-200
    def __init__(self, cloudid, installcode, hostname=None, debug=False):
        if hostname:
            self.api_url = "http://%s/cgi-bin/post_manager" % (hostname)
        else:
            self.api_url = "http://eagle-%s.local/cgi-bin/post_manager" % (cloudid)
        
        self.debug=debug
        self.construct_headers(cloudid,installcode)
        self.devices = None
        self.devices = self.query_device_list()

    #Prepares the authentication and content type headers that are sent in all API requests
    def construct_headers(self, cloudid, installcode):
        auth = base64.b64encode(("%s:%s" % (cloudid, installcode)).encode('ascii'))
        self.headers = {'Authorization': ("Basic %s" % auth.decode('ascii')), 'Content-Type': 'text/xml'}
        if self.debug:
            print("Request Headers:")
            print(self.headers)
        return self.headers;

    #Prepares the base XML element tree for an API command
    def construct_root(self, name, hardwareaddress=None):
        command_base = etree.Element('Command')
        command_name = etree.Element('Name')
        command_name.text = name
        command_base.append(command_name)
        if(hardwareaddress):
            devdetails = etree.Element('DeviceDetails')
            hwaddr = etree.Element('HardwareAddress')
            hwaddr.text = str(hardwareaddress)
            devdetails.append(hwaddr)
            command_base.append(devdetails)
        return command_base

    #Returns an error string if a response is an error response
    def check_error(self, resp):
        if(hasattr(resp,'Error')):
            return str(resp.__dict__)
        else:
            return None

    #Sends a request to the EAGLE-200 device and returns the response
    def send_request(self, data):
        req = requests.post(self.api_url,data=data,headers=self.headers)
        if(self.debug):
                print(self.api_url)
                print(data)
                print(req.text)
        return req

    def query_device_list(self, refresh=False):
        if(self.devices and (not refresh)):
            return self.devices

        self.devices=dict()
        x_root = self.construct_root('device_list')
        
        #Send it and parse the result
        response = self.send_request(etree.tostring(x_root, pretty_print=self.debug))
        responseobj = objectify.fromstring(response.text)
        
        #error checks
        err = self.check_error(responseobj)
        if(err):
            raise exceptions.EAGLEError(err)

        #Build the devices list
        for dev in responseobj.iterchildren():
            self.devices[dev.HardwareAddress]=device.Device(self,dev.__dict__)
        
        return self.devices

if __name__ == "__main__":
        eagle = EagleLocalHTTP('YOUR_CLOUD_ID', 'YOUR_INSTALL_CODE')
        for mac, device in eagle.query_device_list().items():
            print("---FOUND DEVICE %s---" % (mac))
            device_vars = device.query_device_details()
            print(device.query_device_values(device_vars,strip_units=False))
