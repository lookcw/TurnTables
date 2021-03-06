
import RPi.GPIO as GPIO
from RpiMotorLib import RpiMotorLib

#define GPIO pins


class StepperController:
    
    def __init__(self):
        with open('curr_step.txt','r') as f:
            self.curr_step = int(f.readline())
             
        self.step_file = open('curr_step.txt','w')
        self._set_angle(self.curr_step)
        GPIO_pins = (14, 15, 18) # Microstep Resolution MS1-MS3 -> GPIO Pin
        direction= 20       # Direction -> GPIO Pin
        step = 21      # Step -> GPIO Pin
        self.mymotortest = RpiMotorLib.A4988Nema(direction, step, GPIO_pins, "A4988")

    def goto_angle(self, angle):
        desired_step = self._angle2step(angle)
        if angle - self.curr_angle  <= 180 and angle >= self.curr_angle or \
            angle - self.curr_angle <= -180 and angle <= self.curr_angle:
            #clockwise
            print(self.curr_step)
            num_steps = (desired_step - self.curr_step) % 200
            self._step(True,num_steps)
        else:
            num_steps = (desired_step - self.curr_step - 100) % 200
            self._step(False,num_steps)
        self.curr_step = desired_step
        self._set_angle(self.curr_step)
        
        print(self.curr_angle)
        print(self.curr_step)
        self._record_step()

    
    def _record_step(self):
        self.step_file.write(str(self.curr_step))


    def _step(self,clockwise=True,num_steps=0):
        print(f'stepping {num_steps} steps')
        self.mymotortest.motor_go(clockwise, "Full" , int(num_steps), 0.004, False, .05)

    def _angle2step(self,angle):
        return int(angle*200/360)

    def _set_angle(self,step):
        self.curr_angle = step*360/200
    
    def get_source_angle(self, vol1,vol2,vol3):
        src = -1
        #vol 1 is at 0 degrees
        #vol 2 is at 120 degrees
        #vol 3 is at 240 degrees
        vols = [vol1,vol2,vol3]
        vols.sort()
        vol1 -= vols[0]
        vol2 -= vols[0]
        vol3 -= vols[0]
        min = vols[0]
        for i in range(len(vols)):
            vols[i] -= min

        to_add = 120 - vols[1]/(vols[2] + vols[1]) * 120
        print(to_add)
        if vols[1] == vol1:
            if vol3 > vol2:
                to_add = -to_add
            src = 0 + to_add
        elif vols[1] == vol2:
            if vol3 < vol1:
                to_add = -to_add
            src = 120 + to_add
        else:
            if vol2 > vol1:
                to_add = -to_add
            src = 240 + to_add
        return src % 360

    def close(self):
        self.step_file.close()

if __name__ == "__main__":
    s = StepperController()
    print(s.get_source_angle(10,10,20))
    s.goto_angle(90)
    s.close()



        
    