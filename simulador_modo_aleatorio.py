import paho.mqtt.client as mqtt
import time
import random
import math
import json


# =========================================
# MQTT
# =========================================

broker = "broker.hivemq.com"
topico = "gerador/virtual/tcc"

client = mqtt.Client()
client.connect(broker, 1883, 60)


# =========================================
# PARÂMETROS DA REDE
# =========================================

vrms_nominal = 127


# =========================================
# CONTROLE DE EVENTOS
# =========================================

evento = "normal"
tempo_evento = 0

# THD simulada
thd = 0.0

# tempo da simulação
t = 0


print("Simulação iniciada...")


while True:

    # =====================================
    # GERENCIAMENTO DE EVENTOS
    # =====================================

    if tempo_evento <= 0:

        sorteio = random.random()

        # 35% normal por 3 s
        if sorteio < 0.35:

            evento = "normal"
            tempo_evento = 3

        # 20% afundamento por 5 s
        elif sorteio < 0.55:

            evento = "afundamento"
            tempo_evento = 5

            print("\nAFUNDAMENTO DETECTADO")

        # 20% sobretensão por 4 s
        elif sorteio < 0.75:

            evento = "sobretensao"
            tempo_evento = 4

            print("\nSOBRETENSÃO DETECTADA")

        # 10% transitório por 1 s
        elif sorteio < 0.85:

            evento = "transitorio"
            tempo_evento = 1

            print("\nTRANSITÓRIO DETECTADO")

        # 15% harmônicas por 6 s 
        else:

            evento = "harmonica"
            tempo_evento = 6

            print("\nHARMÔNICAS DETECTADAS")

    # =====================================
    # REDUZ TEMPO DO EVENTO
    # =====================================
    # Taxa de amostra = Aproximadamente 6,67 amostras por s
     
    tempo_evento -= 0.15


    # =====================================
    # TENSÃO BASE
    # =====================================

    tensao_rms = vrms_nominal

    # Reinicia a THD para cada ciclo
    thd = 0.0


    # =====================================
    # EVENTOS
    # =====================================

    # AFUNDAMENTO
    if evento == "afundamento":

        tensao_rms *= 0.80


    # SOBRETENSÃO
    elif evento == "sobretensao":

        tensao_rms *= 1.15


    # TRANSITÓRIO
    elif evento == "transitorio":

        tensao_rms *= random.uniform(1.3, 1.6)


    # HARMÔNICAS
    elif evento == "harmonica":

        # Componentes harmônicas simuladas
        harm3 = 4 * math.sin(
            2 * math.pi * 5 * t
        )

        harm5 = 2 * math.sin(
            2 * math.pi * 9 * t
        )

        tensao_rms += harm3 + harm5

        # Cálculo simplificado da THD para representar o cenário 
        # considerando as amplitudes das
        # componentes harmônicas simuladas

        rms_harm3 = 4 / math.sqrt(2)
        rms_harm5 = 2 / math.sqrt(2)

        thd = (
            math.sqrt(
                rms_harm3**2 +
                rms_harm5**2
            )
            / vrms_nominal
        ) * 100


    # =====================================
    # RUÍDO
    # =====================================

    ruido = random.uniform(-2, 2)

    tensao_rms += ruido


    # =====================================
    # LIMITES
    # =====================================

    if tensao_rms < 0:

        tensao_rms = 0


    # =====================================
    # ENVIO MQTT
    # =====================================

    valor_envio = round(tensao_rms, 2)
    valor_thd = round(thd, 2)

    payload = {

        "tensao": valor_envio,
        "evento": evento,
        "thd": valor_thd
    }

    client.publish(
        topico,
        json.dumps(payload)
    )


    # =====================================
    # MONITORAMENTO NO TERMINAL
    # =====================================

    print(
        f"Evento: {evento} | "
        f"Tensão RMS: {valor_envio} V | "
        f"THD: {valor_thd}%"
    )


    # =====================================
    # AVANÇA TEMPO
    # =====================================

    t += 0.15

    # velocidade dashboard
    time.sleep(0.15)