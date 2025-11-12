# ❤️ Heart Rate and HRV Monitor (Raspberry Pi Pico + Kubios Cloud)
[![MicroPython](https://img.shields.io/badge/MicroPython-1.22+-blue.svg)](https://micropython.org)
[![Raspberry Pi Pico](https://img.shields.io/badge/Platform-Raspberry%20Pi%20Pico-red.svg)](https://www.raspberrypi.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Kubios Cloud](https://img.shields.io/badge/API-Kubios%20Cloud-orange.svg)](https://www.kubios.com/)

A **real-time heart rate (HR) and heart rate variability (HRV)** monitor built on the **Raspberry Pi Pico**, using **MicroPython**, **OLED visualization**, and **Kubios Cloud** for advanced analytics.

---

## 🩺 Features
- Real-time ECG/PPG sampling via ADC (GPIO 26, 250 Hz)
- On-device HRV computation:  
  `meanHR`, `meanPPI`, `SDNN`, `RMSSD`, `SD1`, `SD2`
- OLED display with live signal and menu navigation
- Rotary encoder input with push-button control
- LED pulse indicator synchronized with heartbeat
- Wi-Fi integration for Kubios Cloud readiness analysis
- Persistent JSON storage for session history
- Error feedback on OLED for network or sensor faults

---

## System Overview

```
        ┌──────────────┐
        │  PPG Sensor  │
        └──────┬───────┘
               │ ADC (26)
        ┌──────┴───────┐
        │ Raspberry Pi │
        │     Pico     │
        └──────┬───────┘
     ┌─────────┴─────────┐
     │ Signal Processing  │ → HR + HRV
     └─────────┬─────────┘
               │
   ┌───────────┴────────────┐
   │ OLED Display / Encoder │
   └───────────┬────────────┘
               │
          Kubios Cloud
```
## Hardware Setup
| Component              | GPIO               | Function         |
| ---------------------- | ------------------ | ---------------- |
| **PPG/ECG Sensor**     | 26                 | Analog input     |
| **OLED (SSD1306 I²C)** | SDA = 14, SCL = 15 | 128×64 display   |
| **Rotary Encoder A/B** | 10 / 11            | Menu rotation    |
| **Encoder Button**     | 12                 | Selection        |
| **PWM LED**            | 21                 | Pulse feedback   |
| **Onboard LED**        | "LED"              | Status indicator |
Power: via USB 5 V
Sampling Rate: 250 Hz
Display Refresh: ~25 Hz

## Menu Navigation

Use the rotary encoder to scroll and press the button to select.
| Mode             | Description                              |
| ---------------- | ---------------------------------------- |
| **Measure HR**   | 60 s sampling, computes HR + HRV metrics |
| **HRV Analysis** | Displays results on OLED                 |
| **History**      | Shows last saved session                 |
| **Kubios**       | Uploads RR data for cloud analysis       |

## Example Outputs
OLED Display
```
MeanHR: 73 bpm
SDNN: 41 ms
RMSSD: 28 ms
SD1: 20  SD2: 55
```
Serial Console
```
--- Kubios HRV Summary ---
Mean HR: 72.6 bpm
SDNN: 41.2 ms
RMSSD: 27.8 ms
PNS Index: 0.65
SNS Index: -0.42
Readiness: 7.9
```
## HRV Metrics
| Metric              | Description                                |
| ------------------- | ------------------------------------------ |
| **SDNN**            | Standard deviation of NN intervals         |
| **RMSSD**           | Root mean square of successive differences |
| **SD1 / SD2**       | Poincaré plot short/long term variability  |
| **PNS / SNS index** | Parasympathetic & sympathetic balance      |

## Skills Demonstrated

- Embedded systems design
- Real-time signal acquisition
- HRV time-domain analysis
- OAuth2 + REST API integration
- I²C, ADC, PWM, interrupt-driven input
- MicroPython async and timer programming

## License
Distributed under the MIT License. See LICENSE for details.
