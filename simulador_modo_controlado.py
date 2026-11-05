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
# MODO DE SIMULAÇÃO
# =========================================

MODO_SIMULACAO = "normal"

# Opções:
# "normal" -> geração aleatória
# "teste"  -> valores controlados

CENARIO_TESTE = "trip_sub_curto"


# =========================================
# CENÁRIOS CONTROLADOS
# =========================================

CENARIOS = {

    # -----------------------------------------
    # Teste da histerese na região de subtensão
    # -----------------------------------------
    "histerese_sub": [

        (127.0, 6.0, "normal"),

        # Entra em condição crítica
        (105.0, 1.0, "afundamento"),

        # Ainda abaixo do limite de saída
        (114.0, 1.0, "afundamento"),
        (116.0, 1.0, "afundamento"),

        # A partir de 117 V deve sair da condição crítica
        (117.0, 7.0, "normal"),
        (118.0, 3.0, "normal"),

        # Retorno ao nominal
        (127.0, 2.0, "normal"),
    ],


    # -----------------------------------------
    # Teste da histerese na região de sobretensão
    # -----------------------------------------
    "histerese_sobre": [

        (127.0, 2.0, "normal"),
        (140.0, 2.0, "sobretensao"),
        (134.0, 2.0, "sobretensao"),
        (132.0, 2.0, "normal"),
        (127.0, 2.0, "normal"),
    ],


    # -----------------------------------------
    # Teste de subtensão crítica prolongada
    # -----------------------------------------
    "trip_sub": [

        (127.0, 2.0, "normal"),
        (105.0, 8.0, "afundamento"),
        (127.0, 2.0, "normal"),
    ],


    # -----------------------------------------
    # Teste de subtensão crítica curta
    # Deve NÃO ocorrer TRIP
    # -----------------------------------------
    "trip_sub_curto": [

        (127.0, 5.0, "normal"),
        (121.0, 5.0, "normal"),


        # Entra em condição crítica
        (105.0, 3.0, "afundamento"),

        # Retorna antes de completar os 4 s
        (127.0, 5.0, "normal"),
    ],


    # -----------------------------------------
    # Teste de sobretensão crítica prolongada
    # -----------------------------------------
    "trip_sobre": [

        (127.0, 5.0, "normal"),
        (140.0, 8.0, "sobretensao"),
        (127.0, 5.0, "normal"),
    ],


    # -----------------------------------------
    # Teste de transitório
    # -----------------------------------------
    "transitorio": [

        (127.0, 5.0, "normal"),

        # Início do transitório
        (170.0, 0.15, "transitorio"),
        (195.0, 0.15, "transitorio"),
        (180.0, 0.15, "transitorio"),
        (200.0, 0.15, "transitorio"),
        (175.0, 0.15, "transitorio"),
        (190.0, 0.15, "transitorio"),
        (165.0, 0.15, "transitorio"),

        # Retorno ao nominal
        (127.0, 4.0, "normal"),
    ],


    # -----------------------------------------
    # Teste de harmônicas
    # -----------------------------------------
    "harmonica": [

        (127.0, 4.0, "normal"),

        # Condição com distorção harmônica
        (127.0, 6.0, "harmonica"),

        # Retorno ao nominal
        (127.0, 4.0, "normal"),
    ],


    # -----------------------------------------
    # Teste de filtragem com ruído
    # -----------------------------------------
    "filtragem_ruido": [

        (127.0, 2.0, "normal"),

        # 127 V com ruído aleatório de ±2 V
        (127.0, 8.0, "ruido"),

        # Retorno ao nominal sem ruído
        (127.0, 3.0, "normal"),
    ]
}


# =========================================
# CONTROLE DE EVENTOS
# =========================================

evento = "normal"
tempo_evento = 0

# Controle do modo teste
indice_teste = 0
tempo_teste = 0

# THD simulada
thd = 0.0

# Tempo da simulação
t = 0


print("Simulação iniciada...")
print("Modo:", MODO_SIMULACAO)

if MODO_SIMULACAO == "teste":
    print("Cenário:", CENARIO_TESTE)


# =========================================
# LOOP PRINCIPAL
# =========================================

while True:

    # =====================================
    # GERENCIAMENTO DE EVENTOS
    # =====================================

    if MODO_SIMULACAO == "normal":

        # =================================
        # MODO NORMAL - EVENTOS ALEATÓRIOS
        # =================================

        if tempo_evento <= 0:

            sorteio = random.random()

            # 35% normal
            if sorteio < 0.35:

                evento = "normal"
                tempo_evento = 3

            # 20% afundamento
            elif sorteio < 0.55:

                evento = "afundamento"
                tempo_evento = 5

                print("\nAFUNDAMENTO DETECTADO")

            # 20% sobretensão
            elif sorteio < 0.75:

                evento = "sobretensao"
                tempo_evento = 4

                print("\nSOBRETENSÃO DETECTADA")

            # 10% transitório
            elif sorteio < 0.85:

                evento = "transitorio"
                tempo_evento = 1

                print("\nTRANSITÓRIO DETECTADO")

            # 15% harmônicas
            else:

                evento = "harmonica"
                tempo_evento = 6

                print("\nHARMÔNICAS DETECTADAS")

        # Reduz tempo do evento
        tempo_evento -= 0.15


    else:

        # =================================
        # MODO TESTE - CENÁRIO CONTROLADO
        # =================================

        if tempo_teste <= 0:

            # Verifica se terminou o cenário
            if indice_teste >= len(CENARIOS[CENARIO_TESTE]):

                print("\n=================================")
                print("TESTE CONCLUÍDO")
                print("=================================")

                break

            # Carrega próximo estágio
            tensao_teste, duracao_teste, evento = \
                CENARIOS[CENARIO_TESTE][indice_teste]

            tempo_teste = duracao_teste

            print(
                f"\nTESTE {indice_teste + 1}: "
                f"{tensao_teste:.2f} V | "
                f"{evento} | "
                f"{duracao_teste:.1f} s"
            )

            indice_teste += 1

        # Reduz tempo do estágio de teste
        tempo_teste -= 0.15


    # =====================================
    # TENSÃO BASE
    # =====================================

    if MODO_SIMULACAO == "teste":

        # Recupera o valor do estágio atual
        indice_atual = max(0, indice_teste - 1)

        tensao_rms = \
            CENARIOS[CENARIO_TESTE][indice_atual][0]

    else:

        tensao_rms = vrms_nominal


    # =====================================
    # INICIALIZA THD
    # =====================================

    thd = 0.0


    # =====================================
    # EVENTOS - MODO NORMAL
    # =====================================

    if MODO_SIMULACAO == "normal":

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

            harm3 = 4 * math.sin(
                2 * math.pi * 5 * t
            )

            harm5 = 2 * math.sin(
                2 * math.pi * 9 * t
            )

            tensao_rms += harm3 + harm5

            # THD simulada
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
    # EVENTOS - MODO TESTE
    # =====================================

    else:

        # HARMÔNICAS
        if evento == "harmonica":

            # THD simulada para o teste controlado
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

    if MODO_SIMULACAO == "normal":

        ruido = random.uniform(-2, 2)
        tensao_rms += ruido

    else:

        # Ruído controlado somente no cenário
        # de filtragem
        if evento == "ruido":

            ruido = random.uniform(-2, 2)
            tensao_rms += ruido

        else:

            ruido = 0


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

    time.sleep(0.15)