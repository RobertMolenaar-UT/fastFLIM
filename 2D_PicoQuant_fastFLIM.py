# -*- coding: utf-8 -*-
#Copyright Robert Molenaar 2401128


#### Experimental INFO ####

class Set_Channel_Info:
        
    def __init__(self, Channel, Name, Brighter, PIE_TimeGate, ch_irf):
        self.Channel        = Channel-1               # SPAD channel converted to index
        self.ChannelName    = f'Ch{Channel}'          # Channel string
        self.Name           = Name                    # String: Name / discription of the channel
        self.Brighter       = Brighter                # double: scale factor to increase brightness of the FLIM image
        self.TimeGate       = PIE_TimeGate-1          # TimeGate for the Channel
        self.TAC_start      = 0                       # int: filled with Timegate start TAC value
        self.TAC_end        = 1                       # int: filled with Timegate  end  TAC value 
        self.irf            = ch_irf                  # float: channel specific property onset of Instrumet response
        self.Tau_min        = 0                       # min Tacg for cmap image scaling
        self.Tau_max        = 0                       # max Tavg for cmap image scaling 
        self.FFtav          = 0                       # 2d result, float64 array with the FastFlim tavg (FFtav) values 
        self.FFCmap         = 0                       # 2D result, flaot64 scalled FastFlim colourmap (FFcmap) Flim image, color map 0:1 for this channel
        self.FFint          = 0                       # 2D result, flaot64 FastrFlim intensity (FFint) image for this channel 
        
        
        
"""##################  START of user input ###########"""

#set here your channel information 
Config1 = Set_Channel_Info(1,
                           'Ch1 Namelabel'   ,           #name/dye channel 1
                           Brighter=1.2      ,      #Make FLIM image a fraction brighter for beter visibility
                           PIE_TimeGate=1  ,        #excitation (PIE) time-gate, Timing is automatically calculated
                           ch_irf=1.86)             #Instrument Response Function: offset, Measure the direct reflection of a coverslip/mirror

Config2 = Set_Channel_Info(2,
                           'Ch2 Namelabel'      ,
                           Brighter=1.2      ,
                           PIE_TimeGate=2  ,
                           ch_irf=1.85)

Config3 = Set_Channel_Info(3,
                           'Ch3 Namelabel',
                           Brighter=1.2          ,
                           PIE_TimeGate=2     , 
                           ch_irf=2.6)
Config4 = Set_Channel_Info(4,  
                           'Ch4 Namelabel'  ,
                           Brighter=1.2    ,
                           PIE_TimeGate=3      , 
                           ch_irf=2.55)

#File picking    
GUI_MultiPick        =True     #Set to Flase to proccess the full folder with the GUI (default True).
Default_prompt       =r'C:'    #Default folder to pick your files, advice use our .SPTW folder.

#Lifetime settings
Tau_min              =  0       # ns. start Lifetime Cmap , below is clipped.
Tau_max              =  4       # ns. end   Lifetime Cmap , above is clipped.
TCSPC_PIE_Start_ns   =  0       # ns. Include TCSPC data in Fastflim from. 
TCSPC_PIE_End_ns     =  16      # ns. Include TCSPC data in Fastflim untill (FastFlim mesaured average arrival time, in FLIM counts are limited and in many cases late photons are noise, and bias Tavg longer, enhanchin color noise)

#lateral image settings
Channel_Binning      =  False   #Merge all channels into channel 1, multiple detectors combined to one (please match IRF onset in symphotine64 and use beamsplitters)
Binning              =  1       #Pixel Binning 1,2,3 = 1x1, 2x2 , 3x3 etc before fastFLIM conversion
bi_shift             =  0.0     #bi-derctional line pixel correction,  float anything between 0.0 -3.0

#figure plot options
scalebar             =  True    #insert a scalebar in FLIM image instead of axis
tav_cbar_ticks       =  7       #number of ticks in the lifetime cmap

overlap_FLIMchannels =  False    #in multchannels FLIM image can be ovelapped 
overlap_projection   = 'maximum' #or 'sum'

