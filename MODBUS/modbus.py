import threading
import base64
import json
import paho.mqtt.client as mqtt
import sys
import os
import pycurl
import requests
import subprocess
import logging
import time
import datetime

from threading import Thread, Lock
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.version import version
from pymodbus.server.sync import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSparseDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.transaction import ModbusRtuFramer, ModbusBinaryFramer

from pyModbusTCP.server import ModbusServer, DataBank


#################################################GLOBAL VARIABLES

APIjwt = ''
devEUItab=[]
devADRtab=[]

##################################################LOGGING
logging.basicConfig(filename='modbus.log',level=logging.DEBUG,\
      format='%(asctime)s -- %(levelname)s -- %(message)s')


######################################################################################################
#Function run_server: Initialize and start modbus slaves server--------------------------------------#
######################################################################################################
def run_server():

    server = ModbusServer(host="", port=502, no_block=True)
    try:
        server.start()
        logging.info("Modbus server started")
        #Initialize 500 registers from address 0
        DataBank.set_words(0,[0x0000]*500)
        while True  :
            continue

    #Stop server if interrupted
    except:
        server.close()

######################################################################################################
#Function on_connect: connect to gateway mqtt broker and subscribe to Chirpstack backend-------------#
######################################################################################################

def on_connect(client, userdata, flags, rc):

    #print("----Connected to gateway MQTT broker - Result code: " + str(rc) + "----")
    logging.info('Connected to gateway MQTT broker - Result code: %s', str(rc))
    #Topic used by Chirpstack
    client.subscribe("application/#")


######################################################################################################
#Handler on_message:  Process gateway uplink messages and place payload in MODBUS table (slave)------#
######################################################################################################

def on_message(client, userdata, message):

    global gatewayID

    newDev = 1
    i = 0
    date_array = [0,0,0,0,0,0,0]

    modbus_client = ModbusClient(host="localhost", port=502)

    #Get the JSON message as a string
    jsonStr = str(message.payload.decode('utf-8'))
  
    #Get the topic
    gatewayTopic = message.topic
       
    #Check if message is uplink
    if((gatewayTopic.find("event/up") != -1)):
        
        #get devEUI
        devEUI_str = gatewayTopic.split('/', 6)[3]
        #encode devEUI to hex
        devEUI_hex = int(devEUI_str, 16)

        #Check if message devEUI has a matching address in MODBUS table
        for dev in devEUItab:
            #print ("device tab EUI: " + dev)
            #print ("device message EUI : " + devEUI_str)
            if(dev == devEUI_str):
                #print("Uplink received - devEUI : " + devEUItab[i]  + " - devADR : " + str(devADRtab[i]))
                logging.info('Uplink received - devEUI : %s - devADR : %s', devEUItab[i], str(devADRtab[i]))
                newDev=0
                break
            i=i+1

	#If there is no match in MODBUS table
        if(newDev == 1):
            #Add new device to device file
            #print("Adding new device in list :" + devEUI_str)
            logging.info('New device %s added in list', devEUI_str)
            devices = open("/home/ogate/MODBUS/modbus.dev", "a")
            devices.write(devEUI_str + ',,\n')
            devices.close()
            #And update MODBUS table once device added to list
            makeTab()

        #Parse the json to get loRa uplink message payload
        jsonDat = json.loads(jsonStr)
        #Encode Chirpstack default base64 payload to hexadecimal
        loraPayload_bytes = base64.b64decode(jsonDat['data'])
        #Get payload byte number
        bytesNumber = len(loraPayload_bytes)

        #Create array of 0 bytes to fill the 32 bytes gap
        zeroArray = bytearray(32-bytesNumber) 

        #Convert to hex
        #loraPayload_hex = int.from_bytes(loraPayload_bytes, "big")

        #Get timestamp with format below
        #[----byte1][----byte2]...
        #[--Century][-----Year]...
        now_tm = datetime.datetime.now()
        date_array[0]=int(now_tm.year/100)#century
        date_array[1]=now_tm.year % 100
        date_array[2]=now_tm.month
        date_array[3]=now_tm.day
        date_array[4]=now_tm.hour
        date_array[5]=now_tm.minute
        date_array[6]=now_tm.second

        #Prepare the content to be stored in MODBUS table

        #Format below is set for MODBUS table register (10 bytes per device) :
        #[byte #1-2][byte #3-4][byte #5-6][byte #7-8][byte #9-10][byte #11-12][byte #13-14][byte #15-16][byte #13-14][byte #15-16][byte #17-18][byte #19-20][byte #21-22][byte #23-24][byte #25-26][byte #27-28]
        #[------------------------------------devEUI][----------------------------------------Timestamp][--------------------------------------------------------------------------------------------------------------------        

	#Use builder to format MODBUS table content
        builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Big)
	#First 4 bytes are used to store devEUI
        builder.add_64bit_uint(devEUI_hex)
	#Then 8 bytes are used to store timestamp
        builder.add_16bit_uint(date_array[0])
        builder.add_8bit_uint(date_array[1])
        builder.add_8bit_uint(date_array[2])
        builder.add_8bit_uint(date_array[3])
        builder.add_8bit_uint(date_array[4])
        builder.add_8bit_uint(date_array[5])
        builder.add_8bit_uint(date_array[6])


	#Add the zero bytes to fill the 32 bytes field
        for id1 in range(0, len(zeroArray)):
            builder.add_8bit_uint(zeroArray[id1])

        #Add the payload bytes
        for id2 in range(0, bytesNumber):
            builder.add_8bit_uint(loraPayload_bytes[id2])

        content = builder.build()

        #Write to corresponding register
        result  = modbus_client.write_registers(devADRtab[i], content, skip_encode=True)

        if result:
            #print('Uplink stored in register address: ' + str(devADRtab[i]))
            logging.info('Uplink stored in register address: %s', str(devADRtab[i]))
        else:
            #print('Problem storing uplink message in register')
            logging.error('Problem storing uplink message in register')

        #Get devices file content
        devices = open("/home/ogate/MODBUS/modbus.dev", "r")
        devicesLines = devices.readlines()
        devices.close()

        #Update the device file with new content and new date
        devices = open("/home/ogate/MODBUS/modbus.dev", "w")
        payloadStr = loraPayload_bytes.hex()
        payloadLen = len(payloadStr)

        #Prepare timestamp string
        date_str="00"
        for k in range(0,7):
            if(len(hex(date_array[k])) <= 3):
                date_str = date_str + '0'
            date_str = date_str + hex(date_array[k])[2:]
        
        print("Date string : " + date_str)

        #Fill the payload string with 0 if necessary (to get 16 bits)
        for i in range(payloadLen, 64):
            payloadStr = '0' + payloadStr

        for line in devicesLines:
            if(line.split(',')[0] == devEUI_str):
                devices.write(devEUI_str + ',' + devEUI_str + date_str + payloadStr + ',' + str(now_tm) + '\n')
            else:
                devices.write(line)
                

        devices.close()
        

