import threading
import base64
import json
from threading import Thread, Lock
import time
import paho.mqtt.client as mqtt
import sys
import serial
import RPi.GPIO as GPIO
import os
import pycurl
import requests
import subprocess
import logging
from datetime import datetime

#################################################MACCROS

#SIM7070 power pin is GPIO4 on Raspberry Pi
PWR_SIM7070 = 4

#################################################GLOBAL VARIABLES
ATbuffer = []
ssl = 0
APIjwt = '' 
rssi=""
snr=""
LTEMstate=""


################################################LOGGING
logging.basicConfig(filename='ltem.log',level=logging.DEBUG,\
      format='%(asctime)s -- %(levelname)s -- %(message)s')

######################################################################################################
#Function serialProcess: read SIM7070 UART data and forward downlink or configuration to gateway-----#
######################################################################################################
def serialProcess():

    while True:
        
        bytes = ser.inWaiting()
        if bytes > 0:
            
            serialMutex.acquire()
            inputData = ser.readline()
            inputString = str(inputData, 'utf-8', 'ignore')
            
            #1. Check for downlink message in uart
            if((inputString.find("down") != -1)):
                
                #print("+SPUB : " + inputString)
                #Isolate payload
                inputJSON = inputString.split(',', 1)[1]
                #Remove the " "
                inputJSON = inputJSON[1:-3]
                print('downlink JSON :', inputJSON)
                #Parse the json
                jsonDat = json.loads(inputJSON)
                #Isolate devEUI
                devEUI = jsonDat['devEUI']
                
                gatewayTopic = "application/1/device/" + devEUI + "/command/down"
                #print("+SPUB Topic :" + gatewayTopic)
                #print("+SPUB Payload :" + inputPayload)
                #print("+SPUB devEUI :" + devEUI)
                logging.info('Downlink - devEUI : %s - Topic : %s - Payload : %s', devEUI, gatewayTopic, inputJSON)

                client.publish(gatewayTopic,inputJSON)
            
            #2. check for configuration message in uart : hotspot
            elif((inputString.find("configuration/hotspot") != -1)):
                #print("+SPUB : " + inputString)
                #Isolate payload
                inputPayload = inputString.split(',', 1)[1]
                #print("+SPUB Payload :" + inputPayload)		

                if(inputPayload.find("1") != -1):
                    #Turn hotspot on
                    #print("----Turning Hotspot ON----")
                    logging.info('Server publish : hotspot ON')
                    os.system("systemctl enable hostapd")
                    os.system("systemctl start hostapd")

                elif(inputPayload.find("0") != -1):
                    #turn hotspot off
                    #print("----Turning Hotspot OFF----")
                    logging.info('Server publish : hotspot OFF')
                    os.system("systemctl disable hostapd")
                    os.system("systemctl stop hostapd")

            #3. check for configuration message in uart : add device
            elif((inputString.find("configuration/add") != -1)):
                #print("+SPUB : " + inputString)
                logging.info('Server publish : adding device')

                #Isolate payload
                inputPayload = inputString.split(',', 1)[1]
                inputPayload = inputPayload[1:-3]
                #print("+SPUB Payload :" + inputPayload)
                
                #Parse the json
                jsonDat = json.loads(inputPayload)

                #Add the device
                chirpstackAdd(jsonDat['devEUI'], jsonDat['name'], jsonDat['description'], jsonDat['appKey'])


            #4. check for configuration message in uart : delete device
            elif((inputString.find("configuration/delete") != -1)):
                #print("+SPUB : " + inputString)
                logging.info('Server publish : deleting device')

                #Isolate payload
                inputPayload = inputString.split(',', 1)[1]
                inputPayload = inputPayload[1:-3]
                #print("+SPUB Payload :" + inputPayload)

                #Parse the json
                jsonDat = json.loads(inputPayload)

                #Add the device
                chirpstackDelete(jsonDat['devEUI'])

            #5. check for configuration message in uart : reboot gateway
            elif((inputString.find("configuration/reboot") != -1)):
                #print("+SPUB : " + inputString)
                logging.info('Server publish : rebooting gateway')
                #Isolate payload
                inputPayload = inputString.split(',', 1)[1]
                #print("+SPUB Payload :" + inputPayload)         

                if(inputPayload.find("1") != -1):
                    #Reboot gateway
                    #print("----Rebooting gateway----")
                    os.system("sudo reboot")

            #6. check for no CARRIER bug
            elif((inputString.find("NO CARRIER") != -1)):
                flushAT()
                sendAT("AT\r")
                logging.warning('Server publish : carrier problem')

            #else:
            #    print("UART : " + inputString)

            serialMutex.release()

