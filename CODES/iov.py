import RPi.GPIO as GPIO
import serial
import random
import thread
import telegram
import urllib2
import os
import time
from telegram.ext import Updater, CommandHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


import email
import email.utils

import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders

from pynmea import nmea
from geopy.geocoders import GoogleV3


class Text():
    # 'a' for append, 'r' for read, 'w' for write
    def __init__(self,name):
        self.name=name

    def Text_write(self,data,fn):
        try:
            self.file=open(str(self.name)+".txt",str(fn))
            self.file.write(data)
            self.file.close()
        except:
            pass

    def Text_read(self,length=None):
        try:
            self.file=open(str(self.name)+".txt","r")
            if length is not None:
                data=self.file.read(int(length))
            else:
                data=self.file.readline()
            
            return data
        except:
            pass



iov_bb=Text("iov_bb")

user_tele_id='0'
#bck_id='391982524'
puser_tele_id='0'

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(40,0)   # Motor 1
GPIO.setup(38,0)   # Motor 1
GPIO.setup(36,0)    # Motor 2
GPIO.setup(32,0)   # Motor 2

GPIO.setup(12,0)   # Horn
GPIO.setup(10,0)     # Right Indicator
GPIO.setup(8,0)     # Left Indicator
GPIO.setup(21,0)     # ultra light

GPIO.setup(29,1,pull_up_down=GPIO.PUD_UP)    # Alcahol Sensor
GPIO.setup(23,1,pull_up_down=GPIO.PUD_UP)    # fire Sensor
GPIO.setup(19,1,pull_up_down=GPIO.PUD_UP)    # thief
GPIO.setup(24,1,pull_up_down=GPIO.PUD_UP)    # Speed Sensor
GPIO.setup(22,1,pull_up_down=GPIO.PUD_UP)    # Piezo Sensor


GPIO.setup(37,1,pull_up_down=GPIO.PUD_UP)    # LI
GPIO.setup(35,1,pull_up_down=GPIO.PUD_UP)    # RI
GPIO.setup(33,1,pull_up_down=GPIO.PUD_UP)    # Horn
GPIO.setup(31,1,pull_up_down=GPIO.PUD_UP)    # Brake

trigger_pin = 16
echo_pin = 18

GPIO.setup(trigger_pin,0)
GPIO.setup(echo_pin,1)

GPIO.output(12,1)

gpsser=serial.Serial('/dev/ttyUSB0',baudrate=9600,timeout=1)
#disser=serial.Serial('/dev/ttyUSB0',baudrate=9600,timeout=.1)

right=0
left=0
fwd=0
rev=0
dis=0
tim='0'
run=0
s_run=1
a_run=0
RI='Right Indicator OFF'
LI='Left Indicator OFF'
H='Horn OFF'
B='Brake Not Pressed'

ls='0'
rot='0'

gps_position='MG University'


