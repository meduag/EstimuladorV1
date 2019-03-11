// Carrega a biblioteca Wire
#include <Wire.h>
// Endereco I2C do MPU6050
const int MPU = 0x68;
unsigned long ini = 0, fin = 0;
// Variaveis para armazenar valores dos sensores
long AcX, AcY, AcZ;
void setup(){
  Serial.begin(115200);
  Wire.begin();
  Wire.setClock(400000);

  Wire.beginTransmission(MPU);
  Wire.write(0x6B);
  // Inicializa o MPU-6050
  Wire.write(0);
  Wire.endTransmission(true);
}

void loop(){
  if (Serial.available() != 0)
  {
    Serial.readString();
    //delay(1000);
    Serial.print("Inicio: ");
    ini = micros();
    Serial.println(ini);
    read_mpu();
    fin = micros() - ini;
    Serial.print("Fin: ");
    Serial.println(fin);
    //Serial.readString();
  }
}

void read_mpu(){
  // int c = 0;
  /*Serial.println("tempo pedido accel");
  delay(100);
  ini = micros();
  Serial.println(ini);*/
  Wire.beginTransmission(MPU);
  Wire.write(0x3B); // starting with register 0x3B (ACCEL_XOUT_H)
  Wire.endTransmission(false);
  /*fin = micros() - ini;
  Serial.println(fin);


  Serial.println("tempo req");
  ini = micros();
  Serial.println(ini);*/
  // Solicita os dados do sensor
  Wire.requestFrom(MPU, 6, true);
 /* fin = micros() - ini;
  Serial.println(fin);



  Serial.println("tempo dados accel");
  delay(100);
  ini = micros();
  Serial.println(ini);*/
  // Armazena o valor dos sensores nas variaveis correspondentes
  AcX = Wire.read() << 8 | Wire.read(); // 0x3B (ACCEL_XOUT_H) & 0x3C (ACCEL_XOUT_L)
  /* Serial.print(AcX);
  Serial.write(0x3B);
  while(c <= 100000){
  c = c + 1;
  }
  c=0;*/

  AcY = Wire.read() << 8 | Wire.read(); // 0x3D (ACCEL_YOUT_H) & 0x3E (ACCEL_YOUT_L)
  /*Serial.print(AcY);
  Serial.write(0x3B);
  while(c <= 100000){
  c = c + 1;
  }*/
  AcZ = Wire.read() << 8 | Wire.read(); // 0x3F (ACCEL_ZOUT_H) & 0x40 (ACCEL_ZOUT_L)
/*  fin = micros() - ini;
  Serial.println(fin);
  Serial.print(AcZ);
  Serial.write(0x3B);*/
  // Envia valor X do acelerometro para a serial e o LCD

  /*Serial.println("tempo impresao");
  ini = micros();
  Serial.println(ini);*/
  Serial.print("AcX = ");
  Serial.print(AcX);
  Serial.print(" | AcY = ");
  Serial.print(AcY);
  Serial.print(" | AcZ2 = ");
  Serial.println(AcZ);
  /*fin = micros() - ini;
  Serial.println(fin);*/
}