######################################################################################################
#Function timeFrame: check LTEM network, connection to MQTT server, GNSS signal----------------------#
######################################################################################################
def timeFrame():
    
    global ATbuffer
    global rssi
    global snr
    global LTEMstate
    global MQTTstate
    global gatewayID
    global confPubHeader

    while True:

        #Check every 5 minutes
        #time.sleep(300)

        mqtt = 0
        ltem = 0
        brkInd = 0
        lat = "0"
        long = "0"
        alt = "0"

        #Clean log file
        logClean()

        serialMutex.acquire()

        time.sleep(2)

        #print("----Checking gateway details----")
        logging.info('Checking gateway details')

        flushAT()

        #Edit data file
        file = open("/home/ogate/LTEM/ltem.dat", "w")

        try :

            #Get the signal RSSI and SNR

            sendAT('AT+CPSI?\r')
            time.sleep(0.2)

            LTEMstate = ATbuffer[1].split(',', 13)[1]
            rssi = ATbuffer[1].split(',', 13)[12]
            snr = ATbuffer[1].split(',', 13)[13]

            #remove last characters of the string
            snr = snr[:-2]
            #print('snr--' + snr + '--')
            time.sleep(0.2)
            
            #Check connection to MQTT server
            sendAT('AT+SMSTATE?\r')
            time.sleep(0.2)

            MQTTstate = ATbuffer[1]
            
            #Get GNSS signal
            sendAT('AT+SGNSCMD=1,0\r')
            time.sleep(0.2)
        
            while brkInd < 1000000:
            
                try : 
                    
                    dataRaw = ser.readline()
                    dataStr = str(dataRaw, 'utf-8', 'ignore')
                    if(dataStr.find("+SGNSCMD:") != -1):
                        
                        #Isolate the time
                        timeStr=dataStr.split(',', 11)[1]
                        #print('Got time from GPS : ' + timeStr)
                        #Isolate locate
                        lat=dataStr.split(',', 11)[2]
                        long=dataStr.split(',', 11)[3]
                        alt=dataStr.split(',', 11)[6]
                        #print('Got location from GPS : ' + lat + "," + long + "," + alt)
                        logging.info('Gateway location : %s,%s,%s',lat,long,alt)
                        #Update raspberry Pi time
                        timeCmd = "sudo date -s \"" + timeStr + "\""
                        os.system(timeCmd)
                        break

                    elif(dataStr.find("+SGNSERR:") != -1):
                        #print('Unable to get GNSS signal')
                        logging.warning('Unable to get GNSS signal')
                        break 
                except :
                    dataStr =  ''

                brkInd = brkInd + 1
            
            #Determine network state
            if(LTEMstate.find("Online") != -1):
                #print("Gateway is connected in LTEM")
                logging.info('Gateway connected to LTE-M network')
                file.write("LTEM=1\n")
                #print("LTE-M RSSI : " + rssi + "dB")
                logging.info('Gateway LTE-M RSSI : %s dB', rssi)
                file.write("RSSI=" + rssi + "\n")

                #print("LTE-M SNR : " + snr + "dB")
                logging.info('Gateway LTE-M SNR : %s dB', snr)
                file.write("SNR=" + snr + "\n")

            else:
                #print("Connection to LTEM has been lost")
                logging.warning('Gateway disconnected from LTE-M network')
                file.write("LTEM=0\n")
                file.write("RSSI=-db\n")
                file.write("SNR=-dB\n")

            if(MQTTstate.find("+SMSTATE: 1") != -1):
                #print("Gateway is connected to remote MQTT broker")
                logging.info('Gateway connected to MQTT remote broker')
                file.write("MQTT=1\n")
                #get time and date to timestamp the message
                timeStamp = datetime.now()
                timeStamp = timeStamp.strftime("%d/%m/%Y %H:%M:%S")
                logging.info('Gateway time : %s', timeStamp)

                #Prepare time frame
                timeFrame = "{\"gatewayID\":\"" + gatewayID + "\", \"ltemRSSI\":" + rssi + ", \"ltemRSSNR\":"  + snr +  ", \"time\":\"" + timeStamp + "\", \"latitude\":" + lat + ", \"longitude\":" + long + ", \"altitude\":" + alt + "}"
                
                topic = confPubHeader + "/up"
                ATstr = 'AT+SMPUB=\"'+ topic +'\",'+ str(len(timeFrame)) +',1,1\r'
                ser.write(bytes(ATstr,'utf-8'))
                time.sleep(0.2)
                #Send content over UART
                ser.write(bytes(timeFrame,'utf-8'))
                time.sleep(2)
                logging.info('Uplink message sent to MQTT topic %s : %s\n',topic, timeFrame)

            else:
                #print("Connection to remote MQTT broker has been lost")
                logging.warning('Gateway disconnected from MQTT remote broker')
                file.write("MQTT=0\n")
                resetMQTT()
                        
        except :
            
            #print('Problem checking LTE-M network and MQTT connection')
            logging.error('Error checking gateway details')
        
        serialMutex.release()
        
        file.close()

        #Check every 5 minutes
        time.sleep(300)

