# Ender S3 Pro Thumbnail Embedder
A python post processing script for PrusaSlicer to embed the thumbnail and print information into GCode in the correct format for the Ender S3 Pro.

# Instructions for PrusaSlicer
First, download the python file and save it in a safe location (such as `C:\Users\user\AppData\Roaming\PrusaSlicer\scripts\`).
Ensure that you also have python installed and that you have it saved in a known location.

## Print Settings > Output options
Now open PrusaSlicer and ensure that you are in Expert mod and then navigate to Print Settings > Output options.
In Output options, you should see a Post-processing scripts option. In this option, you want to enter a call to the thumbnailEmbedder - 
`"...\pythonw.exe"  "...\thumbnailEmbedder.py";` - making sure that you enter the full filepath for pythonw.exe and the thumbnailEmbedder file.
Now save your print settings so you don't have to do this again!

## Printer Settings > General
Next you want to navigate to Printer Settings > General. You should now see a Firmware option category. Change the options here to reflect the following screenshot.

![image](https://github.com/rowan-gray/EnderS3ProThumbnailEmbedder/assets/63951256/7fefc5c4-7184-4903-96ef-005672770629)

This tells PrusaSlicer to add a 300x300 PNG image of the print to the outputted GCode which the python script will then transform into the correct format.

## Printer Settings > General
Now navigate to Printer Settings > General. You now want to modify the Start G-code to include the following lines at the top.
```
;MINX:{first_layer_print_min[0]}
;MINY:{first_layer_print_min[1]}
;MINZ:{first_layer_height}
;MAXX:{first_layer_print_max[0]}
;MAXY:{first_layer_print_max[1]}
;MAXZ:{first_layer_height * total_layer_count}
```
These lines do not change the gcode actions in any way (they are merely comments). They allow the Ender S3 Pro to show the print information.
Make sure you have the Printer Settings now too so you don't have to repeat these steps.

That should be it. Try exporting a test print and see if your Ender S3 Pro shows the screenshot and print information.