#Saving optons
Clean_Imsave         = True       #save tif files, intensity and cmap
Save_tiff_LTstack    = False      #save image tiff stack, for phasor post analysis, x,y,time slices per bin.
Save_data_files      = True       #Write CSV data files with intensity of all channels 8.dat
Fig_dpi              =  200       #output figure resolution 100→300
FLIM_Database_NPZ    = True       #Save FLIM_data_stack to npz file, speed increase since it skips photon conversion for large files.
FLIM_Sync_Rate_Fraction = 0.2     #Pixels counts can not be to high: FLIM countrate should not be beyond 10-[20]pct

folder_com_pre       =''          #optinal prefic for a saving folder
folder_com           =f'{folder_com_pre}TAC_{Tau_min:.2f}-{Tau_max:.2f}'



"""################## END of user input ###########"""


from readPTU_FLIM_bidirect import PTUreader
from readPTU_FLIM_bidirect import get_lifetime_image
from matplotlib_scalebar.scalebar import ScaleBar
from ctypes     import wintypes, windll
from functools  import cmp_to_key
from matplotlib import cm
from matplotlib import colors
import numpy as np
import matplotlib.pyplot as plt
import os
import getpass
import wx
import imageio


try:
    plt.style.use('seaborn-v0_8-dark')     #  seaborn-dark  https://matplotlib.org/3.1.1/gallery/style_sheets/style_sheets_reference.html
except:
    plt.style.use('seaborn')              #  seaborn-dark  https://matplotlib.org/3.1.1/gallery/style_sheets/style_sheets_reference.html


def GUI_select_Multi_file(message):
    """ Function selects one or multiple PTU filenames via a GUI,
        It starts at the current working directory of the process
    """
    wildcard = "picoquant PTU (*.ptu)| *.ptu"
    app = wx.App(False, clearSigInt=False)
    frame = wx.Frame(None, -1, 'win.py', style=wx.STAY_ON_TOP)
    frame.SetSize(0,0,200,50)
    FilePicker = wx.FileDialog(frame, "Select you PTU files | single or Multiple", defaultDir=Default_prompt, wildcard=wildcard, style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST)
    FilePicker.ShowModal()
    FileNames=FilePicker.GetPaths()
    app.Destroy()
    return FileNames

def GUI_select_folder(message):
    """ A function to select a PTU filename via a GUI,
        It starts at the current working directory of the process
    """
    wildcard = "picoquant PTU (*.ptu)| *.ptu"
    app = wx.App(False, clearSigInt=False)
    path = wx.FileSelector(message='Select you the folder', default_path=Default_prompt, default_extension='*.ptu', wildcard=wildcard)
    directory,filename=os.path.split(path)
    app.Destroy()
    print('Selected file folder: '+path)
    return directory

def winsort(data):
    """ Python indexes files not as windows shows in File explorer this definition reorganises
    """
    _StrCmpLogicalW = windll.Shlwapi.StrCmpLogicalW
    _StrCmpLogicalW.argtypes = [wintypes.LPWSTR, wintypes.LPWSTR]
    _StrCmpLogicalW.restype  = wintypes.INT
    cmp_fnc = lambda psz1, psz2: _StrCmpLogicalW(psz1, psz2)
    return sorted(data, key=cmp_to_key(cmp_fnc))

def Read_objective():
    """ Extracts the objective setting in symphotime.
    Here you can add the full `name of the lens set in the microscope
    Set your objectives
    If objectives have been defined in Symphotime64 configuration these specific names are passed
    """
    lens=ptu_file.head['ImgHdr_ObjectiveName']    
    if lens =='20x':
        lens='UCPLFLN20x NA0.6'
    elif lens =='40x':
        lens=' PLN40x NA0.65'
    elif lens =='60x':
        lens=' UPLSAPO60x NA1.2'
    elif lens =='63x':
        lens=' C-planApo63x NA1.4'
    return lens

