
"""
Reproduz sinais do dataset SEED-PQD no tópico MQTT usado pelo Node-RED.

Arquivos necessários na mesma pasta:
- Pure_Sinusoidal.csv
- Sag.csv
- Swell.csv
- Harmonics.csv

Instalação:
    python -m pip install pandas numpy paho-mqtt

ATENÇÃO:
- Execute este script no lugar do gerador antigo, não junto com ele.
- Os valores em volts usam uma escala hipotética calibrada para que
  o RMS médio da classe Pure_Sinusoidal corresponda a 127 V.
- Cada linha do CSV representa um sinal de 100 amostras.
- O intervalo MQTT é o intervalo de reprodução, não a duração física
  original entre sinais.
"""

from pathlib import Path
import json
import time

import numpy as np
import pandas as pd
import paho.mqtt.client as mqtt


# =====================================
# CONFIGURAÇÃO
# =====================================

BROKER = "broker.hivemq.com"
PORTA = 1883
TOPICO = "gerador/virtual/tcc"

FREQUENCIA_HZ = 50
TAXA_AMOSTRAGEM_HZ = 5000
TENSAO_NOMINAL_V = 127.0
INTERVALO_ENVIO_S = 0.15

# Para testes iniciais, use 20 ou 50 sinais por classe.
# Para todos os sinais, configure como None.
SINAIS_POR_CLASSE = 50

# Quantidade de sinais normais enviados após cada distúrbio.
# A configuração usada na validação com o dataset utiliza 3 amostras.
SINAIS_RECUPERACAO = 15

ARQUIVOS = [
    ("Pure_Sinusoidal.csv", "normal", "Pure_Sinusoidal"),
    ("Sag.csv", "afundamento", "Sag"),
    ("Swell.csv", "sobretensao", "Swell"),
    ("Harmonics.csv", "harmonica", "Harmonics"),
]


# =====================================
# LEITURA DOS SINAIS
# =====================================

def carregar_sinais(caminho: Path) -> np.ndarray:
    """Lê CSV sem cabeçalho; cada linha deve conter 100 amostras."""

    dados = pd.read_csv(caminho, header=None).to_numpy(dtype=float)

    if dados.ndim != 2 or dados.shape[1] != 100:
        raise ValueError(
            f"{caminho.name}: esperado CSV com 100 colunas por sinal; "
            f"formato encontrado: {dados.shape}"
        )

    if not np.isfinite(dados).all():
        raise ValueError(
            f"{caminho.name}: foram encontrados valores inválidos."
        )

    return dados


# =====================================
# CÁLCULO DO RMS
# =====================================

def calcular_rms(sinal: np.ndarray) -> float:
    """Calcula o valor eficaz do sinal."""

    return float(np.sqrt(np.mean(np.square(sinal))))


# =====================================
# ESTIMATIVA DE THD
# =====================================

def calcular_thd_percentual(sinal: np.ndarray) -> float:
    """
    Estima a distorção harmônica total por FFT para uma janela
    de 20 ms a 5 kHz, considerando uma fundamental de 50 Hz.

    É uma estimativa para análise exploratória, não uma medição
    certificada de qualidade de energia.
    """

    sinal = np.asarray(sinal, dtype=float)
    sinal = sinal - np.mean(sinal)

    espectro = np.abs(np.fft.rfft(sinal))

    if len(espectro) < 3 or espectro[1] <= 1e-12:
        return 0.0

    # Bin 1 corresponde a 50 Hz em uma janela de 20 ms.
    fundamental = espectro[1]

    harmonicos = []
    max_ordem = min(49, len(espectro) - 1)

    for ordem in range(2, max_ordem + 1):
        harmonicos.append(espectro[ordem] / fundamental)

    return float(
        100.0 * np.sqrt(np.sum(np.square(harmonicos)))
    )


# =====================================
# PUBLICAÇÃO MQTT
# =====================================

def publicar_sinal(
    client,
    sinal,
    fator_escala,
    evento,
    classe,
    indice
):
    """Calcula RMS e THD e publica um sinal no MQTT."""

    tensao_rms = calcular_rms(sinal) * fator_escala
    thd = calcular_thd_percentual(sinal)

    payload = {
        "tensao": round(tensao_rms, 2),
        "evento": evento,
        "thd": round(thd, 2),
        "classe_dataset": classe,
        "indice_sinal": indice,
    }

    info = client.publish(
        TOPICO,
        json.dumps(payload),
        qos=0
    )

    if info.rc != mqtt.MQTT_ERR_SUCCESS:
        print(
            f"Aviso: falha ao enfileirar publicação: "
            f"{classe}, sinal {indice}."
        )

    return payload


# =====================================
# RECUPERAÇÃO COM SINAIS NORMAIS
# =====================================

