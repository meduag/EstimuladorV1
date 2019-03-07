import sys
import matplotlib.pyplot as plt
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
import serial
import threading
import numpy as np
import math
import time
from scipy.signal import butter, lfilter, medfilt

__author__ = 'Miguel Gutierrez'

# Original ports
serPort1 = "COM14"  # Stim
serPort3 = "COM15"  # Loadc
baudRate = 2000000

# lock to serialize console output
lock = threading.Lock()

msg = ""
msg_bytes = ''  # Para mandar el mensaje

cs = ">"  # Caracter de separacion

############################################
"""************ unsigned int ************/
// 0 - ts
// 1 - pw
// 2 - pwr
// 3 - l_mai
// 4 - l_maf
// 5 - min_t > us
// 6 - seg_t > us
// 7 - ms_t  > us """
ul_var = [0, 0, 0, 0, 0, 60000000, 1000000, 100000]

############################################
""" variables para canal 1 y 2
// 0 - ch activation
// 1 - ma
// 2 - ton ou t sustentacion
// 3 - toff
// 4 - ri
// 5 - rf """
ch1 = [0, 0, 0, 0, 0, 0]
ch2 = [0, 0, 0, 0, 0, 0]

############################################
""" valores de los limites del harware
ch1 y ch2 = max y min """
val_mm = [1883, 1842, 2047, 2047]


############################################
""" 0 - Tex activation
 1 - Stop control
 2 - Update data"""
