#!/usr/bin/env python

import math
import numpy as np
import os
import shutil
import scipy
from scipy import loadtxt, optimize
import mysubsprograms as my
import sys
import time
import random
from scipy.interpolate import interp1d


msun = 1.9892e33
rsun = 6.9598e10
rearth = 6.371008e8
mjup = 1.8986e30
rjup = 6.9911e9
mearth = 5.97e27
sigma=5.67e-5
au = 1.496e13



#Calculate the density of the planet
def calculate_rho(mp, enFrac, comp_mod):
	if (os.path.isfile('LOGS/' + comp_mod) == True):

		planet_mass_list, planet_radius_list = loadtxt('LOGS/' + comp_mod, unpack=True, skiprows =6, usecols=[6,4])
		observed_Mcore, observed_Rcore = loadtxt('coreMRcomp2_v40_all.txt', unpack=True, skiprows =11, usecols=[0,1])
		log_age = loadtxt('LOGS/' + comp_mod, unpack=True, skiprows =6, usecols=[0])
		my_type = str(type(planet_mass_list))

		if (my_type == "<type 'numpy.ndarray'>"):
			if (max(log_age) > 2.5):
				planet_mass = planet_mass_list[-1] / mearth
				planet_radius = planet_radius_list[-1] / rearth

				core_radius_function = interp1d(observed_Mcore,observed_Rcore)

				#In units of Rearth and Mearth
				planet_core_mass = (planet_mass*(1-enFrac))
				planet_core_radius = core_radius_function(planet_core_mass)

				#Convert everything back to cgs
				planet_core_mass = planet_core_mass * mearth
				planet_core_radius = planet_core_radius * rearth

				#Calculate Core Density
				core_volume = (4./3.) * (3.14159) * (planet_core_radius ** 3)
				rhocore = planet_core_mass/float(core_volume)
				return rhocore
			else:
				return -1
		else:
			return -1
	else:
		return -1

def create_planet(minitial,y,z,inlist1,createmod):
	start_time = time.time()
	print ("create initial planet")
	f = open('inlist_create', 'r')
	g = f.read()
	f.close()
	g = g.replace("<<initial_mass>>", str(minitial*mearth))
	g = g.replace("<<z>>",str(z))
	g = g.replace("<<y>>",str(y))
	g = g.replace("<<smwtfname>>", '"' + createmod + '"')
	h = open(inlist1, 'w')
	h.write(g)
	h.close()
	shutil.copyfile(inlist1,"inlist")
	os.system('./star_make_planets')
	run_time = time.time() - start_time
	print ("run time for create_planets in sec=",run_time)
	return run_time



def relax_comp(y,z,inlistcomp,createmod,comp_mod):
	start_time = time.time()
	print ("Relax Dude")
	f = open('inlist_comp', 'r')
	g = f.read()
	f.close()
	g = g.replace("<<loadfile>>",'"' + createmod + '"')
	g = g.replace("<<smwtfname>>", '"' + comp_mod + '"')
	g = g.replace("<<y>>",str(y))
	h = open(inlistcomp, 'w')
	h.write(g)
	h.close()
	shutil.copyfile(inlistcomp,"inlist")
	os.system('./star_make_planets')
	run_time = time.time() - start_time
	return run_time



# put in the core if me > 0.0
def put_core_in_planet(mcore,rhocore,inlist2,comp_mod,coremod):
	start_time = time.time()
	print ("put core in planet")
	f = open('inlist_core', 'r')
	g = f.read()
	f.close()
	g = g.replace("<<loadfile>>",'"' + comp_mod + '"')
	g = g.replace("<<smwtfname>>", '"' + coremod + '"')
	g = g.replace("<<new_core_mass>>",str(mcore*mearth/msun))
	g = g.replace("<<core_avg_rho>>",str(rhocore))
	h = open(inlist2, 'w')
	h.write(g)
	h.close()
	shutil.copyfile(inlist2,"inlist")
	os.system('./star_make_planets')
	run_time = time.time() - start_time
	print ("run time to put in core in sec=",run_time)
	print ("rhocore=", rhocore)
	return run_time