def Channels_list(data_stack):
    """Function screens all 4 data channels if intensity >0 channel is probably used and pit into the outlist 
    Practical sometime there a countable counts in an image, so intensity need to be larger than the number of lines pixY
    """
    ch=np.linspace(0,np.shape(flim_data_stack)[2]-1, np.shape(flim_data_stack)[2]).astype(int)
    CLSch=[Config1,Config2,Config3,Config4]
    out=np.empty(0)
    out2=np.empty(0)
    info= ''
    for i in ch:
      if np.sum(data_stack[:,:,i]) >= ptu_file.head["ImgHdr_PixY"]+5:
          out=np.append(out,CLSch[i])
          info=info+'Ch'+str(i+1)+' '
          out2=np.append(out2,'Ch'+str(i+1))
    return out, out2



def Read_SEPIA_used_laser_lines():
    """This fuction, extracts the used laser lines by reading the intensity from laser (Sep2_SLM_200_FineIntensity)
    if it's 0, it's OFF. 
    Returns an array of used laser lines: used for calulation in TimeGates
    info: string text of laser summary
    Colour_out: an array with sugested color used in AutoColour option    
    """
    recommend_colour=['Red','Yellow','Green','Blue']
    line=np.empty(0,dtype=int)
    str_info=''
    Colour_out=[]
    
    for i, a in enumerate([200,300,400,500,600]):
        try:
            #more robust exception when a PDL 828module is not installed or removed.
            if ptu_file.head[f"Sep2_SLM_{a}_FineIntensity"] !=0:
                line=np.append(line, int(ptu_file.head[f'UsrHeadName({i})'][:3]))
                Colour_out=np.append(Colour_out,recommend_colour[i])
                str_info=f'{str_info} '+str(int(ptu_file.head[f'UsrHeadName({i})'][:3]))+f'nm {ptu_file.head[f"Sep2_SLM_{a}_FineIntensity"]}% '  
        except:
            continue

    return line,str_info,Colour_out

def print_header_info(): 
    """ This function prints a short summary of exeperimental settings of the ptu file
    """
    print('-Experimental settings-----\n')
    print(f'Objective  {Read_objective()}')
    print(f"Resolution  {ptu_file.head['ImgHdr_PixX']} x {ptu_file.head['ImgHdr_PixY']}p")
    print(f"FOV         {ptu_file.head['ImgHdr_PixX']*ptu_file.head['ImgHdr_PixResol']} x {ptu_file.head['ImgHdr_PixY']*ptu_file.head['ImgHdr_PixResol']}um")
    print(f"Offset      {ptu_file.head['ImgHdr_X0']} x {ptu_file.head['ImgHdr_Y0']}um")
    print(f"Dwell Time  {ptu_file.head['ImgHdr_TimePerPixel']*1000:.1f} us")
    if ptu_file.head['ImgHdr_BiDirect']:
        print(f"Scanning:   bi-directional   offset {ptu_file.head['ImgHdr_BiDirectOffset']}")
    else:
        print('Scanning:   mono-directional')
    print(f"PTU File:   {ptu_file.head['ImgHdr_MaxFrames']} frame(s)")
    print(f"SYNC-rate:  {ptu_file.head['TTResult_SyncRate']/1E6:.1f} Mhz")
    print(f"\n-File comment--------------\n{ptu_file.head['File_Comment']}")    
    print('----------------------------\n')

if Save_tiff_LTstack:
    from PIL import Image
    def save_as_tif(framelist, name):
            imlist = [Image.fromarray(fr) for fr in framelist]
            imlist[0].save(name, compression="tiff_deflate", save_all=True, append_images=imlist[1:])

Errors=['']

#%% 

#Read PTU files SinglePick selects a single file
#Read Z-stack processes all *.ptu files in the folder (typica with a stack)

if GUI_MultiPick==True:
    #single or multiple proccess
    print('Single or Multiple files')
    path_select=GUI_select_Multi_file('Select a file')
    path_select=winsort(path_select) 
else:
    #FUll Folder proccess
    print('Converting all *.ptu images in the folder')
    GUI_MultiPick=False
    path =GUI_select_folder('Select a folder')
    os.listdir(path)
    FileList=[]
    
    
    for i, file in enumerate(os.listdir(path)):
    
       if file.endswith(".ptu"):
            FileList.append(os.path.join(path, file))
    path_select=winsort(FileList)    