######################################################################################################
#Function logClean: Keep last 1000 lines in log file-------------------------------------------------#
######################################################################################################

def logClean():

    logFile = open("/home/ogate/LTEM/ltem.log", "r")
    logLines = logFile.readlines()
    lastLines = logLines[-1000:]
    logFile.close()

    logFile = open("/home/ogate/LTEM/ltem.log", "w")
    for logLine in lastLines:
        logFile.write(logLine)
    logFile.close()


######################################################################################################
#Function on_connect: connect to gateway mqtt broker and subscribe to gateway backend----------------#
######################################################################################################

def on_connect(client, userdata, flags, rc):

    #print("----Connected to gateway MQTT broker - Result code: " + str(rc) + "----")
    logging.info('Connected to gateway MQTT broker - Result code: %s', str(rc))
    client.subscribe("application/#")

######################################################################################################
#Handler on_message:  Print and forward gateway messages to server broker----------------------------#
######################################################################################################

def on_message(client, userdata, message):

    #serialMutex.acquire()
    global gatewayID
    global ATbuffer

    jsonStr=str(message.payload.decode('utf-8'))
  
    gatewayTopic=message.topic
    #print("+GPUB " + str(len(json)) + "bytes - Topic " + gatewayTopic  + " :" + json)
    
    #Check if uplink message
    if((gatewayTopic.find("event/up") != -1)):
        
        #get devEUI
        devEUI = gatewayTopic.split('/', 6)[3]

        #format server topic
        #serverTopic = confPubHeader + "/up"

        #Parse the json
        jsonDat = json.loads(jsonStr)
        
        #get time and date to timestamp the message
        now = datetime.now()
        timeStamp = now.strftime("%d/%m/%Y %H:%M:%S")

        #Keep usefull fields
        jsonLte = "{\"gatewayID\":\"" + jsonDat['rxInfo'][0]['gatewayID'] + "\", \"devEUI\":\"" + jsonDat['devEUI'] + "\", \"loraRSSI\":" + str(jsonDat['rxInfo'][0]['rssi']) + ", \"loraSNR\":" + str(jsonDat['rxInfo'][0]['loRaSNR']) + ", \"fport\":" + str(jsonDat['fPort']) + ", \"fcnt\":" + str(jsonDat['fCnt'])  + ", \"time\":\"" + timeStamp  + "\", \"data\":\"" + base64.b64decode(jsonDat['data']).hex() + "\"}\n"

        #Store message in file
        fileMutex.acquire()
        file = open("/home/ogate/LTEM/ltem.up", "a")
        file.write(jsonLte)
        file.close()
        fileMutex.release()

        logging.info('Uplink message placed in buffer file: %s', jsonLte)
        