#Relaxes the mass
def reduce(Rmp,inlist3,coremod,reducemod):
	start_time = time.time()
	print ("reducing mass")
	print ("target mass=",str(Rmp))
	f = open('inlist_reducemass', 'r')
	g = f.read()
	f.close()
	g = g.replace("<<loadfile>>",'"' + coremod + '"')
	g = g.replace("<<smwtfname>>", '"' + reducemod + '"')
	g = g.replace("<<new_mass>>",str(Rmp*mearth/msun))
	h = open(inlist3, 'w')
	h.write(g)
	h.close()
	shutil.copyfile(inlist3,"inlist")
	os.system('./star_make_planets')
	run_time = time.time() - start_time
	print ("run time to put in core in sec=",run_time)
	return run_time

#Increases the entropy of the planet
def heating(targetEntropy,luminosity,inlist4,reducemod,heatingmod,maxage,currentropy):
	start_time = time.time()
	print ("setting initial entropy")
	print ("target entropy=",str(targetEntropy))
	f = open('inlist_heating', 'r')
	g = f.read()
	f.close()
	g = g.replace("<<loadfile>>",'"' + reducemod + '"')
	g = g.replace("<<smwtfname>>", '"' + heatingmod + '"')
	g = g.replace("<<maxage>>",str(maxage))
	g = g.replace("<<Lc>>", str(luminosity))
	g = g.replace("<<entropy>>",str(targetEntropy))
	h = open(inlist4, 'w')
	h.write(g)
	h.close()
	shutil.copyfile(inlist4,"inlist")
	os.system('./star_make_planets')
	run_time = time.time() - start_time
	print ("run time to set entropy=",run_time)
	print ("entropy", currentropy)
	print ("luminosity", luminosity)
	return run_time

#Decreases the entropy
def cooling(targetEntropy,luminosity,inlist6,reducemod,coolingmod,maxage,currentropy):
	start_time = time.time()
	print ("cooling (nosetS)")
	print ("target entropy=",str(targetEntropy))
	f = open('inlist_cooling', 'r')
	g = f.read()
	f.close()
	g = g.replace("<<loadfile>>",'"' + reducemod + '"')
	g = g.replace("<<smwtfname>>", '"' + coolingmod + '"')
	g = g.replace("<<maxage>>",str(maxage))
	g = g.replace("<<entropy>>",str(targetEntropy))
	h = open(inlist6, 'w')
	h.write(g)
	h.close()
	shutil.copyfile(inlist6,"inlist")
	os.system('./star_make_planets')
	run_time = time.time() - start_time
	print ("run time to evolve in sec=",run_time)
	print ("entropy", currentropy)
	print ("luminosity", luminosity)
	return run_time


#Removes the heating core of the planet
def remove_core_heating(maxage,inlist5,heatingmod,removeheatingmod,knob):
	start_time = time.time()
	print ("remove core dissipation")
	f = open('inlist_remove_heating', 'r')
	g = f.read()
	f.close()
	g = g.replace("<<loadfile>>",'"' + heatingmod + '"')
	g = g.replace("<<smwtfname>>", '"' + removeheatingmod + '"')
	g = g.replace("<<maxage>>",str(maxage))
	g = g.replace("<<knob>>", str(knob) ) 
	h = open(inlist5, 'w')
	h.write(g)
	h.close()
	shutil.copyfile(inlist5,"inlist")
	os.system('./star_make_planets')
	run_time = time.time() - start_time
	print ("run time to evolve in sec=",run_time)
	return run_time

#Removes the heating core of the planet
def remove_core_cooling(maxage,inlist7,coolingmod,removecoolingmod,knob):
	start_time = time.time()
	print ("remove core dissipation")
	f = open('inlist_remove_cooling', 'r')
	g = f.read()
	f.close()
	g = g.replace("<<loadfile>>",'"' + coolingmod + '"')
	g = g.replace("<<smwtfname>>", '"' + removecoolingmod + '"')
	g = g.replace("<<maxage>>",str(maxage))
	g = g.replace("<<knob>>", str(knob) ) 
	h = open(inlist7, 'w')
	h.write(g)
	h.close()
	shutil.copyfile(inlist7,"inlist")
	os.system('./star_make_planets')
	run_time = time.time() - start_time
	print ("run time to evolve in sec=",run_time)
	return run_time


