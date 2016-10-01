from __future__ import division
import math
import pandas as pd
import numpy as np

from Parameters import *

pipe_construction_data = pd.read_csv('data/pipe_construction_data.csv')
pump_construction_data = pd.read_csv('data/pump_construction_data.csv')
pipe_construction_data=pipe_construction_data[pipe_construction_data['Material']=='PVC']
nominal_diameter_list=np.array(pipe_construction_data['size_mm'])
pump_size_list=np.array(pump_construction_data['Rating_hp'])

def find_nearest(array,value):
    idx = (np.abs(array-value)).argmin()
    return array[idx]

class Pipes():
	def __init__(self, pipe_diameter, demand_m3_s, pipe_length):
		self.pipe_diameter = pipe_diameter
		self.demand_m3_s = demand_m3_s
		self.pipe_length = pipe_length

	def mass_PVC(self):
		diameter_mm=self.pipe_diameter
		diameter=find_nearest(nominal_diameter_list,diameter_mm)
		pipe_index=pipe_construction_data.set_index('size_mm')
		pipe_weight_kg=pipe_index.Wt_kg_m[diameter]*self.pipe_length
		return pipe_weight_kg

	def PVC_energy(self):
		pipe_index=pipe_construction_data.set_index('size_mm')
		diameter_mm=self.pipe_diameter
		diameter=find_nearest(nominal_diameter_list,diameter_mm)
		PVC_energy_MJ_y=pipe_index.Embodied_Energy_MJ_kg[diameter]*self.mass_PVC()/PVC_lifetime
		PVC_energy_kWh_m3 = PVC_energy_MJ_y/(3.6*self.demand_m3_s*3600*24*365)
		return PVC_energy_kWh_m3 # Kwh_m3


class Pumps():
	def __init__(self, pipe_diameter, demand_m3_s, elevation_head, pump_pressure, pipe_length):
		self.pipe_diameter = pipe_diameter
		self.demand_m3_s = demand_m3_s
		self.elevation_head = elevation_head
		self.pump_pressure = pump_pressure
		self.pipe_length = pipe_length

	def pipe_velocity(self):
		area=math.pi*(self.pipe_diameter*0.001/2)**2
		pipe_velocity=self.demand_m3_s/area
		return pipe_velocity #m/s

	def headloss(self):
		headloss=0.03*self.pipe_length*(self.pipe_velocity()**2)/(2*self.pipe_diameter*0.001*9.81)
		if headloss > self.elevation_head*0.5:
			headloss = self.elevation_head*0.3
		return headloss #m

	def total_head(self):
		vel_pressure = (self.pipe_velocity()**2)*water_density/2
		cons_pressure = self.pump_pressure/10*101325
		elev_head = (self.elevation_head*gravity*water_density)
		headloss_pressure = self.headloss()*gravity*water_density
		total_head = (vel_pressure + cons_pressure + elev_head + headloss_pressure)/(gravity*water_density)
		return total_head #m

	def pump_efficiency(self):
		p_hp=(specific_weight_water*self.total_head()*self.demand_m3_s/(0.4*motor_efficiency))*1.34
		if p_hp<3:
			pump_efficiency=0.4
		if 3<=p_hp<7:
			pump_efficiency=0.45
		if 7<=p_hp<15:
			pump_efficiency=0.5
		if 15<=p_hp<40:
			pump_efficiency=0.55
		if 40<=p_hp<60:
			pump_efficiency=0.6
		else:
			pump_efficiency=0.7
		return pump_efficiency

	def pump_energy(self):
		Pump_operat_energy=specific_weight_water*self.total_head()*self.demand_m3_s*24*365/(self.pump_efficiency()*motor_efficiency)/(self.demand_m3_s*3600*24*365)
		return Pump_operat_energy #KWh/m3

	def pump_size(self):
		size = self.pump_energy()*(self.demand_m3_s*3600)*1.34
		pump_index=pump_construction_data.set_index('Rating_hp')
		pump_hp=find_nearest(pump_size_list,size)
		return pump_hp

