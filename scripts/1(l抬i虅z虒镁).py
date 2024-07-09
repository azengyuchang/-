#!/usr/bin/env python2
# coding:UTF-8
# Version: V1.0.1
import os
import threading
import RPi.GPIO as GPIO
import time
import serial
from imu_information import *
from imu_usb import *
from go_straight import *
from go_straight_mountain import *
from go_straight_longroad import *
from Rosmaster_Lib import Rosmaster
from follow_common import *
from long_bridge import *
from go_platform import *
from slow_speed import *
from simple_input import *
from roadback import *
# RED: 0, 85, 126, 9, 253, 255
RAD2DEG = 180 / math.pi
bot = Rosmaster()
flag_tracking = 0

total_ret = ""
total_frame = ""
camera_flag = 1
pitch_info = 0.0
clock_flag = 1
sensor_flag_old = 1
sensor_res = 2
change_clock_flag = 0
start_change_flag = 0
finsh_flag = 0

prev_error_m1 = 0
prev_error_m2 = 0
prev_error_m3 = 0
prev_error_m4 = 0
integral_m1 = 0.0
integral_m2 = 0.0
integral_m3 = 0.0
integral_m4 = 0.0
start_vertical_time = 0
speed_gear = 7


alpha = 0.8
beta = 10

# flag = 0
class LineDetect:
    def __init__(self):
        #rospy.on_shutdown(self.cancel)
        #rospy.init_node("LineDetect", anonymous=False)
        #self.imu = imuSub() 
        #self.imu_node = imuNode()
        self.img = None
        self.circle = ()
        self.hsv_range = ((0, 0, 221),
                          (180, 30, 255))
        self.Roi_init = ()
        self.warning = 1
        self.Start_state = True
        #self.dyn_update = False
        self.Buzzer_state = False
        self.select_flags = False
        self.Track_state = 'identify'
        self.windows_name = 'frame'
        #self.ros_ctrl = ROSCtrl()
        self.color = color_follow()
        self.cols, self.rows = 0, 0
        self.Mouse_XY = (0, 0)
        self.img_flip = False
        self.VideoSwitch = True
        self.rear_prev_error = 0.0
        self.rear_integral = 0.0
        self.front_prev_error = 0.0
        self.front_integral = 0.0
        #self.hsv_text = rospkg.RosPack().get_path("yahboomcar_linefollw")+"/scripts/LineFollowHSV.text"
        #Server(LineDetectPIDConfig, self.dynamic_reconfigure_callback)
        
        #self.dyn_client = Client("LineDetect", timeout=60)
        #print(1)
        #self.scale = 500
        #self.FollowLinePID = (45, 0, 30)
        #self.linear = 0.3
        
        #self.PID_init()
        #self.pub_rgb = rospy.Publisher("/linefollw/rgb", Image, queue_size=1)
        #self.pub_Buzzer = rospy.Publisher('/Buzzer', Bool, queue_size=1)
        self.flag1 = -1
        self.cnt = 0
        self.turn_flag = 1
        self.up_flag = 0
        self.break_flag = 0
        self.cancel_flag = 0
  
        #self.total_ret = ""
        #self.total_frame = ""
	#self.imu = imuSub() 
	#self.port = '/dev/ttyUSB0' # USB serial port #/dev/ttyS3
        #self.baud = 9600   # Same baud rate as the INERTIAL navigation module
        #self.ser = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.5)

        #if self.VideoSwitch == False:
            #print(1)
            #from cv_bridge import CvBridge-4.7021484375
            #self.bridge = CvBridge()
            #self.sub_img = rospy.Subscriber("/usb_cam/image_raw/compressed", CompressedImage, self.compressed_callback)
    #def get_frame(self):
        #print("frame1",self.total_frame)
        #return self.total_frame

    def cancel(self):
        #self.Reset()
        self.cancel_flag = 1
        self.VideoSwitch = False
        bot.set_car_motion(0,0,0)
        #time.sleep(5)
        #self.ros_ctrl.cancel()
        #self.sub_img.unregister()
        print(0)
        #self.pub_rgb.unregister()
        #self.pub_Buzzer.unregister()
        
        print ("Shutting down this node.")
        if self.VideoSwitch==False:
            #self.sub_img.unregister()
            print(2)
            
            cv.destroyAllWindows()

         
    def read_GPIO(self):
        input_pin =11
        sensor_flag = 1
        global sensor_flag_old
        global sensor_res
        GPIO.setmode(GPIO.BCM)  # BCM pin-numbering scheme from Raspberry Pi
        GPIO.setup(input_pin, GPIO.IN)  # set pin as an input pin
        values = []
        try:
            while True:
                value = GPIO.input(input_pin)
                values.append(value)
                if len(values) == 20:
                    if sum(values):
                        sensor_flag = 1 
                    else:
                        sensor_flag = 0
                    values = []
                    if sensor_flag != sensor_flag_old:
                        sensor_res = sensor_flag
                        print("get",sensor_res)
                        sensor_flag_old = sensor_flag  
        finally:
            GPIO.cleanup()
        
        return value

    def process(self, rgb_img, action, cnt_target, cnt_corss):
        global pitch_info
        global alpha
        global beta
        global flag_tracking
        global finsh_flag
        binary = []
        flag = 0
        flag_all = 1
        global speed_gear
        t1=time.time()
        if self.img_flip == True: rgb_img = cv.flip(rgb_img, 1)
        if action == 32: self.Track_state = 'tracking'
        elif action == ord('i') or action == 105: self.Track_state = "identify"
        elif action == ord('q') or action == 113: self.cancel() 
        if self.Track_state != 'init' and len(self.hsv_range) != 0 and self.turn_flag == 1:
            rgb_img, binary, self.circle ,flag= self.color.line_follow(rgb_img, self.hsv_range,self.flag1,cnt_target, cnt_corss,finsh_flag,alpha,beta)
            self.flag1 = flag
            #print("3",time.time()-t1)
        if self.Track_state == 'tracking': 
            #print(flag_tracking)
            if flag_tracking == 1:
                #start_platform()
                flag_tracking = 0
                #speed_gear == 1            
            #print("4",time.time()-t1)            
            if flag == 0 and self.cancel_flag == 0:  
                flag_all = 0
            elif flag != 0 and self.cancel_flag == 0:
                threading.Thread(target = self.PID_control, args=(self.front_prev_error, self.front_integral, self.rear_prev_error, self.rear_integral, self.circle[0])).start()
                #print("5",time.time()-t1)
            elif self.cancel_flag == 1:
                bot.set_car_motion(0,0,0)

        return rgb_img, binary, flag_all 


    def PID_control(self, front_prev_error, front_integral, rear_prev_error, rear_integral, Center_x):
        global speed_gear
        #correct_sp_l = 0
        #correct_sp_r = 0 
        if speed_gear == 1:
            front_Kp = 0.8  # ?¡ã??
            front_Ki = 0  # ?¡ã??
            front_Kd = 0.3  # ?¡ã??
            rear_Kp = 0.8  # o¨®??
            rear_Ki = 0  # o¨®??
            rear_Kd = 0.3  # o¨®??
            k = 1  #¨¢¨¦???¨¨
            v_motor = 30    #?¨´¡À??¨´?¨¨
            v_threshold = 50  #?D?¦Ì

        elif speed_gear == 2:
            front_Kp = 0.8  # ?¡ã??
            front_Ki = 0  # ?¡ã??
            front_Kd = 1  # ?¡ã??
            rear_Kp = 0.8  # o¨®??
            rear_Ki = 0  # o¨®??
            rear_Kd = 1  # o¨®??
            k = 0.6  #¨¢¨¦???¨¨
            v_motor = 60    #?¨´¡À??¨´?¨¨
            v_threshold = 40  #?D?¦Ì

        elif speed_gear == 3:
            front_Kp = 0.8  # ?¡ã??
            front_Ki = 0  # ?¡ã??
            front_Kd = 5  # ?¡ã??
            rear_Kp = 0.8  # o¨®??
            rear_Ki = 0  # o¨®??
            rear_Kd = 5 # o¨®??
            k = 0.4  #¨¢¨¦???¨¨
            v_motor = 60   #?¨´¡À??¨´?¨¨
            v_threshold = 30  #?D?¦Ì

        elif speed_gear == 4:  # ???¨´¡ä?
            front_Kp = 0.9  # ?¡ã??
            front_Ki = 0.04  # ?¡ã??
            front_Kd = 0.6  # ?¡ã??
            rear_Kp = 0.9  # o¨®??
            rear_Ki = 0.01  # o¨®??
            rear_Kd = 0.6  # o¨®??
            k = 0.4  #¨¢¨¦???¨¨
            v_motor = 54    #?¨´¡À??¨´?¨¨
            v_threshold = 40  #?D?¦Ì

        elif speed_gear == 5:  # ¨ª?¦Ì¨¤
            front_Kp = 0.8  # ?¡ã??
            front_Ki = 0  # ?¡ã??
            front_Kd = 0.3  # ?¡ã??
            rear_Kp = 0.8  # o¨®??
            rear_Ki = 0  # o¨®??
            rear_Kd = 0.3  # o¨®??
            k = 1  #¨¢¨¦???¨¨
            v_motor = 35    #?¨´¡À??¨´?¨¨
            v_threshold = 50  #?D?¦Ì

        if speed_gear == 6: #?¨²?a??¦Ì¦Ì??¨¦???¦Ì¡Â??????PID ?¡À?¨®?¨¹?a?????t¦Ì????- ¡ä¨®??¨¬¡§?¨¨?¡è¡Á? pitch??¡À?o¨® ??¨¨??a??¦Ì¦Ì??¦Ì??2?¡À?? ¨°a?¨¨?¡§?¡ã¦Ì?¦Ì¨²????¦Ì?¦Ì¨²1???¡¤?¨² ¨¨?o¨®??¨¨?o¨®??¦Ì????- 3?¨º??¡¥¦Ì¦Ì?????a6¦Ì2 ?¨´?¨¨10??20 ?¡ä?¨¦??¦Ì¡Â?? ¡Á???¨°a¦Ì?¨º??¨¨ 2?¨°a?¡¥adjust_speed¨¤???¦Ì?2?¨ºy DT??¨ª¨º¦Ì?2?¨ºy??¦Ì?????¨¨£¤ ?-??¦Ì?2?¨ºy?-?o?e ¡Á?o?D¡ä¨°???¨¨??? ¡¤?¡À?o¨®?????¨® 2???¦Ì????-?¡À?¨®?¨º?¨°??
            front_Kp = 0.8  # ?¡ã??
            front_Ki = 0  # ?¡ã??
            front_Kd = 0.3  # ?¡ã??
            rear_Kp = 0.8  # o¨®??
            rear_Ki = 0  # o¨®??
            rear_Kd = 0.3  # o¨®??
            k = 1  #¨¢¨¦???¨¨
            v_motor = 20    #?¨´¡À??¨´?¨¨
            v_threshold = 30  #?D?¦Ì

        if speed_gear == 7:
            front_Kp = 0.8  # ?¡ã??
            front_Ki = 0  # ?¡ã??
            front_Kd = 0.6  # ?¡ã??
            rear_Kp = 0.8  # o¨®??
            rear_Ki = 0  # o¨®??
            rear_Kd = 0.6  # o¨®??
            k = 1  #¨¢¨¦???¨¨
            v_motor = 30    #?¨´¡À??¨´?¨¨
            v_threshold = 35  #?D?¦Ì
    
        elif speed_gear == 8:  # ¨¬YD?¨¦?
            front_Kp = 0.9  # ?¡ã??
            front_Ki = 0  # ?¡ã??
            front_Kd = 3  # ?¡ã??
            rear_Kp = 0.9  # o¨®??
            rear_Ki = 0  # o¨®??
            rear_Kd = 3  # o¨®??
            k = 0.3  #¨¢¨¦???¨¨
            v_motor = 35    #?¨´¡À??¨´?¨¨
            v_threshold = 40  #?D?¦Ì


        #if speed_gear == 4:
         #   left_rear = get_GPIO(19)
           # right_rear = get_GPIO(26)
           # if left_rear == 0 and right_rear == 1:
             #   correct_sp_l = 20
             #   correct_sp_r = 0
            #if left_rear == 1 and right_rear == 0:
               #correct_sp_l = 0
                #correct_sp_r = 20
                
        front_error = (320 - Center_x) * k
        #print(320 - Center_x)
        
        self.front_integral += front_error
    
        front_derivative = front_error - self.front_prev_error
   
        front_output = front_Kp * front_error + front_Ki * self.front_integral + front_Kd * front_derivative
   
        front_output = max(min(front_output, v_threshold), -1.0*v_threshold)
        rear_error = (320 - Center_x)*k
    
        self.rear_integral += rear_error
   
        rear_derivative = rear_error - self.rear_prev_error
   
        rear_output = rear_Kp * rear_error + rear_Ki * self.rear_integral + rear_Kd * rear_derivative
 
        rear_output = max(min(rear_output, v_threshold), -1.0*v_threshold)
        bot.set_motor(v_motor-front_output, v_motor-rear_output, v_motor+front_output, v_motor+rear_output)
       # print("output",rear_output,front_output)
        self.front_prev_error = front_error
        self.rear_prev_error = rear_error
        
    def adapt_light(self,capture,state):#¡ã¡Á¨¬¨¬¡Á¡ä¨¬??a1 ¨ª¨ª¨¦?¡Á¡ä¨¬??a0
        global alpha
        global beta
        total_ret,src = capture.read()
        average = np.mean(src)
        print('light',average)
        light_p=0
        standard=120
        step=10
        if state==1:
            standard=80
            step=10
        else:
            standard=160
            step=20
        while (average <= standard):
            if(light_p <=100):light_p+=step
            print("step",step)
            if light_p>100:
                break
            capture.set(cv.CAP_PROP_GAIN, light_p)
            total_ret,src = capture.read()
            average = np.mean(src)
            print('light',average)      
        return

    def openCapture(self):
        global total_ret
        global total_frame
        global camera_flag
        try:
            capture = cv.VideoCapture('/dev/camera1', cv.CAP_V4L2)  
            #capture = cv.VideoCapture(1, cv.CAP_V4L2)
            capture.set(cv.CAP_PROP_FOURCC, cv.VideoWriter_fourcc(*'XVID'))
            #capture.set(6, cv.VideoWriter.fourcc('M', 'J', 'P', 'G'))
            capture.set(cv.CAP_PROP_FRAME_WIDTH, 640)
            capture.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
            capture.set(5,120)
            capture.set(cv.CAP_PROP_AUTO_EXPOSURE, 0.25)
            capture.set(cv.CAP_PROP_GAIN, 10)
            #capture.set(10,20)
            capture.set(cv.CAP_PROP_AUTO_EXPOSURE,0)
           #capture.set(cv.CAP_PROP_AUTOWB,0)
            print("open")
            print(capture.isOpened())
            if capture.isOpened():
                 self.adapt_light(capture,0)
                 #print(1)
            #print(2)
            while capture.isOpened():
                 #print(3)
                 total_ret,frame = capture.read()
                 #print("1",frame)
                 while frame is None or frame == "":
                     total_ret,frame = capture.read()
                     #print("2",frame)
                 total_frame = frame.copy()
                 #print(total_frame)
                 if camera_flag == 0:
                     break
        except Exception as e:
            print("error",e)
        finally:
            if capture is not None:
                capture.release()
        cv.destroyAllWindows()

    

    def change_flag(self):
        global clock_flag
        time.sleep(1)
        clock_flag = 1 

    def change_flag1(self):
        global clock_flag
        time.sleep(4)
        clock_flag = 1

    def check_green_color(self,image):
        image1 = image.copy()
        height=480
        width=640 
        #startRow, startCol = int(height * .25), int(width * .25)
        #endRow, endCol = int(height * .75), int(width * .75)
        croppedImage = image1[1:360,1:639]
        hsv_image = cv.cvtColor(croppedImage, cv.COLOR_BGR2HSV)
        lower_green = (25, 25, 25)
        upper_green = (90, 180, 180)
        mask = cv.inRange(hsv_image, lower_green, upper_green)
        green_pixels = cv.countNonZero(mask)
        if green_pixels > 120:
            flag = 1
        else:
            flag = 0
        return flag

    def rgb_open(self):
        while 1:
            i = 0
            for i in range(100):
                bot.set_colorful_lamps(i,255,255,255)
 
