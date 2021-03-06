#!/usr/bin/env python
#python script created by Phil Arras UVA, modified by HW Chen NU and then modified more by Isaac Malsky
import numpy as np
import os
import scipy
from scipy import loadtxt, optimize
import mysubsprograms as my
import sys

#Constants
msun = 1.9892e33
rsun = 6.9598e10
rearth = 6.371008e8
mjup = 1.8986e30
rjup = 6.9911e9
mearth = 5.97e27
sigma=5.67e-5
au = 1.496e13

####################################################
#########         PARAMETERS LISTS         #########
####################################################
mpList=[10]
enFracList=[.05]
entropyList=[8.0,10.0]
yList = [.24]
zList = [.02]
oribitalList=[.5]

####################################################
#########        IRRAD/EVOL CONDITIONS        ######
####################################################
minitial=30						#Initial Planet Mass
yinitial = .24							#Initial He4				
rs = .464				        #star radius in rsun
Teff_star = 3318			           #stellar Teff  
BA= 0.2                          #planet Bond albedo
irrad_col = 300					  #irradiation depth

n_frac = .1 					  #frac_absorbed_euv
a = 1.    				      #frac_absorbing_radius
ms = .452                            #host_star_mass
rf = 1.                #escape_rate_reduction_factor
ec = 1e9                           #eddy coefficient

