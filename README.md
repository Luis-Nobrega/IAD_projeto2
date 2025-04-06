# IAD Projeto 2 - Rastreamento de Movimento

Este repositório contém o código e os recursos necessários para o desenvolvimento de um sistema de rastreamento de movimento que utiliza um Raspberry Pi e um Arduino. O sistema é capaz de detectar objetos em movimento, rastreá-los e, quando comandado, disparar um "míssil" (simulado por um motor servo).

## Estrutura do Repositório

O repositório está organizado em várias pastas, cada uma com um propósito específico. Abaixo está uma descrição de cada subpasta e seus conteúdos:

### 1. `motion_tracking_nova/`
Esta pasta contém a versão mais recente do sistema de rastreamento de movimento. Usa a aborgadem de steps mas tem partes não funcionais. 

- **`run.py`**: Script principal para executar a aplicação.
- **`app/`**: Contém o código principal da aplicação, incluindo a interface gráfica e a lógica de rastreamento.
- **`arduino/`**: Contém o código Arduino necessário para controlar os servos e outros componentes.

### 2. `motion_tracking_old_but_gold/`
Esta pasta contém versões antigas e funcionais do sistema. Nenhum ficheiro tem tudo a funcionar. Alguns têm partes que complementam os outros 

- **`arduino.ino`**: Código Arduino para controle dos servos e disparo do míssil.
- **`G8_Enes_Funcional.py`**: Uma versão funcional do sistema de rastreamento, com lógica de detecção e rastreamento de objetos.

### 3. `Old/`
Esta pasta contém versões experimentais e testes antigos do sistema. Os nomes dos arquivos refletem o estado de desenvolvimento ou humor do autor no momento.

- Exemplos de arquivos:
  - `G8_Enes_VAI_FUNCIONAR_CONFIA.py`
  - `G8_Enes_AGORA_O_BICHO_VAI_PÉGÁ.py`
  - `G8_Enes_Reduzido.py`

> **Nota:** Use esta pasta apenas para referência histórica ou para recuperar ideias de implementações anteriores.

### 4. `Testes_nando/`
Esta pasta contém testes e implementações específicas realizadas por "Nando". É uma área de experimentação e desenvolvimento.

- **`Tracking_funcional_Nando.py`**: Uma versão funcional do sistema com ajustes e melhorias específicas.
- **`arduino_Nando.ino`**: Código Arduino correspondente para os testes realizados nesta pasta.
- **`Nando_teste.py`**: Scripts de teste para funcionalidades específicas.

---

## Objetivo do Projeto

O objetivo principal é criar um sistema de rastreamento de movimento que:
1. Detecte objetos em movimento usando uma câmera conectada ao Raspberry Pi.
2. Rastreie o maior objeto detectado e mova os servos para centralizá-lo.
3. Dispare um "míssil" (servo motor) quando comandado.

---

## Como Usar

### 1. Configuração do Hardware
- Conecte o Raspberry Pi à câmera e ao Arduino.
- No Arduino, conecte os servos aos pinos especificados no código (`servo1`, `servo2`, `servo3`).

### 2. Executar o Sistema
- Navegue até a pasta `motion_tracking_nova/`.
- Execute o script principal:
  ```bash
  python3 run.py