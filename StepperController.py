
import RPi.GPIO as GPIO
from RpiMotorLib import RpiMotorLib

#define GPIO pins

NUM_STEPS_IN_CIRCLE = 200

class StepperController:
    
    def __init__(self):
        self.tot_steps = NUM_STEPS_IN_CIRCLE
        with open('curr_step.txt','r') as f:
            self.curr_step = int(f.readline())
        self.step_file = open('curr_step.txt','w')
        self.curr_angle = self._step2angle(self.curr_step)
        GPIO_pins = (14, 15, 18) # Microstep Resolution MS1-MS3 -> GPIO Pin
        direction= 20       # Direction -> GPIO Pin
        step = 21      # Step -> GPIO Pin
        self.mymotortest = RpiMotorLib.A4988Nema(direction, step, GPIO_pins, "A4988")

    def goto_angle(self, angle):
        angle = int(angle)
        desired_step = self._angle2step(angle)
        dist_step = (desired_step - self.curr_step)  
        print(dist_step)
        if angle - self.curr_angle  <= 180 and angle >= self.curr_angle or \
            angle - self.curr_angle <= -180 and angle <= self.curr_angle:
            #clockwise
            to_turn = dist_step % self.tot_steps
            print(to_turn)
            print('clockwise')
            self._step(True,to_turn)
        else:
            to_turn = -dist_step % self.tot_steps
            print(to_turn)
            self._step(False,to_turn)
        self.curr_step = desired_step
        self.curr_angle = self._step2angle(desired_step)
        print('writing')
        self.step_file.write(f'{self.curr_step}')


    def _step(self,clockwise=True,num_steps=0):
        self.mymotortest.motor_go(clockwise, "Full" , num_steps, 0.004, False, .05)

    def _angle2step(self,angle):
        return int(angle*self.tot_steps/360)

    def _step2angle(self,step):
        return step*360/self.tot_steps
    
    def get_source_angle(self, vol1,vol2,vol3):
        print('in get source angle')
        #vol 1 is at 0 degrees
        #vol 2 is at 120 degrees
        #vol 3 is at 240 degrees
        vols = [vol1,vol2,vol3]
        vols.sort()
        print('sorted')
        vol1 -= vols[0]
        vol2 -= vols[0]
        vol3 -= vols[0]
        min = vols[0]
        for i in range(len(vols)):
            vols[i] -= min
        vols[2] += 1
        to_add = 120 - vols[1]/(vols[2] + vols[1]) * 120
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
    s.goto_angle(290)
    s.close()



        
    