#File list now goes into a for loop cycling over the files.

""" ################################################
########         MAIN Processing loop       ########
################################################ """

for path in path_select:
    #Main loop that procceses all *.PTU files (path_select) from Multiple file pick or folder
    
    #read ptu file
    print(f'FLIM_Database_NPZ = True\nConverting TCSPC-data from | {os.path.split(path)[1]} | to a fastFLIM image.\n')    
    ptu_file  = PTUreader((path), print_header_data = False)
    
    #File checking if its 1D or 2d: skip to next file if 1D
    if ptu_file.head["Measurement_SubMode"] !=  3:
        Errors=np.append(Errors,path)
        print('NOTE: File is a Point-measurement: skip to next *.PTU file')
        continue
    
    #make saveing file and directory names
    os.path.dirname(path)
    d_name, f_name=os.path.split(path)
    f_name, ex=os.path.splitext(f_name)
    
    if FLIM_Database_NPZ:
        db_name=f'{d_name}\\DataStack_DB'
        os.makedirs(db_name,exist_ok=True)
        db_name=f'{db_name}\\{f_name}.npz'
 
    print_header_info()
    #convert FIFO data into a histogram 4D x,y,channel, hsitodata, returns 4d datastack and intnsity image
    
    DataBase_present=False
    if FLIM_Database_NPZ and os.path.exists(db_name):
        print(f'NOTE: file already converted & loading flim_data_stack ..\DataStack_DB\{f_name}.npz')
        DataBase_present=True
        database=np.load(db_name) 
        flim_data_stack=database['flim_data_stack']
        intensity_image=database['intensity_image']
        #check if file is bi-direct and bi-shift is identical
        if ptu_file.head['ImgHdr_BiDirect'] and (np.abs(bi_shift - database['bi_shift'])) >= 0.001: # floatcomparisson thing
            print(f'NOTE: bi-shift {bi_shift:.1f}p is different from DataBase {database["bi_shift"]:.1f}p ! Photonconversion again and updating Database.')
            DataBase_present=False            
        
        print('')
        del database
        
   
    if DataBase_present==False:
        try:
            # READ PTU data into FLIM data stack
            print('Waiting: Photoconverting PTU to FLIM DataStack')
            flim_data_stack, intensity_image = ptu_file.get_flim_data_stack(bi_shift)
        except:
            Errors=np.append(Errors,path)
            print(f'WARNING: File-ERROR: in {f_name} in read PTU_reader get_Flim_data_stack ')
            continue
        
        #reduce data type(dont expect pixel tac values to go higer than 8or16bit)
        if np.max(flim_data_stack)<=255:
            flim_data_stack=flim_data_stack.astype(np.uint8)
            intensity_image=intensity_image.astype(np.uint16)
            bitdepth='as 8bit'
        else:
            flim_data_stack=flim_data_stack.astype(np.uint16)
            intensity_image=intensity_image.astype(np.uint16)
            bitdepth='as 16bit'
    
        if FLIM_Database_NPZ:
            print(f'NOTE: saving flim_data_stack ..\DataStack_DB\{f_name}.npz {bitdepth}')
            np.savez(db_name,flim_data_stack=flim_data_stack,intensity_image=intensity_image,bi_shift=np.array(bi_shift, dtype=np.float16))
  

    try:
        # search flim_data_stack for avaialble channels
        ch_list, _=Channels_list(flim_data_stack)
    except:
        Errors=np.append(Errors,path)
        print(f'WARNING: File-ERROR: in {f_name} channels auto detection')
        continue
        
   
    if Binning>=2:
        #Reshape the FLIM datastack for Binning
        print(f'NOTE: Binning mode is enabled by setting Binning to {Binning}!')
        #reshape by grouping adjecent pixels 2x2
        reshaped_flim_data_stack = flim_data_stack.reshape(int(np.shape(flim_data_stack)[0]/2), 2, int(np.shape(flim_data_stack)[1]/2), 2, np.shape(flim_data_stack)[2], np.shape(flim_data_stack)[3])
        flim_data_stack = reshaped_flim_data_stack.sum(axis=(1, 3))
        del reshaped_flim_data_stack
    
        reshaped_intensity_image = intensity_image.reshape(int(np.shape(intensity_image)[0]/2), 2, int(np.shape(intensity_image)[1]/2),2)
        intensity_image = reshaped_intensity_image.sum(axis=(1, 3))
        del reshaped_intensity_image
            
        ptu_file.head["ImgHdr_PixX"]=int(ptu_file.head["ImgHdr_PixX"]/Binning)
        ptu_file.head["ImgHdr_PixY"]=int(ptu_file.head["ImgHdr_PixY"]/Binning)
        ptu_file.head["ImgHdr_PixResol"] = ptu_file.head["ImgHdr_PixResol"]*Binning

    if Channel_Binning:
        # channel Binning
        initial_channels=len(ch_list)
        
        if 'Combined SPADs' not in ch_list[0].Name:
            ch_list[0].Name = f'{ch_list[0].Name} Combined SPADs'  
            ch_list[0].ChannelName = f'{ch_list[0].ChannelName}→{ch_list[len(ch_list)-1].Channel+1}'  
            folder_com=f'ChBin_{folder_com}'
        
        flim_data_stack=np.expand_dims(np.sum(flim_data_stack, axis=2), axis=2).astype(np.uint16)
        #Since channels are gone, configuration are copied from the first channel in the list
        ch_list=ch_list[:1]
        print("NOTE: Channel_Binning is enabled all channels are merged.")
        
    
    #Create supporting info
    LaserLines, LaserInfo, _ =Read_SEPIA_used_laser_lines()    
    Objective=Read_objective()
    d_name=f"{d_name}\Python_Converted_{folder_com}_{getpass.getuser()}\\"
    os.makedirs(d_name,exist_ok=True)
    
    #Making timegate boundaries and put these into each channel config files
    #convert optial TAC limit from ns to TAC timebins

    PieBaseLen=int(np.trunc(len(flim_data_stack[0,0,0])/len(LaserLines)))
        
    FLIM_sync_limit=ptu_file.head['ImgHdr_TimePerPixel']*Binning**2/(ptu_file.head['MeasDesc_GlobalResolution']*1000)*FLIM_Sync_Rate_Fraction    
    if Channel_Binning:
        FLIM_sync_limit=initial_channels*FLIM_sync_limit
    
    print(f'FLIM datastack ready - creating FLIM image  20% Sync limit = {FLIM_sync_limit:.0f}cnts')
    
    if ptu_file.head['UsrPulseCfg'] == 'PIE':
        print(f'PIE Excitation: {LaserInfo}')
        Excitation=f'PIE {LaserInfo}'
        for chan in ch_list:
            chan.TAC_start=  (chan.TimeGate*PieBaseLen)+round(TCSPC_PIE_Start_ns/(ptu_file.head['MeasDesc_Resolution']*1E9))
            chan.TAC_stop =  (chan.TimeGate*PieBaseLen)+round(TCSPC_PIE_End_ns/(ptu_file.head['MeasDesc_Resolution']*1E9))
            print(f'TimeGate {chan.ChannelName} {chan.TAC_start*ptu_file.head["MeasDesc_Resolution"]*1E9:.1f}-{chan.TAC_stop*ptu_file.head["MeasDesc_Resolution"]*1E9:.1f}ns')
    else:
        print(f'Normal Excitation: {LaserInfo}')
        Excitation=f'Normal {LaserInfo}'
        for chan in ch_list:
            chan.TAC_start=  0+round(TCSPC_PIE_Start_ns/(ptu_file.head['MeasDesc_Resolution']*1E9))
            chan.TAC_stop =  round(TCSPC_PIE_End_ns/(ptu_file.head['MeasDesc_Resolution']*1E9))
   
        #Loop over channel configurations and fill the color the FLIM colourscale

   