######################################################################################################
#Function publish: send uplink messages to MQTT broker---------------------------------------------#
######################################################################################################

def publish():

    global gatewayID
    global confPubHeader
    global ATbuffer

    while True:
        #Check if there are any uplink messages in buffer file
        if os.path.isfile('/home/ogate/LTEM/ltem.up'):
            fileMutex.acquire()
            #Open uplink file
            uplink = open("/home/ogate/LTEM/ltem.up", "r")
            uplinkLines = uplink.readlines()
            uplink.close()
            os.remove("/home/ogate/LTEM/ltem.up")
            fileMutex.release()

            for line in uplinkLines:
                #remove the \n from line
                line=line[:-1]
                #convert to json
                jsonLine = json.loads(line)
                #Isolate devEUI
                devEUI = jsonLine['devEUI']

                #format server topic
                serverTopic = confPubHeader + "/up"
                
                #Make the publish command
                serialMutex.acquire()
                ser.write(bytes('AT+SMSTATE?\r', 'utf-8'))
                time.sleep(0.2)
                ser.write(bytes('AT+SMPUB=\"'+ serverTopic +'\",'+ str(len(line)) +',1,1\r', 'utf-8'))
                time.sleep(0.2)
                #Send content over UART
                ser.write(bytes(line,'utf-8'))
                serialMutex.release()
                time.sleep(3)
                logging.info('Uplink message sent to MQTT topic %s : %s',serverTopic, line)

######################################################################################################
#Function subscribing: check continusously messages from gateway mqtt broker-------------------------#
######################################################################################################

def subscribing():

    #Flush all messages
    #client.publish(topic, new byte[]{}, 0, true);
    #Define callback function when message is received on gateway mqtt broker
    client.on_message = on_message
    client.loop_forever()

######################################################################################################
#Function sendAT: send AT command to SIM7070 and save answer in global list--------------------------#
######################################################################################################

def sendAT(ATcommand):

    global ATbuffer
    ATbuffer.clear()
    ind = 0
    ser.write(bytes(ATcommand, 'utf-8'))
    time.sleep(0.2)

    #Check the response    
    buffer = ser.inWaiting()
    while(buffer > 0):
        inData = ser.readline()
        ATbuffer.append(str(inData, 'utf-8', 'ignore'))
        print ("UART " + str(ind) + " -> " +  ATbuffer[ind])
        ind = ind + 1
        time.sleep(0.2)
        buffer = ser.inWaiting()   

    return ind

######################################################################################################
#Function flushAT: flush UART from AT command--------------------------------------------------------#
######################################################################################################

def flushAT():

    flush = ser.inWaiting()
    while(flush > 0):
        inData = ser.readline()
        flush = ser.inWaiting()


######################################################################################################
#Function simcomInit: initialize SIM7070 for MQTT transfer with server-------------------------------#
######################################################################################################