if __name__ == '__main__':    
    #bot = Rosmaster()    
    #while(1):
    #imu.return_angle()
    flag_gogogo = 0
    flag_all = 1
    cnt_target = 6
    cnt_corss = 0
    middle_platform_flag = 0
    road_select = 0
    mountain_time = 0
    start_rush_time = time.time() + 1000
    old_angle =0
    mountain_flag = 1
    angle_standard = 0
    this_time = time.time()
    last_time = time.time() 
    line_detect = LineDetect()
    #print(1)
    #line_detect.PID_init()
    #port = '/dev/ttyUSB0' # USB serial port #/dev/ttyS3
    #baud = 9600   # Same baud rate as the INERTIAL navigation module
    #ser1 = serial.Serial('/dev/ttyUSB0', 9600, timeout=0.5)
    print ("HSV: ", line_detect.hsv_range)
    if line_detect.VideoSwitch==False:rospy.spin()
    else:
        threading.Thread(target = line_detect.openCapture).start()
        #threading.Thread(target = line_detect.getting_pitch).start()
        #threading.Thread(target = line_detect.rgb_open).start()
        pitch_correction()#??¨¬?¡¤???¨¤??1D¨¨¨°a¨¬???
        #time.sleep(6)

        while line_detect.VideoSwitch == True and flag_gogogo == 0:
          
            while total_frame == "" or total_frame is None:
                #print("sb")
                i=1
            flag_gogogo = line_detect.check_green_color(total_frame)
         
            print("wait for promitting")
        print("gogogo")
        bot.create_receive_threading()
        enable = True
        bot.set_auto_report_state(enable, forever=False)

        flag_tracking = 1
        flag_vertical = 0
        t_angle = 0
        treasure = -1
        while line_detect.VideoSwitch==True :
            
            while flag_all !=0: 
                                             
                #print("imu_data",imu.return_angle()[2])
                start = time.time()
                #ret, frame = capture.read()
                action = cv.waitKey(10) & 0xFF
                #print("1",time.time()-start)
                frame = total_frame.copy()
                #print("2",time.time()-start)
                #print("frame",frame)
                #if frame == "":
                #    continue
                frame1, binary, flag_all = line_detect.process(frame, action,cnt_target,cnt_corss)
                #print("flag_all",flag_all)
                #print(binary)
                pitch = return_pitch()
                print(pitch) 
                left_front = get_GPIO(11)
                right_front = get_GPIO(5)
                left_rear = get_GPIO(19)
                right_rear = get_GPIO(26)
                left_middle = get_GPIO(9)
                right_middle = get_GPIO(6)
                #if pitch > 5 and cnt_target == 1 and cnt_corss == 1 and finsh_flag == 0:
                #?-1y?¨¤¡¤?????¡ê??e¨º???¨¬¡§o¨ª3¡è??????2¨¦¨®?¡ä?¨º¨®??
                    #print("go bridge")
                    #bot.set_motor(90,90,90,90)               
                    #cross_bridge()
                    #finsh_flag = 1
                
                #if pitch > 5 and cnt_target == 2 and cnt_corss == 0 and finsh_flag == 0:
                    #print("go platform2")
                    #bot.set_motor(80,80,80,80)                    
                    #low_platform(2) 
                    # t_angle = return_angle() - 40
                    #flag_platform1 = 1
                    #speed_gear = 7
                    #finsh_flag = 1                

                #if cnt_target == 2 and cnt_corss == 1 and time.time() - mountain_time > 2 and finsh_flag == 0:
                    #go_t_mountain()
                    #print("down t mountain")
                    #finsh_flag = 1
                    #speed_gear = 1
                if pitch > 5 and cnt_target == 1 and cnt_corss == 1:
                    speed_gear = 4
  
                if pitch > 5 and cnt_target == 3 and cnt_corss == 0 and finsh_flag == 0:
                    print("3")
                    low_platform(3)
                    print("go platform3")
                    cnt_target += 1
                    cnt_corss = 0
                    start_rush_time = time.time()
                if cnt_target == 4 and cnt_corss == 0 and left_front == 1 and right_front == 1 and left_middle == 1 and right_middle == 1 and time.time() - start_rush_time > 1: #finsh
                    print("40 sensor")
                    process_speed_longroad_new(60)
                    finsh_flag = 1
                    flag_all =0
                if cnt_target == 4 and cnt_corss == 9 and time.time() - start_rush_time > 0.4 and left_front == 1 and right_front == 1 :#finsh
                    print("49 sensor")
                    process_speed_longroad_new(50)
                    finsh_flag = 1
                    flag_all =0
                if cnt_target == 5 and cnt_corss == 0 and time.time() - start_rush_time > 0.6 and left_front == 1 and right_front == 1 and left_middle == 1 and right_middle == 1 :#finsh
                    print("50 sensor")
                    process_speed_longroad_new_50(60)
                    finsh_flag = 1
                    flag_all =0
                if cnt_target == 4 and cnt_corss == 10 and time.time() - start_rush_time > 0.6 and left_front == 1 and right_front == 1 and left_middle == 1 and right_middle == 1:#finsh
                    print("410 sensor")
                    process_speed_longroad_new_410(60)
                    finsh_flag = 1
                    flag_all =0


                if pitch > 5 and cnt_target == 7 and cnt_corss == 10 and finsh_flag == 0 and (road_select == 1  or road_select == 4 or road_select == 5):
                    print("0")
                    low_platform(0)
                    print("go platform0")
                    finsh_flag = 1
                    cnt_target += 1
                    cnt_corss = 0
                if pitch > 5 and cnt_target == 7 and cnt_corss == 10 and finsh_flag == 0 and (road_select == 2 or road_select == 3):
                    print("3")
                    low_platform(3)
                    print("go platform3")
                    finsh_flag = 1
                    speed_gear = 7
                    cnt_target += 1
                    cnt_corss = 0
                    #start_rush_time = time.time()

                #if cnt_target == 3 and cnt_corss == 0 and time.time() - start_rush_time > 1 and finsh_flag == 0:
                    #print("rush")
                    #process_speed_longroad(60,"pitch > 5")
                    #low_platform(4)
                    #cnt_target += 1
                    #cnt_corss = -1
                    #print("go platform4")
                    #finsh_flag = 1

                if pitch > 5 and cnt_target == 6 and cnt_corss == 0  and (left_middle == 0 and right_middle == 0 or time.time() - mountain_time > 3) and finsh_flag == 0 and mountain_flag == 1:   #finsh_flag=0 
                    angle_standard = go_t_mountain()
                    start_rush_time = time.time()
                    mountain_flag = 0 
                    print("down t mountain")
                    speed_gear = 1
                    finsh_flag = 0
                if middle_platform_flag==1 and cnt_target == 6 and cnt_corss == 0:
                    
                    bot.set_car_motion(0,0,0)
                    
                    time.sleep(5)
                    middle_platform()
                    print("down mid_platform")
                    turn_cross(180,-1)
                    finsh_flag = 1
                    speed_gear = 4
                
               
                if pitch > 5 and cnt_target == 6 and cnt_corss == 1 and finsh_flag == 0 :
                    angle_standard = go_t_mountain()
                    print("down t mountain")
                    finsh_flag = 1
                    speed_gear = 3
                if pitch > 5 and cnt_target == 6 and cnt_corss == 2 and finsh_flag == 0:
                    high_platform()
                    print("down high_platform")
                    finsh_flag = 1
                    speed_gear = 4
                if cnt_target == 6 and cnt_corss == 0 and finsh_flag == 0 and time.time() - start_rush_time > 1.5 and left_front == 1 and right_front == 1 and left_middle == 1 and right_middle == 1 :
                    finsh_flag = 0
                    slow_speed(50, "time.time() - start_time > 5")
                if cnt_target == 6 and cnt_corss == 0 and finsh_flag == 0 and time.time() - start_rush_time > 6:
                    print("time")
                    middle_platform_flag = 1
                    speed_gear = 1
                


                end = time.time()
                #print("timepro", end - start)
                fps = 1 / (end - start)
                text = "FPS : " + str(int(fps))
                cv.putText(frame1, text, (30, 30), cv.FONT_HERSHEY_SIMPLEX, 0.6, (100, 200, 200), 1)
                cv.imshow('frame',binary)
                cv.imshow('frame2', frame1)
                if action == ord('q') or action == 113: 
                    line_detect.break_flag = 1
                    camera_flag = 0
                    break
                this_time = time.time()
            if this_time-last_time > 1:
                clock_flag = 1
                last_time = time.time()
            else: clock_flag = 0
            print("clock",clock_flag)
            print("finish",finsh_flag)
            if clock_flag and finsh_flag:
                cnt_corss += 1
                #if cnt_target == 1 and cnt_corss == 1:
                #    threading.Thread(target = line_detect.change_flag1).start()
                #else:
                last_time = time.time()
            if(line_detect.break_flag == 1):
                break
            if cnt_target == 1 and cnt_corss == 1 and clock_flag:                
                print(1,1)
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0,0,0)
                turn_cross(35,1)
                #finsh_flag = 0
                #¨¨?1?1y???¨´¡ä?¨®D¡Á¡§??o¡¥¨ºy
                #1y???¨´¡ä?
            elif cnt_target == 1 and cnt_corss == 2 and clock_flag and finsh_flag:
                print(1,2)
                speed_gear = 3
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0,0,0)
                turn_cross(20,-1)
            elif cnt_target == 1 and cnt_corss == 3 and clock_flag and finsh_flag:
                print(1,3)
                clock_flag = 0
                flag_all = 1
                finsh_flag = 0
                cnt_target = 3
                cnt_corss = 0                
                # time.sleep(1)

            elif cnt_target == 4 and cnt_corss == 1 and clock_flag:
                speed_gear = 1
                clock_flag = 0
                flag_all = 1
                print(4,1)
                bot.set_car_motion(0, 0, 0)
                time.sleep(0.3)
                turn_cross(40, -1)

            elif cnt_target == 4 and cnt_corss == 2 and clock_flag:
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0,0,0)
                print(4,2)
                color_num = color_recognition()
                print("color_num",color_num)
                #time.sleep(1)
                if color_num == 2:
                    print("road_select:2")
                    speed_gear = 3
                    road_select = 2
                    cnt_corss = 9
                    start_rush_time = time.time()
                else: 
                    process_speed_back(-30)
                    cnt_corss += 1
                    turn_cross(40, -1)
                    print(4,3)
            elif cnt_target == 4 and cnt_corss == 4 and clock_flag:
                print(4,4)
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0, 0, 0)
                color_num = color_recognition()
                if color_num == 1:
                    print("road_select:1")
                    speed_gear = 3
                    road_select = 1
                    cnt_corss = 8

                else:
                    speed_gear = 3
                    process_speed_back(-30)
                    cnt_corss += 1
                    turn_cross(90,1)
                    print(4,5)
            elif cnt_target == 4 and cnt_corss == 6 and clock_flag:
                print(4,6)
                clock_flag = 0
                flag_all = 1
            elif cnt_target == 4 and cnt_corss == 7 and clock_flag:
                print(4,7)
                speed_gear = 1
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0,0,0)
                turn_cross(90,-1)
            elif cnt_target == 4 and cnt_corss == 8 and clock_flag:
                speed_gear = 1
                print(4, 8)
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0,0,0)
                color_num = color_recognition()
                if color_num == 1:
                    print("road_select:4")
                    road_select = 4
                    cnt_corss = 11
                    speed_gear = 3
                elif color_num == 0:
                    print("road_select:5")
                    road_select = 5
                    cnt_corss = 11
                    speed_gear = 3
                else:
                    print("road_select:3")
                    road_select = 3
                    cnt_corss = 13
                    process_speed_back(-30)
                    speed_gear = 3
                    turn_cross(45,-1)

            elif cnt_target == 4 and cnt_corss == 9 and clock_flag:
                print(4,9)
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0,0,0)
                turn_cross(90,-1)
                cnt_target += 1
                cnt_corss = 0
                start_rush_time = time.time()


            elif cnt_target == 4 and cnt_corss == 10 and clock_flag:
                print(4,10)
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0,0,0)
                time.sleep(0.1)
                turn_cross(120,-1)
                start_rush_time = time.time()
            elif cnt_target == 4 and cnt_corss == 11 and clock_flag:
                print(4,11)
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0,0,0)
                time.sleep(0.2)
                turn_cross(45,-1)
                cnt_target += 1
                cnt_corss = 0
                start_rush_time = time.time()

            elif cnt_target == 4 and cnt_corss == 12 and clock_flag:
                print(4,12)
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0, 0, 0)
                time.sleep(0.2)
                turn_cross(90, 1)
            elif cnt_target == 4 and cnt_corss == 13 and clock_flag:
                clock_flag = 0
                flag_all = 1
                print(4, 13)
                #ÐèÒª¹ý5ºÅµãÎ»
            elif cnt_target == 4 and cnt_corss == 14 and clock_flag:
                clock_flag = 0
                flag_all = 1
                print(4, 14)
            elif cnt_target == 4 and cnt_corss == 15 and clock_flag:
                clock_flag = 0
                flag_all = 1
                print(4, 15)
                bot.set_car_motion(0, 0, 0)
                time.sleep(0.2)
                turn_cross(90, 1)
            elif cnt_target == 4 and cnt_corss == 16 and clock_flag:
                clock_flag = 0
                flag_all = 1
                print(4, 16)
                bot.set_car_motion(0, 0, 0)
                time.sleep(0.2)
                turn_cross(90, -1)
                #Ö±Á¢ÐÍ¾°µã
            elif cnt_target == 4 and cnt_corss == 17 and clock_flag:
                clock_flag = 0
                flag_all = 1
                print(4, 17)
                bot.set_car_motion(0, 0, 0)
                time.sleep(0.2)
                turn_cross(90, -1)
            elif cnt_target == 4 and cnt_corss == 18 and clock_flag:
                clock_flag = 0
                flag_all = 1
                print(4, 18)
                bot.set_car_motion(0, 0, 0)
                time.sleep(0.2)
                turn_cross(90, -1)
            elif cnt_target == 4 and cnt_corss == 19 and clock_flag:
                clock_flag = 0
                flag_all = 1
                print(4, 19)
                bot.set_car_motion(0, 0, 0)
                time.sleep(0.2)
                turn_cross(90, 1)
                # Ö±Á¢ÐÍ¾°µã
            elif cnt_target == 4 and cnt_corss == 20 and clock_flag:
                clock_flag = 0
                flag_all = 1
                print(4, 20)
                bot.set_car_motion(0, 0, 0)
                time.sleep(0.2)
                turn_cross(90, 1)
                cnt_target = 5
                cnt_corss = 0
                start_rush_time = time.time()
            elif cnt_target == 4 and cnt_corss == 21 and clock_flag:
                print(4,21)
                clock_flag = 0
                flag_all = 1
            elif cnt_target == 4 and cnt_corss == 22 and clock_flag:
                print(4,22)
                clock_flag = 0
                flag_all = 1
            elif cnt_target == 4 and cnt_corss == 23 and clock_flag:
                print(4,23)
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0,0,0)
                turn_cross(45,-1)
                cnt_target = 5
                cnt_corss = 0
                start_rush_time = time.time()
                #1y???¨´¡ä?*2
            elif cnt_target == 5 and cnt_corss == 1 and clock_flag:
                print(5,1)
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0, 0, 0)
                time.sleep(0.2)
                turn_cross(90, 1)
            elif cnt_target == 5 and cnt_corss == 2 and clock_flag:
                print(5,2)
                clock_flag = 0
                flag_all = 1
                #Ö±Á¢ÐÍ¾°µã
                #bot.set_car_motion(0, 0, 0)
                #time.sleep(0.2)
                #turn_cross(90, 1)
                #time.sleep(0.5)
                #process_speed_back(-40)
                #turn_cross(90,-1)
            elif cnt_target == 5 and cnt_corss == 3 and clock_flag:
                print(5, 3)
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0, 0, 0)
                time.sleep(0.2)
                turn_cross(90, 1)

            elif cnt_target == 5 and cnt_corss == 4 and clock_flag:
                print(5, 4)
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0, 0, 0)
                time.sleep(0.2)
                turn_cross(90, 1)

            elif cnt_target == 5 and cnt_corss == 5 and clock_flag:
                print(5,5)
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0, 0, 0)
                time.sleep(0.2)
                turn_cross(120, -1)

            elif cnt_target == 5 and cnt_corss == 6 and clock_flag and finsh_flag:
                print(5, 6)
                finsh_flag = 0
                clock_flag = 0
                flag_all = 1
                cnt_corss = 0
                cnt_target += 1
                bot.set_car_motion(0, 0, 0)
                turn_cross(150, -1)
                speed_gear = 1
                #¸ßÆ½Ì¨
                #1y¨¬YD?¨¦?

            elif cnt_target == 6 and cnt_corss == 1 and clock_flag:
                print(6, 1)
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0, 0, 0)
                time.sleep(0.2)
                turn_cross(120, 1)
                speed_gear = 3
                #1y¨¬YD?¨¦?

            elif cnt_target == 6 and cnt_corss == 2 and clock_flag:
                print(6, 2)
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0, 0, 0)
                time.sleep(0.2)
                turn_cross(90, -1)
                speed_gear = 3
                #¨¦???,?¡À?¨®¦Ì13¦Ì¦Ì??¡¤?¨²¡ê?¡Áa¨ª?
            elif cnt_target == 6 and cnt_corss == 3 and clock_flag:
                print(6, 3)
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0, 0, 0)
                turn_cross(90,-1)

            elif cnt_target == 6 and cnt_corss == 4 and clock_flag:
                print(6,4)
                clock_flag = 0
                flag_all = 1
                speed_gear = 1

            elif cnt_target == 6 and cnt_corss == 5 and clock_flag:
                print(7,3)
                speed_gear = 3
                clock_flag = 0
                flag_all = 1
                cnt_target = 7
                cnt_corss = 0
                bot.set_car_motion(0, 0, 0)
                turn_cross(90, -1)

            elif road_select == 1:
                if cnt_target == 7 and cnt_corss == 1 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(90, -1)
                    speed_gear = 1

                elif cnt_target == 7 and cnt_corss == 2 and clock_flag:
                    print(7,2)
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(90, -1)
                    stand_scene()
                    turn_cross(90, 1)
                elif cnt_target == 7 and cnt_corss == 3 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(90, 1)
                    speed_gear = 3
                elif cnt_target == 7 and cnt_corss == 4 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(90, 1)
                    stand_scene()
                    turn_cross(90, -1)
                    speed_gear = 1
                elif cnt_target == 7 and cnt_corss == 5 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(90, -1)
                    speed_gear = 3
                    #ÎåºÅ
                elif cnt_target == 7 and cnt_corss == 6 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                elif cnt_target == 7 and cnt_corss == 7 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                elif cnt_target == 7 and cnt_corss == 8 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(50, -1)
                    speed_gear = 3
                elif cnt_target == 7 and cnt_corss == 9 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(110, 1)
                    speed_gear = 3
                elif cnt_target == 7 and cnt_corss == 10 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(135, -1)
                    speed_gear = 3
                elif cnt_target == 7 and cnt_corss == 11 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                elif cnt_target == 7 and cnt_corss == 12 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(90, -1)
                    speed_gear = 3
                elif cnt_target == 7 and cnt_corss == 13 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(40, 1)
                    speed_gear = 4
                elif cnt_target == 7 and cnt_corss == 14 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(40, -1)
                    speed_gear = 3
                    #ÆðÊ¼Æ½Ì¨
            elif road_select == 2:
                if cnt_target == 7 and cnt_corss == 1 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(90, -1)
                    speed_gear = 1

                elif cnt_target == 7 and cnt_corss == 2 and clock_flag:
                    print(7,2)
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(90, -1)
                    stand_scene()
                    turn_cross(90, 1)
                elif cnt_target == 7 and cnt_corss == 3 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(90, 1)
                    speed_gear = 3
                elif cnt_target == 7 and cnt_corss == 4 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(90, 1)
                    stand_scene()
                    turn_cross(90, -1)
                    speed_gear = 1
                elif cnt_target == 7 and cnt_corss == 5 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(90, -1)
                    speed_gear = 3
                    #ÎåºÅ
                elif cnt_target == 7 and cnt_corss == 6 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                elif cnt_target == 7 and cnt_corss == 7 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                elif cnt_target == 7 and cnt_corss == 8 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(50, -1)
                    speed_gear = 3
                elif cnt_target == 7 and cnt_corss == 9 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                elif cnt_target == 7 and cnt_corss == 10 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                elif cnt_target == 7 and cnt_corss == 11 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(130, -1)
                    speed_gear = 3
                elif cnt_target == 7 and cnt_corss == 12 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(40, 1)
                    speed_gear = 4
                elif cnt_target == 7 and cnt_corss == 13 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(40, -1)
                    speed_gear = 3
                    # ÆðÊ¼Æ½Ì¨
            elif road_select == 3:
                if cnt_target == 7 and cnt_corss == 1 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(90, -1)
                    speed_gear = 1

                elif cnt_target == 7 and cnt_corss == 2 and clock_flag:
                    print(7,2)
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(90, -1)
                    stand_scene()
                    turn_cross(90, 1)
                elif cnt_target == 7 and cnt_corss == 3 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(90, 1)
                    speed_gear = 3
                elif cnt_target == 7 and cnt_corss == 4 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(90, 1)
                    stand_scene()
                    turn_cross(90, -1)
                    speed_gear = 1
                elif cnt_target == 7 and cnt_corss == 5 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(90, -1)
                    speed_gear = 3
                    #ÎåºÅ
                elif cnt_target == 7 and cnt_corss == 6 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                elif cnt_target == 7 and cnt_corss == 7 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                elif cnt_target == 7 and cnt_corss == 8 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(50, -1)
                    speed_gear = 3
                elif cnt_target == 7 and cnt_corss == 9 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(110, -1)
                elif cnt_target == 7 and cnt_corss == 10 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                elif cnt_target == 7 and cnt_corss == 11 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(130, 1)
                elif cnt_target == 7 and cnt_corss == 12 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(130, -1)
                    speed_gear = 4
                elif cnt_target == 7 and cnt_corss == 13 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(40, -1)
                    speed_gear = 4
                    #ÆðÊ¼
            elif road_select == 4:
                if cnt_target == 7 and cnt_corss == 1 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(45, 1)
                    speed_gear = 1
                elif cnt_target == 7 and cnt_corss == 2 and clock_flag:
                    print(7,2)
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(80, -1)
                elif cnt_target == 7 and cnt_corss == 3 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(130, 1)
                    speed_gear = 3
                elif cnt_target == 7 and cnt_corss == 4 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                elif cnt_target == 7 and cnt_corss == 5 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(90, 1)
                elif cnt_target == 7 and cnt_corss == 6 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(130, -1)
                    speed_gear = 4
                elif cnt_target == 7 and cnt_corss == 7 and clock_flag:
                    clock_flag = 0
                    flag_all = 1
                    bot.set_car_motion(0, 0, 0)
                    time.sleep(0.2)
                    turn_cross(40, -1)
                    speed_gear = 4
                    #ÆðÊ¼
            else : flag_all = 1
            
        #print(3)




