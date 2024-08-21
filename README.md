# fastFLIM
Create fastFLIM images from PicoQuant PTU files.

![Shep2_8__FLIM_Ch2](https://github.com/user-attachments/assets/e0e79cfb-ae82-4749-bbf3-0a56ec9524e6)
*Figure 1, Example of a 1 channel fastFLIM converted image, of cells labelled with FluoVolt dye, that shows change in lifetime*

## Discription
The main purpose of the fastFLIM script is one can convert by batch multiple PTU files, or a folder with PTU files, and get a series Fluorescent fastFLIM images with minimal user input. This is usefull for screening results during imaging and to be used in presentations. FastFLIM calculates the average arrival time, which is a fast method to get a fluorescent lifetime information for image with low photon counts per pixel, which is typical for TCSPC methods. 

### Dependencies
A PicoQuant microscope MT200 with FLIMbee scanner. 

The script is developed and tested on Python 3.11, Install:
1. wx python 4.2.1 for the file selector app.
2. imageIO
3. matplotlib-scalebar 
4. updated readPTU_FLIM-bidirect version is inlcuded, source [PTU file reader](https://github.com/RobertMolenaar-UT/readPTU_FLIM) 

### Script features:  
1. File Check, if it is a 2D  image.
2. Autodetects the number of APD channels, and laser lines used. 
3. Supports 'normal' and 'PIE' excitation, one can set channel Timegate.
4. fastFLIM/rapidFLIM Conversion.
5. Optional: **binning** Image pixels .
6. Optional: **channel_binning** Combine TCSPC of multiple SPAD's into channel 1.
7. Optional: **shorter_End_PIE_ns** Crop TCSPC TimeGate. 
8. Optional: **clean_imsave** saves clean TIF images and datafiles.
9. Any File-errors are catched and reported in the end.

![Screenshot 2024-08-01 115904](https://github.com/user-attachments/assets/d5c1737b-26cc-4bff-8c75-d49b447a3d44)

*Figure 2: command line PTU file experiment setitings summary*

## Usage: 

Put the 2D_PicoQuant_fastFLIM.py and readPU_FLUM_bidirect.py files in the sample folder, preferable with you data. The File readPTU_FLIM_bidirect is modified from https://github.com/RobertMolenaar-UT/readPTU_FLIM and expanded with bidirection line-offset correction. pixles shift correction is set by *bi-direct* variable.

1. Set the Channel configuration according optical setup.

>Detector Channels need to be configured:
Config1 = Set_Channel_Info(1,
			   'Namelabel',
			   Brighter=1.2,
			   PIE_TimeGate=1,
			   ch_irf=2.55)
>1. *Namelabel*: name of the used dye or sample.
>2. *Brigther*: 	intensity is maximum scaled, increasing brightness helps visibility.
>3. *PIE TimeGate*: Contrast can be enhanced by using Pulsed Interlieved Excitation in the measurment to supress any cross-excitation. 
>4. *ch_irf*: instrument response, channel specific time offset.
	
2. Read and set all options in the section -- USER input --  upon description.
3. Run 2D_PicoQuant_fastFLIM.py.
4. Note the pop-up window in the taskbar and browse and select the PTU files.
5. Next the *.PTU files are proccessed, and images are shown in the command line. (for large PTU file size it can take time to proccess)
6. Images and data files are saved in folder /Python_converted_TAC-range_* Username* /
7. Errors on files are listed at the end.

>**The countrate in FLIM should not exceed 10-20%, *FLIM_sync_limit* shows the 20% count limit value.**

### OUTPUT

1. Summary Intensity plus FLIM image. *Figure1*
2. optional *clean_imsave*, saves a clean, FLIM and Intensity TIF file for each channel.
3. optional *Save_tiff_stack*, saves a tiffstack: 2D image stack, slices are the timebin, used for [FLUTE phasor post analysis](https://github.com/LaboratoryOpticsBiosciences/FLUTE).
4. optional *Save_data_files*, saves a csv data of intensity and Tavg lifetimes.



### Known limitations: 

1. Files sizes > 1GB use a lot of Memory. 64GB or higher is recommended for 1GB PTU files. 
2. Multiframe PTU conversion appears to skip a Frame, modification needed in the readPTU_FLIM code. aug '24

Script is used on a Picoquant MT200 with FLIMBEE laserscanner with 4x SPAD detectors and a multiharp 150N.
v1.0 - 1 August 2024 Robert Molenaar ©.



### Workflow summary
 
1.  wx 'GUI_select_Multi_file' app prompts to select (multiple) *.PTU files. 
2.  The main For-loop proccesses all files sequentially.
3.  The PTU file is read by "ptu_file  = PTUreader((path), print_header_data = False)"
4.  File is checked if it's a 2D image file:
5.  The PTU file is converted "flim_data_stack, intensity_image = ptu_file.get_flim_data_stack()"
6.  FLIM data stack is checked for avaialbe channels 'ch_list, ch_listst=Channels_list(flim_data_stack)'
7.  Option: with pixel binning set to 2 or higher, FLIM data stack is reshaped.
8.  If 'PIE'exication is used, Timegates are calcualted.
9.  For each channel, FLIM data is converted for the current channel and timegates from the FLIM data stack
10. For each channel, Colour map is applied on the FLIM data, based on the Tau min & max.
11. Option. Tav and intensity csv data is saved.
12. Figure is plotted.
13. Option  FLIM image and Intensity tif image is saved.
14. Option, FLIM images from multiple channels can be overlapped by overlap_FLIMchannels.
---
### Multicolour fastFLIM

![BPAE_FluoCells_2_Intensity-combi](https://github.com/user-attachments/assets/3bc7ef2d-39e6-474c-a55f-072f75c9a33d)

*Figure 3: Example of 3 colours BPAE, Fluorescent colors overlay made with [PicoQuant-multi channel screen](https://github.com/RobertMolenaar-UT/PicoQuant-multi_channel_screen), and FLIM with this fastFLIM script.*