def simcomInit():

    global ssl
    global gatewayID
    global ATbuffer
    global rssi
    global snr
    global LTEMstate



    #print("----Gateway ID : " + gatewayID + "----")
    logging.info('Gateway ID : %s', gatewayID)
    logging.info('network APN : %s',confAPN)
    logging.info('MQTT broker URL : %s',confURL)
    logging.info('MQTT broker port : %s',confPort)
    logging.info('MQTT broker topic publish header : %s',confPubHeader)
    logging.info('MQTT broker topic subscribe header : %s',confSubHeader)
    logging.info('MQTT broker username : %s',confUsername)
    logging.info('MQTT broker client ID : %s',confClid)


    #print("----Resetting SIM7070 module----")
    logging.info('Resetting SIM7070 module')
    #Reseting the module : toggle rPI GPIO4
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PWR_SIM7070, GPIO.OUT)
    GPIO.output(PWR_SIM7070, GPIO.LOW)
    time.sleep(2)
    GPIO.output(PWR_SIM7070, GPIO.HIGH)
    time.sleep(2)
    GPIO.output(PWR_SIM7070, GPIO.LOW)
    time.sleep(2)
    GPIO.output(PWR_SIM7070, GPIO.HIGH)
    time.sleep(2)
    GPIO.output(PWR_SIM7070, GPIO.LOW)
    GPIO.cleanup()
    time.sleep(5)
    
    #print("----Configurating SIM7070 module----")
    logging.info('Configurating SIM7070 module')
    flushAT()

    sendAT('AT\r')
    time.sleep(0.1)

    #Check if connection to MQTT broker must be secured
    if(ssl != 0):
                
        #Remove the previous certificates from SIM7070 ROM
        sendAT('AT+CFSINIT\r')
        time.sleep(0.1)

        sendAT('AT+CFSDFILE=3,\"module.cer\"\r')
        time.sleep(0.1)

        sendAT('AT+CFSDFILE=3,\"module.key\"\r')
        time.sleep(0.1)

        sendAT('AT+CFSDFILE=3,\"server.cer\"\r')
        time.sleep(2)

        #Check SSL type : CA only (ssl=2) or module certificate too (ssl=1)
        
        if os.path.isfile('/home/ogate/LTEM/certificates/server.cer'):
            ssl = 1
            #print ("Server CA root certificate found")
        else:
            #print ("Problem : CA root certificate not found - MQTTS connection not possible")
            ssl = 0

        if os.path.isfile('/home/ogate/LTEM/certificates/module.cer'):
            #print ("Client certificate found")
            ssl = 1
        else:
            #print ("Client certificate not found")
            ssl = 2

        if os.path.isfile('/home/ogate/LTEM/certificates/module.key'):
            #print ("Client key found")
            ssl = 1
        else:
            #print ("Client key not found")
            ssl = 2

	#Open certificate files saved on RPi
        logging.info('Loading SSL certificates')

        serverCert = open("/home/ogate/LTEM/certificates/server.cer", "r")
        serverCertLines = serverCert.readlines()
        serverCert.close()


        if ssl == 1:

            moduleKey = open("/home/ogate/LTEM/certificates/module.key", "r")
            moduleKeyLines = moduleKey.readlines()
            moduleCert = open("/home/ogate/LTEM/certificates/module.cer", "r")
            moduleCertLines = moduleCert.readlines()
            moduleCert.close()
            moduleKey.close()
            
	#Get size of the certificates

        serverCertLen = os.path.getsize("/home/ogate/LTEM/certificates/server.cer")
        #print("Server certificate found : " + str(serverCertLen)  + " bytes")
        logging.info('Server certificate found : %s bytes', str(serverCertLen))

        if ssl == 1:

            moduleCertLen = os.path.getsize("/home/ogate/LTEM/certificates/module.cer")
            #print("Module certificate found : " + str(moduleCertLen)  + " bytes")
            logging.info('Module certificate found : %s bytes', str(moduleCertLen))
        
            moduleKeyLen = os.path.getsize("/home/ogate/LTEM/certificates/module.key")
            #print("Module key found : " + str(moduleKeyLen)  + " bytes")
            logging.info('Module key found : %s bytes', str(moduleKeyLen))
        
        #Upload certificates over uart
        ################################################################################SERVER.CER
        ATstring = 'AT+CFSWFILE=3,\"server.cer\",0,' + str(serverCertLen) + ',10000\r'
        sendAT(ATstring)
        time.sleep(0.4)
        #send over uart
        for line in serverCertLines :
            ser.write(bytes(line.strip(), 'utf-8'))
            ser.write(bytes('\n','utf-8'))
            #print(line.strip())
        
        endAT = ''
        while(endAT.find("OK") == -1):
            sendAT(' \r')      
            time.sleep(0.1)
            try :
                endAT = ATbuffer[1]
            except : 
                endAT = ''

        time.sleep(2)

        if ssl == 1:

            ##############################################################################MODULE.CER
            ATstring = 'AT+CFSWFILE=3,\"module.cer\",0,' + str(moduleCertLen) + ',10000\r'
            sendAT(ATstring)
            time.sleep(0.4)
            #send over uart
            for line in moduleCertLines :
                ser.write(bytes(line.strip(), 'utf-8'))
                ser.write(bytes('\n','utf-8'))
                #print(line.strip())
        
            endAT = ''
            while(endAT.find("OK") == -1):
                sendAT(' \r')      
                time.sleep(0.1)
                try :
                    endAT = ATbuffer[1]
                except : 
                    endAT = ''

            time.sleep(2)

            ##############################################################################MODULE.KEY
            ATstring = 'AT+CFSWFILE=3,\"module.key\",0,' + str(moduleKeyLen) + ',10000\r'
            sendAT(ATstring)
            time.sleep(0.4)
            #send over uart
            for line in moduleKeyLines :
                ser.write(bytes(line.strip(), 'utf-8'))
                ser.write(bytes('\n','utf-8'))
                #print(line.strip())
        
            endAT = ''
            while(endAT.find("OK") == -1):
                sendAT(' \r')      
                time.sleep(0.1)
                try :
                    endAT = ATbuffer[1]
                except : 
                    endAT = ''

            time.sleep(2)

        sendAT('AT+CFSTERM\r')
        time.sleep(0.5)

        sendAT('AT+CSSLCFG=\"convert\", 2, \"server.cer\"\r')
        time.sleep(0.5)

        if ssl == 1:

            sendAT('AT+CSSLCFG=\"convert\",1,\"module.cer\",\"module.key\"\r')
            time.sleep(0.5)

        #Check certificates
        certState = ATbuffer[1]
        if(certState.find("OK") != -1):
            #print("Certificates uploaded sucessfully")
            logging.info('SSL certificates uploaded sucessfully')

        else:
            #print("Problem uploading certificates")
            logging.error('Problem uploading certificates')


        #reboot the module
        sendAT('AT+CREBOOT\r')
        time.sleep(60)

        sendAT('AT\r')
        time.sleep(1)


    sendAT('AT+CNMP=38\r')
    time.sleep(0.5)

    sendAT('AT+CMNB=1\r')
    time.sleep(0.5)

    ATstring = 'AT+CNCFG=0,1,\"' + confAPN + '\"\r'
    sendAT(ATstring)
    time.sleep(0.5)

    sendAT('AT+CNACT=0,1\r')
    time.sleep(0.5)

    #print("----Checking network connection----")
    logging.info('Checking network and server connection')
    
    sendAT('AT+CPSI?\r')
    time.sleep(0.1)
    
    #Get the signal RSSI ans SNR
    try:
        LTEMstate = ATbuffer[1].split(',', 13)[1]
        rssi = ATbuffer[1].split(',', 13)[12]
        snr = ATbuffer[1].split(',', 13)[13]
        snr = snr[:-2]

    except:
        rssi = "00"
        snr = "00"
        LTEMstate = "00"

    #Edit data file
    file = open("/home/ogate/LTEM/ltem.dat", "w")

    if(LTEMstate.find("Online") != -1):
        #print("Gateway is connected in LTEM")
        logging.info('Gateway connected to LTE-M network')
        file.write("LTEM=1\n")

    else:
        #print("Connection to LTEM has been lost")
        logging.warning('Gateway disconnected from LTE-M network')
        file.write("LTEM=0\n")
    
    #print("LTE-M RSSI : " + rssi + "dB")
    logging.info('LTE-M RSSI : %s dB', rssi)
    file.write("RSSI=" + rssi + "\n")

    #print("LTE-M SNR : " + snr + "dB")
    logging.info('LTE-M SNR : %s dB', snr)
    file.write("SNR=" + snr + "\n")

    file.write("MQTT=0\n")

    file.close()

    if(ssl == 1):
        sendAT('AT+SMSSL=1,\"server.cer\",\"module.cer\"\r')
        time.sleep(0.5)

    elif(ssl == 2):
        #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!IMPOSSIBLE TO USE MQTTS WITHOUT CLIENT FILES FOR NOW
        sendAT('AT+SMSSL=1,"server.cer"')
        time.sleep(2)

    ATstring = 'AT+SMCONF=\"URL\",\"' + confURL + '\",' + confPort + '\r'
    sendAT(ATstring)
    time.sleep(0.5)

    sendAT('AT+SMCONF=\"KEEPTIME\",60\r')
    time.sleep(0.5)

    ATstring = 'AT+SMCONF=\"USERNAME\",\"' + confUsername  + '\"\r'
    sendAT(ATstring)
    time.sleep(0.5)

    ATstring = 'AT+SMCONF=\"PASSWORD\",\"' + confPassword + '\"\r'
    sendAT(ATstring)
    time.sleep(0.5)

    sendAT('AT+SMCONF=\"CLEANSS\",1\r')
    time.sleep(0.5)

    sendAT('AT+SMCONF=\"CLIENTID\",\"'+confClid+'\"\r')
    time.sleep(2)

    #Try to connect to server as long connection is set
    logging.info('Trying to connect to server MQTT broker ...')
    while True:

        sendAT('AT+SMCONN\r')
        time.sleep(10)
        sendAT('AT+SMSTATE?\r')
        time.sleep(1)
        try :
            smState = ATbuffer[1]
        except :
            smState = ''

        if(smState.find("+SMSTATE: 1") != -1):
            break

        #print("Unable to connect to server MQTT broker - Retrying")
        logging.error('Unable to connect to server MQTT broker - Retrying')

    logging.info('Connected to server MQTT broker')

    #Subscribe to gateway topic when connection is set
    ATstring = 'AT+SMSUB=\"' + confSubHeader +'/#\",1\r'
    sendAT(ATstring)
    time.sleep(0.5)


