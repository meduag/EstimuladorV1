#include <SPI.h>                // Library for SPI communication
#include "I2Cdev.h"
#include "MPU6050.h"
#if I2CDEV_IMPLEMENTATION == I2CDEV_ARDUINO_WIRE
#include "Wire.h"
#endif

// Output pins
#define RELAY_CH_1 6            // Relay for CH1
#define RELAY_CH_2 7            // Relay for CH2
#define BuzzerPin 9             // Buzzer pin activation for status messages
#define DAC_SS_PIN 10			// Pin for enable DAC communication

// Input pins
#define Pin_Inter 23            // Emergency Button

// Values for DAC calibration
#define CH1_MAX_POS 1883		// Ch1 max positive value
#define CH1_MIN_NEG 1842		// Ch1 max negative value
#define CH2_MAX_POS 2047		// Ch2 max positive value
#define CH2_MIN_NEG 2047		// Ch2 max negative value
#define STIM_ZERO 2047      // Zero valoue for reference on DAC 
#define min_stim 5          // Estimulacion minima para ZeroChannels

// Byte of
#define fin '>'             // Character separator used for split data '>'
#define num_struc 2

#define t_min 60000000
#define t_seg 1000000
#define t_mil 100000

// criação do Objeto do Aclererometro
MPU6050 acel;

// variaveis de control y captura de dados do alcelerometro
// 0 - eixo X
// 1 - eixo Y
// 2 - eixo Z
int16_t acxyz[] = {0, 0, 0}; 


//unsigned int pwrc = 2e6;    // Time of rest used in tests rh and cr AINDA SIM USAR

// Matrix Output_Pins
int Output_Pins[] = {RELAY_CH_1, RELAY_CH_2, BuzzerPin, DAC_SS_PIN};

// For input data
String data_in = "0";           // General variable for data in serial communication

// Global variables
/************* BOOL *******************/
// 0 - loop_s
// 1 - tex
// 2 - ar ---- trocar por activacion de rampa
// 3 - upd
bool b_var[] = {1, 0, 0, 0};

/************ unsigned int ************/
// 0 - ts
// 1 - pw
// 2 - pwr
// 3 - l_mai
// 4 - l_maf
// 5 - min_t > us
// 6 - seg_t > us
// 7 - ms_t  > us

unsigned long ul_var[] = {0, 0, 0, 0, 0, t_min, t_seg, t_mil};

/************* Unsigned long for time ******************/
// 0 - time for final ts
// 1 - time for final ton/tsus, toff, ri and rf
// 2 - time for final pw and pwr
// 3 - time for minute lapse in control stimulation
// 4 - buzer time on stimulation function
unsigned long ul_vt[] = {0, 0, 0, 0, 0};
//unsigned long* ul_vt = NULL;

/*************** Struct for channels data **************/
// ch - ma - tn - tf >> sps
// 0 - ch_act   // 1 - ma     // 2 - tn     // 3 - tf
// 4 - ri     // 5 - rf

struct sp { //stimulation_parameters
  unsigned long sps[6] = {0, 0, 0, 0, 0, 0};
};

// Initialize structure
struct sp * data_sp; // stimulation values for CH1


