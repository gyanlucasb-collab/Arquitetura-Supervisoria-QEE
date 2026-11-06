# Protótipo ESP32

O arquivo `prototipo_esp32.ino` implementa a leitura de um potenciômetro, classifica a escala simulada de tensão e publica as informações pelo MQTT.

## Preparação

1. Abra o arquivo na Arduino IDE.
2. Selecione uma placa ESP32 compatível.
3. Instale a biblioteca `PubSubClient`.
4. Substitua os valores `***` nas variáveis `ssid` e `senha` pelas credenciais Wi-Fi locais.
5. Grave o firmware e acompanhe as mensagens pela Serial.

A configuração de rede permanece como placeholder neste repositório. Não publique suas credenciais reais.

O firmware lê o potenciômetro no GPIO 34 e aciona LEDs nos GPIOs 25, 26 e 27. A entrada ADC é convertida para uma escala simulada de 0 a 180 V. Não conecte o circuito diretamente à rede elétrica: o protótipo não possui condicionamento, isolamento ou medição de tensão de rede.
