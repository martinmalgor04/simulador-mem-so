"""
Simulador de Asignación de Memoria y Planificación de Procesos
============================================================
Este programa simula un Sistema Operativo básico con las siguientes características:
- Gestión de Memoria: Particiones fijas con algoritmo Best-Fit.
- Planificación de CPU: Algoritmo SRTF (Shortest Remaining Time First).
- Multiprogramación: Grado máximo de 5 procesos (3 en RAM + 2 suspendidos).

Autor: Sistema de Simulación de SO
"""

import heapq
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
import os
import sys
import subprocess

# Intentar importar tabulate, instalar si no existe
try:
    from tabulate import tabulate
except ImportError:
    print("Advertencia: tabulate no está instalado. Instalando...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tabulate"])
    from tabulate import tabulate

# --- GESTIÓN DE COLORES PARA LA TERMINAL ---
class Colores:
    """Códigos de escape ANSI para colorear la salida en terminal"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    ROJO = "\033[91m"
    VERDE = "\033[92m"
    AMARILLO = "\033[93m"
    AZUL = "\033[94m"
    MAGENTA = "\033[95m"
    CIAN = "\033[96m"
    BLANCO = "\033[97m"

    # Fondos
    BG_ROJO = "\033[41m"
    BG_VERDE = "\033[42m"
    BG_AZUL = "\033[44m"

    # Estilos extra
    ITALIC = "\033[3m"

class EstadoProceso(Enum):
    """Enumeración de los posibles estados de un proceso"""
    NUEVO = "Nuevo"
    LISTO = "Listo"
    LISTO_SUSPENDIDO = "Listo/Suspendido"
    EJECUCION = "Ejecución"
    TERMINADO = "Terminado"

    def __str__(self):
        return self.value

@dataclass
class Proceso:
    """
    Representa un proceso (PCB - Process Control Block simplificado).
    Contiene toda la información necesaria para gestionar el ciclo de vida del proceso.
    """
    id: str                     # Identificador del proceso (String para permitir A1, P1, etc.)
    tamaño: int                 # Tamaño en KB requerido en memoria
    tiempo_arribo: int          # Momento en que el proceso llega al sistema
    tiempo_irrupcion: int       # Tiempo total de CPU necesario (Burst Time)
    titulo: str = ""            # Nombre descriptivo del proceso

    # Atributos de gestión (se inicializan o calculan durante la ejecución)
    tiempo_restante: int = None      # Tiempo de CPU que le falta para terminar
    tiempo_inicio: int = None        # Momento en que entra a ejecución por primera vez
    tiempo_finalizacion: int = None  # Momento en que termina su ejecución
    tiempo_arribo_listos: int = None # Momento en que entra a la cola de listos (RAM o Suspendido)
    estado: EstadoProceso = EstadoProceso.NUEVO
    particion_asignada: int = None   # ID de la partición de memoria asignada

    def __post_init__(self):
        """Inicializa el tiempo restante igual a la irrupción al crear el objeto"""
        if self.tiempo_restante is None:
            self.tiempo_restante = self.tiempo_irrupcion

    def __lt__(self, other):
        """
        Sobrecarga del operador 'menor que' (<).
        Crucial para el algoritmo SRTF: permite que el heap ordene automáticamente
        los procesos por 'tiempo_restante' ascendente (Min-Heap).
        """
        if self.tiempo_restante == other.tiempo_restante:
            # Desempate por orden de llegada (FIFO) si tienen mismo tiempo restante
            return self.tiempo_arribo < other.tiempo_arribo
        return self.tiempo_restante < other.tiempo_restante

@dataclass
class Particion:
    """Representa una partición fija de memoria"""
    id: int
    direccion_inicio: int           # Dirección base en KB
    tamaño: int                     # Tamaño total de la partición en KB
    proceso_asignado: Optional[str] = None # ID del proceso asignado (None si está libre)

    @property
    def libre(self) -> bool:
        return self.proceso_asignado is None

    @property
    def fragmentacion_interna(self) -> int:
        """La fragmentación se calcula dinámicamente según el proceso asignado"""
        return 0 # El cálculo real se hace en el GestorMemoria

class GestorMemoria:
    """
    Simula la unidad de gestión de memoria (MMU simplificada).
    Utiliza Particiones Fijas y algoritmo de asignación Best-Fit.
    """

    def __init__(self):
        # Configuración de particiones fijas según especificación del TP
        self.particiones = [
            Particion(0, 0, 100),    # Partición 0: Reservada para SO
            Particion(1, 100, 250),  # Partición 1: Trabajos grandes
            Particion(2, 350, 150),  # Partición 2: Trabajos medianos
            Particion(3, 500, 50),   # Partición 3: Trabajos pequeños
        ]
        # Mapa para búsqueda rápida de procesos en memoria: {id_proceso: ObjetoProceso}
        self.procesos_en_memoria: Dict[str, Proceso] = {}

        # Cargar el Sistema Operativo en memoria (Partición 0)
        self._cargar_so()

    def _cargar_so(self):
        """Inicializa el proceso del SO en la partición reservada"""
        # ID del SO es "1" (como string)
        proceso_so = Proceso(id="1", tamaño=100, tiempo_arribo=0, tiempo_irrupcion=0, titulo="Sistema Operativo")
        proceso_so.estado = EstadoProceso.EJECUCION
        proceso_so.particion_asignada = 0
        self.particiones[0].proceso_asignado = "1"
        self.procesos_en_memoria["1"] = proceso_so

    def algoritmo_bestfit(self, proceso: Proceso) -> bool:
        """
        Intenta asignar memoria a un proceso usando el algoritmo **Best-Fit**.

        Best-Fit: Busca la partición libre más pequeña donde quepa el proceso.
        Esto minimiza la fragmentación interna, aunque puede dejar huecos muy pequeños ("astillas").

        Retorna: True si se asignó, False si no hay partición adecuada disponible.
        """
        # Seguridad: No reasignar SO
        if proceso.id == "1":
            return False

        # 1. Filtrar particiones candidatas (Libres, tamaño suficiente, no es la del SO)
        particiones_candidatas = [
            p for p in self.particiones[1:]
            if p.libre and p.tamaño >= proceso.tamaño
        ]

        if not particiones_candidatas:
            return False

        # 2. Aplicar Best-Fit: Elegir la candidata con menor tamaño
        mejor_particion = min(particiones_candidatas, key=lambda p: p.tamaño)

        # 3. Asignar
        mejor_particion.proceso_asignado = proceso.id
        proceso.particion_asignada = mejor_particion.id
        self.procesos_en_memoria[proceso.id] = proceso

        return True

    def liberar_memoria(self, proceso_id: str) -> bool:
        """Libera la partición ocupada por un proceso."""
        if proceso_id not in self.procesos_en_memoria or proceso_id == "1":
            return False

        proceso = self.procesos_en_memoria[proceso_id]
        particion = self.particiones[proceso.particion_asignada]
        particion.proceso_asignado = None # Marcar partición como libre

        del self.procesos_en_memoria[proceso_id]
        return True

    def obtener_fragmentacion_interna(self, particion_id: int) -> int:
        """Calcula desperdicio de memoria: Tamaño Partición - Tamaño Proceso"""
        particion = self.particiones[particion_id]
        if particion.libre or particion.proceso_asignado == "1": # SO no tiene fragmentación visible
            return 0

        proceso = self.procesos_en_memoria.get(particion.proceso_asignado)
        if not proceso:
            return 0

        return particion.tamaño - proceso.tamaño

    def obtener_tabla_particiones(self) -> List[List]:
        """Genera los datos para la tabla visual de particiones"""
        datos_tabla = []
        for p in self.particiones:
            # Datos por defecto (Partición Libre)
            estado_str = f"{Colores.VERDE}Libre{Colores.RESET}"
            proceso_info = "-"
            frag_str = "-"
            tiempo_restante_str = "-"
            tam_proceso_str = "-"

            # Datos si está ocupada
            if not p.libre:
                pid = p.proceso_asignado
                if pid == "1":
                    estado_str = f"{Colores.AZUL}SO{Colores.RESET}"
                    proceso_info = "Sistema Operativo"
                    frag_str = "0 KB"
                    tiempo_restante_str = "∞"
                    tam_proceso_str = "100 KB"
                else:
                    proc = self.procesos_en_memoria.get(pid)
                    if proc:
                        estado_str = f"{Colores.ROJO}Ocupada{Colores.RESET}"
                        proceso_info = f"ID: {pid} ({proc.titulo})"
                        frag = self.obtener_fragmentacion_interna(p.id)
                        frag_str = f"{frag} KB"
                        tiempo_restante_str = f"{proc.tiempo_restante}"
                        tam_proceso_str = f"{proc.tamaño} KB"

            datos_tabla.append([
                f"#{p.id}",
                f"{p.tamaño} KB",
                tam_proceso_str,
                estado_str,
                proceso_info,
                frag_str,
                tiempo_restante_str
            ])
        return datos_tabla

class PlanificadorSRTF:
    """
    Planificador de CPU con algoritmo SRTF (Shortest Remaining Time First).
    Es la versión apropiativa (preemptive) de SJF.
    """

    def __init__(self):
        # Min-Heap para mantener procesos ordenados por tiempo restante eficientemente
        self.cola_listos = []
        self.proceso_actual: Optional[Proceso] = None

    def agregar_proceso_listo(self, proceso: Proceso):
        """Ingresa un proceso a la cola de listos."""
        if proceso.id == "1": return # Ignorar SO

        proceso.estado = EstadoProceso.LISTO
        heapq.heappush(self.cola_listos, proceso)

    def obtener_siguiente_proceso(self) -> Optional[Proceso]:
        """Extrae el proceso con menor tiempo restante del heap."""
        if not self.cola_listos:
            return None
        return heapq.heappop(self.cola_listos)

    def ejecutar_proceso(self, proceso: Proceso, tiempo_actual: int):
        """Simula la ejecución de un ciclo de CPU para el proceso."""
        if proceso.tiempo_inicio is None:
            proceso.tiempo_inicio = tiempo_actual

        proceso.estado = EstadoProceso.EJECUCION

        if proceso.tiempo_restante > 0:
            proceso.tiempo_restante -= 1

        if proceso.tiempo_restante == 0:
            proceso.estado = EstadoProceso.TERMINADO
            proceso.tiempo_finalizacion = tiempo_actual + 1

    def verificar_apropiacion(self, nuevo_proceso: Proceso) -> bool:
        """
        Regla de oro de SRTF: Si llega un proceso con menor tiempo restante
        que el que se está ejecutando, se produce una apropiación (context switch).
        """
        if self.proceso_actual is None:
            return True
        return nuevo_proceso.tiempo_restante < self.proceso_actual.tiempo_restante

class SimuladorSO:
    """
    Clase principal que orquesta la Memoria, el Planificador y los Eventos.
    """

    MAX_MULTIPROGRAMACION = 5 # Límite estricto del TP: 3 en RAM + 2 Suspendidos

    def __init__(self):
        self.gestor_memoria = GestorMemoria()
        self.planificador = PlanificadorSRTF()

        # Colas de procesos
        self.procesos_nuevos = []      # Aún no arriban o esperando cupo
        self.procesos_suspendidos = [] # En disco (Listo/Suspendido)
        self.procesos_terminados = []  # Finalizados

        self.tiempo_actual = 0

        # Control de cambios para la interfaz gráfica
        self.estado_previo = {}

    def calcular_grado_multiprogramacion(self) -> int:
        """
        Grado actual = Procesos en RAM (excluyendo SO) + Procesos Suspendidos.
        """
        en_ram = len([p for p in self.gestor_memoria.procesos_en_memoria.values() if p.id != "1"])
        return en_ram + len(self.procesos_suspendidos)

    # --- LÓGICA DE TRANSICIÓN DE ESTADOS ---

    def admitir_proceso_a_ram(self, proceso: Proceso, verificar_apropiacion: bool = True) -> bool:
        """Intenta pasar un proceso a estado LISTO (asignándole RAM)."""
        if proceso.id == "1": return False

        if not self.gestor_memoria.algoritmo_bestfit(proceso):
            return False

        # Verificar si este proceso debe expropiar al actual (SRTF)
        if verificar_apropiacion and self.planificador.proceso_actual:
            if self.planificador.verificar_apropiacion(proceso):
                # Desalojar proceso actual
                proc_saliente = self.planificador.proceso_actual
                proc_saliente.estado = EstadoProceso.LISTO
                self.planificador.agregar_proceso_listo(proc_saliente)
                self.planificador.proceso_actual = None

        self.planificador.agregar_proceso_listo(proceso)
        return True

    def intentar_admitir_proceso(self, proceso: Proceso) -> Tuple[bool, Optional[str]]:
        """
        Gestiona la admisión de un proceso nuevo al sistema.
        Decide si va a RAM (Listo) o a Disco (Suspendido) según disponibilidad.
        
        Retorna: (éxito, mensaje_opcional) donde mensaje es un evento a mostrar al usuario.
        """
        # Limpieza previa
        if proceso in self.procesos_nuevos: self.procesos_nuevos.remove(proceso)
        if proceso in self.procesos_suspendidos: self.procesos_suspendidos.remove(proceso)

        # 0. Validar tamaño máximo de partición (250KB) - RECHAZAR SI ES MUY GRANDE
        max_particion = 250
        if proceso.tamaño > max_particion:
            msg = f"{Colores.ROJO}⛔ RECHAZADO{Colores.RESET} Proceso {proceso.id}: Tamaño {proceso.tamaño}KB excede partición máxima ({max_particion}KB)"
            # No se agrega a ninguna cola, efectivamente descartado del sistema
            return (False, msg)

        # Verificar límite global de multiprogramación
        if self.calcular_grado_multiprogramacion() >= self.MAX_MULTIPROGRAMACION:
            self.agregar_a_cola_nuevos(proceso)
            return (False, None)

        # Intento 1: Asignar directamente a RAM
        if self.admitir_proceso_a_ram(proceso):
            if proceso.tiempo_arribo_listos is None:
                proceso.tiempo_arribo_listos = self.tiempo_actual
            return (True, None)

        # Intento 2: Si no hay RAM pero hay cupo de multiprogramación -> Suspendido
        proceso.estado = EstadoProceso.LISTO_SUSPENDIDO
        if proceso.tiempo_arribo_listos is None:
            proceso.tiempo_arribo_listos = self.tiempo_actual
            
        if proceso not in self.procesos_suspendidos:
            self.procesos_suspendidos.append(proceso)
        return (False, None)

    def intentar_swap_srtf(self) -> bool:
        """
        Implementa una optimización agresiva de SRTF:
        Si un proceso en SUSPENDIDO tiene menor tiempo restante que el que se está
        EJECUTANDO en RAM, vale la pena hacer un SWAP (Intercambio).
        Ahora siempre se intenta hacer swap si hay un candidato más corto, incluso
        si se supera temporalmente el grado de multiprogramación máximo.
        """
        if not self.planificador.proceso_actual: return False

        # Buscar el mejor candidato en suspendidos (el más corto)
        candidato = self.buscar_proceso_suspendido_mas_corto(self.planificador.proceso_actual)
        if not candidato: return False

        # Realizar SWAP - siempre se hace si hay un candidato más corto
        proc_saliente = self.planificador.proceso_actual

        # 1. Sacar de RAM al actual
        self.gestor_memoria.liberar_memoria(proc_saliente.id)
        proc_saliente.estado = EstadoProceso.LISTO_SUSPENDIDO
        self.procesos_suspendidos.append(proc_saliente)

        # 2. Meter a RAM al candidato (Best-Fit encontrará hueco ahora)
        if self.gestor_memoria.algoritmo_bestfit(candidato):
            self.procesos_suspendidos.remove(candidato)
            candidato.estado = EstadoProceso.EJECUCION
            if candidato.tiempo_inicio is None:
                candidato.tiempo_inicio = self.tiempo_actual
            self.planificador.proceso_actual = candidato
            return True
        else:
            # Rollback si falla la asignación (muy raro si acabamos de liberar)
            self.procesos_suspendidos.remove(proc_saliente)
            self.gestor_memoria.algoritmo_bestfit(proc_saliente)
            self.planificador.proceso_actual = proc_saliente
            proc_saliente.estado = EstadoProceso.EJECUCION
            return False

    # --- MÉTODOS AUXILIARES ---
    def agregar_a_cola_nuevos(self, proceso: Proceso):
        proceso.estado = EstadoProceso.NUEVO
        if proceso not in self.procesos_nuevos:
            self.procesos_nuevos.append(proceso)
        self.procesos_nuevos.sort(key=lambda p: p.tiempo_arribo)

    def buscar_proceso_suspendido_mas_corto(self, proceso_actual: Optional[Proceso]) -> Optional[Proceso]:
        if not self.procesos_suspendidos: return None
        mejor_suspendido = min(self.procesos_suspendidos, key=lambda p: p.tiempo_restante)

        if proceso_actual and mejor_suspendido.tiempo_restante < proceso_actual.tiempo_restante:
            return mejor_suspendido
        return None # No vale la pena hacer swap

    def procesar_arribos(self) -> List[str]:
        """Verifica procesos que llegan en t = tiempo_actual.
        Retorna: Lista de mensajes de eventos (rechazos, arribos, etc.)
        """
        mensajes = []
        for p in self.procesos_nuevos[:]:
            if p.tiempo_arribo <= self.tiempo_actual:
                self.procesos_nuevos.remove(p)
                exito, msg = self.intentar_admitir_proceso(p)
                if msg:
                    mensajes.append(msg)
        return mensajes

    def intentar_admitir_suspendidos(self) -> List[Proceso]:
        """Intenta mover procesos de Suspendido -> Listo cuando se libera RAM"""
        admitidos = []
        # Ordenar por SRTF para dar prioridad al más corto
        candidatos = sorted(self.procesos_suspendidos, key=lambda p: p.tiempo_restante)

        for p in candidatos:
            if self.calcular_grado_multiprogramacion() >= self.MAX_MULTIPROGRAMACION: break

            # Intentar mover a RAM
            if self.admitir_proceso_a_ram(p):
                admitidos.append(p)
                self.procesos_suspendidos.remove(p)
        return admitidos

    def intentar_admitir_procesos_nuevos(self) -> List[Proceso]:
        """Intenta mover procesos de Nuevo -> Listo/Suspendido si hay cupo"""
        admitidos = []
        esperando = [p for p in self.procesos_nuevos if p.tiempo_arribo <= self.tiempo_actual]

        while esperando and self.calcular_grado_multiprogramacion() < self.MAX_MULTIPROGRAMACION:
            # Elegir el más corto de los que esperan (SRTF desde el inicio)
            mejor = min(esperando, key=lambda p: p.tiempo_irrupcion)
            exito, msg = self.intentar_admitir_proceso(mejor)
            if exito:
                admitidos.append(mejor)
                # Las listas se actualizan dentro de intentar_admitir_proceso
                esperando.remove(mejor)
            else:
                break
        return admitidos

    # --- MOTOR DE SIMULACIÓN ---

    def ejecutar_ciclo(self) -> Dict:
        """
        Avanza un 'tick' lógico del reloj y gestiona todos los eventos.
        Retorna un resumen de lo ocurrido para mostrarlo al usuario.
        """
        cambios = {'hay_cambios': False, 'eventos': []}

        # 0. Procesar nuevos arribos (Llegada de procesos) - PRIMERO para que entren en consideración
        mensajes_arribo = self.procesar_arribos()
        if mensajes_arribo:
            cambios['hay_cambios'] = True
            cambios['eventos'].extend(mensajes_arribo)

        # 1. Verificar si el proceso en ejecución terminó
        proc_actual = self.planificador.proceso_actual
        if proc_actual and proc_actual.id != "1" and proc_actual.tiempo_restante <= 0:
            proc_actual.estado = EstadoProceso.TERMINADO
            if proc_actual.tiempo_finalizacion is None:
                proc_actual.tiempo_finalizacion = self.tiempo_actual
            self.procesos_terminados.append(proc_actual)
            self.gestor_memoria.liberar_memoria(proc_actual.id)
            self.planificador.proceso_actual = None

            cambios['hay_cambios'] = True
            cambios['eventos'].append(f"Proceso {proc_actual.id} finalizó su ejecución.")

            # Al liberar RAM, intentamos traer procesos de afuera
            self.intentar_admitir_suspendidos()
            self.intentar_admitir_procesos_nuevos()

        # 2. Verificar Swap SRTF (Optimización agresiva - siempre intenta)
        if self.intentar_swap_srtf():
            cambios['hay_cambios'] = True
            cambios['eventos'].append("Swap SRTF: Proceso suspendido desplazó al actual.")



        # 4. Planificación de CPU (Seleccionar siguiente)
        # Si hubo desalojo o terminó el actual, buscar el siguiente
        if self.planificador.proceso_actual:
            # Verificar si en la cola de listos hay alguien mejor (Apropiación)
            if self.planificador.cola_listos:
                mejor_listo = self.planificador.cola_listos[0] # Mirar tope del heap
                if mejor_listo.tiempo_restante < self.planificador.proceso_actual.tiempo_restante:
                    # Cambio de Contexto
                    saliente = self.planificador.proceso_actual
                    saliente.estado = EstadoProceso.LISTO
                    self.planificador.agregar_proceso_listo(saliente)

                    entrante = heapq.heappop(self.planificador.cola_listos)
                    entrante.estado = EstadoProceso.EJECUCION
                    if entrante.tiempo_inicio is None: entrante.tiempo_inicio = self.tiempo_actual
                    self.planificador.proceso_actual = entrante

                    cambios['hay_cambios'] = True
                    cambios['eventos'].append(f"Apropiación SRTF: Proceso {entrante.id} desplazó a {saliente.id}")

        # Si CPU libre, tomar el siguiente
        if not self.planificador.proceso_actual or self.planificador.proceso_actual.id == "1":
            siguiente = self.planificador.obtener_siguiente_proceso()
            if siguiente:
                siguiente.estado = EstadoProceso.EJECUCION
                if siguiente.tiempo_inicio is None:
                    siguiente.tiempo_inicio = self.tiempo_actual
                self.planificador.proceso_actual = siguiente
                cambios['hay_cambios'] = True
                
                # Chequea por un swap inmediato si un proceso suspendido es mejor
                if self.intentar_swap_srtf():
                    cambios['hay_cambios'] = True
                    cambios['eventos'].append("Swap SRTF inmediato: Proceso suspendido desplazó al nuevo actual.")

        # Verificar si hubo cambios globales relevantes
        grado_actual = self.calcular_grado_multiprogramacion()
        if grado_actual != self.estado_previo.get('grado', -1):
            cambios['hay_cambios'] = True

        return cambios

    def calcular_tiempo_proximo_evento(self) -> int:
        """Calcula saltos de tiempo para no simular tick a tick si no pasa nada"""
        tiempos = []

        # Próximo arribo
        if self.procesos_nuevos:
            tiempos.append(min(p.tiempo_arribo for p in self.procesos_nuevos))

        # Fin del proceso actual
        proc = self.planificador.proceso_actual
        if proc and proc.id != "1" and proc.estado == EstadoProceso.EJECUCION:
            tiempos.append(self.tiempo_actual + proc.tiempo_restante)

        futuros = [t for t in tiempos if t > self.tiempo_actual]
        if not futuros:
            # Si hay actividad, avanzar 1 al menos
            if proc or self.planificador.cola_listos or self.procesos_suspendidos:
                return self.tiempo_actual + 1
            return self.tiempo_actual

        return min(futuros)

    # --- VISUALIZACIÓN Y REPORTES ---

    def mostrar_estado_sistema(self, info_cambios: Dict):
        """Imprime el dashboard principal del simulador con colores"""
        os.system('cls' if os.name == 'nt' else 'clear')

        print(f"\n{Colores.BOLD}{Colores.BG_AZUL} SIMULADOR DE SO - TIEMPO: {self.tiempo_actual} {Colores.RESET}")

        # 1. Tabla de Procesador
        proc = self.planificador.proceso_actual
        if proc:
            estado_cpu = f"{Colores.VERDE}OCUPADO{Colores.RESET}"
            detalle = f"{Colores.BOLD}Proceso {proc.id}{Colores.RESET} ({proc.titulo})"
            restante = f"{proc.tiempo_restante}"
        else:
            estado_cpu = f"{Colores.AMARILLO}LIBRE{Colores.RESET}"
            detalle, restante = "-", "-"

        tabla_cpu = [[estado_cpu, detalle, restante]]
        print(f"\n{Colores.BOLD}➤ ESTADO DEL PROCESADOR:{Colores.RESET}")
        print(tabulate(tabla_cpu, headers=["Estado", "Proceso en Ejecución", "Tiempo Restante"], tablefmt="fancy_grid"))

        # 2. Tabla de Memoria
        print(f"\n{Colores.BOLD}➤ TABLA DE PARTICIONES (Best-Fit):{Colores.RESET}")
        datos_memoria = self.gestor_memoria.obtener_tabla_particiones()
        print(tabulate(datos_memoria,
                      headers=["ID", "Tam. Part.", "Tam. Proc.", "Estado", "Proceso Asignado", "Frag. Interna", "T. Restante"],
                      tablefmt="fancy_grid"))

        # 3. Colas
        print(f"\n{Colores.BOLD}➤ COLA DE LISTOS / SUSPENDIDOS:{Colores.RESET}")
        suspendidos_data = []
        if self.procesos_suspendidos:
            for p in self.procesos_suspendidos:
                suspendidos_data.append([
                    f"{Colores.ROJO}{p.id}{Colores.RESET}",
                    p.titulo,
                    f"{p.tamaño} KB",
                    p.tiempo_restante
                ])
            print(tabulate(suspendidos_data, headers=["ID", "Título", "Tamaño", "T. Restante"], tablefmt="simple"))
        else:
            print(f"  {Colores.AMARILLO}No hay procesos suspendidos.{Colores.RESET}")

        # 4. Cola de nuevos en espera
        print(f"\n{Colores.BOLD}➤ COLA DE NUEVOS EN ESPERA:{Colores.RESET}")
        nuevos_esperando = [p for p in self.procesos_nuevos if p.tiempo_arribo <= self.tiempo_actual]
        if nuevos_esperando:
            nuevos_data = []
            for p in nuevos_esperando:
                nuevos_data.append([
                    f"{Colores.AMARILLO}{p.id}{Colores.RESET}",
                    p.titulo,
                    f"{p.tamaño} KB",
                    p.tiempo_irrupcion,
                    p.tiempo_arribo
                ])
            print(tabulate(nuevos_data, headers=["ID", "Título", "Tamaño", "T. Irrupción", "T. Arribo"], tablefmt="simple"))
        else:
            print(f"  {Colores.AMARILLO}No hay procesos nuevos esperando.{Colores.RESET}")

        # 5. Info General
        grado = self.calcular_grado_multiprogramacion()
        print(f"\n{Colores.CIAN}ℹ Grado de Multiprogramación: {grado}/{self.MAX_MULTIPROGRAMACION}{Colores.RESET}")

        # 7. Eventos recientes
        if info_cambios.get('eventos'):
            print(f"\n{Colores.BOLD}🔔 EVENTOS DEL CICLO:{Colores.RESET}")
            for ev in info_cambios['eventos']:
                print(f"  • {ev}")

    def calcular_estadisticas(self):
        """Genera el informe final de rendimiento"""
        if not self.procesos_terminados:
            print("No hay estadísticas para mostrar.")
            return

        print(f"\n{Colores.BOLD}{Colores.BG_VERDE} === INFORME ESTADÍSTICO FINAL === {Colores.RESET}\n")

        tabla_stats = []
        t_retorno_total = 0
        t_espera_total = 0

        for p in sorted(self.procesos_terminados, key=lambda x: str(x.id)):
            # CORRECCIÓN: Referencia Arribo a Cola de Listos (No Memoria/Sistema)
            ref_arribo = p.tiempo_arribo_listos if p.tiempo_arribo_listos is not None else p.tiempo_arribo

            t_retorno = p.tiempo_finalizacion - ref_arribo
            t_espera = t_retorno - p.tiempo_irrupcion # Wait = Turnaround - Burst

            t_retorno_total += t_retorno
            t_espera_total += t_espera

            tabla_stats.append([
                f"P{p.id}",
                ref_arribo,
                p.tiempo_inicio,
                p.tiempo_finalizacion,
                t_retorno,
                t_espera
            ])

        # Promedios
        n = len(self.procesos_terminados)
        prom_retorno = t_retorno_total / n
        prom_espera = t_espera_total / n

        tabla_stats.append(["PROM", "-", "-", "-", f"{prom_retorno:.2f}", f"{prom_espera:.2f}"])

        print(tabulate(tabla_stats,
                      headers=["Proceso", "Arribo (Listos)", "Inicio", "Fin", "T. Retorno", "T. Espera"],
                      tablefmt="github"))

        rendimiento = n / self.tiempo_actual if self.tiempo_actual > 0 else 0
        print(f"\n{Colores.BOLD}Rendimiento del Sistema:{Colores.RESET} {rendimiento:.4f} procesos/unidad de tiempo")

    def ejecutar_simulacion(self, paso_a_paso: bool = True):
        """Bucle principal de la simulación"""
        print(f"{Colores.VERDE}Iniciando simulación...{Colores.RESET}")
        self.mostrar_estado_sistema({'hay_cambios': True})
        if paso_a_paso: input("Presiona Enter para comenzar...")

        self.estado_previo['grado'] = self.calcular_grado_multiprogramacion()

        while (self.procesos_nuevos or self.planificador.cola_listos or
               (self.planificador.proceso_actual and self.planificador.proceso_actual.id != "1") or
               self.procesos_suspendidos):

            # Avanzar tiempo inteligentemente
            prox_evento = self.calcular_tiempo_proximo_evento()

            if prox_evento > self.tiempo_actual:
                delta = prox_evento - self.tiempo_actual

                # Actualizar proceso en ejecución durante el salto
                proc = self.planificador.proceso_actual
                if proc and proc.id != "1" and proc.estado == EstadoProceso.EJECUCION:
                    descuento = min(delta, proc.tiempo_restante)
                    proc.tiempo_restante -= descuento
                    if proc.tiempo_inicio is None: proc.tiempo_inicio = self.tiempo_actual

                self.tiempo_actual = prox_evento

            # Ejecutar lógica del ciclo
            cambios = self.ejecutar_ciclo()

            if paso_a_paso and cambios['hay_cambios']:
                self.mostrar_estado_sistema(cambios)
                input(f"\n{Colores.RESET}{Colores.ITALIC}Presiona Enter para continuar...{Colores.RESET}")

            # Actualizar estado previo
            self.estado_previo['grado'] = self.calcular_grado_multiprogramacion()

            if self.tiempo_actual > 2000: # Freno de seguridad
                print("Límite de tiempo excedido.")
                break

        print(f"\n{Colores.BOLD}Simulación finalizada en T={self.tiempo_actual}{Colores.RESET}")
        self.calcular_estadisticas()
        input(f"\n{Colores.BOLD}Presiona Enter para cerrar el simulador...{Colores.RESET}")

    # --- CARGA DE DATOS ---
    def cargar_procesos_desde_archivo(self, ruta: str) -> bool:
        if not os.path.exists(ruta): return False
        try:
            with open(ruta, 'r') as f:
                for linea in f:
                    parts = linea.strip().split(',')
                    if len(parts) < 4 or linea.startswith('#'): continue

                    # Ahora se acepta el ID tal cual viene del archivo (string)
                    pid = parts[0].strip()
                    if pid == "1": continue # Reservado SO

                    p = Proceso(
                        id=pid,
                        tamaño=int(parts[1]),
                        tiempo_arribo=int(parts[2]),
                        tiempo_irrupcion=int(parts[3]),
                        titulo=f"Proceso {pid}"
                    )
                    self.procesos_nuevos.append(p)
            self.procesos_nuevos.sort(key=lambda x: x.tiempo_arribo)
            return True
        except Exception as e:
            print(f"Error cargando archivo: {e}")
            return False

    def cargar_procesos_manual(self) -> bool:
        """Permite al usuario ingresar procesos uno a uno desde la consola"""
        print(f"\n{Colores.BOLD}=== CARGA MANUAL DE PROCESOS ==={Colores.RESET}")
        print("Ingrese los datos. Escriba 'FIN' en el ID para terminar.")

        i = 1
        while True:
            print(f"\n{Colores.CIAN}--- Proceso #{i} ---{Colores.RESET}")
            pid = input("ID del Proceso (ej: P1): ").strip()

            if pid.upper() == 'FIN':
                break

            if not pid:
                print(f"{Colores.ROJO}El ID no puede estar vacío.{Colores.RESET}")
                continue

            if pid == "1":
                print(f"{Colores.ROJO}El ID '1' está reservado para el Sistema Operativo.{Colores.RESET}")
                continue

            # Verificar duplicados
            if any(p.id == pid for p in self.procesos_nuevos):
                print(f"{Colores.ROJO}Ya existe un proceso con ID {pid}.{Colores.RESET}")
                continue

            try:
                tam = int(input("Tamaño (KB): "))
                arr = int(input("Tiempo de Arribo: "))
                irr = int(input("Tiempo de Irrupción: "))

                if tam <= 0 or arr < 0 or irr <= 0:
                    print(f"{Colores.ROJO}Valores inválidos. Tamaño/Irrupción > 0, Arribo >= 0.{Colores.RESET}")
                    continue

                p = Proceso(
                    id=pid,
                    tamaño=tam,
                    tiempo_arribo=arr,
                    tiempo_irrupcion=irr,
                    titulo=f"Proceso {pid}"
                )
                self.procesos_nuevos.append(p)
                print(f"{Colores.VERDE}Proceso agregado correctamente.{Colores.RESET}")
                i += 1

            except ValueError:
                print(f"{Colores.ROJO}Error: Debe ingresar números enteros válidos para Tamaño, Arribo e Irrupción.{Colores.RESET}")

        if self.procesos_nuevos:
            self.procesos_nuevos.sort(key=lambda x: x.tiempo_arribo)
            return True
        return False

def main():
    sim = SimuladorSO()
    print(f"{Colores.BOLD}{Colores.CIAN}=== SIMULADOR DE MEMORIA Y PROCESOS ==={Colores.RESET}")
    print("Config: Particiones Fijas + Best-Fit + SRTF")

    while True:
        print(f"\n{Colores.BOLD}Seleccione el método de carga:{Colores.RESET}")
        print("1. Cargar desde archivo")
        print("2. Cargar manualmente")
        opcion = input("Opción (1/2): ").strip()

        if opcion == "1":
            archivo = input("Ingrese nombre del archivo (ej: archivo.txt): ").strip()
            if sim.cargar_procesos_desde_archivo(archivo):
                break
            else:
                print(f"{Colores.ROJO}No se pudo cargar el archivo.{Colores.RESET}")
        elif opcion == "2":
            if sim.cargar_procesos_manual():
                break
            else:
                print(f"{Colores.AMARILLO}No se cargaron procesos.{Colores.RESET}")
                return
        else:
            print(f"{Colores.ROJO}Opción inválida.{Colores.RESET}")

    sim.ejecutar_simulacion(paso_a_paso=True)

if __name__ == "__main__":
    os.system("")
    main()
    