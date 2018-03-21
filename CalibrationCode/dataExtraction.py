f = open('easRV12_28_Oct_2016_04_39_20.log', 'rb')

# Each DAQpack is 24 bytes long

# Reads the entire text file
data = f.read()

# Split the file up into the header and raw data.
# THIS needs tweaking, some log files will have a larger header,
# but data always begins at a multilpe of 0x400
header = data[:0x400]
rawData = data[0x400:]

splitData = []
brokenDown = []

# Convert header to string
header = header.decode("utf-8")

header = header.split('-----')

presCalibrations = {}


def coefS16(string, points):
    result = coefU(string, points)
    if result > 32767:
        result -= 65536
    return result


def coefU(string, points):
    return int(''.join([string[i] for i in points]), 16)


def coefS8(string, points):
    result = coefU(string, points)
    if result > 127:
        result -= 256
    return result

for i in range(0, len(header)):
    header[i] = header[i].splitlines()
    header[i][:] = [item for item in header[i] if item]

    # This part might not be necessary once we get the beginning of the raw
    # data down cold
    if "\x00\x00\x00" in header[i][0]:
        del(header[i])

    elif "BME280 Temperature Humidity Pressure Sensor" in header[i][1]:
        # This part is just for debugging at the moment. It lists BME280s
        # print("Found a pressure sensor at index " + str(i))

        # Initialize a new entry in the dictionary of calibrations.
        presCalibrations[header[i][0].split(': ')[1]] = {}

        # Parse the calibration line to be only the characters that we want
        calString = (header[i][5].split('||')[1])

        # Calculate the temperature calibration values
        presCalibrations[header[i][0].split(': ')[1]]['temperature'] = [
                           coefU(calString, [2, 3, 0, 1]),
                           coefS16(calString, [6, 7, 4, 5]),
                           coefS16(calString, [10, 11, 8, 9])
                          ]

        # Calculate the Pressure calibration values
        presCalibrations[header[i][0].split(': ')[1]]['pressure'] = [
                               coefU(calString, [14, 15, 12, 13]),
                               coefS16(calString, [18, 19, 16, 17]),
                               coefS16(calString, [22, 23, 20, 21]),
                               coefS16(calString, [26, 27, 24, 25]),
                               coefS16(calString, [31, 30, 28, 29]),
                               coefS16(calString, [34, 35, 32, 33]),
                               coefS16(calString, [38, 39, 36, 37]),
                               coefS16(calString, [42, 43, 40, 41]),
                               coefS16(calString, [46, 47, 44, 45])
                               ]

        # Calculate the humidity calibrations values
        presCalibrations[header[i][0].split(': ')[1]]['humidity'] = [
                               coefU(calString, [48, 49]),
                               coefS16(calString, [52, 53, 50, 51]),
                               coefU(calString, [54, 55]),
                               # These variables here are weird, because of
                               # how they are set up
                               # (h4 and h5 share some data in registers)

                               # This way of doing it is copied from
                               # adafruit's library, lines 166 through 173
                               ((coefS8(calString, [56, 57]) << 4) \
                                   | (coefU(calString, [58, 59]) & 0x0F)),

                               (coefS8(calString, [60, 61]) << 4 \
                                   | (coefU(calString, [58, 59]) >> 4 & 0x0F)),

                               coefS8(calString, [62, 63])]

#Seperate the Raw data into each packet
#This seems to cut off the last data section right now
for i in range(0,int(len(rawData) / 24)):
    splitData.append(rawData[24*i:24*i+24])

#Split the information in each packet into the proper type
uCompData = [{}] * len(splitData)
for i in range(0, len(splitData)):
    packetType = int.from_bytes(splitData[i][4:8], byteorder='little')
    if packetType == 0:
        #Undef, What is this
        pass
    elif packetType == 0x01:
        pass
        #Timestamp packet. Talk to Dr. Davis
    elif packetType == 0x02:
        #This is for the Acclerometer. Currently uses signed short 16, so we need to be careful abou this one
         uCompData[i] = {'ID': int.from_bytes(splitData[i][0:4], byteorder='little'),
                        'type': packetType,
                         'uAccX': int.from_byte(splitData[i][8:10], byteorder='little'),
                         'uAccY': int.from_byte(splitData[i][10:12], byteorder='little'),
                         'uAccZ': int.from_byte(splitData[i][12:14], byteorder='little')}

    elif packetType == 0x03:
        #Barotemp type packet. Used with the BMP180
        uCompData[i] = {'ID': splitData[i][0],
                        'type': packetType,
                        'uPres': int.from_byte(splitData[i][8:12], byteorder='little'),
                        'uTemp': int.from_byte(splitData[i][12:14], byteorder='little'),
                        }
        pass
    elif packetType == 0x04:
        #Gyro Type Sensor. unused in code (commit  182fe0c)
        pass
    elif packetType == 0x05:
        #Strain Gauge. CUrrently unused in code (commit  182fe0c)
        pass
    elif packetType == 0x06:
        #CLOCK_T Unknown use
        pass
    elif packetType == 0x07:
        #MPU6050_t
        uCompData[i] = {'ID': int.from_bytes(splitData[i][0:4], byteorder='little')
                        'type': packetType,
                        'uAccX': int.from_byte(splitData[i][8:10], byteorder='big'),
                        'uAccY': int.from_byte(splitData[i][10:12], byteorder='big'),
                        'uAcczZ': int.from_byte(splitData[i][12:14], byteorder='big'),
                        'uGyroX': int.from_byte(splitData[i][14:16], byteorder='big'),
                        'uGyroY': int.from_byte(splitData[i][16:18], byteorder='big'),
                        'uGyroZ': int.from_byte(splitData[i][18:20], byteorder='big'),
                        'uTemp': int.from_byte(splitData[i][20:22], byteorder='big'),
                        }
        pass
    elif packetType == 0x08:
        #ADXL345_t currently unused in code (commit 182fe0c)
        pass
    elif packetType == 0x09:
        #BMP180_t currently unused (commit  182fe0c)
        pass
    elif packetType == 0x0a:
        #Prestemphuhid type packet. Used by BME280
         uCompData[i] = {'ID': int.from_bytes(splitData[i][0:4], byteorder='little')
                        'uPres': int.from_bytes(splitData[i][8:12], byteorder='big'),
                         'uTemp': int.from_bytes(splitData[i][12:16], byteorder='big'),
                         'uHumid': int.from_bytes(splitData[i][16:18], byteorder='big')
                        }
    elif packetType == 0x0b:
        #HSCpress packet. Used by our relative pressure sensors (pitot tubes)

        uCompData[i] = {'ID': splitData[i][0],
                        'type': packetType,
                        #TODO add the stuff to read this one. It is a bit weird)
                        }
    elif packetType == 0x0c:
        #DUAL_Clock_t unknown use
        pass
    elif packetType == 0x0d:
        pass

#Packet Format is 1 byte ID for sensor, then a 4 byte ID for the packet type
#The rest of the bytes (19 of them) hold the data. The format for this changes
#Per sensor type. See eas_daq_pack.h in github repo for more info.

print(item for item in uCompData if (item['ID'] == 2))

#for item in uCompData if item['ID'] == 2:
 #   print('hello')