/**************************************************************/
/************************* Setup ******************************/
/**************************************************************/
void setup() {
    // join I2C bus (I2Cdev library doesn't do this automatically)
  #if I2CDEV_IMPLEMENTATION == I2CDEV_ARDUINO_WIRE
    Wire.begin();
  #elif I2CDEV_IMPLEMENTATION == I2CDEV_BUILTIN_FASTWIRE
    Fastwire::setup(400, true);
  #endif

  // Initialize parameters for Stim-PC communication
  Serial.begin(2000000);
  Serial.setTimeout(1);
  Serial.flush();

  // Initializa SPI comunication
  SPI.begin();
  acel.initialize();

  // Initialize Output pins
  for (int i = 0; i < 4; i++) {
    pinMode(Output_Pins[i], OUTPUT);
    digitalWrite(Output_Pins[i], 0);
  }

  // SPI disable with 1- Ena 0
  digitalWrite(Output_Pins[3], 1);

  pinMode(Pin_Inter, INPUT);              				// Extern interruption
  attachInterrupt(Pin_Inter, Stop_fx, RISING); 	// Extern interruption configuration

  // Initialize allocated memory for 4 structures
  data_sp = (struct sp *) malloc(num_struc * sizeof(struct sp));

  //ul_vt = (unsigned long*) malloc(1 * sizeof(unsigned long));

  // Inizialite structures with 0 value
  for (int i = 0; i < num_struc; i++) {
    InitializVal_struct(i);
  }

  // Initialize stimulation with preload
  zeroChannels();

  // Bipp of initialization
  beep(2, 100, 2);
}


/**************************************************************/
/************************* Loop ******************************/
/**************************************************************/
void loop() {
  // Loops for check input data
  while (b_var[0]) {
    // Function for input data
    read_dataIn();
  }

  Serial.println("Pasando a Stimulacion");

  stimulation();

  zeroChannels();

  b_var[0] = 1;
}


/**************************************************************/
/******************** Read input data *************************/
/**************************************************************/
void read_dataIn() {
  /// Example data in
  // 10>500>19000>1>20>1>1500>2>2>5>5>1>1500>2>2>5>5>0>1>0>
  if (Serial.available() != 0) {
    //data_in = Serial.readString();
    //Serial.println(data_in);

    /* ----Read --- Geral parameters
      // 0 Therapy time
      // 1 Pulse Width
      // 2 Pulse Width rest
      // 3 Limit mA inf
      // 4 Limit mA sup */
    for (int i = 0; i < 5; i++) {
      data_in = Serial.readStringUntil(fin);
      ul_var[i] = data_in.toInt();
    }

    /* ---- Read --- CH1 & CH2 ---- x2
      // 0 Ch activation
      // 1 mA
      // 2 Ton
      // 3 Toff
      // 4 Ramp Up
      // 5 Ramp Down */
    for (int i = 0; i < 2; i++) {
      for (int j = 0; j < 6; j++) {
        data_in = Serial.readStringUntil(fin);
        data_sp[i].sps[j] = data_in.toInt();
      }
    }

    /* --- Read --- Activations
      // 1 Excitability test
      // 2 Stop Control / Emergency stop
      // 3 Update Values */
    for (int i = 1; i < 4; i++) {
      data_in = Serial.readStringUntil(fin);
      b_var[i] = data_in.toInt();
    }

    //---------- Clean buffer input  ----------//
    Serial.readString(); // Read the rest of the message if has
    Serial.flush();      // Wait the last byte of In/Out

    //******* End data split *******//
    ul_var[0] = ul_var[0] * ul_var[5]; // * min_t

    // Pass data to structures de CH1 and CH2 in us
    for (int i = 0; i < 2; i++) {
      for (int j = 2; j < 6; j++) {
        if (j < 4) {
          data_sp[i].sps[j] = data_sp[i].sps[j] * ul_var[6]; // ton toff
        } else {
          data_sp[i].sps[j] = data_sp[i].sps[j] * ul_var[7]; // ri rf *
        }
      }
    }

    // Stop all types of process
    if (b_var[2] == 1) { // value of 1 for exit read data
      // Exit from read input data
      b_var[0] = false;
    } else {
      // Stop stimulation
      zeroChannels();

      // Return to while for input data
      b_var[0] = true;
    }

    // Check if input data is right
    if ((data_sp[0].sps[0] + data_sp[1].sps[0] + b_var[1]) == 0) {
      // Return to while for input data
      b_var[0] = true;
      Serial.println("Corrupt message or no stimulation - Try again");
    } else {
      print_dataIn();
      b_var[0] = false;
    }

  }// End if serial available

}// End function read_data