#Relax irradiation
def relax_irradiate_planet(Teq,irrad_col,flux_dayside,maxage_irrad,inlist8,relaxirradmod,orb_sep,Rmp,enFrac,targetEntropy,which_s,y,z,removeheatingmod, removecoolingmod):
	start_time = time.time()
	kappa_v=1/float(irrad_col)
	print ("Relax Irradiation")
	f = open('inlist_relax_irradiation', 'r')
	g = f.read()
	f.close()
	if (which_s == 1):
		g = g.replace("<<loadfile>>",'"' + removeheatingmod + '"')
	elif (which_s == -1):
		g = g.replace("<<loadfile>>",'"' + removecoolingmod + '"')
	else:
		pass
	g = g.replace("<<smwtfname>>", '"' + relaxirradmod + '"')
	g = g.replace("<<irrad_col>>", str(irrad_col) )
	g = g.replace("<<flux_dayside>>", str(flux_dayside) )
	g = g.replace("<<maxage>>",str(maxage_irrad))
	#g = g.replace("<<knob>>", str(knob)) 
	#g = g.replace("<<pl_param>>", str(random.uniform(0,2)) )
	g= g.replace("<<orbital_distance>>", str(orb_sep) )
	#g= g.replace("<<historyName>>", str(Rmp) + "_" + str(enFrac)+ "_" +str(targetEntropy)+ "_" + str(y) + "_" + str(z) + "_" + str(orb_sep))
	h = open(inlist8, 'w')
	h.write(g)
	h.close()
	shutil.copyfile(inlist8,"inlist")
	os.system('./star_make_planets')
	run_time = time.time() - start_time
	print ("run time to relax irradiation in sec=",run_time)
	return run_time

#regular mass-loss evolution
def evolve_planet(Teq,maxage,initialage,inlist9,relaxirradmod,evolvemod,
				orb_sep,Rmp,enFrac,targetEntropy,knob,y,z,irrad_col,n_frac, a, ms, rf, ec):
	start_time = time.time()
	kappa_v=1/float(irrad_col)
	print ("evolve planet")
	f = open('inlist_evolve', 'r')
	g = f.read()
	f.close()
	g = g.replace("<<loadfile>>",'"' + relaxirradmod + '"')
	g = g.replace("<<smwtfname>>", '"' + evolvemod + '"')
	g = g.replace("<<maxage>>",str(maxage))
	g = g.replace("<<initial_age>>",str(initialage))
	g = g.replace("<<Teq>>", str(Teq) ) 
	g = g.replace("<<kappa_v>>", str(kappa_v)) 

	#x_controls
	g = g.replace("<<n_frac>>", str(n_frac))
	g = g.replace("<<a>>", str(a)) 
	g = g.replace("<<ms>>", str(ms)) 
	g = g.replace("<<rf>>", str(rf))
	g = g.replace("<<orbital_distance>>", str(orb_sep))
	g = g.replace("<<ec>>", str(ec))

	g= g.replace("<<historyName>>", str(Rmp) + "_" + str(enFrac)+ "_" +str(targetEntropy)+ "_" + str(y) + "_" + str(z) + "_" + str(orb_sep))
	h = open(inlist9, 'w')
	h.write(g)
	h.close()
	shutil.copyfile(inlist9,"inlist")
	os.system('./star_make_planets')
	run_time = time.time() - start_time
	print ("run time to evolve in sec=",run_time)
	return run_time

# print stuff
def print_parameters(Rmp,enFrac,rhocore,mcore,y,z):
	print ('######################################################')
	print ('parameters:')
	print ('mp=', Rmp)
	print ('enFrac=', enFrac)
	print ('rhocore/cgs=',rhocore)
	print ('mcore=', mcore)
	print ('z=',z)
	print ('y=',y)
	print ('evolve to age/Myr=')
	print ('######################################################')
	return

