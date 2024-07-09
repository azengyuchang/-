
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
from go_straight import process_speed
from Rosmaster_Lib import Rosmaster
from follow_common import *
from long_bridge import *
from go_platform import *
# RED: 0, 85, 126, 9, 253, 255
RAD2DEG = 180 / math.pi
bot = Rosmaster()

bot.clear_auto_report_data()
bot.reset_flash_value()
bot.create_receive_threading()
enable = True
bot.set_auto_report_state(enable, forever=False)

flag_tracking = 0

total_ret = ""
total_frame =""
camera_flag = 1
pitch_info = 0.0
clock_flag = 1
sensor_flag_old = 1
sensor_res = 2
change_clock_flag = 0
start_change_flag = 0
finsh_flag = 1

prev_error_m1 = 0
prev_error_m2 = 0
prev_error_m3 = 0
prev_error_m4 = 0
integral_m1 = 0.0
integral_m2 = 0.0
integral_m3 = 0.0
integral_m4 = 0.0
start_vertical_time = 0
speed_gear = 4

alpha = 0.8
beta = 10

motor_1=motor_2=motor_3=motor_4= 0
#flag = 0
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
        pitch = return_pitch()

        global motor_1
        global motor_2
        global motor_3 
        global motor_4
        is_common = [1,1,1,1,1]
        #self.rgb_open()
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
           # if flag_tracking == 1:
           #     start_platform()
           #     flag_tracking = 0
                #speed_gear == 1            
            #print("4",time.time()-t1)
            if cnt_target == 1 and cnt_corss == 9:
                is_common ,motor_1,motor_2,motor_3,motor_4  = self.abs_protect(motor_1,motor_2,motor_3,motor_4)
                if is_common[0]==0:
                    motor_strength=[0,80,80,80,80]
                    for i in range(1,5):
                        if is_common[i] == 0:
                            motor_strength[i] = 100
                    bot.set_motor(motor_strength[1],motor_strength[2],100,100)
                    time.sleep(0.3)
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
        #print("SB")
        print(Center_x)
        if speed_gear == 1:
            front_Kp = 0.8  # 前轮
            front_Ki = 0  # 前轮
            front_Kd = 0.3  # 前轮
            rear_Kp = 0.8  # 后轮
            rear_Ki = 0  # 后轮
            rear_Kd = 0.3  # 后轮
            k = 1  #灵敏度
            v_motor = 30    #基本速度
            v_threshold = 50  #阈值

        elif speed_gear == 2:
            front_Kp = 0.8  # 前轮
            front_Ki = 0  # 前轮
            front_Kd = 1  # 前轮
            rear_Kp = 0.8  # 后轮
            rear_Ki = 0  # 后轮
            rear_Kd = 1  # 后轮
            k = 0.6  #灵敏度
            v_motor = 60    #基本速度
            v_threshold = 40  #阈值

        elif speed_gear == 3:
            front_Kp = 0.8  # 前轮
            front_Ki = 0  # 前轮
            front_Kd = 5  # 前轮
            rear_Kp = 0.8  # 后轮
            rear_Ki = 0  # 后轮
            rear_Kd = 5 # 后轮
            k = 0.4  #灵敏度
            v_motor = 60   #基本速度
            v_threshold = 30  #阈值

        elif speed_gear == 4:  # 减速带
            front_Kp = 0.9  # 前轮
            front_Ki = 0.04  # 前轮
            front_Kd = 0.6  # 前轮
            rear_Kp = 0.9  # 后轮
            rear_Ki = 0.01  # 后轮
            rear_Kd = 0.6  # 后轮
            k = 0.4  #灵敏度
            v_motor = 55    #基本速度
            v_threshold = 40  #阈值

        elif speed_gear == 5:  # 弯道
            front_Kp = 0.8  # 前轮
            front_Ki = 0  # 前轮
            front_Kd = 0.3  # 前轮
            rear_Kp = 0.8  # 后轮
            rear_Ki = 0  # 后轮
            rear_Kd = 0.3  # 后轮
            k = 1  #灵敏度
            v_motor = 35    #基本速度
            v_threshold = 50  #阈值

        if speed_gear == 6: #在这个档位上面调整下坡PID 直接跑这个文件的逻辑 从平台先盲走 pitch改变后 进入这个档位的巡直线 要稳定寻到第坡下的第1个路口 然后进入后面的逻辑 初始化档位改为6挡 速度10～20 看情况调整 最重要的是稳 不要动adjust_speed里面的参数 修改完的参数记得改回去 谁改的参数谁负责 最好写一个日志 方便后面对接 不懂的逻辑直接问我们
            front_Kp = 0.8  # 前轮
            front_Ki = 0  # 前轮
            front_Kd = 0.3  # 前轮
            rear_Kp = 0.8  # 后轮
            rear_Ki = 0  # 后轮
            rear_Kd = 0.3  # 后轮
            k = 1  #灵敏度
            v_motor = 20    #基本速度
            v_threshold = 30  #阈值

        if speed_gear == 7:
            front_Kp = 0.8  # 前轮
            front_Ki = 0  # 前轮
            front_Kd = 0.6  # 前轮
            rear_Kp = 0.8  # 后轮
            rear_Ki = 0  # 后轮
            rear_Kd = 0.6  # 后轮
            k = 1  #灵敏度
            v_motor = 30    #基本速度
            v_threshold = 35  #阈值
    
        elif speed_gear == 8:  # 梯形山
            front_Kp = 0.9  # 前轮
            front_Ki = 0  # 前轮
            front_Kd = 3  # 前轮
            rear_Kp = 0.9  # 后轮
            rear_Ki = 0  # 后轮
            rear_Kd = 3  # 后轮
            k = 0.3  #灵敏度
            v_motor = 35    #基本速度
            v_threshold = 40  #阈值
        

        elif speed_gear == 9:  # 梯形山
            front_Kp = 0.8  # 前轮
            front_Ki = 0  # 前轮
            front_Kd = 0.3  # 前轮
            rear_Kp = 0.8  # 后轮
            rear_Ki = 0  # 后轮
            rear_Kd = 0.3  # 后轮
            k = 1.5  #灵敏度
            v_motor = 55    #基本速度
            v_threshold = 30  #阈值


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
        print("output",rear_output,front_output)
        self.front_prev_error = front_error
        self.rear_prev_error = rear_error


    def t_mountain(self):
        success_flag = 0
        error_a = 0
        last_error_a = 0
        acc_error_a = 0
        p_m = 2
        i_m = 0.06
        p_b = 2
        i_b = 0.06
        pwm_a = 0
        pwm_b = 0
        pwm_c = 0	
        pwm_d = 0
        set_speed = 90	
        a1 = set_speed
        b1 = set_speed
        c1 = set_speed
        d1 = set_speed
        bot.set_motor(set_speed,set_speed,set_speed,set_speed)
        target_angle = return_angle()
        count = 0
        while (1):        
            pitch = return_pitch()
            if pitch > 20:
                success_flag = 1        
            now_angle = return_angle()     
            error_a = target_angle - now_angle
            if (-180 < error_a < 180):
                error_b = target_angle - now_angle
                acc_error_a = acc_error_a + error_b
                pwm_a = p_b*error_b  + i_b*acc_error_a
                pwm_b = p_b*error_b  + i_b*acc_error_a
                pwm_c = p_m*error_b  + i_m*acc_error_a
                pwm_d = p_m*error_b  + i_m*acc_error_a
                bot.set_motor(a1-pwm_a,b1-pwm_b,c1+pwm_c,d1+pwm_d)
                print("1",a1-pwm_a,"2",b1-pwm_b+40,"3",c1+pwm_c,"4",d1+pwm_d+40)
            if (error_a > 180):
                error_c = target_angle - now_angle - 360
                acc_error_a = acc_error_a + error_c
                pwm_a = p_b*error_c  + i_b*acc_error_a
                pwm_b = p_b*error_c  + i_b*acc_error_a
                pwm_c = p_m*error_c  + i_m*acc_error_a
                pwm_d = p_m*error_c  + i_m*acc_error_a
                bot.set_motor(a1-pwm_a,b1-pwm_b,c1+pwm_c,d1+pwm_d)
                print("1",a1-pwm_a,"2",b1-pwm_b+40,"3",c1+pwm_c,"4",d1+pwm_d+40)
            if (error_a < -180):
                error_d = target_angle - now_angle + 360
                acc_error_a = acc_error_a + error_d
                pwm_a = p_b*error_d  + i_b*acc_error_a
                pwm_b = p_b*error_d  + i_b*acc_error_a
                pwm_c = p_m*error_d  + i_m*acc_error_a
                pwm_d = p_m*error_d  + i_m*acc_error_a
                bot.set_motor(a1-pwm_a,b1-pwm_b,c1+pwm_c,d1+pwm_d)
                print("1",a1-pwm_a,"2",b1-pwm_b+40,"3",c1+pwm_c,"4",d1+pwm_d+40)

            print(pwm_a,pwm_b,pwm_c,pwm_d)
            while pitch > 40:
                pitch = return_pitch()
                bot.set_motor(0,0,0,0)

            #if pitch < 3 and success_flag == 1:
             #   bot.set_motor(0,0,0,0)
              #  break
            if pitch < -5:
                count = 1

            if -5 < pitch < 5 and count == 1:
                bot.set_car_motion(0,0,0)
                correct_angle(target_angle)
                break
        

        #process_speed(5,"-5 < pitch < 3")
        

    def adapt_light(self,capture,state):#白天状态为1 晚上状态为0
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

    def getting_pitch(self):
        global pitch_info
        while 1:    
            pitch_info = return_pitch()

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
    def abs_protect(self , past_motor_1,past_motor_2,past_motor_3,past_motor_4):
        is_common = [1,1,1,1,1]
        motor_1,motor_2,motor_3,motor_4= bot.get_motor_encoder()
        thresold = 25
        print("1:    ",motor_1 - past_motor_1,"2:    ",motor_2 - past_motor_2,"3:    ",motor_3 - past_motor_3,"4:    ",motor_4 - past_motor_4)
        #if motor_1 - past_motor_1 > thresold and motor_2 - past_motor_2 > thresold and motor_3 - past_motor_3 > thresold and motor_4 - past_motor_4 > thresold :
        #    print("__________________________________common________________________________________")
        #else:
         #   print("===============rush================")
        if motor_1 - past_motor_1 < thresold :
            is_common[1] = 0
            is_common[0] = 0
        if motor_2 - past_motor_2 <thresold:
            is_common[2] = 0
            is_common[0] = 0
        if motor_3 - past_motor_3 <thresold:
            is_common[3] = 0
            is_common[0] = 0
        if motor_4 - past_motor_4 <thresold:
            is_common[4] = 0
            is_common[0] = 0
        return is_common,motor_1,motor_2,motor_3,motor_4
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
    cnt_corss = 0
    cnt_target = 1 
    road_select = 0
    this_time = time.time()
    last_time = time.time() 
    line_detect = LineDetect()
    gear =9
    #i = 0
    #for i in range(100):
        #bot.set_colorful_lamps(i,0,0,0)
        #bot.set_colorful_lamps(i,255,255,255)
    #for i in range(0,100):
        #bot.set_colorful_lamps(i,255,255,255)
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
        pitch_correction()#具体放那里还需要讨论
        time.sleep(6)
        cnt_jpg = 0
        print("gogogo")
        #flag_bridge = 0
        #flag_platform1 = 0
        #flag_tmountain = 0
        while line_detect.VideoSwitch==True :
            
            while flag_all !=0: 
                cnt_jpg += 1
                cnt_name = str(cnt_jpg)
                jpg_name = "./photo1/" + cnt_name+".jpg"                              
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
                #print("main",pitch) 
                end = time.time()
                #print("timepro", end - start)
                fps = 1 / (end - start)
                text = "FPS : " + str(pitch)
                cv.putText(frame1, text, (30, 30), cv.FONT_HERSHEY_SIMPLEX, 0.6, (100, 200, 200), 1)
                cv.imshow('frame',binary)
                cv.imshow('frame2', frame1)
                cv.imwrite(jpg_name,frame1)
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
            if cnt_target == 1 and cnt_corss == 1:                
                print(1,1)
                clock_flag = 0
                flag_all = 1
                speed_gear = gear
                #bot.set_motor(25,25,40,40)                
                #cross_bridge()
                #bot.set_car_motion(0,0,0)

                #time.sleep(5)                
                continue
            elif cnt_target == 1 and cnt_corss == 2 and clock_flag:
                clock_flag = 0
                print(1, 2)
                flag_all = 1
                speed_gear = gear
                #low_platform(2)
                #bot.set_motor(59,69,61,71)
                #time.sleep(0.7)
                #bot.set_car_motion(0,0,0)
                #turn_cross(170,1)
                #bot.set_motor(59,69,61,71)
                #time.sleep(5)
                #line_detect.low_platform()
                #low_platform()
                cnt_corss += 1
            elif cnt_target == 1 and cnt_corss == 3 and clock_flag:
                clock_flag = 0
                print(1, 3)
                speed_gear = gear
                flag_all = 1 
                cnt_corss += 1               
                # time.sleep(1)
            elif cnt_target == 2 and cnt_corss == 2 and clock_flag:
                clock_flag = 0
                print(1, 4)
                flag_all = 1
                #bot.set_motor(59,69,61,71)
                #time.sleep(0.2)
                bot.set_car_motion(0,0,0)
                #time.sleep(1)
                #finsh_flag = 0
                time.sleep(10)
                speed_gear = 8
            elif cnt_target == 2 and cnt_corss == 3 and clock_flag:
                clock_flag = 0
                print(2, 3)
                flag_all = 1
                continue
            elif cnt_target == 2 and cnt_corss == 4 and clock_flag:
                clock_flag = 0
                print(2, 4)
                flag_all = 1
       		#×ó×ª45
                #bot.set_motor(59,69,61,71)
                #time.sleep(0.1)
                #time.sleep(2)
                #bot.set_motor(59,69,61,71)
                #time.sleep(0.8)                
                #turn_cross(180,1)    
                #time.sleep(1)
                bot.set_car_motion(0,0,0)
                turn_cross(40,1)
                start_vertical_time = time.time()
       		#µôÍ·180
          
            elif cnt_target == 2 and cnt_corss == 5 and clock_flag:
                clock_flag = 0
                print(2, 6)
                flag_all = 1
       		#×ó×ª135
                bot.set_car_motion(0,0,0)
                turn_cross(135,1) 
                speed_gear = 1
                cnt_target += 1
                cnt_corss = 0
                speed_gear = 1
                finsh_flag = 0

            elif cnt_target == 3 and cnt_corss ==1 and clock_flag:
                clock_flag = 0
                print(3, 1)
                flag_all = 1
                speed_gear = 3

            elif cnt_target == 3 and 1 < cnt_corss < 4 and clock_flag:
                clock_flag = 0
                print(3, cnt_corss)
                flag_all = 1
                
                #bot.set_car_motion(0,0,0)
                #turn_cross(130,-1)
                #time.sleep(1)
                continue
            elif cnt_target == 3 and cnt_corss == 4 and clock_flag:
                clock_flag = 0
                print(3, cnt_corss)
                flag_all = 1
                #low_platform(3)
                print("NB")
            elif cnt_target == 4 and cnt_corss == 1 and clock_flag:
                speed_gear = 1
                clock_flag = 0
                flag_all = 1
                print(4,1)
                bot.set_car_motion(0,0,0)
                turn_cross(35,-1)
            elif cnt_target == 4 and cnt_corss == 2 and clock_flag:
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0,0,0)
                print(4,2)
                color_num = color_recognition()
                print("color_num",color_num)
                #time.sleep(1)
                if color_num == 1:
                    road_select == 2
                    cnt_corss = 8
                else: turn_cross(180,1)
            elif cnt_target == 4 and cnt_corss == 3 and clock_flag:
                print(4,3)
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0,0,0)
                turn_cross(135,1)
            elif cnt_target == 4 and cnt_corss == 4 and clock_flag:
                print(4,4)
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0,0,0)
                color_num = color_recognition()
                if color_num == 1:
                    road_select == 1
                    cnt_corss = 10
                else: turn_cross(180,1)
            elif cnt_target == 4 and cnt_corss == 5 and clock_flag:
                print(4,5)
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0,0,0)
                turn_cross(90,-1)
            elif cnt_target == 4 and cnt_corss == 6 and clock_flag:
                print(4,6)
                clock_flag = 0
                flag_all = 1
            elif cnt_target == 4 and cnt_corss == 7 and clock_flag:
                print(4,7)
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0,0,0)
                turn_cross(90,-1)
            elif cnt_target == 4 and cnt_corss == 8 and clock_flag:
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0,0,0)
                color_num = color_recognition()
                if color_num == 1:
                    road_select == 4
                    cnt_corss = 11
                elif color_num == 0:
                    road_select == 5
                    cnt_corss = 11             
                else:
                    road_select == 3
                    cnt_corss = 12
                    turn_cross(180,1)
            elif cnt_target == 4 and cnt_corss == 9 and clock_flag:
                clock_flag = 0
                flag_all = 1
            elif cnt_target == 4 and cnt_corss == 10 and clock_flag:
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0,0,0)
                turn_cross(45,1)
                cnt_target += 1
                cnt_corss = 0
            elif cnt_target == 4 and cnt_corss == 11 and clock_flag:
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0,0,0)
                turn_cross(90,1)
                cnt_target += 1
                cnt_corss = 0
            elif cnt_target == 4 and cnt_corss == 12 and clock_flag:
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0,0,0)
                turn_cross(90,1)
                cnt_target += 1
                cnt_corss = 0
            elif cnt_target == 4 and cnt_corss == 13 and clock_flag:
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0,0,0)
                turn_cross(135,1)
            elif cnt_target == 4 and cnt_corss == 14 and clock_flag:
                clock_flag = 0
                flag_all = 1
            elif cnt_target == 4 and cnt_corss == 15 and clock_flag:
                clock_flag = 0
                flag_all = 1
            elif cnt_target == 4 and cnt_corss == 16 and clock_flag:
                clock_flag = 0
                flag_all = 1
                bot.set_car_motion(0,0,0)
                turn_cross(135,1)
                cnt_target += 1
                cnt_corss = 0
            else : flag_all = 1
            
        #print(3)