#%% Data FLIM converation and Colourmap generation

    for chan in ch_list:
               
        #import average lifetime over the configuration/channel files
        try:
            chan.FFtav , chan.FFint = get_lifetime_image(flim_data_stack, chan.Channel, chan.TAC_start, chan.TAC_stop, ptu_file.head['MeasDesc_Resolution']*1E9, chan.irf)
        except:
               Errors=np.append(Errors,path)
               print('WARNING: error in FLIM tavg conversion ')
               continue
        #replace nan for -1
        chan.FFtav[np.isnan(chan.FFtav)] = -1
        
        #set cmap boundaries
        if chan.Tau_min !=Tau_min:
            chan.Tau_min=Tau_min
        if chan.Tau_max !=Tau_max:
            chan.Tau_max=Tau_max

        #aplication of a CMAP on FLIMdata does not supress the darks 
        #To normalize cmap, 1) IRF is subracted 2) and normalzied to Tau_max 3) outliers are clipped beteen 0:1
        #Here a cmap is apllied on the FLIM data, that generates a RGB image
        #Most convient is to convert RGB→HSV and apply the intensity to the V plane of the HSV and get back HSV→RGB                 
   
        #CMAP also gives a RGBI array only RGB are passed by [:,:,:3]
        FLIM_hsv=colors.rgb_to_hsv(cm.jet(np.clip(((chan.FFtav-chan.Tau_min)/(chan.Tau_max-chan.Tau_min)),0,1))[:,:,:3])
        #overwrite the intensity map with the real intensity map (in HSV colorspace it's easier than RGB space)
        FLIM_hsv[:,:,2]=np.clip(chan.FFint/(np.max(chan.FFint)*(1/chan.Brighter)),0,1)
        chan.FFcmap =  colors.hsv_to_rgb(FLIM_hsv)
                
        if Save_data_files:
            d_name_dat=f"{d_name}dat files\\"
            os.makedirs(d_name_dat,exist_ok=True)
            np.savetxt(f'{d_name_dat}{f_name}_FLIM_tav_{chan.ChannelName}_{chan.Name}.dat', chan.FFtav, delimiter=',',fmt='%.3f')
            np.savetxt(f'{d_name_dat}{f_name}_FLIM_int_{chan.ChannelName}_{chan.Name}.dat', chan.FFint  , delimiter=',',fmt='%i')
        
  
