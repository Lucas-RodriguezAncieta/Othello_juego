# Othello Juego

## Descripción general

Este proyecto implementa una versión de **Othello/Reversi** en Python con:

- Un **servidor** que mantiene el estado oficial de la partida.
- Un **cliente humano** con interfaz gráfica en `pygame`.
- Una base para un **agente inteligente** que toma decisiones con **poda alfa-beta** y una **función heurística de evaluación**.
- Un entorno adicional orientado a simulación mediante clases de agente/entorno.

El tablero es de `8x8` y utiliza la convención:

- `0`: casilla vacía
- `1`: ficha negra
- `2`: ficha blanca

En la inicialización estándar:

- Negro (`1`) comienza la partida.
- Se colocan las 4 fichas centrales con la configuración clásica de Othello.

## Estructura del proyecto

- [servidor.py](/Users/henryriveramendez/Documents/SistemasInteligentes/Othello_juego/servidor.py): servidor TCP que administra conexiones, turnos, validación de jugadas, volteo de fichas y finalización de partida.
- [cliente_base.py](/Users/henryriveramendez/Documents/SistemasInteligentes/Othello_juego/cliente_base.py): capa base de comunicación por sockets para clientes.
- [cliente_humano.py](/Users/henryriveramendez/Documents/SistemasInteligentes/Othello_juego/cliente_humano.py): cliente jugable con interfaz gráfica.
- [interfaz_grafica.py](/Users/henryriveramendez/Documents/SistemasInteligentes/Othello_juego/interfaz_grafica.py): renderizado del tablero, piezas, movimientos válidos y estado de la partida.
- [TableroOthello.py](/Users/henryriveramendez/Documents/SistemasInteligentes/Othello_juego/TableroOthello.py): entorno de juego orientado a agentes, útil para simulación y toma de decisiones de IA.
- [AgenteIA/Agente.py](/Users/henryriveramendez/Documents/SistemasInteligentes/Othello_juego/AgenteIA/Agente.py): abstracción base de un agente.
- [AgenteIA/Entorno.py](/Users/henryriveramendez/Documents/SistemasInteligentes/Othello_juego/AgenteIA/Entorno.py): abstracción base de un entorno multiagente.
- [AgenteIA/AgenteJugador.py](/Users/henryriveramendez/Documents/SistemasInteligentes/Othello_juego/AgenteIA/AgenteJugador.py): lógica general del agente jugador, búsqueda alfa-beta y función heurística.
- [main.py](/Users/henryriveramendez/Documents/SistemasInteligentes/Othello_juego/main.py): archivo de ejemplo generado por PyCharm; no participa en el juego real.
- `intro.png`, `musica.mp3`: recursos multimedia presentes en el repositorio.

## Dependencias

El código usa principalmente:

- `python 3`
- `numpy`
- `pygame`
- librerías estándar: `socket`, `threading`, `json`, `time`, `traceback`, `collections`

Instalación sugerida:

```bash
pip install numpy pygame
```

## Cómo ejecutar

### 1. Iniciar el servidor

```bash
python servidor.py
```

Parámetros interactivos:

- Host por defecto: `127.0.0.1`
- Puerto por defecto: `5555`

### 2. Iniciar el cliente humano

En otra terminal:

```bash
python cliente_humano.py
```

Luego ingresar:

- servidor: `localhost` o la IP del servidor
- puerto: `5555`

Para jugar una partida completa se necesitan **dos clientes conectados** al servidor.

## Arquitectura general

### 1. Modelo cliente-servidor

El proyecto sigue una arquitectura centralizada:

- El **servidor** conserva el estado verdadero del tablero.
- Cada **cliente** recibe actualizaciones y solicita movimientos.
- El servidor valida si una jugada es legal, actualiza el tablero y difunde el nuevo estado a todos los clientes.

### 2. Flujo de una partida

1. Se inicia `GameServer`.
2. Se conectan dos clientes.
3. El servidor asigna color:
   - cliente 0 -> negro (`1`)
   - cliente 1 -> blanco (`2`)
