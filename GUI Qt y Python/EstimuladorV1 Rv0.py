import sys
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox
import threading
import math

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
""" 
 0 - Tex activation
 1 - Stop control
 2 - Update data 
 3 - Control for send value to stim/acel """

flags = [0, 0, 0, 0]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up the user interface from Designer.
        uic.loadUi("EstimuladorV1-Rv0.ui", self)

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
            if (ri1 + rf1) > ton1:
                QMessageBox.about(self, "Error", "Error in Ramp value \nTon is less than (Ramp up + Ramp down) \nMessage no send")
                sout = 1

                ### aqui poso colocar que nao pode enviar valores para o serial
                """while sout == 1:
                    ri1 = self.spinBox_ri1.value()
                    rf1 = self.spinBox_rf1.value()
                    ton1 = self.spinBox_tn1.value()
                    if (ri1 + rf1) > ton1:
                        QMessageBox.about(self, "Error", "Ramp value erro \n Ton is less than (Ramp up + Ramp down)")
                    else:
                        sout = 0"""
            else:
                ch1[2] = int((ton1 - (ri1 + rf1))*10)

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

        if flags[3] == 0:
            print("MSG:  " + msg + " No send")
        else:
            print("MSG:  " + msg)
            ## Aqui pode ser enviado  para el serial

    @staticmethod
    def map(x, in_min, in_max, out_min, out_max):
        return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)

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