flags = [0, 0, 0]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up the user interface from Designer.
        uic.loadUi("Estimulema V1 Rv0.ui", self)

        # Connect up the buttons.
        self.PB_tex.clicked.connect(self.b_tex)  # boton de test de exitabilidad
        self.PB_sp.clicked.connect(self.b_stop)  # boton parada de stimulacion
        self.PB_ch1.clicked.connect(self.b_stch1)  # boton estimulacion canal 1
        self.PB_ch2.clicked.connect(self.b_stch2)  # botton estimulacion canal 2
        self.PB_ch12.clicked.connect(self.b_stch12)  # boton estomulacion ch1 y ch2

        # Training and Rheobase Test
        """self.PB_ch1_tex.clicked.connect(self.btn_ch1_tex)  # boton para estimulacion y tex

        # Boton para funcion de filtrado y plotado de datos
        self.PB_fil_plot.clicked.connect(self.btn_fil_plot)

        # limits for tests
        self.spinBox_limit_ini_mA.valueChanged.connect(self.update_var)
        self.spinBox_limit_fin_mA.valueChanged.connect(self.update_var)

        # for general parameters
        self.spinBox_ts.valueChanged.connect(self.update_var)
        self.spinBox_f.valueChanged.connect(self.update_var)
        self.spinBox_pw.valueChanged.connect(self.update_var)

        # for channel 1
        self.spinBox_tn_1.valueChanged.connect(self.update_var)
        self.spinBox_tf_1.valueChanged.connect(self.update_var)
        self.spinBox_ri_1.valueChanged.connect(self.ramp_check)
        self.spinBox_rf_1.valueChanged.connect(self.ramp_check)
        self.spinBox_ma_1.valueChanged.connect(self.btn_change_ma1)

        # for channel 2
        self.spinBox_tn_2.valueChanged.connect(self.update_var)
        self.spinBox_tf_2.valueChanged.connect(self.update_var)
        self.spinBox_ri_2.valueChanged.connect(self.ramp_check)
        self.spinBox_rf_2.valueChanged.connect(self.ramp_check)
        self.spinBox_ma_2.valueChanged.connect(self.btn_change_ma2)"""

        # update lim fin
        self.spinBox_lfmA.setValue(self.spinBox_ma1.value())

        # Show interface
        self.show()

    def b_tex(self):
        global msg
        self.take_values(0, 0, 1, 0, 0)
        self.lineEdit_terminal.clear()
        self.lineEdit_terminal.setText(msg)

    def b_stop(self):
        global msg
        self.take_values(0, 0, 0, 0, 0)
        self.lineEdit_terminal.clear()
        self.lineEdit_terminal.setText(msg)

    def b_stch1(self):
        global msg, ch2
        self.take_values(1, 0, 0, 0, 0)
        self.lineEdit_terminal.clear()
        self.lineEdit_terminal.setText(msg)

    def b_stch2(self):
        global msg
        self.take_values(0, 1, 0, 0, 0)
        self.lineEdit_terminal.clear()
        self.lineEdit_terminal.setText(msg)

    def b_stch12(self):
        global msg
        self.take_values(1, 1, 0, 0, 0)
        self.lineEdit_terminal.clear()
        self.lineEdit_terminal.setText(msg)

    # buttons functions ---------------------------------------------------------------
    def take_values(self, ch1_act, ch2_act, tex_act, sc_act, upd_act):
        global flags, ul_var, ch1, ch2

        """10 > 500 > 19000 > 1 > 20 >
        1 > 1500 > 2 > 2 > 5 > 5 >
        1 > 1500 > 2 > 2 > 5 > 5 >
        0 > 1 > 0 >"""

        """ 0 - ts 1 - pw 2 - pwr 3 - l_mai
        4 - l_maf 5 - min_t 6 - seg_t 
        7 - ms_t """

        """ variables para canal 1 y 2
        // 0 - ch activation // 1 - ma
        // 2 - ton ou t sustentacion // 3 - toff
        // 4 - ri // 5 - rf """

        #  1
        ul_var[0] = self.spinBox_ts.value()         # TS

        #  2
        ul_var[1] = self.spinBox_pw.value()         # Pw

        #  3
        fqv = self.spinBox_f.value()                # frequencia
        Tp = int(1 / fqv * ul_var[6])               # Periodo
        ul_var[2] = Tp - ul_var[1]                  # Pwr

        #  4
        ul_var[3] = self.spinBox_limA.value()       # Lim de Corrente inf /

        #  5
        ul_var[4] = self.map(self.spinBox_lfmA.value(), 0, 100, 0, val_mm[0]) # Lim superior / maximo

        #################################################################
        """ Channel 1 data """
        #  6
        ch1[0] = ch1_act                            # Activacion canal 1

        #  7
        if self.spinBox_ri1.value() > 0:
            # Tiempo ri / tiempo periodo
            sb_ri = self.spinBox_ri1.value()
            vts = ul_var[6]
            v_ri1 = self.spinBox_ri1.value() * vts
            time_mA1 = float(v_ri1 / Tp)
            time_mA1 = time_mA1 - 1
            mili1 = self.spinBox_ma1.value()

            if mili1 > 3:
                mili1 = mili1 - 2

            step = self.map(mili1, 0, 100, 0, val_mm[0])
            step = step / time_mA1

            ch1[1] = math.floor(step)
        else:
            ch1[1] = 0

        # 8
        ri1 = self.spinBox_ri1.value()
        rf1 = self.spinBox_rf1.value()
        ton1 = self.spinBox_tn1.value()
        if flags[0] == 0:       # para cuando no es Teste de exitabilidad
            ch1[2] = int(ton1 - (ri1 + rf1))
        else:                   # para Teste de exitabilidad
            ch1[2] = int(ton1)

        #  9
        ch1[3] = self.spinBox_tf1.value()

        #  10
        ch1[4] = int(ri1 * 10)

        #  11
        ch1[5] = int(rf1 * 10)

        #################################################################
        """ Channel 2 data """
        #  12
        ch2[0] = ch2_act  # Activacion canal 1

        #  13
        if self.spinBox_ri2.value() > 0:
            # Tiempo ri / tiempo periodo
            time_mA2 = float((self.spinBox_ri2.value() * ul_var[7]) / Tp)
            mili2 = self.spinBox_ma2.value()
            step = self.map(mili2, 0, 100, 0, val_mm[2])
            step = step / time_mA2
            ch2[1] = int(step * 100)
        else:
            ch2[1] = 0

        # 14
        ri2 = self.spinBox_ri2.value()
        rf2 = self.spinBox_rf2.value()
        ton2 = self.spinBox_tn2.value()
        if flags[0] == 0:  # para cuando no es Teste de exitabilidad
            ch2[2] = int(ton2 - (ri2 + rf2))
        else:  # para Teste de exitabilidad
            ch2[2] = int(ton2)

        #  15
        ch2[3] = int(self.spinBox_tf2.value())

        #  16
        ch2[4] = int(ri2 * 10)

        #  17
        ch2[5] = int(rf2 * 10)

        #  18
        flags[0] = tex_act

        #  19
        flags[1] = sc_act

        #  20
        flags[2] = upd_act

        self.concat_msg()

    @staticmethod
    def concat_msg():
        global flags, ul_var, ch1, ch2, msg

        msg = ""

        # general parameters = 3
        for i in range(0, 5):
            msg = msg + (str(ul_var[i]) + cs)

        print("Primeira parte:  " + msg)
        # msg = msg + " --- "

        for i in range(0, 6):
            msg = msg + (str(ch1[i]) + cs)

        print("Add channel 1:  " + msg)
        # msg = msg + " --- "

        for i in range(0, 6):
            msg = msg + (str(ch2[i]) + cs)

        print("Add channel 2:  " + msg)
        # msg = msg + " --- "

        for i in range(0, 3):
            msg = msg + (str(flags[i]) + cs)

        print("MSG:  " + msg)

    @staticmethod
    def map(x, in_min, in_max, out_min, out_max):
        return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)