4. Cuando hay dos clientes activos, el servidor reinicia el juego y envía `game_start`.
5. El jugador en turno envía un mensaje `move`.
6. El servidor valida la jugada con `is_valid_move`.
7. Si es válida, ejecuta `make_move`, voltea fichas y cambia de turno.
8. El servidor envía `game_update`.
9. Si ningún jugador tiene movimientos, la partida termina y se determina el ganador.

## Documentación por módulo

## `servidor.py`

### Clase `GameServer`

Responsabilidad principal: coordinar toda la partida.

#### Atributos relevantes

- `board`: matriz `8x8` con el estado del juego.
- `current_player`: jugador activo (`1` o `2`).
- `clients`: lista de sockets de clientes conectados.
- `client_info`: metadatos de cada cliente.
- `game_over`: indica si la partida terminó.
- `winner`: ganador final (`1`, `2` o `0` para empate).
- `lock`: candado para proteger acceso concurrente a clientes.

#### Métodos principales

- `reset_game()`
  - Reinicia el tablero y el turno.
- `get_valid_moves(player=None)`
  - Recorre el tablero completo y devuelve todas las jugadas legales.
- `is_valid_move(row, col, player)`
  - Verifica si colocar una ficha en una casilla vacía captura al menos una línea rival.
- `make_move(row, col, player)`
  - Aplica una jugada válida, voltea fichas y actualiza el turno.
- `determine_winner()`
  - Cuenta fichas negras y blancas para decidir el resultado final.
- `get_game_state()`
  - Prepara una estructura serializable en JSON para enviar a clientes.
- `send_to_client(...)`
  - Envía mensajes TCP serializados.
- `broadcast_to_all(...)`
  - Difunde mensajes a todos los clientes activos.
- `start_game_if_ready()`
  - Inicia la partida cuando hay exactamente dos jugadores conectados.
- `handle_client(...)`
  - Atiende a cada cliente en un hilo independiente.
- `process_client_message(...)`
  - Procesa mensajes entrantes; actualmente, en especial el tipo `move`.
- `start()`
  - Levanta el socket servidor y acepta nuevas conexiones.
- `stop()`
  - Cierra sockets y detiene el servidor.

### Regla de validación de jugadas

Una jugada es válida si:

- la casilla está vacía, y
- en al menos una de las 8 direcciones existe:
  - una o más fichas rivales consecutivas, seguidas por
  - una ficha propia

Esa es exactamente la lógica de Othello y se implementa en `is_valid_move`.

## `cliente_base.py`

### Clase `ClienteBase`

Encapsula toda la lógica de red del cliente.

#### Responsabilidades

- conectarse al servidor
- recibir mensajes de forma asíncrona
- mantener el último `game_state`
- enviar jugadas
- notificar eventos a una subclase mediante callback

#### Métodos principales

- `connect()`: abre el socket e inicia un hilo receptor.
- `receive_messages()`: recibe mensajes del servidor separados por salto de línea.
- `handle_message(message)`: actualiza el estado local según el tipo de mensaje.
- `send_message(message)`: serializa y envía JSON.
- `send_move(row, col)`: conveniencia para enviar jugadas.
- `disconnect(reason="")`: cierra la conexión.

### Tipos de mensaje manejados

- `welcome`
- `waiting`
- `game_start`
- `game_update`
- `opponent_disconnected`

## `cliente_humano.py`

### Clase `ClienteHumano`

Extiende `ClienteBase` y conecta la red con la interfaz de `pygame`.

#### Responsabilidades

- procesar clics del usuario
- validar si el clic corresponde a un movimiento legal visible
- dibujar la pantalla de espera o el tablero de juego
- gestionar el cierre de la ventana

#### Flujo principal

- `run()` conecta con el servidor.
- En cada iteración:
  - procesa eventos de mouse/ventana
  - dibuja el estado actual
  - limita el refresco a `30 FPS`

## `interfaz_grafica.py`

### Clase `InterfazJuego`

Provee el renderizado visual del juego con `pygame`.

#### Funciones visuales importantes

- `draw_waiting_screen(...)`
  - Muestra un tablero base con una capa oscura y mensajes de espera.
- `draw_game_state(game_state, player_color)`
  - Dibuja el tablero actual, resalta movimientos válidos y muestra información del turno.
- `_draw_grid()`
  - Dibuja la cuadrícula.
