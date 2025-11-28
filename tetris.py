
import random, os, time, copy, ast
import keyboard # pip install keyboard

from threading import Thread

from shapes_dict import shapes
from lines import points_calc
from rotation import orientation_finder


# region -  VARIABLES GLOBALES ------------------------------------------------------------------------------------------------ #

# Constantes
ROWS, COLS = 20, 10                                         # Cantidad de filas y columnas del tablero de juego
KEYS = ['a', 's', 'd', 'q', 'e', 'j', 'k']                  # Teclas a utilizar en el juego
DATABASE = "tetris_scores.txt"                              # Nombre del archivo de base de datos
GOAL = 50                                                   # Cantidad de filas a eliminar

# Variables
gameboard = [[0]*COLS for _ in range(ROWS)]                 # Tablero de juego
active_cells = []                                           # Celdas activas que permiten manipulación del jugador
active_shape, active_orientation = "", ""                   # Forma y orientación de la pieza actual

total_score, total_lines = 0, 0                             # Marcador de puntaje y total de filas eliminadas
scores_table = []                                           # Tabla en memoria de marcadores

playing, win, lose = True, False, False                     # Condición de estado del juego, victoria y derrota

# endregion ------------------------------------------------------------------------------------------------------------------- #

# region - FUNCIONES INICIALES ------------------------------------------------------------------------------------------------ #

def load_database(table) -> list:
    """ Carga la base de datos desde el archivo .txt
    Args:
        table(list): Tabla en memoria de almacenamiento de marcadores
    Returns:
        list: Tabla con los datos cargados desde el archivo .txt
    """

    try:
        file = open(DATABASE, "x")
        file.close()
    except:
        pass

    file = open(DATABASE, "r")
    line = file.readline()

    while line != '':
        saved_score = ast.literal_eval(line) # Carga la línea del .txt como lista
        table.append(saved_score)
        line = file.readline()
    file.close()

    return table


def show_title():
    """ Muestra título inicial del juego
    """
    
    print("Tetris!")
    for s in range(3,0,-1):
        print(f"{s}...")
        time.sleep(1)


def show_score():
    """ Muestra el marcador de puntaje y líneas eliminadas de la partida actual
    """

    global total_score, total_lines

    os.system('cls' if os.name == 'nt' else 'clear') # Limpiar pantalla en Windows o Linux-MacOS
    print(f"\nScore = {total_score}\nTotal lines = {total_lines}\n")


def show_gameboard():
    """ Muestra el estado del tablero de juego
    """
    
    global gameboard

    symbol = " *" # Símbolo a utilizar para representar los bloques de la pieza
    space = "  "  # Símbolo para representar espacios en blanco

    show_score()

    hr_line = '-'*24
    print(f"{hr_line}")
    for line in gameboard:
        print("||", end="")
        for element in line:
            char = symbol if element == 1 else space 
            print(char, end="")
        print("||")
    print(f"{hr_line}\n{hr_line}")


def key_listener(key):
    """ Detecta teclas presionadas
    Args:
        key(str): Tecla detectada
    """
     
    while True:
        keyboard.wait(key)
        key_actions(key)

# Proceso de ejecución para la detección de teclas
threads = [Thread(target=key_listener, kwargs={"key":key}) for key in KEYS]
for thread in threads:
    thread.start()


def save_database():
    """ Guarda la tabla de marcadores en memoria en el archivo .txt
    """

    global scores_table

    file = open(DATABASE, "w")
    
    for line in scores_table:
        file.write(f"{line}\n")
    file.close()


def load_defaults():
    """ Carga los valores por defecto para iniciar nueva partida
    """

    global gameboard, active_shape, active_orientation, active_cells
    global total_lines, total_score, scores_table, win, lose

    gameboard = [[0]*COLS for _ in range(ROWS)]
    active_shape, active_orientation = "", ""
    active_cells = []

    total_lines, total_score = 0, 0
    scores_table = []
    win, lose = False, False

    os.system('cls')


# endregion ------------------------------------------------------------------------------------------------------------------- #

# region - FUNCIONES DE MOVIMIENTO DE LA PIEZA -------------------------------------------------------------------------------- #

