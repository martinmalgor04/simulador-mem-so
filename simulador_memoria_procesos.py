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
        """Calcula la fragmentación interna de la partición"""
        if self.libre:
            return 0
        # Necesitamos el tamaño del proceso para calcular fragmentación
        return 0  # Se calculará en el gestor de memoria

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
    
    def asignar_memoria(self, proceso: Proceso) -> bool:
        """
        Asigna memoria usando algoritmo Best-Fit
        Retorna True si se pudo asignar, False si no
        """
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
        
        proceso = self.procesos_en_memoria[particion.proceso_asignado]
        return particion.tamaño - proceso.tamaño
    
    def obtener_tabla_particiones(self) -> List[Dict]:
        """Retorna información de todas las particiones"""
        tabla = []
        for particion in self.particiones:
            info = {
                'id': particion.id,
                'direccion_inicio': particion.direccion_inicio,
                'tamaño': particion.tamaño,
                'proceso_asignado': particion.proceso_asignado,
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
        """Agrega un proceso a la cola de listos"""
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
        self.procesos_nuevos = []
        self.procesos_suspendidos = []
        self.procesos_terminados = []
        self.tiempo_actual = 0
        self.grado_multiprogramacion = 0
        self.max_multiprogramacion = 5
    
    def cargar_procesos_desde_archivo(self, nombre_archivo: str) -> bool:
        """Carga procesos desde un archivo"""
        try:
            if not os.path.exists(nombre_archivo):
                print(f"Error: El archivo {nombre_archivo} no existe")
                return False
                
            with open(nombre_archivo, 'r') as archivo:
                for linea in archivo:
                    linea = linea.strip()
                    if linea and not linea.startswith('#'):
                        datos = linea.split(',')
                        if len(datos) >= 4:
                            proceso = Proceso(
                                id=int(datos[0]),
                                tamaño=int(datos[1]),
                                tiempo_arribo=int(datos[2]),
                                tiempo_irrupcion=int(datos[3])
                            )
                            self.procesos_nuevos.append(proceso)
            
            # Ordenar por tiempo de arribo
            self.procesos_nuevos.sort(key=lambda p: p.tiempo_arribo)
            return True
            
        except Exception as e:
            print(f"Error al cargar procesos: {e}")
            return False
    
    def procesar_arribos(self):
        """Procesa los procesos que llegan en el tiempo actual"""
        procesos_arribados = []
        for proceso in self.procesos_nuevos[:]:
            if proceso.tiempo_arribo <= self.tiempo_actual:
                procesos_arribados.append(proceso)
                self.procesos_nuevos.remove(proceso)
        
        for proceso in procesos_arribados:
            self.intentar_admitir_proceso(proceso)
    
    def intentar_admitir_proceso(self, proceso: Proceso):
        """Intenta admitir un nuevo proceso al sistema"""
        # Verificar grado de multiprogramación
        if self.grado_multiprogramacion >= self.max_multiprogramacion:
            proceso.estado = EstadoProceso.LISTO_SUSPENDIDO
            self.procesos_suspendidos.append(proceso)
            return
        
        # Intentar asignar memoria
        if self.gestor_memoria.asignar_memoria(proceso):
            self.grado_multiprogramacion += 1
            
            # Verificar apropiación antes de agregar a cola
            if self.planificador.proceso_actual and self.planificador.verificar_apropiacion(proceso):
                # Devolver proceso actual a cola de listos
                self.planificador.agregar_proceso_listo(self.planificador.proceso_actual)
                self.planificador.proceso_actual = None
            
            # Agregar proceso a cola de listos
            self.planificador.agregar_proceso_listo(proceso)
        else:
            # No hay memoria disponible
            proceso.estado = EstadoProceso.LISTO_SUSPENDIDO
            self.procesos_suspendidos.append(proceso)
    
    def ejecutar_ciclo(self):
        """Ejecuta un ciclo de simulación"""
        # Ejecutar proceso actual si existe (ANTES de procesar arribos)
        if self.planificador.proceso_actual:
            self.planificador.ejecutar_proceso(self.planificador.proceso_actual, self.tiempo_actual)
            
            # Verificar si terminó
            if self.planificador.proceso_actual.estado == EstadoProceso.TERMINADO:
                proceso_terminado = self.planificador.proceso_actual
                self.procesos_terminados.append(proceso_terminado)
                self.gestor_memoria.liberar_memoria(proceso_terminado.id)
                self.grado_multiprogramacion -= 1
                self.planificador.proceso_actual = None
                
                # Intentar admitir procesos suspendidos
                self.intentar_admitir_suspendidos()
        
        # Procesar arribos (después de ejecutar)
        self.procesar_arribos()
        
        # Si no hay proceso ejecutándose, tomar el siguiente
        if not self.planificador.proceso_actual:
            siguiente = self.planificador.obtener_siguiente_proceso()
            if siguiente:
                self.planificador.proceso_actual = siguiente
    
    def intentar_admitir_suspendidos(self):
        """Intenta admitir procesos suspendidos cuando hay recursos disponibles"""
        procesos_admitidos = []
        
        for proceso in self.procesos_suspendidos[:]:
            if self.grado_multiprogramacion >= self.max_multiprogramacion:
                break
            
            if self.gestor_memoria.asignar_memoria(proceso):
                self.grado_multiprogramacion += 1
                self.planificador.agregar_proceso_listo(proceso)
                procesos_admitidos.append(proceso)
                self.procesos_suspendidos.remove(proceso)
        
        return procesos_admitidos
    
    def mostrar_estado_sistema(self):
        """Muestra el estado actual del sistema"""
        print(f"\n{'='*60}")
        print(f"TIEMPO: {self.tiempo_actual}")
        print(f"{'='*60}")
        
        # Estado del procesador
        print("\nESTADO DEL PROCESADOR:")
        if self.planificador.proceso_actual:
            proceso = self.planificador.proceso_actual
            print(f"  Ejecutando: Proceso {proceso.id} (Tiempo restante: {proceso.tiempo_restante})")
        else:
            print("  CPU IDLE")
        
        # Tabla de particiones
        print("\nTABLA DE PARTICIONES:")
        print(f"{'ID':<3} {'Dir.Inicio':<10} {'Tamaño':<8} {'Proceso':<8} {'Frag.Int':<8}")
        print("-" * 45)
        
        for particion_info in self.gestor_memoria.obtener_tabla_particiones():
            proceso_str = str(particion_info['proceso_asignado']) if particion_info['proceso_asignado'] else "Libre"
            print(f"{particion_info['id']:<3} {particion_info['direccion_inicio']:<10} "
                  f"{particion_info['tamaño']:<8} {proceso_str:<8} {particion_info['fragmentacion_interna']:<8}")
        
        # Cola de procesos listos
        print(f"\nCOLA DE PROCESOS LISTOS ({len(self.planificador.cola_listos)} procesos):")
        if self.planificador.cola_listos:
            cola_temp = sorted(self.planificador.cola_listos, key=lambda p: p.tiempo_restante)
            for proceso in cola_temp:
                print(f"  Proceso {proceso.id} (Tiempo restante: {proceso.tiempo_restante})")
        else:
            print("  Vacía")
        
        # Procesos suspendidos
        print(f"\nPROCESOS LISTOS/SUSPENDIDOS ({len(self.procesos_suspendidos)} procesos):")
        if self.procesos_suspendidos:
            for proceso in self.procesos_suspendidos:
                print(f"  Proceso {proceso.id} (Tamaño: {proceso.tamaño}KB)")
        else:
            print("  Ninguno")
        
        print(f"\nGrado de Multiprogramación: {self.grado_multiprogramacion}/{self.max_multiprogramacion}")
    
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
        
        print(f"{'Proceso':<8} {'T.Arribo':<9} {'T.Inicio':<9} {'T.Fin':<7} {'T.Retorno':<10} {'T.Espera':<9}")
        print("-" * 70)
        
        for proceso in self.procesos_terminados:
            tiempo_retorno = proceso.tiempo_finalizacion - proceso.tiempo_arribo
            tiempo_espera = proceso.tiempo_inicio - proceso.tiempo_arribo
            
            tiempos_retorno.append(tiempo_retorno)
            tiempos_espera.append(tiempo_espera)
            
            print(f"{proceso.id:<8} {proceso.tiempo_arribo:<9} {proceso.tiempo_inicio:<9} "
                  f"{proceso.tiempo_finalizacion:<7} {tiempo_retorno:<10} {tiempo_espera:<9}")
        
        # Promedios
        tiempo_retorno_promedio = sum(tiempos_retorno) / len(tiempos_retorno)
        tiempo_espera_promedio = sum(tiempos_espera) / len(tiempos_espera)
        
        print("-" * 70)
        print(f"{'PROMEDIOS':<8} {'':<9} {'':<9} {'':<7} {tiempo_retorno_promedio:<10.2f} {tiempo_espera_promedio:<9.2f}")
        
        print(f"\nProcesos terminados: {len(self.procesos_terminados)}")
        print(f"Procesos suspendidos: {len(self.procesos_suspendidos)}")
        print(f"Procesos nuevos pendientes: {len(self.procesos_nuevos)}")
    
    def ejecutar_simulacion(self, mostrar_pasos: bool = True):
        """Ejecuta la simulación completa"""
        print("Iniciando simulación del Sistema Operativo...")
        print(f"Procesos cargados: {len(self.procesos_nuevos)}")
        
        # Continuar mientras haya procesos por procesar o ejecutar
        while (self.procesos_nuevos or 
               self.planificador.cola_listos or 
               self.planificador.proceso_actual or
               self.procesos_suspendidos):
            
            if mostrar_pasos:
                self.mostrar_estado_sistema()
                input("\nPresiona Enter para continuar al siguiente paso...")
            
            self.ejecutar_ciclo()
            self.tiempo_actual += 1
            
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
    print("- Grado máximo de multiprogramación: 5")
    
    # Cargar procesos desde archivo
    nombre_archivo = input("\nIngrese el nombre del archivo de procesos (ejemplo: procesos.txt): ").strip()
    
    if not simulador.cargar_procesos_desde_archivo(nombre_archivo):
        print("No se pudieron cargar los procesos. Finalizando simulación.")
        return
    
    # Opciones de visualización
    mostrar_pasos = input("¿Mostrar paso a paso? (s/n): ").lower().startswith('s')
    
    # Ejecutar simulación
    simulador.ejecutar_simulacion(mostrar_pasos)

if __name__ == "__main__":
    main()