/**************************************************************/
/*************** Stimulation Training function ****************/
/**************************************************************/
void stimulation() {
  //Serial.println("<Estimulacion");
  
  //Start beep
  beep(1, 100, 2);

  // Un segundo antes de comenzar la estimulacion
  Serial.write(micros());
  Serial.write(';0');

  /// Example data in
  // 2>500>19500>1>1883>1>76>1>2>5>5>0>4079>2>5>10>20>0>0>0>



  // Variables auxiliares y sus valores iniciales
  // 0 - seq = 1;                            // secuencia de la senal general  canal 1
  // 1 - spw = 1;                            // secuencia de la señal especifica canal 1
  // 2 - mA = 0;                             // valor de miliamp sendo pasos ou valor final
  // 3 - cont_min = 0;                       // contador de minutos
  int v_aux[] = {1, 1, 0, 0};

  //Serial.print("Paso mA: ");
  //Serial.println(data_sp[0].sps[1]);

  ul_vt[3] = micros() + ul_var[5];          // * min_t
  ul_vt[0] = micros() + ul_var[0];          // ts - valor final de tiempo

  // valor inicial rampa o tsus
  // Serial.println("Ton >>>>>>>");
  if (data_sp[0].sps[4] > 0) { // aqui verifico si la rampa existe
    v_aux[0] = 1;
    Serial.println("Ramp Up");
    Serial.write('1');
    v_aux[2] = data_sp[0].sps[1];
    digitalWrite(Output_Pins[0], 1);
    sendStimValue(0, 1, STIM_ZERO + v_aux[2]);
    ul_vt[1] = micros() + data_sp[0].sps[4];       // tiempo de ramap
  } else {
    v_aux[0] = 2;
    Serial.println("Support");
    v_aux[2] = ul_var[4];
    digitalWrite(Output_Pins[0], 1);
    sendStimValue(0, 1, STIM_ZERO + v_aux[2]);
    ul_vt[1] = micros() + data_sp[0].sps[2];
  }

  ul_vt[2] = micros() + ul_var[1];          // tiempo pwm inicial


  /*************************************************************/
  /////////////////////// tiempo de terapia /////////////////////
  /*************************************************************/
  Serial.print("Inicio: ");
  Serial.println(micros());

  while (micros() < ul_vt[0]) { // ts
    if (data_sp[0].sps[0] == 1) {
      if (micros() > ul_vt[1]) {
        sendStimValue(0, 1, STIM_ZERO + min_stim);
        switch (v_aux[0]) {
          case 1:   // rampa up
            v_aux[0] = 2;
            ul_vt[1] = micros() + data_sp[0].sps[2];
            Serial.println("Support");
            break;
          case 2:  // sustentacion
            if (data_sp[0].sps[5] > 0) {
              v_aux[0] = 3;
              ul_vt[1] = micros() + data_sp[0].sps[5];
              Serial.println("Ramp Down");
            } else {
              v_aux[0] = 4;
              ul_vt[1] = micros() + data_sp[0].sps[3];
              Serial.println("Toff");
              v_aux[2] = 0;
            }
            break;
          case 3:  // ramapa down
            v_aux[0] = 4;
            ul_vt[1] = micros() + data_sp[0].sps[3];
            Serial.println("Toff");
            v_aux[2] = 0;
            break;
          case 4:  // t_off
            if (data_sp[0].sps[4] > 0) {
              v_aux[0] = 1;
              ul_vt[1] = micros() + data_sp[0].sps[4];
              Serial.println("Ramp Up");
            } else {
              v_aux[0] = 2;
              ul_vt[1] = micros() + data_sp[0].sps[2];
              Serial.println("Support");
            }
            break;
        }
      }
    }

    /****************************************************************/
    //////////////////////// Make a signal ///////////////////////////
    /****************************************************************/
    if (micros() >= ul_vt[2] && v_aux[0] < 4) {
      switch (v_aux[1]) {
        case 1:  // mA
          v_aux[1] = 2;
          sendStimValue(0, 1, STIM_ZERO - v_aux[2]);
          ul_vt[2] = micros() + ul_var[1];
          break;
        case 2:
          v_aux[1] = 3;
          //ul_vt[3] = micros(); // para ver el tiempo de pwr menos y hacer alguna cosa
          switch (v_aux[0]) {
            case 1:
              if (v_aux[2] < ul_var[4]) {
                v_aux[2] = v_aux[2] + data_sp[0].sps[1];
              }
              break;
            case 2:
              v_aux[2] = ul_var[4];
              break;
            case 3:
              if (v_aux[2] > 0) {
                v_aux[2] = v_aux[2] - data_sp[0].sps[1];
              }
              break;
          }
          sendStimValue(0, 1, STIM_ZERO - 10);
          //ul_vt[3] = micros() - ul_vt[3];
          //ul_vt[2] = micros() + (ul_var[2] - ul_vt[3]);
          ul_vt[2] = micros() + ul_var[2];
          break;
        case 3:
          v_aux[1] = 1;
          sendStimValue(0, 1, STIM_ZERO + v_aux[2]);
          ul_vt[2] = micros() + ul_var[1];
          break;
      }

    }

    // Verify the time for every minute
    if(micros() >= ul_vt[3]){
      //Serial.println("m");
      v_aux[3] += 1; // contador  para imprimir minutos
      ul_vt[3] = micros() + ul_var[5];          // * min_t
      digitalWrite(Output_Pins[2], 1); // Enable pin buzzer
      ul_vt[4] = 2e5 + micros();
    }

    // Activate the buzzer sequence
    if (micros() >= ul_vt[4]) {
      digitalWrite(Output_Pins[2], 0); // Disable pin buzzer
      ul_vt[4] = ul_vt[0];
    }

    // falta cololocar actualizacion


  }// <<<< End ts >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

  Serial.print("Fim: ");
  Serial.println(micros());
  

  // Bipp for end or stop stimulation
  beep(2, 200, 1);

  // Stop stimulation
  zeroChannels();
}// Ends therapy function


