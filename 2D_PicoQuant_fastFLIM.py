# -*- coding: utf-8 -*-
#Copyright Robert Molenaar 240731

#Update FLIM reader, to accept a specific tac range. (min TAC output is set to 0ns).
#Accept bidirectional scanning, added PIE support and binning.

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



Config1 = Set_Channel_Info(1,
                           'Ch1 name'   ,
                           Brighter=1.2      ,
                           PIE_TimeGate=1  ,
                           ch_irf=2.55)

Config2 = Set_Channel_Info(2,
                           'Ch2 name'      ,
                           Brighter=1.2      ,
                           PIE_TimeGate=2  ,
                           ch_irf=2.25)

Config3 = Set_Channel_Info(3,
                           'Ch3 name',
                           Brighter=1.2          ,
                           PIE_TimeGate=2     , 
                           ch_irf=2.6)
Config4 = Set_Channel_Info(4,  
                           'Ch4 name'  ,
                           Brighter=1.2    ,
                           PIE_TimeGate=3      , 
                           ch_irf=2.55)

#File picking    
GUI_MultiPick=True    #Set TO Flase to proccess the full folder with the GUI
Default_prompt=r'C:'


Tau_min=0                       #start Lifetime Cmap from if set
Tau_max=4                       #end Lifetime Cmap at, above is clipped

shorter_End_PIE_ns   =  0       #cut a piece from the initial x ns 
shorter_Front_PIE_ns =  0       #cut a piece from the start TAC ns to surpess noise
binning              =  1       #Pixel binning 1,2,3 = 1x1, 2x2 , 3x3 etc before fastFLIM conversion
bi_shift             = -1       #bidirectional scanning mode, line mismatch correction

scalebar            =True       #insert a scalebar in FLIM image instead of axis
scalebar_ticks      = 5         #number of ticks in the cmap

#Saving optons
clean_imsave        =True       #save tif files, intensity and cmap
Save_data_files     =True       #Write CSV data files with intensity of all channels 8.dat
fig_dpi             =200        #output figure resolution 100→300

folder_com_pre      =''          #optinal prefic for a saving folder
folder_com          =f'{folder_com_pre}TAC_{Tau_min:.2f}-{Tau_max:.2f}'

