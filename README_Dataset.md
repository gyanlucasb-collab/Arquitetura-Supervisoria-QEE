# SEED-PQD v1 — dados utilizados na validação

Esta pasta contém os quatro arquivos CSV selecionados para a validação complementar da arquitetura: `Pure_Sinusoidal`, `Sag`, `Swell` e `Harmonics`. O conjunto SEED-PQD v1 original disponibiliza 17 classes; somente essas quatro foram incluídas neste repositório porque correspondem aos cenários utilizados no trabalho.

## Fonte e atribuição

**Conjunto de dados:** Khan, Muhammad Umar; Aziz, Sumair; Usman, Adil. *SEED_PQD_v1 (SEED - Power Quality Disturbance Dataset ver1).* Zenodo, versão 1, publicada em 2 maio 2023. Registro: <https://zenodo.org/records/11843312>.

Os autores do conjunto recomendam também citar o artigo associado:

Khan, M. U.; Aziz, S.; Usman, A. XPQRS: Expert power quality recognition system for sensitive load applications. *Measurement*, v. 216, 112889, 2023. DOI: <https://doi.org/10.1016/j.measurement.2023.112889>.

**Licença dos dados:** Creative Commons Attribution 4.0 International (CC BY 4.0). Consulte <https://creativecommons.org/licenses/by/4.0/>. Ao redistribuir os arquivos, mantenha esta atribuição, a referência ao registro original e a indicação de que somente quatro das 17 classes foram selecionadas.

## Características dos sinais

Segundo o registro do conjunto, cada classe contém 1.000 sinais, cada sinal contém 100 amostras, a frequência fundamental é 50 Hz e a taxa de amostragem é 5 kHz (janela de 20 ms). Os CSVs incluídos seguem a organização de 1.000 linhas por 100 colunas.

## Reprodução no projeto

O script `reproduzir_seed_pqd.py` lê os quatro CSVs desta pasta. Ele calcula o RMS de cada linha, estima um indicador de distorção por FFT e converte o valor RMS para uma escala hipotética calibrada pelo RMS médio da classe senoidal pura, correspondente a 127 V. Essa conversão é realizada pelo script; os dados de origem são normalizados e não representam diretamente medições em volts.

Configuração inicial do script: 50 sinais por classe, com 15 sinais normais adicionais após cada classe de distúrbio para permitir a recuperação da janela de média móvel. A validação utiliza o fluxo Node-RED com filtro de 3 amostras.
