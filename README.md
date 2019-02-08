# SoundLocalization

Project designed for localization of sound sources in 3D space. The sound source of a choice is a one emitted by a bouncing ball.

The repository consists of three separate programs:
- driver for Teensy 3.2 handling data read and tranfer from Max11043 ADC

- localizator application, that reads the raw data from USB port, then searches for bouncing ball sound. If found MLE-HLS algorithm is applied to find a src coordinates, based on known (x,y,z) positions of microphones.

- webserver and GUI client is a TypeScript app that handles websocket connections between loclaizator and browser. In a browser the GUI is displayed when connected with the server via HTTP. Its updates are done via websocket

Design documents regarding microphone array elements: ADC board and microphone boards are in /hardware_design directory. You will need Altium designer to open them.

The docs/ folder includes additionall material such as pictures and reference sources used in the thesis. Furthermore datasheets for MAX11043 and other hardware elements can be found there.
