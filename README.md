# Arquitetura Supervisória para Monitoramento e Proteção Simulada de Distúrbios de Tensão

Repositório de códigos-fonte do Trabalho de Conclusão de Curso em Engenharia Elétrica. A arquitetura integra geração de valores RMS em Python, comunicação MQTT, processamento e supervisão no Node-RED e um protótipo funcional de baixa tensão baseado em ESP32.

**Autores:** Gian Luca Silva Soares e Luciano Augusto Moura da Silva.

> **Escopo e segurança:** este é um projeto experimental. Os simuladores Python publicam valores RMS calculados ou definidos por software. O protótipo ESP32 usa um potenciômetro como entrada analógica e converte sua leitura para uma escala simulada de tensão. Não é um instrumento de medição, não comanda um disjuntor físico e não deve ser conectado diretamente à rede elétrica.

## Estrutura

```text
.
├── python/
│   ├── simulador_modo_aleatorio.py
│   └── simulador_modo_controlado.py
├── dataset/
│   ├── reproduzir_seed_pqd.py
│   ├── Pure_Sinusoidal.csv
│   ├── Sag.csv
│   ├── Swell.csv
│   ├── Harmonics.csv
│   └── README.md
├── node-red/
│   ├── flows_completo_10_amostras.json
│   ├── flows_completo_3_amostras_dataset.json
│   └── README.md
├── esp32/
│   ├── prototipo_esp32.ino
│   └── README.md
├── requirements.txt
└── .gitignore
```

## Requisitos

- Python 3.11.9 (ambiente utilizado no desenvolvimento).
- Node-RED 4.1.8.
- Pacote `node-red-dashboard` 3.6.6.
- Arduino IDE com suporte à placa ESP32 e biblioteca `PubSubClient`.

Instale as dependências Python na raiz do repositório:

```bash
python -m pip install -r requirements.txt
```

## Simuladores Python

Os dois simuladores Python publicam no broker MQTT `broker.hivemq.com`, porta `1883`, tópico `gerador/virtual/tcc`.

### Geração aleatória

```bash
python python/simulador_modo_aleatorio.py
```

Os eventos são selecionados aleatoriamente conforme probabilidades e durações definidas no código. O intervalo nominal entre publicações é de 0,15 s (aproximadamente 6,67 publicações por segundo, desconsiderando o tempo de processamento e comunicação).

### Cenários controlados

```bash
python python/simulador_modo_controlado.py
```

Para executar um ensaio controlado, abra o arquivo e ajuste `MODO_SIMULACAO = "teste"` e o parâmetro `CENARIO_TESTE` para um dos cenários predefinidos. O script enviado está configurado inicialmente para `MODO_SIMULACAO = "normal"`.

## Validação com o dataset SEED-PQD v1

A pasta `dataset/` contém o script de reprodução e os quatro arquivos CSV utilizados na validação: `Pure_Sinusoidal`, `Sag`, `Swell` e `Harmonics`. O conjunto original possui 17 classes; este repositório disponibiliza somente as quatro classes selecionadas no trabalho. Consulte `dataset/README.md` para a atribuição, a referência bibliográfica e os termos de licença dos dados.

Execute a partir da raiz do repositório:

```bash
python dataset/reproduzir_seed_pqd.py
```

O script está configurado para enviar 50 sinais de cada classe e 15 sinais normais de recuperação após cada classe de distúrbio. A frequência fundamental considerada é 50 Hz, a amostragem original é 5 kHz e cada sinal contém 100 amostras (20 ms). A conversão dos sinais normalizados para volts é uma escala hipotética calibrada para que o RMS médio da classe senoidal pura corresponda a 127 V; não representa medição real da rede. O intervalo entre publicações MQTT é 0,15 s e não deve ser confundido com o intervalo original entre as amostras de 5 kHz.

Para essa validação, utilize o fluxo Node-RED com média móvel de **3 amostras**.

## Node-RED

Os arquivos em `node-red/` são exportações completas do fluxo:

- `flows_completo_10_amostras.json`: configuração utilizada nos ensaios gerais.
- `flows_completo_3_amostras_dataset.json`: configuração utilizada na validação com o SEED-PQD v1.

Importe apenas um fluxo por vez: menu do Node-RED → **Importar** → selecione o JSON correspondente. O fluxo usa o broker público `broker.hivemq.com:1883` e o tópico `gerador/virtual/tcc`. Confira a instalação do pacote `node-red-dashboard` 3.6.6. Mais orientações em `node-red/README.md`.

A assinatura do Node-RED está configurada com QoS 2, mas os simuladores Python e o firmware ESP32 publicam com QoS 0; portanto, a entrega ponta a ponta é limitada ao QoS 0 do publicador.

## Protótipo ESP32

O firmware está em `esp32/prototipo_esp32.ino`. Antes de gravar a placa, substitua localmente os campos `ssid` e `senha` pelos dados da sua rede Wi-Fi. Não coloque credenciais reais em commits públicos. A leitura do potenciômetro é convertida linearmente para uma escala simulada de 0 a 180 V. Consulte `esp32/README.md`.

## Broker MQTT e limitações de segurança

Os códigos utilizam um broker público, sem autenticação e sem TLS, com porta 1883. O tópico também é público e pode receber mensagens de terceiros. Essa configuração foi adotada para os ensaios acadêmicos; não use esses parâmetros para dados sensíveis nem em uma aplicação real de proteção elétrica.

## Licenças

Os arquivos de dados do SEED-PQD v1 estão identificados em `dataset/README.md` como conteúdo sob **Creative Commons Attribution 4.0 International (CC BY 4.0)**, conforme a fonte do conjunto. Essa licença aplica-se aos dados indicados, não automaticamente aos códigos desenvolvidos pelos autores do TCC. Não foi selecionada uma licença de reutilização para o código-fonte neste repositório.