######################################################################################################
#Function resetMQTT: try to reconnect to MQTT broker-------------------------------------------------#
######################################################################################################

def resetMQTT():
    
    global ssl

    #print("----Resetting MQTT connection----")
    logging.info('Resetting MQTT connection')

    #sendAT('AT+SMDISC\r')
    #time.sleep(0.5)

    #sendAT('AT+CREBOOT\r')
    #time.sleep(30)

    #sendAT('AT\r')
    #time.sleep(1)

    sendAT('AT+CNACT=0,1\r')
    time.sleep(2)

    #if(ssl == 1):

    #    sendAT("AT+SMSSL=1,\"server.cer\",\"module.cer\"\r")
    #    time.sleep(0.5)

    #ATstring = 'AT+SMCONF=\"URL\",\"' + confURL + '\",' + confPort + '\r'
    #sendAT(ATstring)
    #time.sleep(0.5)

    #sendAT('AT+SMCONF=\"KEEPTIME\",180\r')
    #time.sleep(0.5)

    #ATstring = 'AT+SMCONF=\"USERNAME\",\"' + confUsername  + '\"\r'
    #sendAT(ATstring)
    #time.sleep(0.5)

    #ATstring = 'AT+SMCONF=\"PASSWORD\",\"' + confPassword + '\"\r'
    #sendAT(ATstring)
    #time.sleep(0.5)

    #sendAT('AT+SMCONF=\"CLEANSS\",1\r')
    #time.sleep(0.5)

    #sendAT('AT+SMCONF=\"CLIENTID\",\"'+confClid+'\"\r')
    #time.sleep(0.5)

    #Try to connect to server as long connection is set
    logging.info('Trying to connect to server MQTT broker ...')
    while True:

        sendAT('AT+SMCONN\r')
        time.sleep(10)
        sendAT('AT+SMSTATE?\r')
        time.sleep(1)
        try :
            smState = ATbuffer[1]
        except :
            smState = ''

        if(smState.find("+SMSTATE: 1") != -1):
            break

        #print("Unable to connect to server MQTT broker - Retrying")
        #logging.error('Unable to connect to server MQTT broker - Retrying')

    logging.info('Connected to server MQTT broker')

    #Subscribe to gateway topic when connection is set
    ATstring = 'AT+SMSUB=\"' + confSubHeader +'/#\",1\r'
    sendAT(ATstring)
    time.sleep(0.5)

    
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
    #print("----Deleting a device from Chirpstack----")
    logging.info('Deleting device from Chirpstack : %s', devEUI)
    #Prepare the request to remove device
    
    #reqPayload = "{\"device\": {\"applicationID\": \"1\", \"description\": \"" + devDesc + "\", \"devEUI\":\"" + devEUI +"\", \"deviceProfileID\": \"153a8c20-63f1-4633-af31-61075cee5494\", \"isDisabled\"$
    #print('Payload:' + reqPayload)
    reqHeaders = {'Content-Type': 'application/json', 'Grpc-Metadata-Authorization' : APIjwt}
    reqURL = 'http://localhost:8080/api/devices/'+ devEUI +'/keys'

    #Send request
    reqOutput = requests.delete(reqURL,headers=reqHeaders)

    #Print status code from API
    #print("Deleting device - Chirpstack status: " + str(reqOutput.status_code))
    logging.info('Deleting device status : %s', str(reqOutput.status_code))