#%%      
    
    """ #################################################################################
    ############              Image are plotted from here                    ############
    ##################################################################################"""

    #Create some usefull header strings
    date=ptu_file.head["File_CreatingTime"].split(sep=' ')
    DwellTime=f'Pixel dwell-time: {ptu_file.head["ImgHdr_TimePerPixel"]*1000:.1f}$\mu$s'
    extent=[0, ptu_file.head["ImgHdr_PixX"]*ptu_file.head["ImgHdr_PixResol"],ptu_file.head["ImgHdr_PixY"]*ptu_file.head["ImgHdr_PixResol"],0]
    image_pixels=f' | size {ptu_file.head["ImgHdr_PixX"]}x{ptu_file.head["ImgHdr_PixY"]} {ptu_file.head["ImgHdr_PixResol"]:.2f}µm/p  |  sync {ptu_file.head["TTResult_SyncRate"]/1E6:.1f}MHz  |  LIM {FLIM_sync_limit:.0f}cnt.'
    if ptu_file.head['ImgHdr_BiDirect']:
        scan_mode=f'|  ↔ {bi_shift:.1f}p'
    else:
        scan_mode= '|  →'
    
 
    
    for  chan in ch_list:
        
         fig2, axs = plt.subplots(1, 2, figsize=(15.9, 7.5))
         rect = fig2.patch  #modify background color
         rect.set_facecolor('white')
         
         #The sync limit will be show in the int bar, so it needs to be manualy defined here
         int_steps= np.round(np.max(chan.FFint)/7, decimals=-2)
         int_ticks=np.arange(int_steps, np.max(chan.FFint)+int_steps, int_steps)
         
         plt.figtext(0.127,0.925,  f'PTU file: {f_name}', fontsize=14, weight='medium')
         plt.figtext(0.127,0.895  ,f'Time: {date[1]}  {date[0]}  |  {Excitation}  |  {Objective}  {scan_mode}')
         plt.figtext(0.127,0.875  ,f'{DwellTime} {image_pixels}')
         im1 = axs[0].imshow( chan.FFint, cmap='gray', extent=extent)         
                 
         #modification in the intensity cale the sync limit value is replaced with the clossest tick.
                  
         int_ticks[np.abs(int_ticks-FLIM_sync_limit).argmin()]=FLIM_sync_limit
         cbar=fig2.colorbar(im1, ax=axs[0], fraction=0.047, pad=0.02, shrink=0.8, ticks= int_ticks)
         cbar.ax.axhline(FLIM_sync_limit, c='r')
         cbar.ax.tick_params(labelsize=12)
         cbar.set_label('Intensity [counts]', labelpad=8, rotation=90, size=13)
        
         axs[0].set_xlabel('X $\mu$m')
         axs[0].set_ylabel('Y $\mu$m')
         axs[0].grid(False)
                  
         im2 = axs[1].imshow(chan.FFcmap, extent=extent)
         im2.set_cmap(cm.jet) #manual set of colorbar cmap 
         im2.set_clim([chan.Tau_min,chan.Tau_max]) #manaual set range of the colorbar cm
         cbar=fig2.colorbar(im2, ax=axs[1], fraction=0.047, pad=0.02, shrink=0.8, ticks=np.linspace(chan.Tau_min,chan.Tau_max,tav_cbar_ticks))
         cbar.ax.tick_params(labelsize=12)
         cbar.set_label('Average lifetime [ns]', labelpad=8, rotation=90, size=13)

         #ptu_file.head["ImgHdr_PixResol"]
         axs[1].set_title(f'fastFLIM | {chan.ChannelName}: {chan.Name}', size=13)
         if scalebar:
             scalebar_s = ScaleBar(1E-6, location="lower right",  height_fraction=0.015, box_color="black", color="white", pad=1, sep=2, box_alpha=0.25, frameon=True, font_properties={'size':16} ) # 1 pixel = 0.2 meter
             plt.gca().add_artist(scalebar_s)
             plt.axis('off')
         else:        
             axs[1].set_xlabel('X $\mu$m')
             axs[1].set_ylabel('Y $\mu$m')
             axs[1].grid(False)
            
         plt.savefig(f'{d_name}{f_name}__FLIM_{chan.ChannelName}.png',dpi=Fig_dpi)
         
         plt.show()
         
         if Clean_Imsave:
             d_name_tif=f"{d_name}tif files\\"
             os.makedirs(d_name_tif,exist_ok=True)             
             imageio.imwrite(f'{d_name_tif}FLIM_im_{f_name}_{chan.ChannelName}.tif', (255*chan.FFcmap).astype(np.uint8))
             imageio.imwrite(f'{d_name_tif}INT__im_{f_name}_{chan.ChannelName}.tif', chan.FFint.astype(np.uint16))

