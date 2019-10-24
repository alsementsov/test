import numpy as np
import matplotlib.pyplot as plt
from numpy import genfromtxt
import scipy.signal as sig
import pylab
from tkinter import Tk
from tkinter.filedialog import askopenfilename
############ CONSTANT
FPS = 25
A = 104.5
B = 16.5
Lf = 9
Lf_spo2=13
############ Functions
def spo2_calc(IRmax,IRminl,IRminr,Rmax,Rminl,Rminr,A,B):
    Red_DC=(Rminl+Rminr)/2
    Red_AC = Rmax-Red_DC
    IR_DC=(IRminl+IRminr)/2
    IR_AC = IRmax-IR_DC
    ratioAverage=(Red_AC/Red_DC)/(IR_AC/IR_DC)
    #return (A-(B*((Red_AC/Red_DC)/(IR_AC/IR_DC))))
    return (-45.060*ratioAverage* ratioAverage) + (30.354 *ratioAverage) + 94.845 
def CheckForErrors(Left,Center,Right,Told,spo2,Vl,Vc,Vr):
    T = Right-Left
    Error = 0
    if Told!=0:
        div=T/Told
        # Большая разница в периодах
        if (div>2.5)or(div<0.4):
            Error=1
    # Экстремумы слишком близко
    if ((Center<Left)or(Center>Right)or(Right<=Left+3)):
        Error=2
        #падение моментального SPO 
    if (spo2<91)or(spo2>=102)or(Vc<=Vl)or(Vc<=Vl):
        Error=3
    return Error,T
def back_to_extremum (mas,index,sign):
    i=index;
    while ((mas[i-1]>= mas[i])and(sign=="up"))or((mas[i-1]<= mas[i])and(sign=="down")):
        i=i-1
    return mas[i],i 
def MaxMin_search(irmas,irmas_orig,redmas_orig):
    irmax = []
    irmin = []
    irmax_index = []
    irmin_index = []
    rmax=[]
    rmin=[]
    rmin_index=[]
    rmax_index=[]
    irmax_med=[]
    irmin_med=[]
    irmax_med_index=[]
    irmin_med_index=[]
    spo2_mas=[]
    error_mas=np.zeros(len(irmas_orig),dtype=int)
    if (irmas[0]>irmas[1]):
       searching_max=False
    else:
       searching_max = True
    sample_prev = irmas[0]
    Virmax=0
    Virmin=0
    Vrmax=0
    Vrmin=0
    left_index=0
    cnt=0;
    max_index=0;
    T=0
    cnt_empty=0
    HR_counter=0
    for sample in irmas[1:]:
        Flag_extremum=False
        delta=abs(abs(sample)-abs(sample_prev))
        if searching_max:#Max       
            if (sample < sample_prev)and(delta>=5):
                #if abs(abs(last_extremum)-abs(sample))>12:
                Virmax,i = back_to_extremum(irmas_orig,cnt,"up") 
                irmax.append(Virmax)
                irmax_index.append(i)
                searching_max = False
                irmax_med.append(sample_prev)
                irmax_med_index.append(cnt)
                Vrmax=redmas_orig[i]
                rmax.append(Vrmax)
                rmax_index.append(i)
                max_index=i
        elif (sample > sample_prev)and(delta>=5):
            Virmin_new,i = back_to_extremum(irmas_orig,cnt,"down")  
            irmin.append(Virmin_new)
            irmin_index.append(i)
            searching_max = True
            irmin_med.append(sample_prev)
            irmin_med_index.append(cnt)
            Vrmin_new=redmas_orig[i]
            rmin.append(Vrmin_new)
            rmin_index.append(i)
            #SPO2
            if len(rmin)>1:
                Flag_extremum=True
                spo2=spo2_calc(Virmax,Virmin,Virmin_new,Vrmax,Vrmin,Vrmin_new,A,B)
                spo2_mas.append(spo2)
                Told=T
                error,T=CheckForErrors(left_index,max_index,i,Told,spo2,Virmin,Virmax,Virmin_new)
                error_mas[cnt]=error
                if error<=1:
                    HR_counter=HR_counter+1
            left_index=i
            Virmin=Virmin_new
            Vrmin=Vrmin_new
            cnt_empty=0
        sample_prev = sample
        cnt=cnt+1
        cnt_empty=cnt_empty+1
        #print([Flag_extremum,cnt,cnt_empty,T])
        if (Flag_extremum==False)and(T>0):
            if ((cnt_empty/T)>3)or(cnt_empty>62):#Завит от fps
                error_mas[cnt]=4
            else:
                error_mas[cnt]=error_mas[cnt-1]        
                #print([cnt,cnt_empty,T])
    return irmax,irmin,irmax_index,irmin_index,rmax,rmin,rmax_index,rmin_index,irmax_med,\
            irmin_med,irmax_med_index,irmin_med_index,spo2_mas,error_mas,HR_counter