- `_draw_pieces(board)`
  - Dibuja fichas negras y blancas.
- `_draw_valid_moves(valid_moves)`
  - Resalta jugadas posibles para el jugador local.
- `_draw_game_info(...)`
  - Muestra marcador y mensaje de turno o resultado.
- `get_clicked_cell(pos)`
  - Convierte una posición del mouse a coordenadas de tablero.

## `AgenteIA/Agente.py`

### Clase `Agente`

Es una clase base abstracta para agentes.

#### Conceptos manejados

- `percepciones`: información recibida desde el entorno
- `acciones`: decisión calculada por el agente
- `habilitado`: bandera para saber si el agente sigue activo

`programa()` se deja abstracto para que las subclases implementen su comportamiento.

## `AgenteIA/Entorno.py`

### Clase `Entorno`

Representa un entorno genérico que contiene agentes y coordina su evolución.

#### Métodos clave

- `insertar(agente)`: agrega un agente.
- `evolucionar()`: entrega percepciones y ejecuta acciones de agentes activos.
- `run()`: itera hasta que el entorno termina.
- `finalizar()`: concluye si al menos un agente fue inhabilitado.

Esta clase sirve como base conceptual para modelar entornos de agentes más allá de la interfaz de red.

## `TableroOthello.py`

### Clase `TableroOthello`

Extiende `Entorno` y representa el juego desde la perspectiva de simulación de agentes.

#### Estado de juego

Usa la tupla nominal `ElEstado` con campos:

- `jugador`: jugador al que le corresponde mover
- `get_utilidad`: valor asociado al estado
- `tablero`: matriz del tablero
- `movidas`: lista de jugadas legales

#### Métodos principales

- `get_percepciones(agente)`
  - Le asigna al agente el estado actual y dispara su decisión.
- `ejecutar(agente)`
  - Aplica la acción elegida por el agente al estado del juego.
- `mostrar_tablero(tablero)`
  - Imprime una versión de texto del tablero en consola.
- `_is_valid_move(...)`
  - Valida jugadas según reglas de Othello.
- `_get_valid_moves(...)`
  - Enumera todas las jugadas legales de un jugador.

### Observación importante

En este archivo aparece una referencia a `HumanoOthello` dentro de `ejecutar()`, pero esa clase no está definida ni importada en el proyecto actual. Eso sugiere que esta parte proviene de una versión anterior o incompleta del entorno de simulación.

## `AgenteIA/AgenteJugador.py`

### `ElEstado`

Se define como:

```python
ElEstado = namedtuple('ElEstado', 'jugador, get_utilidad, tablero, movidas')
```

Es el contenedor inmutable que representa un nodo del árbol de búsqueda.

### Clase `AgenteJugador`

Es la base del jugador inteligente.

#### Atributos relevantes

- `estado`: estado actual percibido.
- `altura`: profundidad máxima de búsqueda.
- `tecnica`: cadena descriptiva; por defecto `"podaalfabeta"`.

#### Métodos principales del estado actual

- `jugadas(estado)`
  - devuelve directamente `estado.movidas`
- `get_utilidad(estado, jugador)`
  - sigue definido como interfaz pendiente
- `getResultado(estado, accion)`
  - aplica una jugada, voltea fichas, cambia el jugador activo y construye el nuevo estado

La clase sigue siendo una base reutilizable, pero ahora ya incorpora parte importante de la lógica del juego:

- enumeración de acciones posibles
- generación de estados sucesores
- evaluación heurística para la poda alfa-beta

### `testTerminal(estado)`

Devuelve `True` cuando `estado.movidas` está vacío.

En esta implementación, la ausencia de movimientos disponibles se usa como criterio terminal.

### `programa()`

Es el punto de entrada de decisión del agente:

- si no hay jugadas disponibles, almacena `None`
- si hay jugadas, ejecuta `podaAlphaBeta_eval`

## Documentación especial: `funcion_evaluacion`

La función `funcion_evaluacion(self, estado)` es la pieza más importante del agente porque estima qué tan favorable es un estado del tablero cuando la búsqueda alfa-beta aún no llegó a un estado terminal.

### Objetivo

Transformar un estado del juego en un **valor numérico heurístico**:

