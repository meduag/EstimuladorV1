import serial
import time

ser = 0


def init_serial():
    global ser
    port = "COM8"  # Stim
    baud = 2000000

    ser = serial.Serial()
    ser.port = port
    ser.timeout = 1
    ser.baudrate = baud
    ser.xonxoff = 1

    msg_bytes = str.encode("1")

    try:
        ser.open()
    except Exception as e:
        print("Error open serial port: " + str(e) + " En -- read_serial --")
        exit()

    if ser.isOpen():
        try:
            ser.write(msg_bytes)
            print("Start capture for Stim data")
            while 1:
                c = ser.readline()
                if len(c) > 0:
                    time1 = time.time()
                    str_msn = c.decode("utf-8")
                    str_msn = str_msn.rstrip()
                    print(str_msn)
                    time2 = time.time()
                    time3 = time2 - time1
                    print(str(time3))

        except Exception as e1:
            print("Error communicating...: " + str(e1) + "En -- read_serial --")

    else:
        print("Cannot open serial port " + str(port) + "En -- read_serial --")
        exit()


init_serial()

