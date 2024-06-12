# Phone_Sensor_Data_environment

This is a python code that accepts data from phone sensors(accelerometer, gyroscope,magnetometer) and optimize them to calculate phone's orientation


Basically, Sensor Logger Android App is used on device and its http service is used. Setting up Computer ip address and port in the app and pushing data over http web sockets.
The code accepts the data, filters it and calculate euler's angles and visualize the orientation on 3-D space.

Run Following Commands before running the script

pip install -r requirements.txt