################################################################################################################################################Start of program

#Mutex definition
serialMutex=Lock()
fileMutex=Lock()

#Load file configuration
logging.info('Loading configuration file')
file = open("/home/ogate/LTEM/ltem.conf", "r")
# Store configurations in variable
confList = [line for line in file.readlines()]
file.close()
confAPN = confList[0].split('=',1)[1][:-1]
print('network APN : ',confAPN)
confURL = confList[1].split('=',1)[1][:-1]
print('MQTT broker URL : ',confURL)
confPort = confList[2].split('=',1)[1][:-1]
print('MQTT broker port : ',confPort)
confPubHeader = confList[3].split('=',1)[1][:-1]
print('MQTT broker publish topic header : ',confPubHeader)
confSubHeader = confList[4].split('=',1)[1][:-1]
print('MQTT broker subscribe topic header : ',confSubHeader)
confUsername = confList[5].split('=',1)[1][:-1]
print('MQTT broker username : ',confUsername)
confPassword = confList[6].split('=',1)[1][:-1]
#print('MQTT broker password : ',confPassword)
confClid = confList[7].split('=',1)[1][:-1]
print('MQTT broker client ID : ',confClid)
confSSL = confList[8].split('=',1)[1][:-1]

if(confSSL == "1"):
    ssl = 1
    #print("----Secured MQTT (SSL) is activated----")
    logging.info('Secured MQTT (SSL) activated')