overlap_FLIMchannels=False      #in multchannels image cab be ovelapped 
projection          ='maximum'   #or 'sum'


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
    Here you can add the full `name of the lens set in the microscop
    Set your objectives
    If objectives have been defined in Symphotime64 configuration these specific names is passed
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
    ch=[0,1,2,3]
    CLSch=[Config1,Config2,Config3,Config4]
    out=np.empty(0)
    out2=np.empty(0)
    info= ''
    for i in ch:
      if np.sum(data_stack[:,:,i]) >= ptu_file.head["ImgHdr_PixY"]+5:
          out=np.append(out,CLSch[i])
          info=info+'Ch'+str(i+1)+' '
          out2=np.append(out2,'Ch'+str(i+1))
    #print(info+'detected in file: '+f_name)
    #print('Image size: '+str(ptu_file.head['ImgHdr_PixX'])+'p x '+str(ptu_file.head['ImgHdr_PixY'])+'p  Objective: '+Read_objective())
    return out, out2



def Read_SEPIA_used_laser_lines():
    """This fuction, extracts the used laser lines by reading the intensity from laser (Sep2_SLM_200_FineIntensity)
    if it's 0, it's OFF. 
    Returns an array of used laser lines: used for calulation in TimeGates
    info: string text of laser summary
    Colour_out: an array with sugested color used in AutoColour option    
    """
    PDL828_laser_line=[638,560,488,405]    # Set avaialble lasers lines at the SEPIA slot 0,1,2,3
    PDL828_module=[200,300,400,500]   #names of lasers moduls in ptu headerfile
    recommend_colour=['Red','Yellow','Green','Blue']
    out=np.empty(0,dtype=int)
    Colour_out=[]
    info=''

    for i, a in enumerate(PDL828_module):
        if ptu_file.head[f"Sep2_SLM_{a}_FineIntensity"] !=0:
            out=np.append(out,PDL828_laser_line[i])
            Colour_out=np.append(Colour_out,recommend_colour[i])
            info=f'{info} {PDL828_laser_line[i]}nm {ptu_file.head[f"Sep2_SLM_{a}_FineIntensity"]}% '  
    return out,info,Colour_out



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
    print(f"PTU File:   {ptu_file.head['ImgHdr_MaxFrames']} frames")
    print(f"SYNC-rate:  {ptu_file.head['TTResult_SyncRate']/1E6} Mhz")
    print(f"\n-File comment--------------\n{ptu_file.head['File_Comment']}")    
    print('----------------------------\n')
    


Errors=['']
#Z_Slice=0
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
    head, tail = os.path.split(path)
    print('\nConverting TCSPC-data from | '+tail+ ' | to a fastFLIM image.')    
    ptu_file  = PTUreader((path), print_header_data = False, bi_shift=bi_shift)
    
    #File checking if its 1D or 2d: skip to next file if 1D
    if ptu_file.head["Measurement_SubMode"] !=  3:
        Errors=np.append(Errors,path)
        print('NOTE: File is a Point-measurement: skip to next *.PTU file')
        continue
        
    #make saveing file and directory names
    os.path.dirname(path)
    d_name, f_name=os.path.split(path)
    f_name, ex=os.path.splitext(f_name)
    d_name=f"{d_name}\Python_Converted_{folder_com}_{getpass.getuser()}\\"
    os.makedirs(d_name,exist_ok=True)

    print_header_info()
    #convert FIFO data into a histogram 4D x,y,channel, hsitodata, returns 4d datastack and intnsity image
    
    try:
        # READ PTU data into FLIM data stack
        flim_data_stack, intensity_image = ptu_file.get_flim_data_stack()
    except:
        Errors=np.append(Errors,path)
        print(f'WARNING: File-ERROR: in {f_name} to read Datastack ')
        continue
    
    try:
        # search flim_data_stack for use dchannels
        ch_list, _=Channels_list(flim_data_stack)
    except:
        Errors=np.append(Errors,path)
        print(f'WARNING: File-ERROR: in {f_name} channels auto detection')
        continue
    
   
    if binning>=2:
        #Reshape the FLIM datastack for binning
        print(f'NOTE: Binning mode is enabled by setting binning to {binning}!\n')
        #reshape by grouping adjecent pixels 2x2
        reshaped_flim_data_stack = flim_data_stack.reshape(int(np.shape(flim_data_stack)[0]/2), 2, int(np.shape(flim_data_stack)[1]/2), 2, np.shape(flim_data_stack)[2], np.shape(flim_data_stack)[3])
        flim_data_stack = reshaped_flim_data_stack.sum(axis=(1, 3))
        del reshaped_flim_data_stack
    
        reshaped_intensity_image = intensity_image.reshape(int(np.shape(intensity_image)[0]/2), 2, int(np.shape(intensity_image)[1]/2),2)
        intensity_image = reshaped_intensity_image.sum(axis=(1, 3))
        del reshaped_intensity_image
            
        ptu_file.head["ImgHdr_PixX"]=int(ptu_file.head["ImgHdr_PixX"]/binning)
        ptu_file.head["ImgHdr_PixY"]=int(ptu_file.head["ImgHdr_PixY"]/binning)
        ptu_file.head["ImgHdr_PixResol"] = ptu_file.head["ImgHdr_PixResol"]*binning
    #extra info
    
    LaserLines, LaserInfo, _ =Read_SEPIA_used_laser_lines()    
    Objective=Read_objective()
    
    #Making timegate boundaries and put these into each channel config files
    #convert optial TAC limit from ns to TAC timebins

    PieBaseLen=int(np.trunc(len(flim_data_stack[0,0,0])/len(LaserLines)))
        
    if ptu_file.head['UsrPulseCfg'] == 'PIE':
        print(f'PIE Excitation: {LaserInfo}')
        Excitation=f'PIE {LaserInfo}'
        for chan in ch_list:
            chan.TAC_start=  (chan.TimeGate*PieBaseLen)+round(shorter_Front_PIE_ns/(ptu_file.head['MeasDesc_Resolution']*1E9))
            chan.TAC_stop =  ((chan.TimeGate+1)*PieBaseLen)-round(shorter_End_PIE_ns/(ptu_file.head['MeasDesc_Resolution']*1E9))
            print(f'TimeGate {chan.ChannelName} {chan.TAC_start*ptu_file.head["MeasDesc_Resolution"]*1E9:.1f}-{chan.TAC_stop*ptu_file.head["MeasDesc_Resolution"]*1E9:.1f}ns')
    else:
        print(f'Normal Excitation: {LaserInfo}')
        Excitation=f'Normal {LaserInfo}'
        for chan in ch_list:
            chan.TAC_start=  0+round(shorter_Front_PIE_ns/(ptu_file.head['MeasDesc_Resolution']*1E9))
            chan.TAC_stop =  PieBaseLen-round(shorter_End_PIE_ns/(ptu_file.head['MeasDesc_Resolution']*1E9))
   
        #Loop over channel configurations and fill the color the FLIM colourscale

    FLIM_sync_limit=ptu_file.head['ImgHdr_TimePerPixel']*binning**2/(ptu_file.head['MeasDesc_GlobalResolution']*1000)*.2    
    print(f'FLIM conversion  20pct Photon rate = {FLIM_sync_limit:.0f}cnts')
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
    image_pixels=f' | size {ptu_file.head["ImgHdr_PixX"]}x{ptu_file.head["ImgHdr_PixY"]} {ptu_file.head["ImgHdr_PixResol"]:.3f}µm/p | 20% sync lim {FLIM_sync_limit:.0f}cnt | Rate {ptu_file.head["TTResult_SyncRate"]/1E6:.1f}MHz '
 
        
    for  chan in ch_list:
        
         fig2, axs = plt.subplots(1, 2, figsize=(15.9, 7.5))
         rect = fig2.patch  #modify background color
         rect.set_facecolor('white')
         #fig2.suptitle(' Nanobiophysics - PicoQuant MT200', fontsize=14, weight='bold')
         plt.figtext(0.127,0.925,  f'PTU file: {f_name}', fontsize=14, weight='medium')
         plt.figtext(0.127,0.895  ,f'Time: {date[1]}  {date[0]}  |  {Excitation}  |  {Objective}')
         plt.figtext(0.127,0.875  ,f'{DwellTime} {image_pixels}')
         im1 = axs[0].imshow( chan.FFint, cmap='gray', extent=extent)         
         
         cbar=fig2.colorbar(im1, ax=axs[0], fraction=0.047, pad=0.02, shrink=0.8)
         cbar.ax.tick_params(labelsize=12)
         cbar.set_label('Intensity [counts]', labelpad=8, rotation=90, size=13)
         axs[0].set_xlabel('X $\mu$m')
         axs[0].set_ylabel('Y $\mu$m')
         axs[0].grid(False)
                  
         im2 = axs[1].imshow(chan.FFcmap, extent=extent)
         im2.set_cmap(cm.jet) #manual set of colorbar cmap 
         im2.set_clim([chan.Tau_min,chan.Tau_max]) #manaual set range of the colorbar cm
         cbar=fig2.colorbar(im2, ax=axs[1], fraction=0.047, pad=0.02, shrink=0.8, ticks=np.linspace(chan.Tau_min,chan.Tau_max,scalebar_ticks))
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
            
         plt.savefig(f'{d_name}{f_name}__FLIM_{chan.ChannelName}.png',dpi=fig_dpi)
         
         plt.show()
         
         if clean_imsave:
             d_name_tif=f"{d_name}tif files\\"
             os.makedirs(d_name_tif,exist_ok=True)             
             imageio.imwrite(f'{d_name_tif}FLIM_im_{f_name}_{chan.ChannelName}.tif', (255*chan.FFcmap).astype(np.uint8))
             imageio.imwrite(f'{d_name_tif}INT__im_{f_name}_{chan.ChannelName}.tif', chan.FFint.astype(np.uint16))

#%%             
                 
    if len(ch_list)>1 and overlap_FLIMchannels:
        
        if projection=='sum':
        
            for chan in ch_list:
                FFI=FFI+chan.FFint
                FFcmap=FFcmap+chan.FFcmap
            
        if projection== 'maximum':
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
        plt.figtext(0.127,0.895  ,f'Time: {date[1]}  {date[0]}  |  {Excitation}  |  {Objective}')
        plt.figtext(0.127,0.875  ,f'{DwellTime} {image_pixels}')
        im1 = axs[0].imshow( FFI, cmap='gray', extent=extent)         
        
        cbar=fig3.colorbar(im1, ax=axs[0], fraction=0.047, pad=0.02, shrink=0.8)
        cbar.ax.tick_params(labelsize=12)
        cbar.set_label('Intensity [counts]', labelpad=8, rotation=90, size=13)
        axs[0].set_xlabel('X $\mu$m')
        axs[0].set_ylabel('Y $\mu$m')
        axs[0].grid(False)
        
        im2 = axs[1].imshow(FFcmap, extent=extent)
        im2.set_cmap(cm.jet) #manual set of colorbar cmap 
        im2.set_clim([chan.Tau_min,chan.Tau_max]) #manaual set range of the colorbar cm
        cbar=fig3.colorbar(im2, ax=axs[1], fraction=0.047, pad=0.02, shrink=0.8, ticks=np.linspace(chan.Tau_min,chan.Tau_max,scalebar_ticks))
        cbar.ax.tick_params(labelsize=12)
        cbar.set_label('Average lifetime [ns]', labelpad=8, rotation=90, size=13)
        
        #ptu_file.head["ImgHdr_PixResol"]
        axs[1].set_title(f'{projection} projection | fastFLIM | all channels ', size=13)
        if scalebar:
            scalebar_s = ScaleBar(1E-6, location="lower right",  height_fraction=0.015, box_color="black", color="white", pad=1, sep=2, box_alpha=0.25, frameon=True, font_properties={'size':16} ) # 1 pixel = 0.2 meter
            plt.gca().add_artist(scalebar_s)
            plt.axis('off')
        else:        
            axs[1].set_xlabel('X $\mu$m')
            axs[1].set_ylabel('Y $\mu$m')
            axs[1].grid(False)
           
        plt.savefig(f'{d_name}{f_name}__FLIM_overlap_{chan.ChannelName}.png',dpi=fig_dpi)
        
        plt.show()

   

#%%

#ERROR Summary

if len(Errors) != 1  and len(path_select) >= 2:
    print('FLIM file-conversion errors in:')
    for Err in Errors:
        print(Err)
elif len(Errors) == 1 and len(path_select) >= 2:
    print('All *.PTU files proccessed succesfully')     