def read_serial(port, baud):
    global msg_bytes, arrayt
    global start_thread_s

    arrayt = []  # array for stim data

    ser = serial.Serial()
    ser.port = port
    ser.timeout = 1
    ser.baudrate = baud
    ser.xonxoff = 1

    try:
        ser.open()
    except Exception as e:
        print("Error open serial port: " + str(e) + " En -- read_serial --")
        exit()

    if ser.isOpen():
        try:
            while start_thread_s is False:
                pass

            ser.write(msg_bytes)
            print("Start capture for Stim data")
            while start_thread_s is True:
                c = ser.readline()
                with lock:
                    if len(c) > 0:
                        str_msn = c.decode("utf-8")
                        str_msn = str_msn.rstrip()
                        print(str_msn)
                        if str_msn == '>':
                            start_thread_s = False
                            print("End capture about Stim data")
                        else:
                            arrayt.append(str_msn)
            ser.close()

        except Exception as e1:
            print("Error communicating...: " + str(e1) + "En -- read_serial --")

    else:
        print("Cannot open serial port " + str(port) + "En -- read_serial --")
        exit()

    save_data()  # Thread for acel data
    print("End Thread Acel data")


def read_serial2(port, baud):
    global msg_bytes, start, arrayt2
    global start_thread_a

    arrayt2 = []  # Array for acel data

    ser2 = serial.Serial()
    ser2.port = port
    ser2.timeout = 1
    ser2.baudrate = baud
    ser2.xonxoff = 1

    try:
        ser2.open()
    except Exception as e:
        print("Error open serial port: " + str(e) + " En -- read_serial2 --")
        exit()

    if ser2.isOpen():
        try:
            while start_thread_a is False:
                pass

            ser2.write(msg_bytes)
            print("Start capture for Accelerometer data")
            while start_thread_a:
                c = ser2.readline()
                with lock:
                    if len(c) > 0:
                        str_msn = c.decode("utf-8")
                        str_msn = str_msn.rstrip()
                        print(str_msn)
                        if str_msn == '>':
                            start_thread_a = False
                            print("End capture about Accelerometer data")
                        else:
                            arrayt2.append(str_msn)

            ser2.close()

        except Exception as e1:
            print("Error communicating...: " + str(e1) + " En -- read_serial2 --")

    else:
        print("Cannot open serial port " + str(port) + " En -- read_serial2 --")
        exit()

    save_data2()  # Thread for acel data
    print("End Thread Acel data2")