else:
    logging.info('Secured MQTT (SSL) not activated')

#Get gateway Id
#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!RPI0
#os.system("ip link show eth0")
startID = subprocess.check_output("ip link show eth0 | awk '/ether/ {print $2}' | awk -F\: '{print $1$2$3}'", shell = True)
middleID = "fffe"
endID = subprocess.check_output("ip link show eth0 | awk '/ether/ {print $2}' | awk -F\: '{print $4$5$6}'",shell = True)

gatewayID = startID.decode("utf-8")[:-1]  + middleID + endID.decode("utf-8")[:-1] 

print("----Gateway ID : " + gatewayID + "----")
logging.info('Gateway ID: %s', gatewayID)


#Clear previous logs
open("/home/ogate/LTEM/ltem.log", 'w').close()

#MQTT definition
broker='localhost'
port=1883
client = mqtt.Client()
client.connect(broker, port)
client.on_connect = on_connect
time.sleep(1)
#client.on_disconnect = on_disconnect

#UART initialization
ser=serial.Serial('/dev/ttyS0', 115200,parity=serial.PARITY_NONE,stopbits=serial.STOPBITS_ONE,bytesize=serial.EIGHTBITS, timeout=1.0)  

##############################################################################################################################################Thread list
#1time threads
iniS=threading.Thread(target=simcomInit)
iniC=threading.Thread(target=chirpstackInit)
sub=threading.Thread(target=subscribing)
#forever threads
uart=threading.Thread(target=serialProcess, daemon = True)
tim=threading.Thread(target=timeFrame, daemon = True)
pub=threading.Thread(target=publish, daemon = True)
############################################################################################################################################Threads starting

#Start SIMCOM module initialization
iniS.start()
iniS.join()

#Start chirpstack API communication
iniC.start()
iniC.join()

#Start checking network and sending time frame
tim.start()

#Start gateway broker subscrition
sub.start()

#Start publishing downlink messages
pub.start()

#Start listenning  server broker
uart.start()