- un valor mayor indica una posición más favorable para el jugador actual del estado
- un valor menor indica una posición más favorable para el rival

### Entrada

Recibe un `estado` con:

- `estado.tablero`: matriz del tablero
- `estado.jugador`: jugador actual
- `estado.movidas`: jugadas válidas del jugador actual

### Variables internas

- `jugador = estado.jugador`
- `rival = 3 - jugador`
- `size = len(tablero)`

Esto permite trabajar de manera simétrica para ambos jugadores.

### Heurísticas que combina

La evaluación actual está formada por cinco componentes:

#### 1. Diferencia de fichas

```python
fichas_jugador = np.sum(tablero == jugador)
fichas_rival = np.sum(tablero == rival)
score_fichas = fichas_jugador - fichas_rival
```

Mide la ventaja material inmediata:

- positivo: el jugador actual tiene más fichas
- negativo: el rival tiene más fichas

Interpretación:

- es útil para medir dominio actual
- pero en Othello no siempre conviene maximizar fichas temprano, así que este término tiene peso bajo

#### 2. Control de esquinas

```python
esquinas = [(0,0), (0,size-1), (size-1,0), (size-1,size-1)]
```

Luego se suma:

- `+1` por cada esquina propia
- `-1` por cada esquina rival

Interpretación:

- las esquinas son extremadamente valiosas porque no pueden ser volteadas
- controlar esquinas suele estabilizar bordes y mejorar la posición a largo plazo

Por eso en la versión actual su peso es extremadamente alto.

#### 3. Casillas peligrosas alrededor de las esquinas

La nueva versión agrega una heurística que antes no estaba documentada:

```python
peligrosas = [
    (0,1),(1,0),(1,1),
    (0,size-2),(1,size-1),(1,size-2),
    (size-2,0),(size-1,1),(size-2,1),
    (size-2,size-1),(size-1,size-2),(size-2,size-2)
]
```

Estas posiciones son estratégicamente delicadas porque suelen facilitar que el rival capture una esquina vacía.

La lógica aplicada es:

- si una casilla peligrosa pertenece al jugador actual, `score_peligro -= 1`
- si pertenece al rival, `score_peligro += 1`

Interpretación:

- ocupar estas casillas suele ser malo si la esquina asociada todavía no está asegurada
- la heurística intenta desalentar ese comportamiento

#### 4. Movilidad

```python
mis_movidas = len(estado.movidas)
mov_rival = len(temp._get_valid_moves(tablero, rival))
score_movilidad = mis_movidas - mov_rival
```

La movilidad mide cuántas opciones legales tiene cada jugador.

Interpretación:

- tener más movimientos implica mayor flexibilidad estratégica
- reducir la movilidad rival puede forzarlo a malas jugadas o incluso a pasar turno

En Othello esta heurística suele ser muy importante en fases medias del juego.

#### 5. Control de bordes sin contar esquinas

La función recorre el contorno del tablero excluyendo las esquinas y suma:

- `+1` por cada borde del jugador
- `-1` por cada borde del rival

Interpretación:

- los bordes suelen ser más seguros que casillas internas
- pueden ayudar a consolidar estructura
- no son tan definitivos como las esquinas, por eso su peso es intermedio

### Fórmula final actual

La puntuación final ahora es:

```python
2 * score_fichas +
100 * score_esquinas +
-30 * score_peligro +
10 * score_movilidad +
5 * score_bordes
```

O expresado matemáticamente:

```text
Evaluación =
2·(ventaja de fichas) +
100·(ventaja en esquinas) +
-30·(score de casillas peligrosas) +
10·(ventaja de movilidad) +
5·(ventaja en bordes)
```

### Interpretación de los pesos

- `2` para fichas:
  - el material importa un poco más que antes
- `100` para esquinas:
  - las esquinas pasan a dominar fuertemente la evaluación
- `-30 * score_peligro`:
  - penaliza con fuerza ocupar casillas cercanas a esquinas vacías
- `10` para movilidad:
  - duplica su importancia respecto a la versión anterior
- `5` para bordes:
  - aumenta el premio por estabilidad en bordes

### Cambios respecto a la versión anterior