def read_serial3(port, baud):
    global msg_bytes, arrayt
    global start_thread_s

    arrayt = []  # array for stim data

    ser = serial.Serial()
    ser.port = port
    ser.timeout = 1
    ser.baudrate = baud
    ser.xonxoff = 1

    try:
        ser.open()
    except Exception as e:
        print("Error open serial port: " + str(e) + " En -- read_serial --")
        exit()

    if ser.isOpen():
        try:
            while start_thread_s is False:
                pass

            ser.write(msg_bytes)
            print("Start capture for Stim data")
            while start_thread_s is True:
                c = ser.readline()
                with lock:
                    if len(c) > 0:
                        str_msn = c.decode("utf-8")
                        str_msn = str_msn.rstrip()
                        print(str_msn)
                        if str_msn == '>':
                            start_thread_s = False
                            print("End capture about Stim data")
                        else:
                            arrayt.append(str_msn)
            ser.close()

        except Exception as e1:
            print("Error communicating...: " + str(e1) + "En -- read_serial --")

    else:
        print("Cannot open serial port " + str(port) + "En -- read_serial --")
        exit()

    save_data()  # Thread for acel data
    print("End Thread Acel data")


def save_data():
    global arrayt, rh, cr, name_file, file_name_out_s

    if rh is True:
        if name_file is True:
            hora = time.strftime("%H")
            n_dia = time.strftime("%a")
            dia = time.strftime("%d")
            mm = time.strftime("%M")
            file_name_out_s = 'stim_r ' + n_dia + ' ' + dia + ' ' + hora + 'h' + mm + '.txt'
        else:
            file_name_out_s = 'stim_r.txt'
    elif cr is True:
        if name_file is True:
            hora = time.strftime("%H")
            n_dia = time.strftime("%a")
            dia = time.strftime("%d")
            mm = time.strftime("%M")
            file_name_out_s = 'stim_c ' + n_dia + ' ' + dia + ' ' + hora + 'h' + mm + '.txt'
        else:
            file_name_out_s = 'stim_c.txt'

    stim = open(file_name_out_s, 'w')

    for x in arrayt:
        if rh is True:
            stim.write(x)
            stim.write("\n")
        elif cr is True:
            stim.write(x)
            stim.write("\n")
        # print(x)

    stim.close()

    print("End generation of Stim file")
    ex.upd_terminal("End generation of Stim file")


def save_data2():
    global arrayt2, rh, cr, cont_fig, plot_show, sel_test, file_name_out_a
    # global rh_acx, rh_acy, rh_acz, cr_acx, cr_acy, cr_acz
    global name_file, ctrl_ch1_rh

    if rh is True:
        if name_file is True:
            hora = time.strftime("%H")
            n_dia = time.strftime("%a")
            dia = time.strftime("%d")
            mm = time.strftime("%M")
            file_name_out_a = 'acel_r ' + n_dia + ' ' + dia + ' ' + hora + 'h' + mm + '.txt'
        else:
            file_name_out_a = 'acel_r.txt'
    elif cr is True:
        if name_file is True:
            hora = time.strftime("%H")
            n_dia = time.strftime("%a")
            dia = time.strftime("%d")
            mm = time.strftime("%M")
            file_name_out_a = 'acel_c ' + n_dia + ' ' + dia + ' ' + hora + 'h' + mm + '.txt'
        else:
            file_name_out_a = 'acel_c.txt'

    acel = open(file_name_out_a, 'w')

    for x in arrayt2:
        if rh is True:
            acel.write(x)
            acel.write("\n")
            # save array for filter and plot
            # y = np.array(x.rstrip().split(';')).astype(int)
            # rh_acx.append(int(y[1]))
            # rh_acy.append(int(y[2]))
            # rh_acz.append(int(y[3]))
            sel_test = True
        elif cr is True:
            acel.write(x)
            acel.write("\n")
            # save array for filter and plot
            # y = np.array(x.rstrip().split(';')).astype(int)
            # cr_acx.append(y[1])
            # cr_acy.append(y[2])
            # cr_acz.append(y[3])
            sel_test = False
        # print(x)

    acel.close()

    print("End generation of Acel file")
    ex.upd_terminal("End generation of Acel file, (Plot enable)")
    ctrl_ch1_rh = False