#%%             
                 
    if len(ch_list)>1 and overlap_FLIMchannels:
        
        if overlap_projection=='sum':
            FFI=0
            FFcmap=0    
            for chan in ch_list:
                FFI=FFI+chan.FFint
                FFcmap=FFcmap+chan.FFcmap
            
        if overlap_projection== 'maximum':
            if len(ch_list)==2:
                FFcmap=np.max(np.stack((ch_list[0].FFcmap, ch_list[1].FFcmap), axis = -1), axis=3)
                FFI   =np.maximum(ch_list[0].FFint, ch_list[1].FFint)
            if len(ch_list)==3:
                FFcmap=np.max(np.stack((ch_list[0].FFcmap, ch_list[1].FFcmap, ch_list[2].FFcmap), axis = -1), axis=3)
                FFI=np.maximum(np.maximum(ch_list[0].FFint, ch_list[1].FFint), ch_list[2].FFint)
            if len(ch_list)==4:
                FFcmap=np.max(np.stack((ch_list[0].FFcmap, ch_list[1].FFcmap, ch_list[2].FFcmap, ch_list[3].FFcmap), axis = -1), axis=3)
                FFI=np.maximum(np.maximum(np.maximum(ch_list[0].FFint, ch_list[1].FFint), ch_list[2].FFint), ch_list[3])
        
            
        
        fig3, axs = plt.subplots(1, 2, figsize=(15.9, 7.5))
        rect = fig2.patch  #modify background color
        rect.set_facecolor('white')
        #fig2.suptitle(' Nanobiophysics - PicoQuant MT200', fontsize=14, weight='bold')
        plt.figtext(0.127,0.925,  f'PTU file: {f_name}', fontsize=14, weight='medium')
        plt.figtext(0.127,0.895  ,f'Time: {date[1]}  {date[0]}  |  {Excitation}  |  {Objective}  {scan_mode}')
        plt.figtext(0.127,0.875  ,f'{DwellTime} {image_pixels}')
        
        int_steps= np.round(np.max(chan.FFint)/7, decimals=-2)
        int_ticks=np.arange(int_steps, np.max(chan.FFint)+int_steps, int_steps)
                
        im1 = axs[0].imshow( FFI, cmap='gray', extent=extent)         

        cbar=fig3.colorbar(im1, ax=axs[0], fraction=0.047, pad=0.02, shrink=0.8, ticks= int_ticks)
        cbar.ax.tick_params(labelsize=12)
        cbar.set_label('Intensity [counts]', labelpad=8, rotation=90, size=13)
        axs[0].set_xlabel('X $\mu$m')
        axs[0].set_ylabel('Y $\mu$m')
        axs[0].grid(False)
        
        im2 = axs[1].imshow(FFcmap, extent=extent)
        im2.set_cmap(cm.jet) #manual set of colorbar cmap 
        im2.set_clim([chan.Tau_min,chan.Tau_max]) #manaual set range of the colorbar cm
        cbar=fig3.colorbar(im2, ax=axs[1], fraction=0.047, pad=0.02, shrink=0.8, ticks=np.linspace(chan.Tau_min,chan.Tau_max,tav_cbar_ticks))
        cbar.ax.tick_params(labelsize=12)
        cbar.set_label('Average lifetime [ns]', labelpad=8, rotation=90, size=13)
        cbar.ax.axhline(FLIM_sync_limit, c='r')
        
        #ptu_file.head["ImgHdr_PixResol"]
        axs[1].set_title(f'{overlap_projection} projection | fastFLIM | all channels ', size=13)
        if scalebar:
            scalebar_s = ScaleBar(1E-6, location="lower right",  height_fraction=0.015, box_color="black", color="white", pad=1, sep=2, box_alpha=0.25, frameon=True, font_properties={'size':16} ) # 1 pixel = 0.2 meter
            plt.gca().add_artist(scalebar_s)
            plt.axis('off')
        else:        
            axs[1].set_xlabel('X $\mu$m')
            axs[1].set_ylabel('Y $\mu$m')
            axs[1].grid(False)
           
        plt.savefig(f'{d_name}{f_name}__FLIM_overlap_{chan.ChannelName}.png',dpi=Fig_dpi)
        
        if Clean_Imsave:
            d_name_tif=f"{d_name}tiff images\\"
            os.makedirs(d_name_tif,exist_ok=True)  
            imageio.imwrite(f'{d_name_tif}FLIM_combi_im_{f_name}_{chan.ChannelName}.tif', (255*FFcmap).astype(np.uint8))
            imageio.imwrite(f'{d_name_tif}INT_combi_im_{f_name}_{chan.ChannelName}.tif', FFI.astype(np.uint16))
            
        plt.show()

    if Save_tiff_LTstack:
        d_name_tifstack=f"{d_name}LT_tiff_stack\\"
        os.makedirs(d_name_tifstack,exist_ok=True)
        for i, chan in enumerate(ch_list):
            #save each channel as a tiffstack     
            save_as_tif(flim_data_stack[:,:,i,:].transpose(2,0,1),f'{d_name_tifstack}{f_name}__{chan.ChannelName}.tif')

#%%

#ERROR Summary

if len(Errors) != 1  and len(path_select) >= 2:
    print('FLIM file-conversion errors in:')
    for Err in Errors:
        print(Err)
elif len(Errors) == 1 and len(path_select) >= 2:
    print('All *.PTU files proccessed succesfully')     



