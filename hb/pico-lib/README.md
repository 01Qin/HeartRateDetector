# Libraries for Metropolia first year hardware project

This repository is intended to be used as a submodule of student projects. 
The files in the repo need to be copied in /lib of the pico running MicroPython.

The files can also be installed from this repo with the following method:

1. Install MP-remote on your computer: 

   pip install mpremote

2. Clone this repository

3. Start webserver by **python -m http.server** or **python3 -m http.server** depending on your installation

4. Start a terminal and run:

 - **mpremote  mip install http://localhost:8000/**

   or if your pico is not found automatically:

 - **mpremote connect \<device\> mip install http://localhost:8000/**
 
   replace \<device\> with the name of the port that Pico is connected to on your computer

Note that the files will be installed in the **lib** directory of Pico. Which files will be copied is defined in
**package.json**


It is possible to override the default location by specifying --target option. 

