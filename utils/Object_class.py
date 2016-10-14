from __future__ import division
import math
import pandas as pd
import numpy as np

from utils.Parameters import *
from utils.functions import *

pipe_construction_data = pd.read_csv('data/pipe_construction_data.csv')
pipe_maintenance_data = pd.read_csv('data/pipe_maintenance_data.csv')
pump_construction_data = pd.read_csv('data/pump_construction_data.csv')
pipe_construction_data=pipe_construction_data[pipe_construction_data['Material']==pipe_material]
nominal_diameter_list = (50, 100, 160, 200, 350, 375, 450)
pump_size_list=np.array(pump_construction_data['Rating_hp'])


class Pipes():
	def __init__(self, pipe_diameter, demand_m3_s, pipe_length):
		self.pipe_diameter = pipe_diameter
		self.demand_m3_s = demand_m3_s
		self.pipe_length = pipe_length

	def mass_PVC(self):
		diameter = self.pipe_diameter
		pipe_index = pipe_construction_data.set_index('size_mm')
		pipe_weight_kg = pipe_index.Wt_kg_m[diameter]*self.pipe_length
		return pipe_weight_kg

	def PVC_construction(self):
		pipe_index = pipe_construction_data.set_index('size_mm')
		diameter = self.pipe_diameter
		PVC_energy_kWh_m3 = pipe_index.Embodied_Energy_MJ_kg[diameter]*self.mass_PVC()/lifetime/(3.6*self.demand_m3_s*3600*24*365)
		PVC_GHG_m3 = pipe_index.Emissions_kgCO2_eq_m[diameter]*self.pipe_length/lifetime/(self.demand_m3_s*3600*24*365)
		return PVC_energy_kWh_m3, PVC_GHG_m3 # Kwh_m3

	def PVC_excavation(self):
		pipe_index = pipe_construction_data.set_index('size_mm')
		pipe_excav_vol_ef = pipe_index.Excavation_vol_m3_m[self.pipe_diameter]
		Pipe_excavation_vol = self.pipe_length*pipe_excav_vol_ef
		Pipe_excavation_energy_kWh_m3 = Pipe_excavation_vol*(excavation_energy)/lifetime/(3.6*self.demand_m3_s*3600*24*365)
		Pipe_excavation_GHG_m3 = Pipe_excavation_vol*(excavation_GHG)/lifetime/(self.demand_m3_s*3600*24*365)
		return Pipe_excavation_energy_kWh_m3, Pipe_excavation_GHG_m3 # Kwh_m3

	def PVC_transportation(self):
		Pipe_transport_energy_kWh_m3 = transport_energy_MJ_km*km_transport/lifetime/(3.6*self.demand_m3_s*3600*24*365)
		Pipe_transport_GHG_m3 = transport_GHG_kg_km*km_transport/lifetime/(self.demand_m3_s*3600*24*365)
		return Pipe_transport_energy_kWh_m3, Pipe_transport_GHG_m3 # Kwh_m3

	def PVC_maintenance(self):
		pipe_maintenance_data['energy_y'] = pipe_maintenance_data['KWh_m']*self.pipe_length
		pipe_maintenance_data['GHG_y'] = pipe_maintenance_data['energy_y']*Electricity_GHG_LCA
		pipe_maint_lifetime = pipe_maintenance_data[pipe_maintenance_data['year_'] <= lifetime]
		pipe_maint_energy_kWh_m3 = pipe_maint_lifetime['energy_y'].sum()/lifetime/(self.demand_m3_s*3600*24*365)
		pipe_maint_GHG_m3 = pipe_maint_lifetime['GHG_y'].sum()/lifetime/(self.demand_m3_s*3600*24*365)
		return pipe_maint_energy_kWh_m3, pipe_maint_GHG_m3 # Kwh_m3


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

	def pump_operational(self):
		Pump_operat_energy = specific_weight_water*self.total_head()*self.demand_m3_s*24*365/(self.pump_efficiency()*motor_efficiency)/(self.demand_m3_s*3600*24*365)
		Pump_operat_GHG = Pump_operat_energy*Electricity_GHG_LCA
		return Pump_operat_energy, Pump_operat_GHG #KWh/m3

	def pump_size(self):
		pump_energy, pump_GHG = self.pump_operational()
		size = pump_energy*(self.demand_m3_s*3600)*1.34
		pump_index = pump_construction_data.set_index('Rating_hp')
		pump_hp = find_nearest(pump_size_list,size)
		return pump_hp

	def pump_construction(self):
		pump_index=pump_construction_data.set_index('Rating_hp')
		pump_energy_EF=pump_index.Embodied_Energy_MJ[self.pump_size()]
		Pump_const_energy = pump_energy_EF/lifetime_pumps/(self.demand_m3_s*3600*24*365)
		pump_GHG_EF=pump_index.Emissions_kgCO_eq[self.pump_size()]
		Pump_const_GHG = pump_GHG_EF/lifetime_pumps/(self.demand_m3_s*3600*24*365)
		return Pump_const_energy, Pump_const_GHG #KWh/m3

	def pump_transportation(self):
		pump_transport_energy_kWh_m3 = transport_energy_MJ_km*km_transport/lifetime_pumps/(3.6*self.demand_m3_s*3600*24*365)
		pump_transport_GHG_m3 = transport_GHG_kg_km*km_transport/lifetime_pumps/(self.demand_m3_s*3600*24*365)
		return pump_transport_energy_kWh_m3, pump_transport_GHG_m3 # Kwh_m3


