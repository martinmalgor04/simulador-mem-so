"""
Simulador de Asignación de Memoria y Planificación de Procesos
Implementa Best-Fit para asignación de memoria y SRTF para planificación de CPU
Autor: Sistema de Simulación de SO
"""

import heapq
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
import os
try:
    from tabulate import tabulate
except ImportError:
    print("Advertencia: tabulate no está instalado. Instalando...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "tabulate"])
    from tabulate import tabulate

class EstadoProceso(Enum):
    NUEVO = "Nuevo"
    LISTO = "Listo"
    LISTO_SUSPENDIDO = "Listo/Suspendido"
    EJECUCION = "Ejecución"
    TERMINADO = "Terminado"

@dataclass
class Proceso:
    """Representa un proceso en el sistema"""
    id: int
    tamaño: int  # En KB
    tiempo_arribo: int
    tiempo_irrupcion: int
    titulo: str = ""
    tiempo_restante: int = None
    tiempo_inicio: int = None
    tiempo_finalizacion: int = None
    estado: EstadoProceso = EstadoProceso.NUEVO
    particion_asignada: int = None
    
    def __post_init__(self):
        if self.tiempo_restante is None:
            self.tiempo_restante = self.tiempo_irrupcion
    
    def __lt__(self, other):
        """Para usar en heap - prioridad por tiempo restante más corto"""
        return self.tiempo_restante < other.tiempo_restante

@dataclass
class Particion:
    """Representa una partición de memoria"""
    id: int
    direccion_inicio: int  # En KB
    tamaño: int  # En KB
    proceso_asignado: Optional[int] = None
    
    @property
    def libre(self) -> bool:
        return self.proceso_asignado is None
    
    @property
    def fragmentacion_interna(self) -> int:
        """Inicializa la fragmentación interna de la partición"""
        if self.libre:
            return 0
        return 0

class GestorMemoria:
    """Gestor de memoria con particiones fijas y algoritmo Best-Fit"""
    
    def __init__(self):
        # Configuración de particiones según especificación
        self.particiones = [
            Particion(0, 0, 100),    # Sistema Operativo
            Particion(1, 100, 250), # Trabajos grandes
            Particion(2, 350, 150), # Trabajos medianos
            Particion(3, 500, 50),  # Trabajos pequeños
        ]
        self.procesos_en_memoria: Dict[int, Proceso] = {}
        
        # Inicializar proceso Sistema Operativo en partición 0 (permanente)
        proceso_so = Proceso(id=1, tamaño=100, tiempo_arribo=0, tiempo_irrupcion=0, titulo="Sistema Operativo")
        proceso_so.estado = EstadoProceso.EJECUCION
        proceso_so.particion_asignada = 0
        self.particiones[0].proceso_asignado = 1
        self.procesos_en_memoria[1] = proceso_so
    
    def asignar_memoria(self, proceso: Proceso) -> bool:
        """
        Asigna memoria usando algoritmo Best-Fit
        Retorna True si se pudo asignar, False si no
        """
        # No permitir asignar el SO (id 1) a otra partición
        if proceso.id == 1:
            return False
        
        # Excluir partición 0 (Sistema Operativo)
        particiones_disponibles = [p for p in self.particiones[1:] 
                                 if p.libre and p.tamaño >= proceso.tamaño]
        
        if not particiones_disponibles:
            return False
        
        # Best-Fit: seleccionar la partición más pequeña que quepa el proceso
        mejor_particion = min(particiones_disponibles, key=lambda p: p.tamaño)
        
        # Asignar proceso a la partición
        mejor_particion.proceso_asignado = proceso.id
        proceso.particion_asignada = mejor_particion.id
        self.procesos_en_memoria[proceso.id] = proceso
        
        return True
    
    def liberar_memoria(self, proceso_id: int) -> bool:
        """Libera la memoria ocupada por un proceso"""
        if proceso_id not in self.procesos_en_memoria:
            return False
        
        # No permitir liberar el proceso del Sistema Operativo (id 1)
        if proceso_id == 1:
            return False
        
        proceso = self.procesos_en_memoria[proceso_id]
        particion = self.particiones[proceso.particion_asignada]
        particion.proceso_asignado = None
        
        del self.procesos_en_memoria[proceso_id]
        return True
    
    def obtener_fragmentacion_interna(self, particion_id: int) -> int:
        """Calcula la fragmentación interna de una partición"""
        particion = self.particiones[particion_id]
        if particion.libre:
            return 0
        
        if particion.proceso_asignado not in self.procesos_en_memoria:
            return 0
        
        proceso = self.procesos_en_memoria[particion.proceso_asignado]
        
        # El SO (id 1) siempre está en partición 0 y no tiene fragmentación
        if proceso.id == 1:
            return 0
        
        return particion.tamaño - proceso.tamaño
    
    def obtener_tabla_particiones(self) -> List[Dict]:
        """Retorna información de todas las particiones"""
        tabla = []
        for particion in self.particiones:
            # Obtener información del proceso si está asignado
            tiempo_restante = None
            titulo_proceso = None
            proceso_id = particion.proceso_asignado
            
            if particion.proceso_asignado and particion.proceso_asignado in self.procesos_en_memoria:
                proceso = self.procesos_en_memoria[particion.proceso_asignado]
                tiempo_restante = proceso.tiempo_restante
                titulo_proceso = proceso.titulo
            
            info = {
                'id': particion.id,
                'direccion_inicio': particion.direccion_inicio,
                'tamaño': particion.tamaño,
                'proceso_asignado': proceso_id,
                'titulo_proceso': titulo_proceso,
                'tiempo_restante': tiempo_restante,
                'fragmentacion_interna': self.obtener_fragmentacion_interna(particion.id)
            }
            tabla.append(info)
        return tabla

class PlanificadorSRTF:
    """Planificador con algoritmo Shortest Remaining Time First (SRTF)"""
    
    def __init__(self):
        self.cola_listos = []  # Min-heap por tiempo restante
        self.proceso_actual: Optional[Proceso] = None
    
    def agregar_proceso_listo(self, proceso: Proceso):
        """Agrega un proceso a la cola de listos (excluyendo SO)"""
        # No agregar el SO (id 1) a la cola de listos
        if proceso.id == 1:
            return
        proceso.estado = EstadoProceso.LISTO
        heapq.heappush(self.cola_listos, proceso)
    
    def obtener_siguiente_proceso(self) -> Optional[Proceso]:
        """Obtiene el siguiente proceso a ejecutar según SRTF"""
        if not self.cola_listos:
            return None
        
        return heapq.heappop(self.cola_listos)
    
    def ejecutar_proceso(self, proceso: Proceso, tiempo_actual: int):
        """Ejecuta un proceso por una unidad de tiempo"""
        if proceso.tiempo_inicio is None:
            proceso.tiempo_inicio = tiempo_actual
        
        proceso.estado = EstadoProceso.EJECUCION
        
        # Evitar que tiempo_restante sea negativo
        if proceso.tiempo_restante > 0:
            proceso.tiempo_restante -= 1
        
        if proceso.tiempo_restante == 0:
            proceso.estado = EstadoProceso.TERMINADO
            proceso.tiempo_finalizacion = tiempo_actual + 1
    
    def verificar_apropiacion(self, nuevo_proceso: Proceso) -> bool:
        """Verifica si un nuevo proceso debe apropiarse de la CPU"""
        if self.proceso_actual is None:
            return True
        
        return nuevo_proceso.tiempo_restante < self.proceso_actual.tiempo_restante

class SimuladorSO:
    """Simulador principal del Sistema Operativo"""
    
    def __init__(self):
        self.gestor_memoria = GestorMemoria()
        self.planificador = PlanificadorSRTF()
        # procesos_nuevos: Contiene procesos que aún no han arribado Y procesos que ya arribaron 
        # pero están esperando por grado de multiprogramación máximo (ordenados por tiempo_irrupcion)
        self.procesos_nuevos = []
        self.procesos_suspendidos = []
        self.procesos_terminados = []
        self.tiempo_actual = 0
        self.max_multiprogramacion = 5
        # Estados previos para detectar cambios
        self.estado_previo = {
            'grado_multiprogramacion': 0,
            'cola_listos_len': 0,
            'cola_suspendidos_len': 0,
            'proceso_ejecutando': None,
            'procesos_en_memoria': set()
        }
    
    def calcular_grado_multiprogramacion(self) -> int:
        """
        Calcula el grado de multiprogramación actual
        Grado = Procesos en RAM + Procesos suspendidos
        - RAM: máximo 3 procesos (hay 3 particiones disponibles, excluyendo SO)
        - Suspendidos: máximo 2 procesos
        - Total: máximo 5 procesos
        """
        # Procesos en RAM (excluyendo SO que siempre está)
        procesos_en_ram = len([p for p in self.gestor_memoria.procesos_en_memoria.values() 
                              if p.id != 1])
        
        # Procesos suspendidos (en disco)
        procesos_suspendidos = len(self.procesos_suspendidos)
        
        # Grado total de multiprogramación
        return procesos_en_ram + procesos_suspendidos
    
    def aplicar_apropiacion_srtf(self, proceso_nuevo: Proceso) -> bool:
        """
        Aplica apropiación SRTF si el nuevo proceso es más corto que el actual
        Retorna True si se aplicó apropiación
        """
        if not self.planificador.proceso_actual:
            return False
        
        if not self.planificador.verificar_apropiacion(proceso_nuevo):
            return False
        
        # Apropiación: devolver proceso actual a cola de listos
        proceso_anterior = self.planificador.proceso_actual
        proceso_anterior.estado = EstadoProceso.LISTO
        self.planificador.agregar_proceso_listo(proceso_anterior)
        self.planificador.proceso_actual = None
        return True
    
    def admitir_proceso_a_ram(self, proceso: Proceso, verificar_apropiacion: bool = True) -> bool:
        """
        Intenta admitir un proceso a RAM asignándole memoria
        Retorna True si se admitió exitosamente
        """
        # No admitir el SO (id 1) a la cola de listos
        if proceso.id == 1:
            return False
        
        if not self.gestor_memoria.asignar_memoria(proceso):
            return False
        
        # Verificar apropiación SRTF si es necesario
        if verificar_apropiacion:
            self.aplicar_apropiacion_srtf(proceso)
        
        # Agregar proceso a cola de listos
        self.planificador.agregar_proceso_listo(proceso)
        return True
    
    def cargar_procesos_desde_archivo(self, nombre_archivo: str) -> bool:
        """
        Carga procesos desde un archivo
        Formato esperado: ID_Proceso,Tamaño_KB,Tiempo_Arribo,Tiempo_Irrupción,Título
        """
        try:
            if not os.path.exists(nombre_archivo):
                print(f"Error: El archivo {nombre_archivo} no existe")
                return False
                
            with open(nombre_archivo, 'r') as archivo:
                for num_linea, linea in enumerate(archivo, 1):
                    linea = linea.strip()
                    if linea and not linea.startswith('#'):
                        datos = linea.split(',')
                        if len(datos) >= 4:
                            proceso_id = int(datos[0])
                            # Rechazar procesos con id=1 porque está reservado para el SO
                            if proceso_id == 1:
                                print(f"Advertencia (línea {num_linea}): El proceso con ID=1 está reservado para el Sistema Operativo. Ignorando proceso.")
                                continue
                            
                            # El título es opcional (5ta columna), si no está presente usar vacío
                            titulo = datos[4].strip() if len(datos) >= 5 else f"Proceso {proceso_id}"
                            
                            proceso = Proceso(
                                id=proceso_id,
                                tamaño=int(datos[1]),
                                tiempo_arribo=int(datos[2]),
                                tiempo_irrupcion=int(datos[3]),
                                titulo=titulo
                            )
                            self.procesos_nuevos.append(proceso)
                        else:
                            print(f"Advertencia (línea {num_linea}): Formato incorrecto, se requieren al menos 4 campos separados por coma.")
            
            # Ordenar por tiempo de arribo
            self.procesos_nuevos.sort(key=lambda p: p.tiempo_arribo)
            print(f"✓ Cargados {len(self.procesos_nuevos)} procesos desde el archivo.")
            return True
            
        except Exception as e:
            print(f"Error al cargar procesos: {e}")
            return False
    
    def cargar_procesos_manual(self) -> bool:
        """
        Carga procesos manualmente por consola
        El usuario ingresa los procesos uno por uno
        """
        print("\n=== CARGA MANUAL DE PROCESOS ===")
        print("Ingrese los datos de cada proceso.")
        print("Formato: ID, Tamaño (KB), Tiempo de Arribo, Tiempo de Irrupción, Título")
        print("Ingrese 'fin' cuando haya terminado de cargar procesos.\n")
        
        proceso_num = 1
        ids_usados = set()
        
        while True:
            try:
                entrada = input(f"Proceso {proceso_num} (o 'fin' para terminar): ").strip()
                
                if entrada.lower() == 'fin':
                    break
                
                if not entrada:
                    continue
                
                datos = [d.strip() for d in entrada.split(',')]
                
                if len(datos) < 4:
                    print("❌ Error: Debe ingresar al menos 4 valores: ID, Tamaño, Tiempo de Arribo, Tiempo de Irrupción, Título (opcional)")
                    continue
                
                proceso_id = int(datos[0])
                
                # Validaciones
                if proceso_id == 1:
                    print("❌ Error: El ID=1 está reservado para el Sistema Operativo.")
                    continue
                
                if proceso_id in ids_usados:
                    print(f"❌ Error: El ID {proceso_id} ya fue utilizado.")
                    continue
                
                if len(ids_usados) >= 10:
                    print("❌ Error: Se ha alcanzado el máximo de 10 procesos.")
                    break
                
                tamaño = int(datos[1])
                tiempo_arribo = int(datos[2])
                tiempo_irrupcion = int(datos[3])
                titulo = datos[4] if len(datos) >= 5 and datos[4] else f"Proceso {proceso_id}"
                
                # Validar valores positivos
                if tamaño <= 0 or tiempo_irrupcion <= 0 or tiempo_arribo < 0:
                    print("❌ Error: Tamaño y Tiempo de Irrupción deben ser mayores a 0. Tiempo de Arribo debe ser >= 0.")
                    continue
                
                proceso = Proceso(
                    id=proceso_id,
                    tamaño=tamaño,
                    tiempo_arribo=tiempo_arribo,
                    tiempo_irrupcion=tiempo_irrupcion,
                    titulo=titulo
                )
                
                self.procesos_nuevos.append(proceso)
                ids_usados.add(proceso_id)
                proceso_num += 1
                print(f"✓ Proceso {proceso_id} ({titulo}) agregado correctamente.\n")
                
            except ValueError:
                print("❌ Error: Los valores numéricos deben ser enteros válidos.")
            except Exception as e:
                print(f"❌ Error inesperado: {e}")
        
        if not self.procesos_nuevos:
            print("\n⚠ No se cargaron procesos.")
            return False
        
        # Ordenar por tiempo de arribo
        self.procesos_nuevos.sort(key=lambda p: p.tiempo_arribo)
        print(f"\n✓ Total de procesos cargados: {len(self.procesos_nuevos)}")
        return True
    
    def procesar_arribos(self):
        """
        Procesa los procesos que llegan en el tiempo actual
        Los procesos están en procesos_nuevos ordenados por tiempo_arribo
        """
        # Procesar procesos que acaban de arribar (tiempo_arribo <= tiempo_actual)
        for proceso in self.procesos_nuevos[:]:
            if proceso.tiempo_arribo <= self.tiempo_actual:
                # Remover de nuevos y intentar admitir
                self.procesos_nuevos.remove(proceso)
                # Intentar admitir (si no se puede, vuelve a procesos_nuevos)
                self.intentar_admitir_proceso(proceso)
    
    def buscar_proceso_suspendido_mas_corto(self, proceso_actual: Optional[Proceso]) -> Optional[Proceso]:
        """Busca el proceso suspendido con menor tiempo restante"""
        if not self.procesos_suspendidos:
            return None
        
        proceso_mas_corto = min(self.procesos_suspendidos, key=lambda p: p.tiempo_restante)
        
        # Si hay proceso en ejecución, verificar si el suspendido es más corto
        if proceso_actual:
            if proceso_mas_corto.tiempo_restante < proceso_actual.tiempo_restante:
                return proceso_mas_corto
            return None
        
        # Si no hay proceso en ejecución, retornar el más corto
        return proceso_mas_corto
    
    def agregar_a_cola_nuevos(self, proceso: Proceso):
        """Agrega un proceso a la cola de nuevos y ordena por tiempo de arribo"""
        proceso.estado = EstadoProceso.NUEVO
        if proceso not in self.procesos_nuevos:
            self.procesos_nuevos.append(proceso)
        # Ordenar solo por tiempo de arribo
        self.procesos_nuevos.sort(key=lambda p: p.tiempo_arribo)
    
    def intentar_admitir_proceso(self, proceso: Proceso) -> bool:
        """
        Intenta admitir un nuevo proceso al sistema
        Retorna True si se admitió, False si no
        """
        # Asegurarse de que el proceso no esté en ninguna lista previamente
        if proceso in self.procesos_nuevos:
            self.procesos_nuevos.remove(proceso)
        if proceso in self.procesos_suspendidos:
            self.procesos_suspendidos.remove(proceso)
        
        # Verificar grado de multiprogramación
        if self.calcular_grado_multiprogramacion() >= self.max_multiprogramacion:
            self.agregar_a_cola_nuevos(proceso)
            return False
        
        # Intentar admitir a RAM
        if self.admitir_proceso_a_ram(proceso):
            return True
        
        # No hay memoria disponible pero grado < 5 - ir a suspendidos
        proceso.estado = EstadoProceso.LISTO_SUSPENDIDO
        if proceso not in self.procesos_suspendidos:
            self.procesos_suspendidos.append(proceso)
        return False
    
    def intentar_swap_srtf(self) -> bool:
        """
        Intenta hacer swap SRTF con procesos suspendidos
        Retorna True si se hizo un swap
        """
        if not self.planificador.proceso_actual:
            return False
        
        # Buscar proceso suspendido más corto
        proceso_suspendido = self.buscar_proceso_suspendido_mas_corto(self.planificador.proceso_actual)
        
        if not proceso_suspendido:
            return False
        
        # Verificar grado de multiprogramación antes de hacer swap
        grado_actual = self.calcular_grado_multiprogramacion()
        if grado_actual >= self.max_multiprogramacion:
            # Necesitamos liberar memoria del proceso actual para hacer swap
            proceso_actual = self.planificador.proceso_actual
            # Liberar memoria del proceso actual
            self.gestor_memoria.liberar_memoria(proceso_actual.id)
            proceso_actual.estado = EstadoProceso.LISTO_SUSPENDIDO
            self.procesos_suspendidos.append(proceso_actual)
        else:
            # Si hay espacio, solo mover el actual a cola de listos
            proceso_actual = self.planificador.proceso_actual
            proceso_actual.estado = EstadoProceso.LISTO
            self.planificador.agregar_proceso_listo(proceso_actual)
        
        # Intentar asignar memoria al suspendido
        if not self.gestor_memoria.asignar_memoria(proceso_suspendido):
            # Si no se puede asignar, revertir cambios
            if proceso_actual.estado == EstadoProceso.LISTO_SUSPENDIDO:
                self.procesos_suspendidos.remove(proceso_actual)
                self.gestor_memoria.asignar_memoria(proceso_actual)
                proceso_actual.estado = EstadoProceso.LISTO
                self.planificador.agregar_proceso_listo(proceso_actual)
                self.planificador.proceso_actual = proceso_actual
            return False
        
        # Sacar suspendido de la lista y ponerlo en ejecución
        self.procesos_suspendidos.remove(proceso_suspendido)
        proceso_suspendido.estado = EstadoProceso.EJECUCION
        self.planificador.proceso_actual = proceso_suspendido
        
        return True
    
    def ejecutar_ciclo(self) -> Dict:
        """
        Ejecuta un ciclo de simulación
        Retorna diccionario con información de cambios para mostrar
        """
        cambios = {
            'proceso_terminado': None,
            'proceso_swapeado': False,
            'cambio_multiprogramacion': False
        }
        
        # Ejecutar proceso actual si existe (excluyendo SO)
        if self.planificador.proceso_actual and self.planificador.proceso_actual.id != 1:
            self.planificador.ejecutar_proceso(self.planificador.proceso_actual, self.tiempo_actual)
            
            # Verificar si terminó
            if self.planificador.proceso_actual.estado == EstadoProceso.TERMINADO:
                proceso_terminado = self.planificador.proceso_actual
                self.procesos_terminados.append(proceso_terminado)
                self.gestor_memoria.liberar_memoria(proceso_terminado.id)
                self.planificador.proceso_actual = None
                cambios['proceso_terminado'] = proceso_terminado
                
                # Intentar admitir procesos: primero suspendidos, luego nuevos
                self.intentar_admitir_suspendidos()
                self.intentar_admitir_procesos_nuevos()
        
        # Verificar swap SRTF con suspendidos (antes de procesar arribos)
        if self.intentar_swap_srtf():
            cambios['proceso_swapeado'] = True
        
        # Procesar arribos
        self.procesar_arribos()
        
        # Verificar apropiación SRTF de nuevos procesos
        if self.planificador.proceso_actual:
            # Verificar si hay un proceso más corto en la cola de listos
            if self.planificador.cola_listos:
                proceso_mas_corto_cola = min(self.planificador.cola_listos, key=lambda p: p.tiempo_restante)
                if proceso_mas_corto_cola.tiempo_restante < self.planificador.proceso_actual.tiempo_restante:
                    # Apropiación: cambiar procesos
                    proceso_actual = self.planificador.proceso_actual
                    proceso_actual.estado = EstadoProceso.LISTO
                    self.planificador.agregar_proceso_listo(proceso_actual)
                    
                    # Remover el más corto de la cola y ponerlo en ejecución
                    self.planificador.cola_listos.remove(proceso_mas_corto_cola)
                    # Reconstruir heap
                    heapq.heapify(self.planificador.cola_listos)
                    proceso_mas_corto_cola.estado = EstadoProceso.EJECUCION
                    self.planificador.proceso_actual = proceso_mas_corto_cola
                    cambios['proceso_swapeado'] = True
        
        # Si no hay proceso ejecutándose, tomar el siguiente (excluyendo SO)
        if not self.planificador.proceso_actual:
            siguiente = self.planificador.obtener_siguiente_proceso()
            if siguiente and siguiente.id != 1:
                siguiente.estado = EstadoProceso.EJECUCION
                self.planificador.proceso_actual = siguiente
        
        # Verificar cambios en grado de multiprogramación
        grado_actual = self.calcular_grado_multiprogramacion()
        if grado_actual != self.estado_previo['grado_multiprogramacion']:
            cambios['cambio_multiprogramacion'] = True
        
        return cambios
    
    def intentar_admitir_suspendidos(self):
        """
        Intenta admitir procesos suspendidos cuando hay recursos disponibles
        Usa SRTF: prioriza el proceso con menor tiempo_restante
        """
        procesos_admitidos = []
        
        # Ordenar suspendidos por tiempo_restante (SRTF)
        suspendidos_ordenados = sorted(self.procesos_suspendidos, key=lambda p: p.tiempo_restante)
        
        for proceso in suspendidos_ordenados[:]:
            if self.calcular_grado_multiprogramacion() >= self.max_multiprogramacion:
                break
            
            # Asegurarse de que no esté en procesos_nuevos
            if proceso in self.procesos_nuevos:
                self.procesos_nuevos.remove(proceso)
            
            if self.admitir_proceso_a_ram(proceso):
                procesos_admitidos.append(proceso)
                self.procesos_suspendidos.remove(proceso)
        
        return procesos_admitidos
    
    def intentar_admitir_procesos_nuevos(self):
        """
        Intenta admitir procesos desde la cola de nuevos cuando hay espacio
        Usa SRTF: busca entre los procesos que ya arribaron el de menor tiempo_irrupcion
        """
        procesos_admitidos = []
        
        # Buscar procesos que ya arribaron (no los futuros)
        procesos_esperando = [p for p in self.procesos_nuevos if p.tiempo_arribo <= self.tiempo_actual]
        
        # Mientras haya espacio y procesos esperando, usar SRTF
        while procesos_esperando and self.calcular_grado_multiprogramacion() < self.max_multiprogramacion:
            # SRTF: seleccionar el proceso con menor tiempo_irrupcion entre los que ya arribaron
            proceso_srtf = min(procesos_esperando, key=lambda p: p.tiempo_irrupcion)
            
            # Intentar admitir
            if self.intentar_admitir_proceso(proceso_srtf):
                procesos_admitidos.append(proceso_srtf)
                self.procesos_nuevos.remove(proceso_srtf)
                procesos_esperando.remove(proceso_srtf)
            else:
                # Si no se pudo admitir (grado lleno o sin memoria), salir del loop
                break
        
        return procesos_admitidos
    
    def hay_cambios_significativos(self, cambios: Dict) -> bool:
        """Determina si hay cambios significativos que justifiquen mostrar el estado"""
        return True
    
    def mostrar_estado_sistema(self, cambios: Dict = None):
        """Muestra el estado actual del sistema usando tablas tabuladas"""
        if cambios is None:
            cambios = {}
        
        print(f"\n{'='*70}")
        print(f"TIEMPO SIMULADO: {self.tiempo_actual}")
        print(f"{'='*70}")
        
        # Estado del procesador
        estado_procesador = []
        if self.planificador.proceso_actual:
            proceso = self.planificador.proceso_actual
            titulo_display = proceso.titulo if proceso.titulo else f"Proceso {proceso.id}"
            estado_procesador.append([
                "Ocupado",
                f"Proceso {proceso.id} ({titulo_display})",
                proceso.tiempo_restante,
                f"Tamaño: {proceso.tamaño}KB"
            ])
        else:
            estado_procesador.append(["Libre", "-", "-", "-"])
        
        print("\nESTADO DEL PROCESADOR:")
        print(tabulate(estado_procesador, 
                      headers=["Estado", "Proceso", "Tiempo Restante", "Info"],
                      tablefmt="grid"))
        
        # Tabla de particiones
        tabla_particiones = []
        for particion_info in self.gestor_memoria.obtener_tabla_particiones():
            if particion_info['proceso_asignado']:
                proceso_id = "SO" if particion_info['proceso_asignado'] == 1 else str(particion_info['proceso_asignado'])
                titulo = particion_info['titulo_proceso'] if particion_info['titulo_proceso'] else "-"
                # Para SO, el título debería ser "Sistema Operativo" si está disponible
                if particion_info['proceso_asignado'] == 1:
                    titulo = particion_info['titulo_proceso'] if particion_info['titulo_proceso'] else "Sistema Operativo"
                tiempo_restante_str = "-" if particion_info['proceso_asignado'] == 1 else str(particion_info['tiempo_restante'])
            else:
                proceso_id = "-"
                titulo = "-"
                tiempo_restante_str = "-"
            
            tabla_particiones.append([
                particion_info['id'],
                particion_info['direccion_inicio'],
                particion_info['tamaño'],
                proceso_id,
                titulo,
                tiempo_restante_str,
                particion_info['fragmentacion_interna']
            ])
        
        print("\nTABLA DE PARTICIONES:")
        print(tabulate(tabla_particiones,
                      headers=["ID Partición", "Dir. Inicio (KB)", "Tamaño (KB)", 
                              "ID Proceso", "Título", "T. Restante", "Fragmentación (KB)"],
                      tablefmt="grid"))
        
        # Procesos suspendidos
        tabla_suspendidos = []
        if self.procesos_suspendidos:
            for proceso in self.procesos_suspendidos:
                tabla_suspendidos.append([
                    proceso.id,
                    proceso.tiempo_restante,
                    proceso.tamaño
                ])
        else:
            tabla_suspendidos.append(["Ninguno", "-", "-"])
        
        print(f"\nPROCESOS LISTOS/SUSPENDIDOS ({len(self.procesos_suspendidos)} procesos):")
        print(tabulate(tabla_suspendidos,
                      headers=["ID Proceso", "Tiempo Restante", "Tamaño (KB)"],
                      tablefmt="grid"))
        
        # Procesos nuevos en espera (lista simple)
        # Solo mostrar procesos que NO están en suspendidos (para evitar duplicación)
        procesos_nuevos_esperando = [p for p in self.procesos_nuevos 
                                    if p.tiempo_arribo <= self.tiempo_actual 
                                    and p not in self.procesos_suspendidos]
        print(f"\nPROCESOS NUEVOS EN ESPERA (Grado máximo alcanzado) ({len(procesos_nuevos_esperando)} procesos):")
        if procesos_nuevos_esperando:
            lista_ids = ", ".join([str(p.id) for p in procesos_nuevos_esperando])
            print(f"  {lista_ids}")
        else:
            print("  Ninguno")
        
        # Grado de multiprogramación
        grado_actual = self.calcular_grado_multiprogramacion()
        # Procesos en RAM excluyendo SO (id 1)
        procesos_en_ram = len([p for p in self.gestor_memoria.procesos_en_memoria.values() if p.id != 1])
        procesos_suspendidos = len(self.procesos_suspendidos)
        print(f"\nGrado de Multiprogramación: {grado_actual}/{self.max_multiprogramacion}")
        print(f"  - En RAM: {procesos_en_ram}/3")
        print(f"  - Suspendidos: {procesos_suspendidos}/2")
        
        # Mostrar eventos si hay cambios
        if cambios:
            eventos = []
            if cambios.get('proceso_terminado'):
                p = cambios['proceso_terminado']
                titulo_display = f" ({p.titulo})" if p.titulo else ""
                eventos.append(f"✓ Proceso {p.id}{titulo_display} terminado")
            if cambios.get('proceso_swapeado'):
                eventos.append("↔ Intercambio SRTF realizado")
            
            if eventos:
                print("\nEVENTOS EN ESTE CICLO:")
                for evento in eventos:
                    print(f"  {evento}")
    
    def calcular_estadisticas(self):
        """Calcula y muestra estadísticas finales"""
        if not self.procesos_terminados:
            print("\nNo hay procesos terminados para calcular estadísticas.")
            return
        
        print(f"\n{'='*80}")
        print("INFORME ESTADÍSTICO FINAL")
        print(f"{'='*80}")
        
        tiempos_retorno = []
        tiempos_espera = []
        
        tabla_estadisticas = []
        for proceso in sorted(self.procesos_terminados, key=lambda p: p.id):
            tiempo_retorno = proceso.tiempo_finalizacion - proceso.tiempo_arribo
            tiempo_espera = proceso.tiempo_inicio - proceso.tiempo_arribo
            
            tiempos_retorno.append(tiempo_retorno)
            tiempos_espera.append(tiempo_espera)
            
            # Mostrar ID y título si existe
            proceso_display = f"{proceso.id} ({proceso.titulo})" if proceso.titulo else str(proceso.id)
            
            tabla_estadisticas.append([
                proceso_display,
                proceso.tiempo_arribo,
                proceso.tiempo_inicio,
                proceso.tiempo_finalizacion,
                tiempo_retorno,
                tiempo_espera
            ])
        
        # Promedios
        tiempo_retorno_promedio = sum(tiempos_retorno) / len(tiempos_retorno)
        tiempo_espera_promedio = sum(tiempos_espera) / len(tiempos_espera)
        
        tabla_estadisticas.append([
            "PROMEDIO",
            "-",
            "-",
            "-",
            f"{tiempo_retorno_promedio:.2f}",
            f"{tiempo_espera_promedio:.2f}"
        ])
        
        print("\nESTADÍSTICAS POR PROCESO:")
        print(tabulate(tabla_estadisticas,
                      headers=["Proceso", "T. Arribo", "T. Inicio", "T. Fin", 
                              "T. Retorno", "T. Espera"],
                      tablefmt="grid"))
        
        # Rendimiento del sistema
        tiempo_total = self.tiempo_actual
        rendimiento = len(self.procesos_terminados) / tiempo_total if tiempo_total > 0 else 0
        
        print(f"\nRESUMEN GENERAL:")
        resumen = [
            ["Procesos terminados", len(self.procesos_terminados)],
            ["Tiempo de retorno promedio", f"{tiempo_retorno_promedio:.2f}"],
            ["Tiempo de espera promedio", f"{tiempo_espera_promedio:.2f}"],
            ["Rendimiento del sistema", f"{rendimiento:.4f} procesos/unidad_tiempo"],
            ["Tiempo total de simulación", tiempo_total],
            ["Procesos suspendidos al finalizar", len(self.procesos_suspendidos)],
            ["Procesos nuevos pendientes", len(self.procesos_nuevos)]
        ]
        print(tabulate(resumen, headers=["Métrica", "Valor"], tablefmt="grid"))
    
    def ejecutar_simulacion(self, mostrar_pasos: bool = True):
        """
        Ejecuta la simulación completa
        Cada iteración avanza una unidad de tiempo simulada
        """
        print("Iniciando simulación del Sistema Operativo...")
        print(f"Procesos cargados: {len(self.procesos_nuevos)}")
        
        # Actualizar estado previo inicial
        self.estado_previo['grado_multiprogramacion'] = self.calcular_grado_multiprogramacion()
        self.estado_previo['cola_listos_len'] = len(self.planificador.cola_listos)
        self.estado_previo['cola_suspendidos_len'] = len(self.procesos_suspendidos)
        self.estado_previo['proceso_ejecutando'] = self.planificador.proceso_actual.id if self.planificador.proceso_actual else None
        
        # Continuar mientras haya procesos por procesar o ejecutar
        while (self.procesos_nuevos or 
               self.planificador.cola_listos or 
               self.planificador.proceso_actual or
               self.procesos_suspendidos):
            
            # Ejecutar ciclo y obtener cambios
            cambios = self.ejecutar_ciclo()
            
            # Mostrar estado del sistema
            if mostrar_pasos:
                self.mostrar_estado_sistema(cambios)
                input("\nPresiona Enter para avanzar una unidad de tiempo...")
            
            # Actualizar tiempo
            self.tiempo_actual += 1
            
            # Actualizar estado previo para detectar cambios
            self.estado_previo['grado_multiprogramacion'] = self.calcular_grado_multiprogramacion()
            self.estado_previo['cola_listos_len'] = len(self.planificador.cola_listos)
            self.estado_previo['cola_suspendidos_len'] = len(self.procesos_suspendidos)
            self.estado_previo['proceso_ejecutando'] = self.planificador.proceso_actual.id if self.planificador.proceso_actual else None
            
            # Límite de seguridad para evitar bucles infinitos
            if self.tiempo_actual > 1000:
                print("Simulación detenida por límite de tiempo")
                break
        
        print(f"\nSimulación completada en tiempo: {self.tiempo_actual}")
        self.calcular_estadisticas()

def main():
    """Función principal del simulador"""
    simulador = SimuladorSO()
    
    print("=== SIMULADOR DE ASIGNACIÓN DE MEMORIA Y PLANIFICACIÓN DE PROCESOS ===")
    print("Configuración:")
    print("- Particiones fijas: 100K (SO), 250K (grandes), 150K (medianos), 50K (pequeños)")
    print("- Algoritmo de asignación: Best-Fit")
    print("- Algoritmo de planificación: SRTF (Shortest Remaining Time First)")
    print("- Grado máximo de multiprogramación: 5\n")
    
    # Elegir método de carga
    while True:
        metodo = input("¿Cómo desea cargar los procesos?\n  1. Desde archivo\n  2. Manualmente por consola\nSeleccione (1 o 2): ").strip()
        
        if metodo == "1":
            nombre_archivo = input("\nIngrese el nombre del archivo de procesos (ejemplo: procesos.txt): ").strip()
            if simulador.cargar_procesos_desde_archivo(nombre_archivo):
                break
            else:
                print("No se pudieron cargar los procesos desde el archivo.")
                reintentar = input("¿Desea intentar cargar manualmente? (s/n): ").lower().startswith('s')
                if reintentar:
                    metodo = "2"
                    break
                else:
                    print("Finalizando simulación.")
                    return
        elif metodo == "2":
            if simulador.cargar_procesos_manual():
                break
            else:
                print("No se cargaron procesos. Finalizando simulación.")
                return
        else:
            print("❌ Opción inválida. Por favor seleccione 1 o 2.")
    
    # Opciones de visualización
    mostrar_pasos = input("\n¿Mostrar paso a paso? (s/n): ").lower().startswith('s')
    
    # Ejecutar simulación
    simulador.ejecutar_simulacion(mostrar_pasos)

if __name__ == "__main__":
    main()