#All mod files and log files are saved under the name "string_mp_enFrac_entropy_y_z_orbitalseparation"
f=open('logfile','w')
for w in range (0, len(zList)):
	z = zList[w]
	for i in range (0 ,len(yList)):
		y = yList[i]
		createmod = "planet_create_" + str(minitial) + "_" +  str(yinitial) + "_" + str(z)+ ".mod"

		inlist1 = "inlist_create_" + str(minitial) + "_" +  str(yinitial) + "_" + str(z)
		run_time = my.create_planet(minitial,yinitial,z,inlist1,createmod)

		comp_mod = "planet_relax_composition" + str(minitial) + "_" +  str(y) + "_" + str(z)+ ".mod"
		inlistcomp = "inlist_comp_" + str(minitial) + "_" +  str(y) + "_" + str(z)
		run_time = my.relax_comp(y,z,inlistcomp,createmod,comp_mod)

		#Iterate over envelope fractions and masses
		for j in range(0, len(enFracList)):
			for m in range(0, len(mpList)):
				mp = mpList[m]
				enFrac = enFracList[j]
				Rmp = mp
				mcore = mp*(1-enFrac)
				rhocore = my.calculate_rho(mp, enFrac, comp_mod)

				if (rhocore == -1):
					print (mp, enFrac)
				else:
					my.print_parameters(Rmp,enFrac,rhocore,mcore,y,z)
					coremod = "planet_core_" + str(mp) + "_" + str(enFrac)+ "_" + str(y)+ "_" + str(z) + ".mod"
					reducemod = "planet_reduce_" + str(mp) + "_" + str(enFrac)+ "_" + str(y) + "_" + str(z) + ".mod"

					inlist2 = "inlist_core_" + str(mp) + "_" + str(enFrac)+ "_" + str(y)+ "_" + str(z)
					run_time = my.put_core_in_planet(mcore,rhocore,inlist2,comp_mod,coremod)

					inlist3 = "inlist_reduce_" + str(mp) + "_" + str(enFrac)+ "_" + str(y) + "_" + str(z)
					run_time = my.reduce(Rmp,inlist3,coremod,reducemod)

					for b in range (0, len(oribitalList)):
						orb_sep = oribitalList[b]  # orbital sepration in AU (to set day-side flux)  134000,13400000,1340000000 ergs/s/cm^2   ie. 0.032, 0.32,3.2
						flux_dayside = (sigma*Teff_star**4 * ( rs*rsun / orb_sep / au )**2)*(1-BA)	# flux hitting planet's dayside
						Teq = (flux_dayside*(1-BA)/4.0/sigma)**0.25    #equalibrium temperature
						#determining core radius base on mass, from LA Rogers's model

						#Iterates over entropy values without creating new models based on the other parameters for every value
						for q in range (0 ,len(entropyList)):
							which_s = 0
							targetEntropy = entropyList[q]

							#Heating mod and cooling mod MUST be named this way or remove won't read them properly
							heatingmod= "planet_heating_" + str(mp) + "_" + str(enFrac)+ "_" +str(targetEntropy)+ "_" + str(y) + "_" + str(z) + "_" + str(orb_sep)+ ".mod"
							coolingmod= "planet_cooling_" + str(mp) + "_" + str(enFrac)+ "_" +str(targetEntropy)+ "_" + str(y) + "_" + str(z) + "_" + str(orb_sep)+ ".mod"
							removecoolingmod = "planet_remove_cooling_" + str(mp) + "_" + str(enFrac)+ "_" +str(targetEntropy)+ "_" + str(y) + "_" + str(z) + "_" + str(orb_sep)+ ".mod"
							removeheatingmod = "planet_remove_heating_" + str(mp) + "_" + str(enFrac)+ "_" +str(targetEntropy)+ "_" + str(y) + "_" + str(z) + "_" + str(orb_sep)+ ".mod"
							relaxirradmod = "planet_relax_irradiate_" + str(mp) + "_" + str(enFrac)+ "_" +str(targetEntropy)+ "_" + str(y) + "_" + str(z) + "_" + str(orb_sep)+ ".mod"
							evolvemod = "planet_evolve_" + str(mp) + "_" + str(enFrac)+ "_" +str(targetEntropy)+ "_" + str(y) + "_" + str(z) + "_" + str(orb_sep)+ ".mod"

							if (os.path.isfile('LOGS/' + reducemod) == True):
								luminosity_list, entropy_list = loadtxt('LOGS/' + reducemod, unpack=True, skiprows =6, usecols=[1,3])

								luminosity = luminosity_list[-1]* 60 * 3.846e33
								currentropy = entropy_list[-1]

								#The cools or heats the planet, removes the core, and then evolves it
								#chose whether to reduce the entropy by cooling the planet, or increase the entropy by inflating the planet
								if currentropy<float(targetEntropy):
									maxage = 1e8
									which_s = 0
									knob = ".true." #Turns on the relax_L lines in inlist remove
									inlist4 = "inlist_heating_"  + str(mp) + "_" + str(enFrac)+ "_" +str(targetEntropy)+ "_" + str(y) + "_" + str(z) + "_" + str(orb_sep)
									run_time = my.heating(targetEntropy,luminosity,inlist4,reducemod,heatingmod,maxage,currentropy)

									maxage = 1e4
									inlist5 = "inlist_remove_heating_" + str(mp) + "_" + str(enFrac)+ "_" +str(targetEntropy)+ "_" + str(y) + "_" + str(z) + "_" + str(orb_sep)
									run_time = my.remove_core_heating(maxage,inlist5,heatingmod,removeheatingmod,knob)
									which_s = 1

								else:
									maxage= 1e8
									knob= ".false." #Turns off the relax_L lines in inlist remove
									inlist6 = "inlist_cooling_" + str(mp) + "_" + str(enFrac)+ "_" +str(targetEntropy)+ "_" + str(y) + "_" + str(z) + "_" + str(orb_sep)
									run_time = my.cooling(targetEntropy,luminosity,inlist6,reducemod,coolingmod,maxage, currentropy)

									maxage = 1e4
									inlist7 = "inlist_remove_cooling_" + str(mp) + "_" + str(enFrac)+ "_" +str(targetEntropy)+ "_" + str(y) + "_" + str(z) + "_" + str(orb_sep)
									run_time = my.remove_core_cooling(maxage,inlist7,coolingmod,removecoolingmod,knob)
									which_s = -1

								maxage_irrad= 1e6
								initialage = 0
								inlist8 = "inlist_relax_irradiation_" + str(mp) + "_" + str(enFrac)+ "_" +str(targetEntropy)+ "_" + str(y) + "_" + str(z) + "_" + str(orb_sep)
								run_time = my.relax_irradiate_planet(Teq,irrad_col,flux_dayside,maxage_irrad,inlist8,relaxirradmod,orb_sep,Rmp,enFrac,targetEntropy,which_s,y,z,removeheatingmod, removecoolingmod)

								knob= ".true."
								initialage= 5e6   #set 1e8 for planets below 10 Mearth, for better convergence
								maxage= 1e10
								inlist9 = "inlist_evolve_" + str(mp) + "_" + str(enFrac)+ "_" +str(targetEntropy)+ "_" + str(y) + "_" + str(z) + "_" + str(orb_sep)
								run_time = my.evolve_planet(Teq,maxage,initialage,inlist9,relaxirradmod,evolvemod,
									orb_sep,Rmp,enFrac,targetEntropy,knob,y,z,irrad_col,n_frac, a, ms, rf, ec)
f.close()
