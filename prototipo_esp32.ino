#include <WiFi.h>
#include <PubSubClient.h>

// ==========================================
// WIFI 
// ==========================================

const char* ssid = "***";
const char* senha = "***";

// ==========================================
// MQTT
// ==========================================

const char* mqtt_server = "broker.hivemq.com";
const int mqtt_port = 1883;

const char* topico = "gerador/virtual/tcc";

WiFiClient espClient;
PubSubClient client(espClient);

// ==========================================
// POTENCIÔMETRO
// ==========================================

const int pinoPot = 34;

// ==========================================
// LEDs
// ==========================================

const int ledVerde = 25;
const int ledBranco = 26;
const int ledVermelho = 27;


// ==========================================
// CONEXÃO WIFI
// ==========================================

void conectarWiFi() {

  Serial.print("Conectando ao Wi-Fi");

  WiFi.begin(ssid, senha);

  while (WiFi.status() != WL_CONNECTED) {

    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.println("Wi-Fi conectado!");

  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}


// ==========================================
// CONEXÃO MQTT
// ==========================================

void conectarMQTT() {

  while (!client.connected()) {

    Serial.print("Conectando ao MQTT...");

    String clientID = "ESP32_TCC_";
    clientID += String(random(0xffff), HEX);

    if (client.connect(clientID.c_str())) {

      Serial.println(" conectado!");

    } else {

      Serial.print(" falhou. Estado = ");
      Serial.println(client.state());

      delay(2000);
    }
  }
}


// ==========================================
// SETUP
// ==========================================

void setup() {

  Serial.begin(115200);

  analogReadResolution(12);

  // LEDs
  pinMode(ledVerde, OUTPUT);
  pinMode(ledBranco, OUTPUT);
  pinMode(ledVermelho, OUTPUT);

  digitalWrite(ledVerde, LOW);
  digitalWrite(ledBranco, LOW);
  digitalWrite(ledVermelho, LOW);

  // Wi-Fi
  conectarWiFi();

  // MQTT
  client.setServer(mqtt_server, mqtt_port);
}


// ==========================================
// LOOP
// ==========================================

void loop() {

  // Verifica Wi-Fi
  if (WiFi.status() != WL_CONNECTED) {
    conectarWiFi();
  }

  // Verifica MQTT
  if (!client.connected()) {
    conectarMQTT();
  }

  client.loop();


  // ========================================
  // LEITURA DO POTENCIÔMETRO
  // ========================================

  int valorADC = analogRead(pinoPot);

  float tensaoADC = (valorADC / 4095.0) * 3.3;

  // Escala 0–3,3 V → 0–180 V
  float tensaoRede = (tensaoADC / 3.3) * 180.0;


 // ========================================
// CLASSIFICAÇÃO
// ========================================

String evento;

// Desliga todos os LEDs
digitalWrite(ledVerde, LOW);
digitalWrite(ledBranco, LOW);
digitalWrite(ledVermelho, LOW);


// CRÍTICA - SUBTENSÃO
if (tensaoRede < 110.0) {

  evento = "CRITICA_INFERIOR";

  digitalWrite(ledVermelho, HIGH);

}


// PRECÁRIA - SUBTENSÃO
else if (tensaoRede < 117.0) {

  evento = "PRECARIA_INFERIOR";

  digitalWrite(ledBranco, HIGH);

}


// ADEQUADA
else if (tensaoRede <= 133.0) {

  evento = "NORMAL";

  digitalWrite(ledVerde, HIGH);

}


// PRECÁRIA - SOBRETENSÃO
else if (tensaoRede <= 135.0) {

  evento = "PRECARIA_SUPERIOR";

  digitalWrite(ledBranco, HIGH);

}


// CRÍTICA - SOBRETENSÃO
else {

  evento = "CRITICA_SUPERIOR";

  digitalWrite(ledVermelho, HIGH);

}


  // ========================================
  // ENVIA MQTT
  // ========================================

  String payload = "{";
  payload += "\"tensao\":";
  payload += String(tensaoRede, 2);
  payload += ",\"evento\":\"";
  payload += evento;
  payload += "\"}";


  client.publish(
    topico,
    payload.c_str()
  );


  // ========================================
  // MONITOR SERIAL
  // ========================================

  Serial.print("ADC = ");
  Serial.print(valorADC);

  Serial.print(" | Tensao ADC = ");
  Serial.print(tensaoADC, 2);

  Serial.print(" V | Tensao simulada = ");
  Serial.print(tensaoRede, 1);

  Serial.print(" V | Evento = ");
  Serial.println(evento);


  delay(200);
}