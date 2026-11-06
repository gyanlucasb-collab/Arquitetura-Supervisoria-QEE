# Fluxos Node-RED

As duas exportações são completas e derivam do arquivo de fluxo enviado na revisão final. Cada uma contém 61 nós, incluindo a entrada MQTT, extração, filtro, lógica de proteção, temporização, disjuntor virtual, histórico, estatísticas e elementos do dashboard.

- `flows_completo_10_amostras.json`: média móvel com janela de 10 leituras; utilizar nos ensaios gerais.
- `flows_completo_3_amostras_dataset.json`: mesma arquitetura, com janela de 3 leituras; utilizar na validação com o SEED-PQD v1.

**Importante:** importe apenas um dos arquivos por vez para evitar duplicação de abas e elementos do dashboard. No Node-RED, acesse Menu → Importar → selecione o arquivo JSON. Após importar, confira a conexão MQTT. O fluxo requer `node-red-dashboard` 3.6.6 e foi exportado no ambiente Node-RED 4.1.8.

O broker configurado é `broker.hivemq.com`, porta `1883`, tópico `gerador/virtual/tcc`. O nó de entrada MQTT está configurado para QoS 2; contudo, os publicadores usados no projeto enviam com QoS 0.
