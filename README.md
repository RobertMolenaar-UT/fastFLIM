# fastFLIM
PicoQuant PTU file to fastFLIM images

![Shep2_6__FLIM_Ch2](https://github.com/user-attachments/assets/4f1da1a4-1492-414a-8a13-f48ac49522c4)
*Example: example 1 channel fastFLIM converted image*

#
The script is developed and tested on Python 3.11, Install:

- wx python 4.2.1 for the file selector app.
- PicoQuant PTU file reader: https://github.com/RobertMolenaar-UT/readPTU_FLIM

Script is used on a Picoquant MT200 with FLIMBEE laserscanner with 4x SPAD detectors and a multiharp 150.

the main purpose of the MultiChannel script is one can convert batchwise multiple PTU files or a folder with PTU files and get a series Fluorescent fastFLIM images with minimal user input. Usefull for screening results during imaging and to be used in presentations.

Scripts features:  
- File Check, if it is a 2D  image.
- Autodetects the number of APD channels. 
- Supports 'PIE' and 'normal' excitation, one can set channel Timegate
- fastFLIM Conversion
- opional Image pixel binning
- optional Clean TIF images and datafiles are stored
- Common exp file-errors are catched and reported in the end.

Detector Channels need to be configured:
Config1 = Set_Channel_Info(1,
                           'Namelabel'   ,
                           Brighter=1.2      ,
                           PIE_TimeGate=1  ,
                           ch_irf=2.55)

1. *Namelabel*: name of the used coloring or dye.
2. *Brigther*: 	intensity is maximum scaled, increasing brightness helps visibility
3. *PIE TimeGate*: Contrast can be enhanced by using PIE excitation in the experiment to supress any cross-excitation 
	- NOTE: LASER fire order is first the longest wavelenght down to shortest wavelenght as last.
4. *ch_irf*: instrument response, channel specific time offset.

5. readPTU_FLIM_bidirect is modified from https://github.com/RobertMolenaar-UT/readPTU_FLIM and expanded with bidirection lineoffset correction. bi-direct set pixles shift.
   

# Set your MT200 SETUP:

1.  Change the laser lines in order of the SEPIAII rackposition *PDL828_laser_line=[638,560,488,405]*. If lasers are in installed in different SEPIAII rack positions assign these in *def Read_laserLines()*  PDL828_module=[200,300,400,500]  #names of the lasers modules in ptu headerfile of rack position [2,3,4,5] 	
2.  Set the objective full name in Symphotimetime64 application or in the function *Read_objective()*

# Usage: 

1. Set the Channel configuration according optical setup.
2. Read and set all options in the section --- USER input---  upon description.
3. Run the PiqoQuant-multi_channel_screen.py.
4. Note the pop-up window in the taskbar and browse and select the PTU files.
5. PTU files are proccessed, and images are shown in the command line. (large PTU files can take some time to proccess)
6. Images and data files are saved in folder /Python_converted_* Username* /
7. Errors on files are listed in the end, in many cases these are Single Point or cancelled 2D measurements.

Known limitations: 

1. Multiframe PTU conversion appears to skip a Frame, modification needed in the readPTU_FLIM code. aug '24


v1.0 July 2021 Robert Molenaar 




![alt text](https://github.com/RobertMolenaar-UT/PicoQuant-multi_channel_screen/blob/main/Example-Z-stack-projection_1024.png?raw=true)
*Example: Z-stack maximum-projectionm with 3 ch PIE excitation* 






# Workflow summary
 
wx 'GUI_select_Multi_file' app prompts to select (multiple) data files. 

The main For-loop proccesses all files sequentially.

1. The PTU file is read by "ptu_file  = PTUreader((path), print_header_data = False)"
2. File is checked if it's a 2D image file:
3. The PTU file is converted "flim_data_stack, intensity_image = ptu_file.get_flim_data_stack()"
4. FLIM stack is checked for avaialbe channels 'ch_list, ch_listst=Channels_list(flim_data_stack)'
5. first a CS (ColorStack) is created and [ch,x,y,RGB] 
6. second a CZ (Channel_Z) is created (Z slices, x,y,ch]
7A. Filling CZ and CS based on PIE excitation out of the flim_data_stack
	- Calculate the TimeGates
	- CZ Extract from flim_dat_stack the corresponding Ch and PIE-timeGate the stack
	- CS Extract from flim_dat_stack the corresponding Ch and PIE-timeGate the stack, and convert to colour plane by Fill_Colour()
7B. Filling CZ and CS based on Normal excitation out of the flim_data_stack
	- CZ Extract from flim_dat_stack the corresponding Ch and full TAC range the stack
	- CS Extract from flim_dat_stack the corresponding Ch and full TAC range the stack, and convert to colour plane by Fill_Colour(). 

8. Data files are saved
9. Images are created according the number of avaialble channels
10. Optional FRET 
	- FRET donor TimeGate and channels are regognized.
	- FRET efficiency is calculated per pixel.
	- Images are made. caption information is extracted from the 'configX' avaialble from the 'ch_list'
	- Mask intensity for FRET efficiency and histogram.
11. Z stack image projection and Orthogonal planes are made.
	- CZ contains [z, x,y,ch] 
	- For the XY plane the 'mean'or 'max' value is used for the x,y pixel value for each color channel.