def stim_training():  # Function for training
    global serPort1, serPort2, baudRate, msg_bytes, start, start_tread

    if start_tread is True:
        start_tread = False
        try:
            t3 = threading.Thread(target=read_while_stim, args=(serPort2, baudRate))
            t3.daemon = True  # thread dies when main thread (only non-daemon thread) exits.
            t3.start()

        except Exception as e1:
            print("Error: unable to start thread 1" + str(e1))

    ser = serial.Serial()
    ser.port = serPort1
    ser.timeout = 1
    ser.baudrate = baudRate
    ser.xonxoff = 1

    try:
        ser.open()
    except Exception as e:
        print("Error open serial port: " + str(e) + "En -- Stim_training -- ")
        exit()

    if ser.isOpen():
        try:
            ser.write(msg_bytes)

        except Exception as e1:
            print("Error communicating...: " + str(e1) + " En -- Stim_training --")


def read_while_stim(port, baud):
    global start, start_receiver, ts, start_tread, start_rh_test, ntrain

    start_receiver = True
    cont = 0

    ser = serial.Serial()
    ser.port = port
    ser.timeout = 1
    ser.baudrate = baud
    ser.xonxoff = 1

    # Training data
    hora = time.strftime("%H")
    n_dia = time.strftime("%a")
    dia = time.strftime("%d")
    mm = time.strftime("%M")
    # Name for training file
    file_training = 'Treinamento'+ str(ntrain)+ ' ' + n_dia + ' ' + dia + ' ' + hora + 'h' + mm + '.txt'
    # Basic name
    # file_training = "Treinamento" + str(ntrain) + ".txt"

    stim_tr = open(file_training, 'w')

    try:
        ser.open()
    except Exception as e:
        print("Error open serial port: " + str(e) + "En -- read_while_stim --")
        print("Possibly the serial port is already open")
        exit()

    if ser.isOpen():
        try:
            rest = ts - cont
            print("Count Minutes")
            print("Remaining minutes: " + str(rest))
            ex.upd_terminal("Remaining minutes: " + str(rest))
            ex.upd_lcdNumber(rest)
            while start_receiver is True:
                c = ser.readline()
                if len(c) > 0:
                    str_msn = c.decode("utf-8")
                    str_msn = str_msn.rstrip()
                    # print(str_msn)
                    cont_min = str_msn.find("T")

                    if cont_min == 0:  # para T cuando es igual en el primer caratcer
                        print("Llegó un minuto")
                        cont = cont + 1
                        print("Remaining minutes: " + str(ts - cont))
                        ex.upd_terminal("Remaining minutes: " + str(ts - cont))
                        ex.upd_lcdNumber(ts - cont)
                    elif cont_min == -1:  # cuando es diferente de t
                        cont_min = str_msn.find(";") # la coma da un valor mayor que cero
                        if cont_min > 0:
                            stim_tr.write(str_msn)
                            stim_tr.write("\n")
                            print(str_msn)
                        elif str_msn == "f":
                            start_receiver = False
                            print("End therapy time")
                            ex.upd_terminal("End therapy time")

                    """else:
                        cont = cont + 1
                        print("Remaining minutes: " + str(ts - cont))
                        ex.upd_terminal("Remaining minutes: " + str(ts - cont))
                        ex.upd_lcdNumber(ts - cont)"""

            ser.close()
            stim_tr.close()
            ntrain = ntrain + 1
            start_tread = True
            ex.upd_terminal("End therapy time")

        except Exception as e1:
            print("Error communicating...: " + str(e1) + " En -- read_while_stim --")

        ex.upd_terminal("Ends Stimulation ...")
        ex.upd_lcdNumber(0)

        if start_rh_test is True:
            ex.btn_start_rh()


