// Agregando la biblioteca
#include <Wire.h>

// Direccion del Acelerometro
const int MPU = 0x68;

// Variable para control temporal - medir tiempo
unsigned long ini = 0, fin = 0;

// Variables para guardar datos del acelerometro
long AcX, AcY, AcZ;

// Inicializacion
void setup() {
  //Inicio serial
  Serial.begin(115200);
  //Inicio I2C
  Wire.begin();
  //Configuro velocidad maxima do I2C
  Wire.setClock(400000);

  // activar el accel
  Wire.beginTransmission(MPU);
  Wire.write(0x6B);  // envio requisicion de comienzo
  Wire.write(0);     // configuro el envio de datos
  Wire.endTransmission(true); // Termino la transmision y configuracion
}

void loop() {
  // Espera un caracter para realizar una medida
  if (Serial.available() != 0) {
    Serial.readString();
    // para medir inicio y fin
    Serial.print("Inicio: ");
    ini = micros();
    Serial.println(ini);

    read_mpu(); //  leo los datos

    fin = micros() - ini;
    Serial.print("Fin: ");
    Serial.println(fin);

    Serial.print("Inicio: ");
    ini = micros();
    Serial.println(ini);
    int c = 0;
    while (c < 10000) {
      read_mpu(); //  leo los datos
      c += 1;
    }

    fin = micros() - ini;
    Serial.print("Fin: ");
    Serial.println(fin);

  }


}

void read_mpu() {
  Wire.beginTransmission(MPU); //comienzo transmision
  Wire.write(0x3B); // comenzando con el registro 0x3B (ACCEL_XOUT_H)
  Wire.endTransmission(false);

  Wire.requestFrom(MPU, 6, true); // Solicita 6 bytes que son los relacionados a los ejes XYZ

  AcX = Wire.read() << 8 | Wire.read(); // 0x3B (ACCEL_XOUT_H) & 0x3C (ACCEL_XOUT_L)
  AcY = Wire.read() << 8 | Wire.read(); // 0x3D (ACCEL_YOUT_H) & 0x3E (ACCEL_YOUT_L)
  AcZ = Wire.read() << 8 | Wire.read(); // 0x3F (ACCEL_ZOUT_H) & 0x40 (ACCEL_ZOUT_L)

  // Imprime los datos
  Serial.print("AcX = ");
  Serial.print(AcX);
  Serial.print(" | AcY = ");
  Serial.print(AcY);
  Serial.print(" | AcZ2 = ");
  Serial.println(AcZ);
}