def key_actions(key):
    """ Acciones a ejecutar según la tecla detectada
    Args:
        key(str): Tecla detectada
    """

    if playing: # Detección mientras se está en juego
        if key == 'a':
            move_piece(0,-1) # Mover hacia la izquierda
        elif key == 'd':
            move_piece(0,1) # Mover hacia la derecha
        elif key == 's':
            move_piece(1,0) # Mover hacia abajo
        elif key == 'j':
            rotate_piece(0,1) # Rotar CW
        elif key == 'k':
            rotate_piece(1,0) # Rotar CCW
        show_gameboard()


def move_piece(row_offset, col_offset) -> bool:
    """ Verifica el movimiento de la pieza hacia los lados
    Args:
        row_offset(int): Desplazamiento hacia abajo
        col_offset(int): Desplazamiento hacia los lados
    Returns:
        bool: Condición del movimiento de la pieza (movida / no movida)
    """

    global active_cells

    new_piece = copy.deepcopy(active_cells) # Copia profunda de la pieza activa
    next_cells = generate_cells(new_piece, row_offset, col_offset) # Calcula las celdas de la pieza rotada
    
    movement_allowed = check_next_position(active_cells, next_cells) # Verifica si se puede realizar la rotación de la pieza
    if movement_allowed: # Si se puede realizar el movimiento
        modify_cells(0) # Limpia las celdas activas
        active_cells = next_cells
        modify_cells(1) # Rellena las celdas con la pieza desplazada
        return True # Hay movimiento
    return False # Ya no hay movimiento


def find_pivot() -> list:
    """ Encuentra la celda pivote (superior-izquierda) para girar la pieza
    Returns:
        list: Lista de fila y columna de la celda pivote para girar la pieza
    """

    global active_cells

    min_row, min_col = ROWS, COLS # Valores iniciales según filas y columnas del tablero

    for line in active_cells:
        row = line[0]
        min_row = row if row < min_row else min_row # Encuentra la ubicación de la parte superior de la pieza
        for col in line[1]:
            min_col = col if col < min_col else min_col # Encuentra la ubicación de la parte izquierda de la pieza
    return [min_row, min_col]


def rotate_piece(rotation_r, rotation_l):
    """ Gira la pieza en sentido horario o antihorario
    Args:
        rotation_r(int): Rotación 90grd en sentido horario
        rotation_l(int): Rotación 90grd en sentido antihorario
    """

    global active_cells, active_shape, active_orientation

    new_orientation = orientation_finder(active_orientation, rotation_r, rotation_l) # Calcula la nueva orientación de la pieza
    new_piece = copy.deepcopy(shapes[active_shape][new_orientation]) # Copia profunda de la pieza activa
    
    pivot_cell = find_pivot() # Encuentra el punto pivote para el giro
    row_offset, col_offset = pivot_cell[0], pivot_cell[1]
    next_cells = generate_cells(new_piece, row_offset, col_offset) # Calcula las celdas de la pieza rotada
    
    rotation_allowed = check_next_position(active_cells, next_cells) # Verifica si se puede realizar la rotación de la pieza
    if rotation_allowed: # Si se puede realizar la rotación
        modify_cells(0) # Limpia las celdas activas
        active_cells = next_cells
        active_orientation = new_orientation
        modify_cells(1) # Rellena las celdas con la pieza rotada


# endregion ------------------------------------------------------------------------------------------------------------------- #

# region - FUNCIONES DE TRANSFORMACIÓN DEL TABLERO - -------------------------------------------------------------------------- #

def generate_shape() -> bool:
    """ Generar una pieza nueva con forma y orientación aleatoria
    Returns:
        bool: Condición de generación de la pieza (generada / no generada)
    """
    
    global active_cells, active_shape, active_orientation
    
    # Selección aleatoria de pieza y orientación
    active_shape = random.choice(list(shapes.keys()))
    active_orientation = random.choice(list(shapes[active_shape].keys()))
    
    # Copia profunda de pieza desde diccionario de formas
    piece = copy.deepcopy(shapes[active_shape][active_orientation])

    # Posición aleatoria en columnas del tablero
    col_offset = random.randint(0,5)

    # Colocación de celdas de pieza activa en celdas del tablero
    active_cells = generate_cells(piece, 0, col_offset)
    return True


def generate_cells(piece, row_offset, col_offset) -> list:
    """ Genera las posiciones de las celdas de la pieza en el tablero de juego
    Args:
        piece(list): Lista de filas y columnas de la pieza
        row_offset(int): Desplazamiento de posición en las filas
        col_offset(int): Desplazamiento de posición en las columnas
    Returns:
        list: Lista de celdas que conforman la pieza
    """
    
    for line in piece:
        for c in range(len(line[1])):
            line[1][c] += col_offset
        line[0] += row_offset
    return piece