class Tanks_cement():
	def __init__(self, total_demand_m3_d):
		self.total_demand_m3_d = total_demand_m3_d

	def volume(self):
		volume = storage_days*self.total_demand_m3_d
		return volume #m3
    
	def area_cylinder(self):
		radius = math.sqrt(self.volume()/(math.pi*tank_height))
		area = 2*math.pi*radius*tank_height+2*math.pi*radius**2
		return area
    
	def volume_cement(self):
		area = self.area_cylinder()       
		volume = area*tank_thickness
		return volume #m3

	def tank_construction(self):
		tank_cement_energy = self.volume_cement()*reinf_concrete_energy/lifetime/(3.6*self.total_demand_m3_d*365)
		tank_cement_GHG = self.volume_cement()*reinf_concrete_GHG/lifetime/(self.total_demand_m3_d*365)
		return tank_cement_energy, tank_cement_GHG #kWh_m3

	def tank_transportation(self):
		tank_transport_energy_kWh_m3 = transport_energy_MJ_km*km_transport/lifetime/(3.6*self.total_demand_m3_d*365)
		tank_transport_GHG_m3 = transport_GHG_kg_km*km_transport/lifetime/(self.total_demand_m3_d*365)
		return tank_transport_energy_kWh_m3, tank_transport_GHG_m3 # Kwh_m3


