# fastFLIM
PicoQuant PTU file to fastFLIM images

![Shep2_6__FLIM_Ch2](https://github.com/user-attachments/assets/4f1da1a4-1492-414a-8a13-f48ac49522c4)
*Example: example 1 channel fastFLIM converted image, of cells labbelled with FluoVolt dye, that shows change in lifetime*

The script is developed and tested on Python 3.11, Install:

- wx python 4.2.1 for the file selector app.
- imageIO
- scalebar 
- PicoQuant PTU file reader: https://github.com/RobertMolenaar-UT/readPTU_FLIM

Script is used on a Picoquant MT200 with FLIMBEE laserscanner with 4x SPAD detectors and a multiharp 150.

The main purpose of the fastFLIM script is one can convert batchwise multiple PTU files or a folder with PTU files and get a series Fluorescent fastFLIM images with minimal user input. Usefull for screening results during imaging and to be used in presentations.

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

1. *Namelabel*: name of the used dye or sample.
2. *Brigther*: 	intensity is maximum scaled, increasing brightness helps visibility
3. *PIE TimeGate*: Contrast can be enhanced by using PIE excitation in the experiment to supress any cross-excitation 
	- NOTE: LASER fire order is first the longest wavelenght down to shortest wavelenght as last.
4. *ch_irf*: instrument response, channel specific time offset.
5. readPTU_FLIM_bidirect is modified from https://github.com/RobertMolenaar-UT/readPTU_FLIM and expanded with bidirection lineoffset correction. bi-direct variable set pixles shift correction.

![Screenshot 2024-08-01 115904](https://github.com/user-attachments/assets/d5c1737b-26cc-4bff-8c75-d49b447a3d44)
*Example:Command line summary*

# Modification to your your MT200:

1.  Change the laser lines in order of the SEPIAII rackposition *PDL828_laser_line=[638,560,488,405]*. If lasers are in installed in different SEPIAII rack positions assign these in *def Read_laserLines()*  PDL828_module=[200,300,400,500]  #names of the lasers modules in ptu headerfile of rack position [2,3,4,5] 	
2.  Set the objective full name in Symphotimetime64 application or in the function *Read_objective()*

# Usage: 

Put the 2D_PicoQuant_fastFLIM.py and readPU_FLUM_bidirect.py files in the sample folder. (preferable with you data)

1. Set the Channel configuration according optical setup.
2. Read and set all options in the section --- USER input---  upon description.
3. Run the PiqoQuant-multi_channel_screen.py.
4. Note the pop-up window in the taskbar and browse and select the PTU files.
5. PTU files are proccessed, and images are shown in the command line. (large PTU files can take some time to proccess)
6. Images and data files are saved in folder /Python_converted_* Username* /
7. Errors on files are listed in the end, in many cases these are Single Point or cancelled 2D measurements.

Known limitations: 

1. Files sizes > 1GB use a lot of Memory. 64GB or higher is recommended for 1GB ptu files. 
2. Multiframe PTU conversion appears to skip a Frame, modification needed in the readPTU_FLIM code. aug '24


v1.0 - 1 August 2024 Robert Molenaar 



# Workflow summary
 
wx 'GUI_select_Multi_file' app prompts to select (multiple) data files. 

The main For-loop proccesses all files sequentially.

1. The PTU file is read by "ptu_file  = PTUreader((path), print_header_data = False)"
2. File is checked if it's a 2D image file:
3. The PTU file is converted "flim_data_stack, intensity_image = ptu_file.get_flim_data_stack()"
4. FLIM data stack is checked for avaialbe channels 'ch_list, ch_listst=Channels_list(flim_data_stack)'
5. Option: with pixel binning set to 2 or higher, FLIM data stack is reshaped.
6. If 'PIE'exication is used, Timegates are calcualted.
7. For each channel, FLIM data is converted for the current channel and timegates from the FLIM data stack
8. For each channel, Colour map is applied on the FLIM data, based on the Tau min & max.
9. Option. Tav and intensity csv data is saved.
10. Figure is plotted.
11. Option  FLIM image and Intensity tif image is saved.
12. Option, FLIM images from multiple channels can be overlapped by overlap_FLIMchannels.