def modify_cells(condition):
    """ Modifica los valores de las celdas del tablero según la condición de las celdas activas
    Args:
        condition(int): Condición de modificación (0, 1)
    """
        
    global gameboard, active_cells

    for line in active_cells:
        row = line[0]
        for col in line[1]:
            gameboard[row][col] = condition # Cambia a '0' o '1' el valor de la celda en el tablero de juego

# endregion ------------------------------------------------------------------------------------------------------------------- #

# region - FUNCIONES DE VERIFICACIÓN ------------------------------------------------------------------------------------------ #

def check_free_cells(col_offset, row_offset) -> bool:
    """ Verifica si las celdas destino en el tablero de juego están libres para el movimiento lineal
    Args:
        row_offset(int): Desplazamiento de posición en las filas
        col_offset(int): Desplazamiento de posición en las columnas
    Returns:
        bool: Condición de las celdas (libres / ocupadas)
    """
    
    global gameboard, active_cells

    for line in active_cells:
        row = line[0]
        for col in line[1]:
            # Si la celda destino tiene un '1' no está libre
            if gameboard[row + row_offset][col + col_offset] == 1:
                return False
    return True


def check_next_position(actual_cells, next_cells) -> bool:
    """ Verifica si las celdas destino en el tablero de juego están libres y en los límites para la rotación
    Args:
        actual_cells(list): Lista de celdas ocupadas actualmente
        next_cells(list): Lista de celdas destino después de la rotación
    Returns:
        bool: Condición de las celdas (libres / ocupadas o fuera de los límites)
    """
    
    global gameboard

    test_board = copy.deepcopy(gameboard) # Copia profunda del tablero de juego para hacer pruebas

    # Deja libres las celdas actuales
    for line in actual_cells:
        row = line[0]
        for col in line[1]:
            test_board[row][col] = 0
    
    # Simula y verifica la ocupación de las celdas destino
    for line in next_cells:
        row = line[0]
        for col in line[1]:
            if col < 0 or col >= 10: # Verifica de límites laterales del tablero
                return False
            elif row >= 20: # Verifica límite inferior del tablero
                return False
            elif test_board[row][col] == 1: # Verifica si las celdas destino están libres
                return False
    return True


def check_full_lines() -> bool:
    """ Verifica si las líneas del tablero están completas para eliminarlas y modificar los marcadores
    Returns:
        bool: Condición de victoria si se alcanzó la cantidad de líneas a eliminar (alcanzada / no alcanzada)
    """
    
    global gameboard, total_score, total_lines, GOAL

    row = len(gameboard) - 1 # Contador de líneas a verificar
    completed_lines = 0 # Contador de líneas completas en esta verificación

    while row > -1:
        full_cells = 0
        for col in gameboard[row]:
            if col == 1:
                full_cells += 1
                if full_cells == COLS: # Si todas las celdas de la columna tienen '1'
                    gameboard.pop(row) # Elimina la línea llena
                    gameboard.insert(0, [0] * COLS) # Agrega una línea vacía en la parte de arriba del tablero
                    completed_lines += 1
                    row += 1
                    total_lines += 1
        row -= 1 # Se devuelve a la línea anterior para no dejarla sin verificar
    
    current_score = points_calc(completed_lines) # Calcula el puntaje según la cantidad de líneas eliminadas
    total_score += current_score
    
    if total_lines >= GOAL: # Verifica la condición de victoria según las líneas a eliminar
        return True
    return False


# endregion ------------------------------------------------------------------------------------------------------------------- #

# region - FUNCIONES DE CÁLCULO DE PUNTAJE ------------------------------------------------------------------------------------ #

def update_scores_table(table, player, score):
    """ Actualiza la tabla de marcadores
    Args:
        table(list): Lista de marcadores
        player(str): Alias del jugador
        score(int): Puntaje obtenido en la partida actual
    """

    table.append([player, score]) # Agrega el marcador a la tabla en memoria
    table = sort_scores(table) # Ordena los marcadores de mayor a menor
    return table