######################################################################################################
#Function subscribing: check continusously messages from gateway mqtt broker-------------------------#
######################################################################################################

def subscribing():

    #Define callback function when message is received on gateway mqtt broker
    mqtt_client.on_message = on_message
    mqtt_client.loop_forever()


######################################################################################################
#Function chirpstackInit: get Chirpstack token-------------------------------------------------------#
######################################################################################################

def chirpstackInit():

    global APIjwt
    #print("----Start of chirpstack Configuration----")

    #Prepare the request
    reqURL = "http://127.0.0.1:8080/api/internal/login"
    reqPayload = '{"password": "admin", "email": "admin"}'
    reqHeaders = {'Content-Type': 'application/json'}

    #Send request
    reqOutput = requests.post('http://localhost:8080/api/internal/login',headers=reqHeaders, data=reqPayload)

    #Print Token to used to access chirpstack API
    APIjwt = 'Bearer ' + reqOutput.text[8:-2]
    #print("Got Chirpstack API token : " + APIjwt)
    logging.info('Getting Chirpstack API key : %s', APIjwt)

######################################################################################################
#Function chirpstackAdd: add a device to Chirpstack--------------------------------------------------#
######################################################################################################

def chirpstackAdd(devEUI,devName,devDesc,appKey):

    global APIjwt
    print("----Adding a device to Chirpstack----")

    #Prepare the request to add device
    
    reqPayload = "{\"device\": {\"applicationID\": \"1\", \"description\": \"" + devDesc + "\", \"devEUI\":\"" + devEUI +"\", \"deviceProfileID\": \"153a8c20-63f1-4633-af31-61075cee5494\", \"isDisabled\": false, \"name\": \"" + devName + "\", \"referenceAltitude\": 0, \"skipFCntCheck\": false, \"tags\": {}, \"variables\": {}}}"
    print('Payload:' + reqPayload)
    reqHeaders = {'Content-Type': 'application/json', 'Grpc-Metadata-Authorization' : APIjwt}

    #Send request
    reqOutput = requests.post('http://localhost:8080/api/devices',headers=reqHeaders, data=reqPayload)

    #Print status code from API
    print("Adding device - Chirpstack status: " + str(reqOutput.status_code))

    #Prepare the request to change the Application key
    #devEUI=devEUI.lower()
    reqPayload = "{\"deviceKeys\":{\"appKey\":\"" + appKey + "\", \"devEUI\": \""+ devEUI +"\", \"genAppKey\":\"00000000000000000000000000000000\", \"nwkKey\":\""+ appKey +"\"}}"
    print('Payload:' + reqPayload)
    reqHeaders = {'Content-Type': 'application/json', 'Grpc-Metadata-Authorization' : APIjwt}
    reqURL = 'http://localhost:8080/api/devices/'+ devEUI +'/keys'
    print('url:' + reqURL)
    #Send request
    reqOutput = requests.post(reqURL,headers=reqHeaders, data=reqPayload)

    #Print status code from API
    print("Changing keys - Chirpstack status: " + str(reqOutput.status_code))
    #print("Adding Chirpstack device message: " + str(reqOutput.text))

