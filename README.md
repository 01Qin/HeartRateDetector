![image](https://github.com/user-attachments/assets/30551a5b-22f3-43d2-b059-5fe5d50ad412)
Team name: Su Wai Phyoe, Wang Qin, Liu Lu
<Heartie>

Project Report
First-year Hardware Project
School of ICT
Metropolia University of Applied Sciences
14 April 2025 
Abstract
Instructions (REMOVE WHEN READY): The abstract is a brief summary of the complete project report. It includes a brief introduction of your topic, methods, project work, results, and conclusions. The abstract is the first part of the report but typically written last. A suitable length for the abstract is half a page to one page.
The meaning of the abstract is to give a reader an overall view of your research/project. After reading the abstract, the reader can also decide if they should read the rest of the report.
Write the abstract in past tense. If you can summarize the whole project, it has already been finished. Do not introduce any new material in the abstract. 
Version history 
 
Ver 	Description	Date 	Author(s) 
1.0	Wrote introduction part & part of midway summary	9.4.2025	Su Wai Phyoe
	Wrote theoretical background	10.4.2025	Su Wai Phyoe
	Wrote method and materials 	11.4.2023	Su Wai Phyoe
	Wrote final version of midway summary and finalized all three parts	14.4.2025	Su Wai Phyoe
2.0			
			 
  	  	  	  
  	  	  	  
  	  	  	  
 
 
Contents
1	Introduction	1
2	Theoretical Background	1
3	Methods and Material	3
4	Implementation	6
5	Group Work Summary	6
5.1	Midway Summary	7
5.2	Final Summary	8
6	Conclusions	9
References	10
Appendices
Appendix 1: Introducing Figures and Other Items
Appendix 2: Using Appendices 
1	Introduction
Heartie is a real-time heart rate and heart rate variability (HRV) monitoring device created during the First-Year Hardware Project course. The primary objective of the project is to design and build a compact and reliable system that measures and displays a user’s heart rate and related variability metrics using accessible hardware components and MicroPython programming. 
The aim of our team is to design a simple, easy-to-use, heart rate detector that could be built and understood by students or people with a basic technical background. The main reason of this project is to use the skills that we learned from hardware course and use it in real life.
“Heartie” is constructed around the Raspberry Pi Pico, a compact microcontroller board, and integrates a Crowtail pulse sensor with an OLED display. The system is powered via USB, reads the user’s pulse through a fingertip sensor and displays real-time measurements of heart rate and HRV on the screen. The setup allows for live monitoring without the need for external software or complex interfaces.
Our main goals are to:
•	Learn how to connect and program real sensors and displays using MicroPython
•	Build a functioning prototype that can read and display heart rate real time data
•	Understand how heart rate and HRV can be measured and what they reveal about our health
•	Create something that's not just technically functional, but also user-friendly

2	Theoretical Background
Before getting into the technical side of our system, it’s important to understand the basics of heart rate and heart rate variability. Heart rate (HR) is the number of heartbeats per minute. For a healthy adult at rest, this usually falls between 50 and 70 BPM, though athletes may have lower values, and heart rate naturally varies with stress, sleep, activity, and other factors.
Heart Rate Variability (HRV), on the other hand, looks at the timing between individual heartbeats, the variation in the time intervals. These intervals are influenced by the autonomic nervous system, which controls involuntary body functions like heartbeat and breathing. HRV can indicate how well the body is adapting to stress, how rested it is, and even whether someone is recovering properly after exercise.
Some of the common HRV metrics include:
•	SDNN (standard deviation of NN intervals): Measures overall variability.
•	RMSSD (root mean square of successive differences): Sensitive to parasympathetic activity.
These values are commonly used in sports science and health research, and while they are a bit more complex than BPM, they offer a deeper view into how the heart responds to different conditions.
How does “Heartie” measure ?
One of the most materials in our projectis the Crowtail pulse sensor. This sensor works based on a technique called photoplethysmography (PPG). It shines an infrared light into the skin, usually on the fingertip, and detects how much light is reflected back. Since blood absorbs more light than surrounding tissue, the amount of reflected light changes slightly with each heartbeat. This allows the sensor to see each pulse. The sensor outputs an analog signal that fluctuates with each beat. And then, the signal is sent to the Raspberry Pi Pico’s ADC (analog-to-digital converter). The Pico converts this analog signal into digital values that we can process using MicroPython. From there, we can analyze the peaks in the waveform to determine the heart rate and calculate the intervals between beats for HRV analysis.
The data is displayed on OLED screen, which makes it easy to read in real time. We also included filtering and peak detection in our code to make the readings more accurate and stable.By combining simple hardware with straightforward code, Heartie is able to give a live, visual representation of how the heart is performing.

Glossary 
HR	Heart rate
HRV	Heart Rate Variability
SDNN	Standard deviation of NN intervals
RMSSD	Root mean square of successive differences
ADC	Analog-to-digital converter
PPG	Photoplethysmography
BPM	Beat Per Minute
IDE	Integrated Development Environment
PPI	Peak to Peak Interval

3	Methods and Material
This section describes the tools, components, and steps we used to build and test our heart rate detector, Heartie. Our goal is to create a working prototype that could detect a user's pulse in real time, calculate heart rate and heart rate variability (HRV), and display the results clearly on OLED screen. The project involved both hardware setup and software development, using accessible components and open-source tools.

3.1	Components
To build Heartie, we used the following main components:
•	Raspberry Pi Pico
The Raspberry Pi Pico is a small and affordable microcontroller that served as the brain of our system. It comes with an onboard analog-to-digital converter (ADC), which allowed us to read the analog signal from the pulse sensor. We programmed the Pico using MicroPython, which is a simplified version of Python designed for embedded devices.
•	Crowtail Pulse Sensor
This sensor uses an optical method (photoplethysmography) to detect blood flow through a fingertip. When a finger is placed on the sensor, it detects the changes in light caused by the pulse and outputs a signal that represents the heartbeat.
•	OLED Display 
We used a small OLED screen with a resolution of 128×64 pixels to show the user's heart rate and HRV in real time. It connects to the Pico through the I2C interface and is easy to control using MicroPython libraries.
•	USB cable
The Pico was connected to a computer using a USB cable, which provided both power and a way to upload and run our code using Thonny IDE.
•	Thonny IDE
Thonny was the software we used to write and upload our code to the Raspberry Pi Pico . It’s a beginner-friendly Python editor that worked well with MicroPython and made it easy to test and debug our scripts throughout the project.
•	Kubios Cloud
Kubios is a professional cloud-based platform for HRV analysis. We used Kubios Cloud to send peak-to-peak interval data and receive detailed physiological metrics, such as readiness indicators, which were then shown on the OLED screen.
•	Wi-Fi
Since our project included cloud integration, a working Wi-Fi connection was necessary. We used a local Wi-Fi network during development to test the connection and make sure the data was being sent and received correctly. 
3.2	Software and Programming
The device was programmed using MicroPython, a lightweight Python implementation designed for microcontrollers. The programming environment used was Thonny IDE, which offers a simple interface for uploading and executing MicroPython scripts.
Custom scripts were written to:
•	Read the analog signal from the pulse sensor via the ADC
•	Process the signal to detect peaks and intervals
•	Calculate the BPM and HRV values based on the time between pulses
•	Display the results on the OLED in real time
3.3	Testing Procedure
After the hardware assembly and software development were completed, the system was tested under different conditions to verify its performance and reliability:
•	A user placed their finger on the pulse sensor while the device was powered on.
•	The OLED display is monitored to ensure the BPM readings were updating consistently.
•	The signal waveform is observed during development to fine-tune peak detection.
•	Comparisons are made between the device’s readings and those of a digital multimeter (DMM) and known HR values from commercial devices to evaluate accuracy.
Testing also included basic error handling, such as ensuring stable readings during finger movement, verifying sensor connections, and checking the system’s ability to return to normal operation after temporary signal loss.
![image](https://github.com/user-attachments/assets/266fc617-cafa-4676-8ced-be11c3d80688)