class Treatment():
	def __init__(self, total_demand_m3_d, status):
		self.total_demand_m3_d = total_demand_m3_d
		self.status = status


	def RO_construction(self):
		RO_Capital_energy_KWh_m3 = RO_membrane_area*RO_energy_m2/RO_lifetime/(3.6*self.total_demand_m3_d*365)
		RO_Capital_GHG_m3 = RO_membrane_area*RO_GHG_m2/RO_lifetime/(self.total_demand_m3_d*365)
		return RO_Capital_energy_KWh_m3, RO_Capital_GHG_m3 #Kwh_m3, kg/m3

	def RO_transportation(self):
		RO_transport_energy_kWh_m3 = transport_energy_MJ_km*km_transport/RO_lifetime/(3.6*self.total_demand_m3_d*365)
		RO_transport_GHG_m3 = transport_GHG_kg_km*km_transport/RO_lifetime/(self.total_demand_m3_d*365)
		return RO_transport_energy_kWh_m3, RO_transport_GHG_m3 # Kwh_m3, kg/m3

	def UV_construction(self):
		UV_Capital_energy_KWh_m3 = UV_rating*self.total_demand_m3_d*UV_capital_cost*0.76*7.8/UV_lifetime/(3.6*self.total_demand_m3_d*365)
		UV_Capital_GHG_m3 = UV_rating*self.total_demand_m3_d*UV_capital_cost*0.558*0.76/(UV_lifetime)/(self.total_demand_m3_d*365)
		return UV_Capital_energy_KWh_m3, UV_Capital_GHG_m3 #Kwh_m3, kg/m3

	def UV_operation(self):
		UV_Operation_energy_KWh_m3 = UV_rating*self.total_demand_m3_d*UV_usage*365/1000/(self.total_demand_m3_d*365)
		UV_Operation_GHG_m3 = UV_Operation_energy_KWh_m3*Electricity_GHG_LCA
		return UV_Operation_energy_KWh_m3, UV_Operation_GHG_m3 #Kwh_m3, kg/m3

	def UV_transportation(self):
		UV_transport_energy_kWh_m3 = transport_energy_MJ_km*km_transport/UV_lifetime/(3.6*self.total_demand_m3_d*365)
		UV_transport_GHG_m3 = transport_GHG_kg_km*km_transport/UV_lifetime/(self.total_demand_m3_d*365)
		return UV_transport_energy_kWh_m3, UV_transport_GHG_m3 # Kwh_m3, kg/m3

	def Chlorine_Tank_construction(self):
		chlorine_volume=chlorine_retention_time/24*self.total_demand_m3_d
		chlorine_radius=math.sqrt(chlorine_volume/(math.pi*1))
		chlorine_cement_volume=((2*math.pi*chlorine_radius*1)+math.pi*chlorine_radius**2)*0.10
		Chlorine_Tank_energy_KWh_m3 = chlorine_cement_volume*reinf_concrete_energy/lifetime_treatment/(3.6*self.total_demand_m3_d*365)
		Chlorine_Tank_GHG_m3 = chlorine_cement_volume*reinf_concrete_GHG/lifetime_treatment/(self.total_demand_m3_d*365)
		return Chlorine_Tank_energy_KWh_m3, Chlorine_Tank_GHG_m3

	def Chlorine_operation(self):
		Chlorine_Operation_energy_KWh_m3 = chlorine_mass*chlorine_energy/1000/3.6
		Chlorine_Operation_GHG_m3 = chlorine_mass*chlorine_GHG/1000
		return Chlorine_Operation_energy_KWh_m3, Chlorine_Operation_GHG_m3 #Kwh_m3, kg/m3

	def Chlorine_transportation(self):
		Chlorine_transport_energy_kWh_m3 = transport_energy_MJ_km*km_transport/(3.6*self.total_demand_m3_d*365)
		Chlorine_transport_GHG_m3 = transport_GHG_kg_km*km_transport/(self.total_demand_m3_d*365)
		return Chlorine_transport_energy_kWh_m3, Chlorine_transport_GHG_m3 # Kwh_m3, kg/m3

	def Sludge_disposal(self):
		Sludge_disposal_GHG_m3 = landfill_GHG*sludge_mass*0.2*percent_landfill/(1000)+fertilizer_GHG*sludge_mass*0.2*percent_fertilizer/(1000)
		return Sludge_disposal_GHG_m3 #kg/m3

	def Sludge_transportation(self):
		Sludge_transport_energy_kWh_m3 = transport_energy_MJ_km*km_to_disposal/(3.6*self.total_demand_m3_d*365)
		Sludge_transport_GHG_m3 = transport_GHG_kg_km*km_to_disposal/(self.total_demand_m3_d*365)
		return Sludge_transport_energy_kWh_m3, Sludge_transport_GHG_m3 # Kwh_m3, kg/m3

	def Bar_Screen_construction(self):
		Bar_Screen_energy_KWh_m3 = Screen_Filter_capital_energy/lifetime_treatment/(3.6*self.total_demand_m3_d*365)
		Bar_Screen_GHG_m3 = Screen_Filter_capital_GHG/1000/lifetime_treatment/(self.total_demand_m3_d*365)
		return Bar_Screen_energy_KWh_m3, Bar_Screen_GHG_m3

	def Bar_Screen_operation(self):
		Bar_Screen_Operation_energy_KWh_m3 = filter_screen_energy
		Bar_Screen_Operation_GHG_m3 = Bar_Screen_Operation_energy_KWh_m3*Electricity_GHG_LCA
		return Bar_Screen_Operation_energy_KWh_m3, Bar_Screen_Operation_GHG_m3 #Kwh_m3, kg/m3

	#Grinder
	def Grinder_construction(self):
		pump_index = pump_construction_data.set_index('Rating_hp')
		pump_energy_EF = pump_index.Embodied_Energy_MJ[Grinder_pump_hp]
		pump_GHG_EF=pump_index.Emissions_kgCO_eq[Grinder_pump_hp]
		Grinder_Constuction_energy_KWh_m3 = pump_energy_EF/lifetime_pumps/(3.6*self.total_demand_m3_d*365)
		Grinder_Constuction_GHG_m3 = pump_GHG_EF/lifetime_treatment/(self.total_demand_m3_d*365)
		return Grinder_Constuction_energy_KWh_m3, Grinder_Constuction_GHG_m3

	def Grinder_operation(self):
		Grinder_Operation_energy_KWh_m3 = Grinder_pump_hp/1.34*Grinder_pump_usage*365/(self.total_demand_m3_d*365)
		Grinder_Operation_GHG_m3 = Grinder_Operation_energy_KWh_m3*Electricity_GHG_LCA
		return Grinder_Operation_energy_KWh_m3, Grinder_Operation_GHG_m3 #Kwh_m3, kg/m3

	#Grit Chamber
	def Grit_chamb_construction(self):
		Grit_chamb_volume = Grit_chamber_time/24*self.total_demand_m3_d
		Grit_chamb_radius = math.sqrt(Grit_chamb_volume/(math.pi*1))
		Grit_chamb_cement_volume = ((2*math.pi*Grit_chamb_radius*1)+math.pi*Grit_chamb_radius**2)*tank_thickness
		Grit_chamb_Constuction_energy_KWh_m3 = Grit_chamb_cement_volume*reinf_concrete_energy/lifetime/(3.6*self.total_demand_m3_d*365)
		Grit_chamb_Constuction_GHG_m3 = Grit_chamb_cement_volume*reinf_concrete_GHG/lifetime/(self.total_demand_m3_d*365)
		return Grit_chamb_Constuction_energy_KWh_m3, Grit_chamb_Constuction_GHG_m3

	#Flow Equalization
	def Equilization_construction(self):
		equilization_tank_volume = retention_time*self.total_demand_m3_d
		equilization_tank_radius = math.sqrt(equilization_tank_volume/(math.pi*tank_height))
		equilization_tank_area = 2*math.pi*equilization_tank_radius*tank_height+2*math.pi*equilization_tank_radius**2
		equilization_tank_mass_steel = round(equilization_tank_area/steel_sheet_area,0)*steel_sheet_mass
		Equilization_Constuction_energy_KWh_m3 = equilization_tank_mass_steel*steel_energy/lifetime/(3.6*self.total_demand_m3_d*365)
		Equilization_Constuction_GHG_m3 = equilization_tank_mass_steel*steel_GHG/lifetime/(self.total_demand_m3_d*365)
		return Equilization_Constuction_energy_KWh_m3, Equilization_Constuction_GHG_m3

	#MBR
	def MBR_construction(self):
		MBR_Constuction_energy_KWh_m3=0.72/3.6
		MBR_Constuction_GHG_m3=0.061
		return MBR_Constuction_energy_KWh_m3, MBR_Constuction_GHG_m3

	def MBR_operation(self):
		if self.status == 'current':
			MBR_Operation_energy_KWh_m3=(9.5*(self.total_demand_m3_d)**(-0.3))*0.75
			if 9.5*(self.total_demand_m3_d)**(-0.3)>7:
			    MBR_Operation_energy_KWh_m3 = 7*0.75
		elif self.status == 'future':
			MBR_Operation_energy_KWh_m3=(9.5*(self.total_demand_m3_d)**(-0.3))*0.75*0.8
			if 9.5*(self.total_demand_m3_d)**(-0.3)>7:
			    MBR_Operation_energy_KWh_m3 = 7*0.75*0.8
		MBR_Operation_GHG_m3=MBR_Operation_energy_KWh_m3*Electricity_GHG_LCA
		return MBR_Operation_energy_KWh_m3, MBR_Operation_GHG_m3 #Kwh_m3, kg/m3