def enviar_recuperacao_normal(
    client,
    dataset,
    fator_escala
):
    """
    Após um distúrbio, envia sinais da classe senoidal pura.

    Isso permite que a média móvel receba novas amostras normais.
    A recuperação da classificação depende dos valores RMS enviados
    e da lógica de histerese implementada no Node-RED.
    """

    sinais_normais = dataset["Pure_Sinusoidal"]["sinais"]

    quantidade = min(
        SINAIS_RECUPERACAO,
        len(sinais_normais)
    )

    print(
        f"\nEnviando {quantidade} sinais normais "
        f"para recuperação..."
    )

    for indice in range(quantidade):
        sinal = sinais_normais[indice]

        payload = publicar_sinal(
            client=client,
            sinal=sinal,
            fator_escala=fator_escala,
            evento="normal",
            classe="Pure_Sinusoidal",
            indice=indice + 1
        )

        print(
            f"Recuperação {indice + 1}/{quantidade} | "
            f"RMS={payload['tensao']:.2f} V | "
            f"THD~={payload['thd']:.2f}% | "
            f"evento=normal"
        )

        time.sleep(INTERVALO_ENVIO_S)

    # Pequena espera para o processamento das mensagens.
    time.sleep(0.5)


# =====================================
# EXECUÇÃO PRINCIPAL
# =====================================

def main():

    pasta = Path(__file__).resolve().parent

    # ---------------------------------
    # Carrega os quatro arquivos selecionados
    # ---------------------------------

    dataset = {}

    for nome_arquivo, evento, classe in ARQUIVOS:

        caminho = pasta / nome_arquivo

        if not caminho.exists():
            raise FileNotFoundError(
                f"Não encontrei {nome_arquivo}. "
                f"Coloque-o na mesma pasta que "
                f"{Path(__file__).name}."
            )

        dataset[classe] = {
            "sinais": carregar_sinais(caminho),
            "evento": evento,
        }

    # ---------------------------------
    # Calibração hipotética para 127 V
    # ---------------------------------

    sinais_normais = dataset["Pure_Sinusoidal"]["sinais"]

    rms_referencia = float(
        np.mean([
            calcular_rms(sinal)
            for sinal in sinais_normais
        ])
    )

    if rms_referencia <= 1e-12:
        raise ValueError(
            "Não foi possível calcular a referência senoidal."
        )

    fator_escala = TENSAO_NOMINAL_V / rms_referencia

    print("========================================")
    print("REPRODUÇÃO DO DATASET SEED-PQD")
    print(f"Broker MQTT: {BROKER}:{PORTA}")
    print(f"Tópico: {TOPICO}")
    print(f"Frequência considerada: {FREQUENCIA_HZ} Hz")
    print(f"Amostragem considerada: {TAXA_AMOSTRAGEM_HZ} Hz")
    print(
        f"RMS médio da referência: "
        f"{rms_referencia:.6f}"
    )
    print(
        f"Fator de escala hipotético: "
        f"{fator_escala:.3f} V/unidade"
    )
    print(
        f"Sinais por classe: "
        f"{'todos' if SINAIS_POR_CLASSE is None else SINAIS_POR_CLASSE}"
    )
    print(f"Sinais de recuperação: {SINAIS_RECUPERACAO}")
    print("========================================")

    # ---------------------------------
    # Conexão MQTT
    # ---------------------------------

    client = mqtt.Client()

    try:
        client.connect(BROKER, PORTA, 60)
        client.loop_start()

        # Aguarda a conexão iniciar.
        time.sleep(1.0)

        total_sinais_classes = 0
        total_recuperacao = 0

        # ---------------------------------
        # Reproduz cada classe
        # ---------------------------------

        for nome_arquivo, evento, classe in ARQUIVOS:

            sinais = dataset[classe]["sinais"]

            limite = (
                len(sinais)
                if SINAIS_POR_CLASSE is None
                else min(SINAIS_POR_CLASSE, len(sinais))
            )

            print(
                f"\nClasse {classe}: "
                f"enviando {limite} sinais..."
            )

            for indice in range(limite):

                sinal = sinais[indice]

                payload = publicar_sinal(
                    client=client,
                    sinal=sinal,
                    fator_escala=fator_escala,
                    evento=evento,
                    classe=classe,
                    indice=indice + 1
                )

                print(
                    f"{classe} | "
                    f"sinal {indice + 1}/{limite} | "
                    f"RMS={payload['tensao']:.2f} V | "
                    f"THD~={payload['thd']:.2f}% | "
                    f"evento={evento}"
                )

                total_sinais_classes += 1
                time.sleep(INTERVALO_ENVIO_S)

            # ---------------------------------
            # Recuperação após cada distúrbio
            # ---------------------------------

            if classe != "Pure_Sinusoidal":

                enviar_recuperacao_normal(
                    client,
                    dataset,
                    fator_escala
                )

                total_recuperacao += min(
                    SINAIS_RECUPERACAO,
                    len(sinais_normais)
                )

        # Aguarda o envio das últimas mensagens.
        time.sleep(1.0)

        print("\n========================================")
        print("REPRODUÇÃO CONCLUÍDA")
        print(f"Sinais reproduzidos das classes: {total_sinais_classes}")
        print(f"Sinais de recuperação: {total_recuperacao}")
        print(
            f"Total de mensagens de dados: "
            f"{total_sinais_classes + total_recuperacao}"
        )
        print("Confira os indicadores e o histórico no Node-RED.")
        print("========================================")

    except KeyboardInterrupt:
        print("\nReprodução interrompida pelo usuário.")

    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