/**************************************************************/
/********************* Stop everything ************************/
/**************************************************************/
void Stop_fx() {
  zeroChannels();
  data_sp[0].sps[0] = 0;  // ch2 activation off
  data_sp[1].sps[0] = 0;  // ch2 activation off
  data_sp[0].sps[1] = 0;  // ma
  data_sp[1].sps[1] = 0;  // ma
}


/**************************************************************/
/********************* Stop stimulation ***********************/
/**************************************************************/
void zeroChannels() {
  digitalWrite(Output_Pins[0], 0);
  digitalWrite(Output_Pins[1], 0);
  sendStimValue(0, 1, (STIM_ZERO + min_stim));
  sendStimValue(1, 1, (STIM_ZERO + min_stim));
}


/**************************************************************/
/**************** DAC Communication function ******************/
/**************************************************************/
void sendStimValue(int address, int operation_mode, uint16_t value) {
  byte valueToWriteH = 0;
  byte valueToWriteL = 0;
  valueToWriteH = highByte(value);
  valueToWriteH = 0b00001111 & valueToWriteH;
  valueToWriteH = (address << 6) | (operation_mode << 4) | valueToWriteH;
  valueToWriteL = lowByte(value);
  digitalWrite(Output_Pins[3], 0);
  SPI.transfer(valueToWriteH);
  SPI.transfer(valueToWriteL);
  digitalWrite(Output_Pins[3], 1);
}

/**************************************************************/
/********************* Stop stimulation ***********************/
/**************************************************************/
void beep(int qtd, int t, int vc) {
  for (int i = 0; i <= qtd; i++) {
    digitalWrite(Output_Pins[2], 1);
    delay(t * vc);
    digitalWrite(Output_Pins[2], 0);
    delay(t);
  }
  digitalWrite(Output_Pins[2], 0);
}