# Create two threads as follows
def start_test():
    global serPort1, serPort2, baudRate

    try:
        t1 = threading.Thread(target=read_serial, args=(serPort1, baudRate))
        t1.daemon = True  # thread dies when main thread (only non-daemon thread) exits.
        t1.start()

    except Exception as e1:
        print("Error: unable to start thread 1" + str(e1))

    try:
        t1 = threading.Thread(target=read_serial2, args=(serPort2, baudRate))
        t1.daemon = True  # thread dies when main thread (only non-daemon thread) exits.
        t1.start()
    except Exception as e1:
        print("Error: unable to start thread 2" + str(e1))


def plot_and_filt():
    global arrayt, arrayt2, rh, cr, plot_xyz, file_name_out_a, file_name_out_s
    global rh_acx, rh_acy, rh_acz, cr_acx, cr_acy, cr_acz

    data = ""
    data_s = ""

    # aqui testo las saludas
    # rh = False
    rh = True

    if rh is True:
        print("Vamos plotar para Reobase")
        cr = False
    else:
        cr = True
        print("Vamos plotar para Cronaxia")

    file = ""

    if rh is True:
        file = 'acel_r.txt'
        # file = file_name_out_a
    elif cr is True:
        file = 'acel_c.txt'
        # file = file_name_out_s

    try:
        data = np.loadtxt(file, delimiter=';')
    except Exception as e:
        print("Error: " + str(e) + " in --" + file + "-- file")
        exit()

    # data = np.loadtxt(file, delimiter=';')
    # data = np.array(arrayt.rstrip().split(';')).astype(int)

    # data of signal
    eje_x = data[:, 1]
    eje_y = data[:, 2]
    eje_z = data[:, 3]
    signal_pulse = data[:, 4]

    n = len(signal_pulse)

    plt.figure()
    t = np.arange(0, n)

    # Normalize the axis from digital to g(m/s^2)
    bits_dac = 65536  # 2 ^ 16
    eje_x = eje_x / bits_dac
    eje_y = eje_y / bits_dac
    eje_z = eje_z / bits_dac

    eje_x2 = eje_x ** 2
    eje_y2 = eje_y ** 2
    eje_z2 = eje_z ** 2

    xyz = eje_x2 + eje_y2 + eje_z2
    # Magnitude of the resulting vector
    eje_xyz = np.sqrt(xyz)

    # take 500 samples to calculate the average value
    in_sxyz = eje_xyz[:500]
    med_xyz = np.mean(in_sxyz)
    print("valor medio: " + str(med_xyz))
    std_xyz = np.std(in_sxyz)
    print("La desviacion standard es: " + str(std_xyz))

    # Threshold calculation based on standard deviations
    num_std = 4
    thsdxyz = num_std * std_xyz
    lin_thsdxyz = np.ones((n, 1)) * (med_xyz + thsdxyz)

    # Plot the threshold signal
    plt.plot(t, lin_thsdxyz, 'y', label='Threshold')
    if plot_xyz is True:
        plt.plot(t, eje_x, 'b')
        plt.plot(t, eje_y, 'b')
        plt.plot(t, eje_z, 'b')
    #  plt.plot(t, eje_xyz, 'b', linewidth=0.5)

    # Parameters used in the filter
    cut_off = 30
    fs = 1000
    order = 10

    acxyz_fil = butter_lowpass_filter(eje_xyz, cut_off, fs, order)
    plt.plot(t, acxyz_fil, 'r', linewidth=1, label='Butterworth Filter Accel Signal')

    xyz_mf = medfilt(eje_xyz, 5)
    plt.plot(t, xyz_mf, 'b', linewidth=1, label='Median Filter Accel signal')

    val_max = np.max(acxyz_fil)
    print("Valor maximo del vector: " + str(val_max))
    # signal_pulse = signal_pulse * val_max

    # read stim data
    if rh is True:
        file = 'stim_r.txt'
    elif cr is True:
        file = 'stim_c.txt'

    try:
        data_s = np.loadtxt(file, delimiter=';')
    except Exception as e:
        print("Error: " + str(e) + " in --" + file + "-- file")
        print("Please review the file and check the internal format")
        exit()

    # data_s = np.loadtxt(file, delimiter=';')
    data_ma = data_s[:, 1]
    max_ma = np.max(data_ma)
    min_ma = data_ma[1]

    if min_ma == 1:
        min_ma = 0
    else:
        min_ma = min_ma - 1

    # split stimulation signal
    div = val_max / max_ma
    div_signal = div
    new_stim_signal = np.ones((n, 1))
    c1 = 0

    if cr is True:
        div_signal = val_max

    for i in range(n):
        # contar milies
        if signal_pulse[i] == 1:
            c1 = 1
            new_stim_signal[i] = signal_pulse[i] * div_signal
        else:
            new_stim_signal[i] = 0

        if c1 == 1 and signal_pulse[i] == 0:
            if rh is True:
                div_signal = div_signal + div
            elif cr is True:
                div_signal = val_max
            c1 = 0

    # Stimulation signal
    # plt.plot(t, signal_pulse[i], 'g')
    plt.plot(t, new_stim_signal, 'g', label='Stim signal')

    # plt.title = 'Acceleration magnitude resulting from the XYZ axis'
    # plt.xlabel = 'time (s)'
    # plt.ylabel = 'g(m/s^2)'

    # Spike detection
    th = med_xyz + thsdxyz

    # indice de interceptacion y valor en miliaps
    indx_x = 0
    indx_y = 0
    val_int_str = ""

    if rh is True:
        for j in range(500, n):
            # contar milies
            # val_ac = acxyz_fil[j]
            val_ac = xyz_mf[j]
            if val_ac >= th:
                print("Indice de interceptacion: " + str(j))
                indx_x = j
                val_int = new_stim_signal[j]
                val_int = int(val_int / div)
                val_int_str = str(int(val_int + min_ma))
                print("Div miliamps: " + val_int_str)
                indx_y = val_ac
                if val_int > 0:
                    val_int = val_int
                    break
    elif cr is True:
        c_dx = 0  # contador de delta x
        c_ind = []  # index count
        for i in range(n):
            if signal_pulse[i] == 1:
                c_dx = 1
            if signal_pulse[i] == 0 and c_dx == 1:
                # c_ind[i] = 0
                print("sumando")

        for j in range(3000, n):
            val_ac = acxyz_fil[j]
            if val_ac >= th:
                print("Valor de x: ")
                print(j)
                print("Indice de interceptacion: " + str(j))
                val_int = new_stim_signal[j]
                val_int = int(val_int / div)
                print("Div miliamps: " + str(val_int))
                if val_int > 0:
                    # val_int = val_int + 1
                    break

    plt.plot(indx_x, indx_y + (indx_y / 40), marker=11)

    plt.text(indx_x, indx_y + (indx_y / 30), val_int_str, fontsize=16, color='r')

    print("Ends plot desde archivo para aceleracion")
    val_int = 1
    ex.upd_val_rh(val_int * 2)
    ex.upd_terminal("Valor de Reobase: " + str(val_int) + " Setando: " + str(val_int * 2))
    plt.legend(loc=2)
    plt.show()

    ## para leer el valor de la celula de carga


def butter_lowpass(cut_off, fs, order=5):
    nyq = 0.5 * fs
    normal_cut_off = cut_off / nyq
    b, a = butter(order, normal_cut_off, btype='low', analog=False)
    return b, a


def butter_lowpass_filter(data, cut_off, fs, order=5):
    b, a = butter_lowpass(cut_off, fs, order=order)
    y = lfilter(b, a, data)
    return y


def exit_program_and_stim():
    global start_receiver

    start_receiver = False
    print("Aplication closed, Stop Stimulation")
    ex.btn_stop_stim()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.aboutToQuit.connect(exit_program_and_stim)
    ex = MainWindow()
    sys.exit(app.exec_())