######################################################################################################
#Function chirpstackDelete: delete a device to Chirpstack--------------------------------------------#
######################################################################################################

def chirpstackDelete(devEUI):

    global APIjwt
    print("----Deleting a device from Chirpstack----")

    #Prepare the request to remove device
    
    #reqPayload = "{\"device\": {\"applicationID\": \"1\", \"description\": \"" + devDesc + "\", \"devEUI\":\"" + devEUI +"\", \"deviceProfileID\": \"153a8c20-63f1-4633-af31-61075cee5494\", \"isDisabled\"$
    #print('Payload:' + reqPayload)
    reqHeaders = {'Content-Type': 'application/json', 'Grpc-Metadata-Authorization' : APIjwt}
    reqURL = 'http://localhost:8080/api/devices/'+ devEUI +'/keys'

    #Send request
    reqOutput = requests.delete(reqURL,headers=reqHeaders)

    #Print status code from API
    print("Deleting device - Chirpstack status: " + str(reqOutput.status_code))


######################################################################################################
#Function makeTab: prepare MODBUS table according to device file-------------------------------------#
######################################################################################################

def makeTab():

    global devEUItab
    global devADRtab
    i=0
    j=0
    #Empty previous tab variables
    devEUItab=[]
    devADRtab=[]

    #Format below is set to fill those tabs
    #[devEUI#1][devEUI#2][devEUI#3][devEUI#4]....
    #[-----100][-----122][-----144][-----166]....

    #open devEUI file
    devs = open("/home/ogate/MODBUS/modbus.dev", "r")
    devsLines = devs.readlines()
    devs.close()

    #print('Updating device list :')
    logging.info('Updating device list :')

    for line in devsLines :
        if (line != "\n"):
            #Parse the line and get devEUI
            devEUI = line.split(',')[0]
            #remove the last \n
            #devEUI=line[:-1]

            #Add devEUI to table 
            devEUItab.append(devEUI)
            #Add the address indicator to table
            devADRtab.append(j)
            #print("----Device N°" + str(i) + " : " + str(devEUItab[i]) + " -> " + str(devADRtab[i]) + "----")
            logging.info('Device N°%s - devEUI %s - devADR %s ', str(i),str(devEUItab[i]),str(devADRtab[i]))
            i=i+1
            #Increment modbus register address : 1 device = 25 registers (1 register = 2 bytes i.e. 0xFFFF) 
            j=j+25

################################################################################################################################################Start of program

#Clear previous logs
open("/home/ogate/MODBUS/modbus.log", 'w').close()

#Get gateway Id
startID = subprocess.check_output("ip link show eth0 | awk '/ether/ {print $2}' | awk -F\: '{print $1$2$3}'", shell = True)
middleID = "fffe"
endID = subprocess.check_output("ip link show eth0 | awk '/ether/ {print $2}' | awk -F\: '{print $4$5$6}'",shell = True)
gatewayID = startID.decode("utf-8")[:-1]  + middleID + endID.decode("utf-8")[:-1] 
#print("----Gateway ID : " + gatewayID + "----")

#Make MODBUS table from device list file
makeTab()

#Restart mbserverd MODBUS server (slave)
#os.system("sudo killall mbserverd")
#time.sleep(1)
#os.system("sudo mbserverd")
#run_server()

#MQTT definition
broker='localhost'
port=1883
mqtt_client = mqtt.Client()
mqtt_client.connect(broker, port)
mqtt_client.on_connect = on_connect
time.sleep(1)

#MODBUS definition
# TCP auto connect on first modbus request
#modbus_client = ModbusClient(host="127.0.0.1", port=502, unit_id=1, auto_open=True)

#Module init with functions (alternative)
#c = ModbusClient()
#c.host("localhost")
#c.port(502)
#c.unit_id(1)
# managing TCP sessions with call to c.open()/c.close()
#c.open()


##############################################################################################################################################Thread list
#1time threads
#iniMC=threading.Thread(target=run_client)
iniC=threading.Thread(target=chirpstackInit)
sub=threading.Thread(target=subscribing)

#forever threads
iniMS=threading.Thread(target=run_server)

############################################################################################################################################Threads starting

#Start MODBUS server
iniMS.start()
#iniMC.start()


#Start chirpstack API communication
iniC.start()
iniC.join()

#Start gateway broker subscrition
sub.start()
