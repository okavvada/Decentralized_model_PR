from __future__ import division
import math
water_density=1000 #kg/m3
gravity=9.8 #m/s2

def pipe_velocity(pipe_diameter, demand_m3_s):
	area=math.pi*(pipe_diameter*0.001/2)**2
	pipe_velocity=demand_m3_s/area
	return pipe_velocity

def headloss(pipe_diameter, pipe_length, demand_m3_s):
	headloss=0.03*pipe_length*(pipe_velocity(pipe_diameter, demand_m3_s)**2)/(2*pipe_diameter*0.001*9.81)
	return headloss

def total_head(pipe_diameter, demand_m3_s, pump_pressure, pipe_length):
	vel_pressure = (pipe_velocity(pipe_diameter, demand_m3_s)**2)*water_density/2
	cons_pressure = pump_pressure/10*101325
	headloss_pressure = headloss(pipe_diameter, pipe_length, demand_m3_s)*gravity*water_density
	total_head = (vel_pressure + cons_pressure + headloss_pressure)/(gravity*water_density)
	return total_head


pipe_vel = pipe_velocity(100, 20)
head = headloss(100, 8000, 20)
total_head_ = total_head(100, 20, 0, 8000)

print (pipe_vel, head, total_head_)