/**************************************************************/
/********************* Initialize structs *********************/
/**************************************************************/
void InitializVal_struct(int ch) {
  for (int i = 0; i < 4; i++) {
    data_sp[ch].sps[i] = 0;
  }
}


void print_dataIn() {

  Serial.println("\n\n------------------------------------- Print all Data");

  Serial.print("Valor de TS: ");
  Serial.print(ul_var[0]);
  Serial.println("\t ul_var[0]");

  Serial.print("Valor de PW: ");
  Serial.print(ul_var[1]);
  Serial.println("\t ul_var[1]");

  Serial.print("Valor de PW_r: ");
  Serial.print(ul_var[2]);
  Serial.println("\t ul_var[2]");

  /////////////////////////////////////// CH1
  Serial.println("-------------------------------- CH1 ");
  Serial.print("Valor de tn: ");
  Serial.print(data_sp[0].sps[2]);
  Serial.println("\t data_sp[0].sps[2]");

  Serial.print("Valor de tf: ");
  Serial.print(data_sp[0].sps[3]);
  Serial.println("\t data_sp[0].sps[3]");

  Serial.print("Valor de ri: ");
  Serial.print(data_sp[0].sps[4]);
  Serial.println("\t data_sp[0].sps[4]");

  Serial.print("Valor de rf: ");
  Serial.print(data_sp[0].sps[5]);
  Serial.println("\t data_sp[0].sps[5]");

  Serial.print("Valor de pasos ma: ");
//  float paso_p = float(data_sp[0].sps[1]) / 100;
  Serial.print(data_sp[0].sps[1]);
  Serial.println("\t data_sp[0].sps[2]");


  /////////////////////////////////////// CH2
  Serial.println("-------------------------------- CH2 ");
  Serial.print("Valor de tn: ");
  Serial.print(data_sp[1].sps[2]);
  Serial.println("\t data_sp[1].sps[2]");

  Serial.print("Valor de tf: ");
  Serial.print(data_sp[1].sps[3]);
  Serial.println("\t data_sp[1].sps[3]");

  Serial.print("Valor de ri: ");
  Serial.print(data_sp[1].sps[4]);
  Serial.println("\t data_sp[1].sps[4]");

  Serial.print("Valor de rf: ");
  Serial.print(data_sp[1].sps[5]);
  Serial.println("\t data_sp[1].sps[5]");

  Serial.print("Valor de pasos ma: ");
  //paso_p = float(data_sp[1].sps[1]) / 100;
  Serial.print(data_sp[1].sps[1]);
  Serial.println("\t data_sp[1].sps[1]");

  ////////////////////////////// limits
  Serial.println("-------------------------------- Limites ");
  Serial.print("Valor de lim rh ini: ");
  Serial.print(ul_var[3]);
  Serial.println("\t ul_var[3]");


  Serial.print("Valor de lim rh fin: ");
  Serial.print(ul_var[4]);
  Serial.println("\t ul_var[4]");


  /////////////////////////////////////// Activations
  Serial.println("-------------------------------- Activations ");
  Serial.print("Valor de act rh: ");
  Serial.print(b_var[1]);
  Serial.println("\t b_var[1]");

  Serial.print("Valor de act ch1: ");
  Serial.print(data_sp[0].sps[0]);
  Serial.println("\t data_sp[0].sps[0]");

  Serial.print("Valor de act ch2: ");
  Serial.print(data_sp[1].sps[0]);
  Serial.println("\t data_sp[1].sps[0]");

  Serial.print("Valor de act stop control: ");
  Serial.print(b_var[2]);
  Serial.println("\t b_var[2]");

  Serial.print("Valor de act update: ");
  Serial.print(b_var[3]);
  Serial.println("\t b_var[3]");

  Serial.println("");
  Serial.println("");
  Serial.println("");
  Serial.println("");
}