def mail(to,sub):
    try:
        fromaddr = "ajay.mathews777@gmail.com"
        toaddr = to
         
        msg = MIMEMultipart()
         
        msg['From'] = fromaddr
        msg['To'] = toaddr
        msg['Subject'] = sub
        tim=str(time.ctime()) 
        body = "HELP\n"+'gps_position='+str(gps_position)+'\nDate & Time='+tim
         
        msg.attach(MIMEText(body, 'plain'))
         
        filename = "Image"
        attachment = open("/home/pi/Desktop/IOV/image.jpg", "rb")
         
        part = MIMEBase('application', 'octet-stream')
        part.set_payload((attachment).read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
         
        msg.attach(part)
         
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(fromaddr, "08/05/2019")
        text = msg.as_string()
        server.sendmail(fromaddr, toaddr, text)
        server.quit()
        print 'Mail Sent'
    except:
        print 'failed'
 


##mail("rishylorancedata@gmail.com","Test")

def send_trigger_pulse():
    GPIO.output(trigger_pin, True)
    time.sleep(0.0001)
    GPIO.output(trigger_pin, False)
def wait_for_echo(value, timeout):
    count = timeout
    while GPIO.input(echo_pin) != value and count > 0:
        count = count - 1
def get_distance():
    send_trigger_pulse()
    wait_for_echo(True, 10000)
    start = time.time()
    wait_for_echo(False, 10000)
    finish = time.time()
    pulse_len = finish - start
    distance_cm = pulse_len / 0.000058
    distance_in = distance_cm / 2.5
    return (distance_cm)



def position(threadName, delay):
    global gps_position
    while(1):
        
        gps_data=gpsser.read(350)
        geocoder = GoogleV3()
        #print gps_data
        
        try:
            
            if 'GPRMC' in gps_data:
                z=gps_data.index('GPRMC')
                lats=gps_data[z+19:z+28]
                longs=gps_data[z+31:z+41]
                lat1=(float(lats[2]+lats[3]+lats[4]+lats[5]+lats[6]+lats[7]+lats[8]))/60
                lat=(float(lats[0]+lats[1])+lat1)
                long1=(float(longs[3]+longs[4]+longs[5]+longs[6]+longs[7]+longs[8]+longs[9]))/60
                long=(float(longs[0]+longs[1]+longs[2])+long1)
                    
                print 'latitude=',lat
                print 'longitu=',long
                    
                location_list = geocoder.reverse(str(lat)+','+str(long))
                location = location_list[0]
                address = location.address
                gps_position=address
                print address
                print '***************************************************************'
        except:
            gps_position='=Ernakulam'
            #print gps_position
            #print 'no GPS data'



def ultra(threadName, delay):
    global dis,s_run
    global right
    global left
    global fwd
    global rev
    while(1):
        if(s_run==0):
            time.sleep(1)
            dis=get_distance()
            print "distance="+str(dis)
            if(int(dis)<10):
                GPIO.output(21,1)
##                fwd=right=left=rev=0
                
            else:
                GPIO.output(21,0)
                #pass
                
        else:
            GPIO.output(21,0)
            
       



def dev_stop():
    
    GPIO.output(40,0)
    GPIO.output(38,0)
    GPIO.output(36,0)
    GPIO.output(32,0)
    time.sleep(10)
                    
        


def sensors(threadName, delay):
    global a_run
    while(1):
        if(GPIO.input(29)==0):
            if(user_tele_id!='0'):
                bot.sendMessage(user_tele_id,text="Alcohol Detected")
        if(GPIO.input(23)==0):
            if(user_tele_id!='0'):
                bot.sendMessage(user_tele_id,text="Fire Detected")
        if(GPIO.input(19)==0):
            if(user_tele_id!='0'):
                bot.sendMessage(user_tele_id,text="malfuntind")
            
##            os.system("sudo fswebcam -r 320x240 /home/pi/Desktop/IOV/image.jpg")
##            mail("rishylorancedata@gmail.com","Thief")
            print 'mail sent'
            



def vstatus(threadName, delay):
    global run
    global RI
    global LI
    global H
    global B
    global dis
    while(1):
        if(GPIO.input(35)==0):
            GPIO.output(10,1)
            #print 'Right Indicator ON'
            RI='\nRight Indicator ON'
        else:
            GPIO.output(10,0)
            RI='\nRight Indicator OFF'
        if(GPIO.input(37)==0):
            GPIO.output(8,1)
            #print 'Left Indicator ON'
            LI='\nLeft Indicator ON'
        else:
            GPIO.output(8,0)
            LI='\nLeft Indicator OFF'
        if(GPIO.input(33)==0):
            GPIO.output(12,1)
            #print 'Horn ON'
            H='\nHorn Pressed'
        else:
            GPIO.output(12,0)
            H='\nHorn Not Pressed'
        if(GPIO.input(31)==0):
            #print 'Brake Pressed'
            run=1
            B='\nBrake Pressed'
        else:
            B='\nBrake Not Pressed'
        



def motor(threadName, delay):
    global ls
    global rot
    global s_run
    while(1):
        #print rot
        if(a_run==0):
            if(run==0):
                ls='\nUnlock'
                if(fwd==1):
                    GPIO.output(40,1)
                    GPIO.output(38,0)
                    GPIO.output(36,0)
                    GPIO.output(32,1)
                    s_run=0
                    rot=str(random.randrange(25,30,1))
                    #print 'Fwd'
                elif(rev==1):
                    GPIO.output(40,0)
                    GPIO.output(38,1)
                    GPIO.output(36,1)
                    GPIO.output(32,0)
                    s_run=0
                    rot=str(random.randrange(25,30,1))
                    #print 'Rev'
                elif(right==1):
                    GPIO.output(40,0)
                    GPIO.output(38,0)
                    GPIO.output(36,0)
                    GPIO.output(32,1)
                    s_run=0
                    rot=str(random.randrange(25,30,1))
                    #print 'Right'
                elif(left==1):
                    GPIO.output(40,1)
                    GPIO.output(38,0)
                    GPIO.output(36,0)
                    GPIO.output(32,0)
                    s_run=0
                    rot=str(random.randrange(25,30,1))
                    #print 'Left'
                else:
                    GPIO.output(40,0)
                    GPIO.output(38,0)
                    GPIO.output(36,0)
                    GPIO.output(32,0)
                    s_run=1
                    rot='0'
                    #print 'stop'
            else:
                print 'lock'
                ls='\nLock'
                GPIO.output(40,0)
                GPIO.output(38,0)
                GPIO.output(36,0)
                GPIO.output(32,0)
                s_run=1
                rot='0'
        else:
                print 'lock'
                ls='\nLock'
                GPIO.output(40,0)
                GPIO.output(38,0)
                GPIO.output(36,0)
                GPIO.output(32,0)
                s_run=1
                rot='0'
            
def start(bot, update):
    global user_tele_id
    print update.message.chat_id
    user_tele_id=str(update.message.chat_id)
    update.message.reply_text('Welcome')
    custom_keyboard = [['/Drive', '/Status'],['/Camera','/Security'],['/Location','/Help'],['/System_OFF']]
    reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
    bot.sendMessage(update.message.chat_id,text="Loading.....",reply_markup=reply_markup)


def Drive(bot, update):
    if(user_tele_id==str(update.message.chat_id)):
        custom_keyboard = [['/Forward'],['/Left','/Right'],['/Reverse'],['/Stop'],['/start']]
        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
        bot.sendMessage(update.message.chat_id,text="Drive Mode",reply_markup=reply_markup)
    else:
        update.message.reply_text('Permission Denied')
    
def Status(bot, update):
    if(user_tele_id==str(update.message.chat_id)):
        l='Current Status'+RI+LI+H+B+'\nRPM='+rot+ls
        update.message.reply_text(l)
    else:
        update.message.reply_text('Permission Denied')

    
def Camera(bot, update):
    if(user_tele_id==str(update.message.chat_id)):
        custom_keyboard = [['/Capture','/Capture_Video'],['/Recorded_Video'],['/start']]
        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
        bot.sendMessage(update.message.chat_id,text="Capture Mode",reply_markup=reply_markup)
    else:
        update.message.reply_text('Permission Denied')

def Security(bot, update):
    if(user_tele_id==str(update.message.chat_id)):
        custom_keyboard = [['/Lock','/Unlock'],['/start']]
        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
        bot.sendMessage(update.message.chat_id,text="Status",reply_markup=reply_markup)
    else:
        update.message.reply_text('Permission Denied')

def Location(bot, update):
    if(user_tele_id==str(update.message.chat_id)):
        update.message.reply_text('gps_position'+str(gps_position))
    else:
        update.message.reply_text('Permission Denied')

def Help(bot, update):
    if(user_tele_id==str(update.message.chat_id)):
        update.message.reply_text('Police no=1234567891\nAmbulance no=1234554321')
    else:
        update.message.reply_text('Permission Denied')


    
def Forward(bot, update):
    global right
    global left
    global fwd
    global rev
    if((user_tele_id==str(update.message.chat_id))&(a_run==0)):
        update.message.reply_text('Moving Fwd')
        fwd=1
        right=left=rev=0
    else:
        update.message.reply_text('Permission Denied')   

def Reverse(bot, update):
    global right
    global left
    global fwd
    global rev
    if((user_tele_id==str(update.message.chat_id))&(a_run==0)):
        update.message.reply_text('Moving Rev')
        fwd=right=left=0
        rev=1
    else:
        update.message.reply_text('Permission Denied')      

def Left(bot, update):
    global right
    global left
    global fwd
    global rev
    if((user_tele_id==str(update.message.chat_id))&(a_run==0)):
        update.message.reply_text('Moving Left')
        fwd=right=rev=0
        left=1
    else:
        update.message.reply_text('Permission Denied') 
    
    

def Right(bot, update):
    global right
    global left
    global fwd
    global rev
    if((user_tele_id==str(update.message.chat_id))&(a_run==0)):
        update.message.reply_text('Moving Right')
        fwd=left=rev=0
        right=1
    else:
        update.message.reply_text('Permission Denied')
    
        

def Stop(bot, update):
    global right
    global left
    global fwd
    global rev
    if((user_tele_id==str(update.message.chat_id))&(a_run==0)):
        update.message.reply_text('stop')
        fwd=right=left=rev=0
    else:
        update.message.reply_text('Permission Denied')


def Capture(bot, update):
    if(user_tele_id==str(update.message.chat_id)):
        try:
            update.message.reply_text('Capturing.....')
            os.system("sudo fswebcam -r 320x240 /home/pi/Desktop/IOV/image.jpg")
            f = open('/home/pi/Desktop/IOV/image.jpg','rb')
            update.message.reply_text('Sending.....')
            bot.sendPhoto(update.message.chat_id,f)
        except:
            update.message.reply_text('Error While Capturing...')
    else:
        update.message.reply_text('Permission Denied')


def Capture_Video(bot, update):
    if(user_tele_id==str(update.message.chat_id)):
        try:
            update.message.reply_text('Recording.....')
            os.remove('/home/pi/Desktop/IOV/ak.mp4')
            os.system("sudo avconv -t 10 -f video4linux2 -r 15 -s 320x240 -i /dev/video0 /home/pi/Desktop/IOV/ak.mp4")
            update.message.reply_text('Sending.....')
            bot.send_video(update.message.chat_id, video=open('ak.mp4','rb'))
        except:
            update.message.reply_text('Error While Capturing...')
    else:
        update.message.reply_text('Permission Denied')



def Recorded_Video(bot, update):
    if(user_tele_id==str(update.message.chat_id)):
        try:
            update.message.reply_text('Uploading.....')
            bot.send_video(update.message.chat_id, video=open('ak1.mp4','rb'))    
        except:
            update.message.reply_text('Error While Uploading...')
    else:
        update.message.reply_text('Permission Denied')



def Lock(bot, update):
    global run
    if((user_tele_id==str(update.message.chat_id))&(a_run==0)):
        run=1
        update.message.reply_text('Locked')
    else:
        update.message.reply_text('Permission Denied')


def Unlock(bot, update):
    global run
    if((user_tele_id==str(update.message.chat_id))&(a_run==0)):
        run=0
        update.message.reply_text('Unlocked')
    else:
        update.message.reply_text('Permission Denied')



def police(bot, update):
    global puser_tele_id
    puser_tele_id=str(update.message.chat_id)
    if(user_tele_id==str(update.message.chat_id)):
        custom_keyboard = [['/GPS_Location','/Vehicle_Stop'],['/Vehicle_Start','/Vehicle_Documents'],['/Blackbox_Details']]
        reply_markup = telegram.ReplyKeyboardMarkup(custom_keyboard)
        bot.sendMessage(update.message.chat_id,text="Police Mode Activated",reply_markup=reply_markup)
    else:
        update.message.reply_text('Permission Denied')

def Blackbox_Details(bot, update):
    if(user_tele_id==str(update.message.chat_id)):
        try:
            update.message.reply_text('Uploading.....')
            f = open('iov_bb.txt','rb')
            bot.sendDocument(update.message.chat_id,f)
            f.close()
        except:
            update.message.reply_text('Error While Uploading')
            
    else:
        update.message.reply_text('Permission Denied')

def GPS_Location(bot, update):
    if(user_tele_id==str(update.message.chat_id)):
        update.message.reply_text('gps_position'+str(gps_position))
    else:
        update.message.reply_text('Permission Denied')
        

def Vehicle_Stop(bot, update):
    global a_run
    if(user_tele_id==str(update.message.chat_id)):
        a_run=1
        update.message.reply_text('Vehicle Stopped')
    else:
        update.message.reply_text('Permission Denied')

def Vehicle_Start(bot, update):
    global a_run
    if(user_tele_id==str(update.message.chat_id)):
        a_run=0
        update.message.reply_text('Vehicle Start')
    else:
        update.message.reply_text('Permission Denied')

def Vehicle_Documents(bot, update):
    if(user_tele_id==str(update.message.chat_id)):
        l='***Vehicle Details***\n\nVehicle no=KL-08-BB-1234\nModel Year=2015\nManufacturer=Audi\nEngine no=H22A M03737\nCC=2000\nSeat Capacity=5\nFuel Type=Diesel\n\n***Owner Details***\n\nName=iqubal\nContact no=9895097195\nPlace=Thrissur' 
        update.message.reply_text(l)
    else:
        update.message.reply_text('Permission Denied')


def System_OFF(bot, update):
    if(user_tele_id==str(update.message.chat_id)):
        update.message.reply_text('System OFF.......')
        os.system("sudo shutdown -h now")
    else:
        update.message.reply_text('Permission Denied')



def cid(bot, update):
    user_tele_id=str(update.message.chat_id)
    update.message.reply_text('Your Chat ID='+str(user_tele_id)) 

def emg(channel):
    global run
    if(s_run==0):
        run=1
        print 'emergency'
##        os.system("sudo fswebcam -r 320x240 /home/pi/Desktop/IOV/image.jpg")
        tim=str(time.ctime())
        e='\nDate and time='+tim+RI+LI+H+B+'\nRPM='+rot+ls+'\n****************************************************************************'
        iov_bb.Text_write(e,"a")
        bot.sendMessage(chat_id=user_tele_id, text="Emergency") 
##        os.remove('/home/pi/Desktop/IOV/ak1.mp4')
##        os.system("sudo avconv -t 10 -f video4linux2 -r 15 -s 320x240 -i /dev/video0 /home/pi/Desktop/IOV/ak1.mp4")
        em="!!!ACCIDENT!!! \nPosition\n"+str(gps_position)+'\nVehicle Number=KL-08-BB-1234'+"\n Date & Time="+tim
        if(user_tele_id!='0'):
            bot.sendMessage(user_tele_id,text=em)
##        mail("mec2016r@gmail.com","Police")
        #mail("kafarzana93@gmail.com","Ambulance")
        print 'mail sent'
    
bot = telegram.Bot(token='627333566:AAGanhIPY2BP7UqOJcdAhjYR1mOJZG6OuyM')
updater = Updater('627333566:AAGanhIPY2BP7UqOJcdAhjYR1mOJZG6OuyM')


    

updater.dispatcher.add_handler(CommandHandler('start', start))
updater.dispatcher.add_handler(CommandHandler('cid', cid))
updater.dispatcher.add_handler(CommandHandler('Stop', Stop))
updater.dispatcher.add_handler(CommandHandler('Forward', Forward))
updater.dispatcher.add_handler(CommandHandler('Reverse', Reverse))
updater.dispatcher.add_handler(CommandHandler('Left', Left))
updater.dispatcher.add_handler(CommandHandler('Right', Right))
updater.dispatcher.add_handler(CommandHandler('Drive', Drive))
updater.dispatcher.add_handler(CommandHandler('Status', Status))
updater.dispatcher.add_handler(CommandHandler('Help', Help))
updater.dispatcher.add_handler(CommandHandler('Security', Security))
updater.dispatcher.add_handler(CommandHandler('Capture', Capture))
updater.dispatcher.add_handler(CommandHandler('Camera', Camera))
updater.dispatcher.add_handler(CommandHandler('Capture_Video', Capture_Video))
updater.dispatcher.add_handler(CommandHandler('Recorded_Video', Recorded_Video))
updater.dispatcher.add_handler(CommandHandler('police', police))
updater.dispatcher.add_handler(CommandHandler('Lock', Lock))
updater.dispatcher.add_handler(CommandHandler('Unlock', Unlock))
updater.dispatcher.add_handler(CommandHandler('Location', Location))
updater.dispatcher.add_handler(CommandHandler('GPS_Location', GPS_Location))
updater.dispatcher.add_handler(CommandHandler('Blackbox_Details', Blackbox_Details))
updater.dispatcher.add_handler(CommandHandler('Vehicle_Stop', Vehicle_Stop))
updater.dispatcher.add_handler(CommandHandler('Vehicle_Start', Vehicle_Start))
updater.dispatcher.add_handler(CommandHandler('Vehicle_Documents', Vehicle_Documents))
updater.dispatcher.add_handler(CommandHandler('System_OFF', System_OFF))


GPIO.add_event_detect(22,GPIO.FALLING,callback=emg,bouncetime=300)

GPIO.output(12,1)
time.sleep(1)
GPIO.output(12,0)

          
try:    
   thread.start_new_thread(motor, ("Thread-1", 1, ) )
   thread.start_new_thread(vstatus, ("Thread-1", 1, ) )
   thread.start_new_thread(position, ("Thread-1", 1, ) )
   thread.start_new_thread(sensors, ("Thread-1", 1, ) )
   thread.start_new_thread(ultra, ("Thread-1", 1, ) )
   #thread.start_new_thread(front, ("Thread-1", 1, ) )
   #thread.start_new_thread(check1, ("Thread-1", 1, ) )
   print 'on'
   updater.start_polling()
   updater.idle()
  
  
except:
   print "Error: unable to start thread"

while 1:
   pass