def sort_scores(table):
    """ Ordena en memoria la tabla de marcadores de mayor a menor
    Args:
        table(list): Tabla de marcadores a ordenar
    Returns:
        list: Tabla de marcadores ordenada
    """

    # Algoritmo de ordenamiento Bubble Sort
    scores_qty = len(table)
    if scores_qty > 1:
        for _ in range(scores_qty):
            for s in range(scores_qty-1):
                if table[s][1] < table[s+1][1]:
                    total_score = table.pop(s)
                    table.insert(s+1, total_score)
    return table


def show_top_scores(table, qty):
    """ Muestra la tabla de marcadores más altos
    Args:
        table(list): Tabla de marcadores a mostrar
        qty(int): Cantidad de marcadores a mostrar
    """

    print(f"\nTop {qty} scores:\n\n#  Player  Score")
    try:
        for i in range(qty):
            if table[i][1] > 0:
                print(f" {i+1}   {table[i][0]}     {table[i][1]}")
    except:
        pass


def show_end_message(player, win):
    """ Muestra mensaje de final de partida con alias de jugador y puntaje
    Args:
        player(str): Alias del jugador
        win(bool): Condición de victoria
    """
    
    end_condition = "You win" if win else "You lose"
    
    print(f"\n{end_condition} {player}! Total points: {total_score}")


# endregion ------------------------------------------------------------------------------------------------------------------- #

# region - FUNCIONES MISCELÁNEAS ---------------------------------------------------------------------------------------------- #

def calculate_cycle_wait() -> float:
    """ Calcula el tiempo de espera entre ciclos (velocidad del juego)
    Returns:
        float: Tiempo de espera entre ciclos del juego
    """

    initial_wait, end_wait = 1, 0.2 # Tiempo de espera máximo y mínimo
    wait_factor = (initial_wait - end_wait) / GOAL # Factor de modificación de tiempo de espera
    cycle_wait = initial_wait - (total_lines * wait_factor) # Tiempo de espera según líneas eliminadas

    return cycle_wait


def get_player_alias(long) -> str:
    """ Obtiene el nombre del jugador y lo formatea a 3 caracteres
    Args:
        long(int): Longitud del alias
    Returns:
        str: Alias del jugador
    """

    input("Pressed keys: ") # Muestra la secuencia de teclas presionadas

    player = input("Player? (3 chars): ").upper()

    if len(player) < long:
        player += "*" * (long-len(player)) # Agrega '*' si la longitud es menor
    else:
        player = player[0:long] # Recorta el nombre si la longitud es mayor

    return player


def ask_restart_game():
    """ Solicita verificación para iniciar nueva partida
    """

    restart = input("\nPress 'y' to restart: ").lower()

    if restart == 'y':
        load_defaults()
        play_tetris()


# endregion ------------------------------------------------------------------------------------------------------------------- #

# region - FUNCIÓN PRINCIPAL -------------------------------------------------------------------------------------------------- #

def play_tetris():
    """ Corre el juego
    """

    global playing, scores_table, win, lose

    show_title()
    load_defaults()
    scores_table = load_database(scores_table)

    active_piece = False # Al iniciar no hay un pieza activa

    # Ciclo principal del juego
    while playing:
        if not active_piece: # Porque está iniciando o se depositó la pieza en la pila de bloques
            win = check_full_lines() # Verificar si se consiguió la victoria

            active_piece = generate_shape() # Generar una pieza nueva

            lose = not check_free_cells(0, 0) # Verifica que la pieza tiene espacio libre para colocarla en el tablero
            modify_cells(1) # Modifica las celdas del tablero con las celdas activas
        
        show_gameboard() # Actualiza estado del tablero de juego

        # Tiempo de espera entre ciclos (velocidad del juego)
        wait_time = calculate_cycle_wait() 
        time.sleep(wait_time)

        # Si la pieza se movió en el último ciclo
        in_motion = move_piece(1,0)

        if not in_motion: # Si la pieza no se movió significa que ya no está activa
            active_piece = False
        if win or lose: # Si se consigue la condición de victoria o derrota
            playing = False

    # Datos para marcador final
    player = get_player_alias(3)
    show_end_message(player, win)
    scores_table = update_scores_table(scores_table, player, total_score)
    show_top_scores(scores_table, 3)

    # Guardado de datos y reinicio
    save_database()
    ask_restart_game()

# endregion ------------------------------------------------------------------------------------------------------------------- #


# MAIN ------------------------------------------------------------------------------------------------------------------------ #

play_tetris()