##### OPEN
def Filename_request():
    root = Tk()
    root.withdraw()
    root.update() # we don't want a full GUI, so keep the root window from appearing
    Filename = askopenfilename(defaultextension='.csv',filetypes=[('CSV','*.csv')])
    print(Filename)
    return Filename
###############################################################################################
############### MAIN ##########################################################################
###############################################################################################
records = genfromtxt(Filename_request(), delimiter=',')
Red_read = np.array(records[2:,0],dtype=int)
IR_read = np.array(records[2:,1],dtype=int)
#Big MEDIAN = To improve performance (may be excluded)
IR_mean = sig.medfilt(IR_read,81)
IR = IR_read - IR_mean # without DC
# Small MEDIAN
IR_med = sig.medfilt(IR,Lf)
irmax,irmin,irmax_i,irmin_i,rmax,rmin,rmax_i,rmin_i,irmax_med,irmin_med,irmax_med_i,irmin_med_i,spo2,errors,HR_raw= MaxMin_search(IR_med,IR_read,Red_read)  

#### Heart rate & SpO2
spo2_med = sig.medfilt(spo2,Lf_spo2)  # сглаживание spo2
Nsamples=len(Red_read)
T_in_minute = Nsamples/(60*FPS)
#HR_raw = len(irmax)
HR = int(HR_raw/T_in_minute);


#############################PLOT################################################
# plt.subplot(321)
# plt.grid(axis='both',linestyle = '--')
# plt.plot(Red_read)
# plt.plot(rmax_i,rmax,'o')
# plt.plot(rmin_i,rmin,'o')
# plt.title("RED")
# plt.subplot(323)
# plt.grid(axis='both',linestyle = '--')
# plt.plot(errors,color='purple',linewidth ='3')

# plt.subplot(322)
# plt.grid(axis='both',linestyle = '--')
# plt.plot(IR_read)
# plt.plot(irmax_i,irmax,'o')
# plt.plot(irmin_i,irmin,'o')
# plt.title("№ pulses = "+str(len(irmax))+"("+str(int(len(irmax)/T_in_minute))+") /  HR= "+str(HR))
# plt.subplot(324)
# plt.grid(axis='both',linestyle = '--')
# plt.plot(IR_med)
# plt.plot(irmax_med_i,irmax_med,'o')
# plt.plot(irmin_med_i,irmin_med,'o')

# plt.subplot(325)
# plt.ylim((90, 104))
# pylab.yticks(range(80, 104,2)) 
# plt.grid(axis='both',linestyle = '--')
# plt.plot(spo2,color='red',linewidth ='2')
# plt.subplot(326)
# plt.title(" === SpO2 ===")
# plt.ylim((90, 104))
# pylab.yticks(range(90, 104,1))
# plt.grid(axis='both',linestyle = '--')
# plt.plot(spo2_med,color='red',linewidth ='2')
###############################################
plt.subplot(221)
plt.grid(axis='both',linestyle = '--')
plt.plot(Red_read)
plt.plot(rmax_i,rmax,'o')
plt.plot(rmin_i,rmin,'o')
plt.title("RED")
plt.subplot(223)
plt.ylim((0, 4))
plt.grid(axis='both',linestyle = '--')
plt.plot(errors,color='purple',linewidth ='3')#errors
plt.title("Errors")


plt.subplot(222)
plt.grid(axis='both',linestyle = '--')
plt.plot(IR_read)
plt.plot(IR_mean,color='purple',linewidth ='3')
plt.plot(irmax_i,irmax,'o')
plt.plot(irmin_i,irmin,'o')
plt.title("IR pulses = "+str(len(irmax))+"("+str(int(len(irmax)/T_in_minute))+") /  HR= "+str(HR))

plt.subplot(224)
plt.title(" === SpO2 ===")
plt.ylim((93, 100))
pylab.yticks(range(93, 100,1))
plt.grid(axis='both',linestyle = '--')
plt.plot(spo2_med,color='red',linewidth ='2')

figManager = plt.get_current_fig_manager()
figManager.window.showMaximized()
plt.show()
           