- Se agregó una nueva heurística para `casillas peligrosas`.
- Las esquinas pasaron de ser importantes a ser el factor dominante.
- La movilidad ahora pesa más.
- Los bordes también pesan más.
- La diferencia de fichas tiene un peso ligeramente mayor.

### Por qué esta nueva versión puede jugar mejor

La heurística ya no se limita a favorecer esquinas, bordes y movilidad. Ahora además intenta evitar errores típicos de Othello:

- estabilidad posicional
- capacidad de maniobra
- control de zonas seguras
- prevención de jugadas arriesgadas cerca de esquinas

Eso la hace más útil que una utilidad puramente material, especialmente cuando la búsqueda tiene profundidad limitada.

### Limitaciones de la función

Aunque es una buena heurística inicial, tiene varias limitaciones:

- evalúa desde `estado.jugador`, lo que exige coherencia fina en el árbol minimax para no mezclar perspectivas
- crea un `TableroOthello(size)` temporal solo para calcular movilidad del rival, lo cual agrega costo y efectos colaterales de impresión en consola
- no distingue entre fases de apertura, medio juego y final
- sí considera casillas peligrosas cercanas a esquinas, pero con una lista fija y sin evaluar el contexto completo de estabilidad
- no mide fichas estables de manera explícita

### Recomendaciones de mejora

Si se quiere fortalecer la IA, esta función podría ampliarse con:

- pesos dinámicos según la fase de la partida
- refinamiento contextual de las casillas peligrosas según si la esquina correspondiente ya está tomada
- cálculo de estabilidad de fichas
- tablas posicionales predefinidas
- reutilización de una función de movilidad sin instanciar un tablero temporal

## Búsqueda del agente: `podaAlphaBeta_eval`

La IA usa minimax con poda alfa-beta.

### Idea general

- `max_value(...)` intenta maximizar la evaluación.
- `min_value(...)` intenta minimizarla.
- `alpha` representa la mejor cota inferior encontrada para MAX.
- `beta` representa la mejor cota superior encontrada para MIN.
- Si una rama ya no puede mejorar el resultado actual, se poda.

### Condición de corte

La búsqueda se detiene cuando:

- el estado es terminal, o
- se alcanza la profundidad `self.altura`

En ambos casos se usa `funcion_evaluacion`.

### Salida

`podaAlphaBeta_eval` devuelve la mejor acción encontrada para el estado actual.

## Protocolo de mensajes de red

Los mensajes entre cliente y servidor son JSON terminados en salto de línea.

### Mensajes del servidor

- `welcome`
  - informa color asignado y `client_id`
- `waiting`
  - informa que aún falta un oponente
- `game_start`
  - envía el estado inicial
- `game_update`
  - envía el nuevo estado tras una jugada válida
- `move_response`
  - responde si una jugada fue aceptada o rechazada
- `opponent_disconnected`
  - notifica desconexión del rival

### Mensaje del cliente

- `move`
  - incluye `row` y `col`

## Observaciones del análisis del código

Durante la revisión del repositorio se observan varios puntos importantes:

- [main.py](/Users/henryriveramendez/Documents/SistemasInteligentes/Othello_juego/main.py) no forma parte del sistema real; es un archivo de ejemplo.
- La arquitectura de red y la lógica del tablero del servidor están funcionalmente separadas de la arquitectura de agentes.
- `TableroOthello.py` parece pertenecer a una línea de trabajo académica o experimental distinta del cliente-servidor.
- `HumanoOthello` no existe en el proyecto actual.
- `funcion_evaluacion` es la parte estratégica central del agente y está correctamente orientada a heurísticas clásicas de Othello, aunque todavía es mejorable.

## Resumen final

El proyecto combina dos enfoques:

- un juego multijugador cliente-servidor con interfaz gráfica
- una base de inteligencia artificial con búsqueda alfa-beta y evaluación heurística

La lógica del juego está bien separada por responsabilidades:

- servidor: reglas y sincronización
- cliente: interacción y visualización
- agente: razonamiento y evaluación

La función `funcion_evaluacion` del agente jugador usa una heurística ponderada que privilegia:

- esquinas
- movilidad
- bordes
- diferencia de fichas

Esa elección es razonable para Othello porque no solo evalúa cantidad de fichas, sino también calidad posicional y capacidad de maniobra.
