# Plan de Implementación - Simulador de Memoria y Procesos

## 📋 ESTADO ACTUAL DE TAREAS DEL TRELLO

### ✅ TAREAS COMPLETADAS (15/15)

#### PRIORIDAD 1ER (Primera)
1. ✅ **Programar lectura de procesos desde archivo** - COMPLETO
   - Función `cargar_procesos_desde_archivo()` implementada
   - Parseo CSV con formato: `ID,Tamaño,Tiempo_Arribo,Tiempo_Irrupción`
   - Ignora comentarios y líneas vacías
   - Ordena por tiempo de arribo

2. ✅ **Implementar cola de procesos Listos y Listos/Suspendidos** - COMPLETO
   - Cola de listos: min-heap implementado para SRTF
   - Lista de procesos suspendidos implementada
   - Orden correcto mantenido por el heap

3. ✅ **Programar estructura del proceso (ID, tamaño, tiempo arribo, tiempo irrupción)** - COMPLETO
   - Clase `Proceso` con todos los campos requeridos
   - Inicialización correcta de `tiempo_restante`
   - Campos adicionales: `tiempo_inicio`, `tiempo_finalizacion`, `estado`, `particion_asignada`

#### PRIORIDAD 2DA (Segunda)
4. ✅ **Crear función para mostrar tabla de particiones** - COMPLETO
   - Método `obtener_tabla_particiones()` implementado
   - Muestra todas las particiones (incluyendo SO)
   - Información: ID, dirección inicio, tamaño, proceso asignado, fragmentación interna
   - **Formato tabulado con tabulate implementado**

5. ✅ **Crear función para mostrar estado del procesador** - COMPLETO
   - Muestra proceso en ejecución o "CPU IDLE"
   - Muestra tiempo restante y tamaño del proceso
   - **Formato tabulado con tabulate implementado**

6. ✅ **Programar algoritmo Best-Fit** - COMPLETO
   - Implementado en `asignar_memoria()`
   - Excluye partición del SO (partición 0)
   - Selecciona la partición más pequeña que quepa el proceso

7. ✅ **Calcular fragmentación interna por partición** - COMPLETO
   - Método `obtener_fragmentacion_interna()` implementado
   - Cálculo: `tamaño_particion - tamaño_proceso`
   - Retorna 0 si la partición está libre

8. ✅ **Implementar suspensión de procesos cuando no hay memoria** - COMPLETO
   - Cambio de estado a `LISTO_SUSPENDIDO` cuando no hay memoria
   - Lista `procesos_suspendidos` implementada
   - Intenta admitir suspendidos cuando se libera memoria

9. ✅ **Implementar interrupción por SRTF cuando llega proceso más corto** - COMPLETO
   - Método `verificar_apropiacion()` implementado
   - Apropiación completa en `intentar_admitir_proceso()`
   - Proceso actual se devuelve correctamente a la cola
   - Apropiación ocurre al arribo y durante ejecución
   - **Incluye swap con procesos suspendidos**

10. ✅ **Mostrar salidas cuando llega un nuevo proceso y cuando termina uno** - COMPLETO
    - Mensajes informativos al arribo de nuevos procesos
    - Mensajes informativos al terminar procesos
    - Muestra estado completo del sistema en cada iteración
    - **Formato de tabla tabulada con eventos destacados**

11. ✅ **Completar transiciones de estado (agregar Terminado)** - COMPLETO
    - Estado TERMINADO en enum
    - Transición a TERMINADO cuando `tiempo_restante == 0`
    - Liberación de memoria al terminar

#### PRIORIDAD 3ER (Tercera)
12. ✅ **Implementar cambios de estado (Nuevo → Listo → Ejecución)** - COMPLETO
    - Enum `EstadoProceso` con todos los estados
    - Transiciones implementadas correctamente
    - Sincronización: proceso no puede estar en múltiples estados

13. ✅ **Programar algoritmo SRTF básico** - COMPLETO
    - Min-heap para cola de listos implementado
    - Método `obtener_siguiente_proceso()` implementado
    - Método `verificar_apropiacion()` implementado
    - **Apropiación completa implementada**

14. ✅ **Implementar control de multiprogramación (máximo 5 procesos)** - COMPLETO
    - Función `calcular_grado_multiprogramacion()` implementada
    - Cuenta procesos en memoria, cola de listos, ejecución y suspendidos
    - Control de máximo 5 procesos implementado
    - Respeta límite en admisión de procesos

15. ✅ **Calcular tiempo de retorno, espera y promedio por proceso** - COMPLETO
    - Cálculo de tiempo de retorno: `tiempo_finalizacion - tiempo_arribo`
    - Cálculo de tiempo de espera: `tiempo_inicio - tiempo_arribo`
    - Cálculo de promedios implementado
    - **Rendimiento del sistema calculado**: `procesos_terminados / tiempo_total`
    - **Formato tabulado con tabulate**

---

## 🎯 RESUMEN GENERAL

### ✅ TOTAL: 15/15 TAREAS COMPLETADAS (100%)

Todas las tareas del Trello han sido implementadas y probadas:

- **1ER Prioridad**: 3/3 completadas ✅
- **2DA Prioridad**: 7/7 completadas ✅
- **3ER Prioridad**: 4/4 completadas ✅
- **BONUS**: Rendimiento del sistema agregado ✅

### 📝 MEJORAS ADICIONALES IMPLEMENTADAS

1. ✅ **Formato de tablas con tabulate** - Todas las salidas usan formato tabulado
2. ✅ **Swap SRTF con suspendidos** - Intercambio entre procesos suspendidos y en ejecución
3. ✅ **Detección de eventos** - Sistema muestra eventos importantes en cada ciclo
4. ✅ **Control de tiempo simulada** - Avance manual con Enter (no tiempo real)
5. ✅ **Informe estadístico completo** - Incluye rendimiento, promedios y resumen general

---

## FASE 1: ESTRUCTURA BASE Y LECTURA DE PROCESOS (PRIORIDAD: 1ER)

### 1.1 Programar estructura del proceso ✅ (COMPLETO)
- [x] Crear clase `Proceso` con atributos básicos
- [x] Verificar que todos los campos necesarios estén presentes
- [x] Asegurar que `tiempo_restante` se inicialice correctamente
- **Estado**: ✅ COMPLETADO

### 1.2 Programar lectura de procesos desde archivo ✅ (COMPLETO)
- [x] Implementar función `cargar_procesos_desde_archivo()`
- [x] Parsear formato CSV: `ID,Tamaño,Tiempo_Arribo,Tiempo_Irrupción`
- [x] Ignorar comentarios y líneas vacías
- [x] Ordenar procesos por tiempo de arribo
- **Estado**: ✅ COMPLETADO

### 1.3 Implementar cola de procesos Listos y Listos/Suspendidos ✅ (COMPLETO)
- [x] Cola de listos implementada con heap (min-heap para SRTF)
- [x] Lista de procesos suspendidos implementada
- [x] Verificar que las colas mantengan el orden correcto
- [x] Asegurar sincronización (proceso no puede estar en múltiples estados)
- **Estado**: ✅ COMPLETADO

---

## FASE 2: ALGORITMOS DE ASIGNACIÓN Y PLANIFICACIÓN (PRIORIDAD: 2DA y 3ER)

### 2.1 Programar algoritmo Best-Fit ✅ (COMPLETO)
- [x] Implementar `asignar_memoria()` con algoritmo Best-Fit
- [x] Excluir partición del SO (partición 0)
- [x] Seleccionar la partición más pequeña que pueda contener el proceso
- [x] Verificar que no se asignen procesos mayores a ninguna partición disponible
- **Estado**: ✅ COMPLETADO

### 2.2 Programar algoritmo SRTF básico ✅ (COMPLETO)
- [x] Implementar min-heap para cola de listos
- [x] Método `obtener_siguiente_proceso()` 
- [x] Método `verificar_apropiacion()` para SRTF
- [x] Implementar apropiación correcta cuando llega proceso más corto
- [x] Asegurar que el proceso actual se devuelva a cola antes de apropiación
- [x] Swap SRTF con procesos suspendidos implementado
- **Estado**: ✅ COMPLETADO

### 2.3 Implementar cambios de estado (Nuevo → Listo → Ejecución) ✅ (COMPLETO)
- [x] Enum `EstadoProceso` con todos los estados
- [x] Transiciones básicas implementadas
- [x] Verificar todas las transiciones de estado
- [x] Asegurar que un proceso no esté en múltiples estados simultáneamente
- **Estado**: ✅ COMPLETADO

### 2.4 Completar transiciones de estado (agregar Terminado) ✅ (COMPLETO)
- [x] Estado TERMINADO en enum
- [x] Transición a TERMINADO cuando `tiempo_restante == 0`
- [x] Liberación de memoria al terminar
- **Estado**: ✅ COMPLETADO

---

## FASE 3: CONTROL DE MULTIPROGRAMACIÓN Y SUSPENSIÓN (PRIORIDAD: 3ER y 2DA)

### 3.1 Implementar control de multiprogramación (máximo 5 procesos) ✅ (COMPLETO)
- [x] Función `calcular_grado_multiprogramacion()` implementada
- [x] Constante `max_multiprogramacion = 5`
- [x] Cuenta procesos en memoria, cola de listos, ejecución y suspendidos
- [x] Control respeta límite de 5 procesos
- **Estado**: ✅ COMPLETADO (Según aclaraciones: máximo 5 procesos totales, 3 en RAM)

### 3.2 Implementar suspensión de procesos cuando no hay memoria ✅ (COMPLETO)
- [x] Cambio de estado a `LISTO_SUSPENDIDO` cuando no hay memoria
- [x] Lista `procesos_suspendidos` para almacenar procesos fuera de RAM
- [x] Verificar que se intente admitir suspendidos cuando se libera memoria
- [x] Asegurar que la suspensión respete el grado de multiprogramación
- **Estado**: ✅ COMPLETADO

### 3.3 Implementar interrupción por SRTF cuando llega proceso más corto ✅ (COMPLETO)
- [x] Método `verificar_apropiacion()` implementado
- [x] Lógica completa de apropiación en `intentar_admitir_proceso()`
- [x] Proceso actual se devuelve correctamente a la cola
- [x] Apropiación ocurre tanto al arribo como durante ejecución
- [x] Swap SRTF con procesos suspendidos implementado
- **Estado**: ✅ COMPLETADO

---

## FASE 4: FUNCIONES DE VISUALIZACIÓN (PRIORIDAD: 2DA)

### 4.1 Crear función para mostrar tabla de particiones ✅ (COMPLETO)
- [x] Método `obtener_tabla_particiones()` implementado
- [x] Mostrar todas las particiones incluyendo la del SO
- [x] Información: ID, dirección inicio, tamaño, proceso asignado, fragmentación interna
- [x] **Formato de tabla tabulada con tabulate implementado**
- **Estado**: ✅ COMPLETADO

### 4.2 Calcular fragmentación interna por partición ✅ (COMPLETO)
- [x] Método `obtener_fragmentacion_interna()` implementado
- [x] Cálculo: `tamaño_particion - tamaño_proceso`
- [x] Retorna 0 si la partición está libre
- **Estado**: ✅ COMPLETADO

### 4.3 Crear función para mostrar estado del procesador ✅ (COMPLETO)
- [x] Mostrar proceso en ejecución o "CPU IDLE"
- [x] Mostrar tiempo restante del proceso
- [x] **Formato de tabla tabulada con tabulate implementado**
- **Estado**: ✅ COMPLETADO

### 4.4 Mostrar salidas cuando llega un nuevo proceso y cuando termina uno ✅ (COMPLETO)
- [x] Agregar mensajes informativos al arribo de nuevos procesos
- [x] Agregar mensajes informativos al terminar procesos
- [x] Mostrar estado completo del sistema en cada iteración
- [x] Asegurar que se muestre en formato de tabla tabulada
- [x] Sistema de eventos destacados implementado
- **Estado**: ✅ COMPLETADO

---

## FASE 5: ESTADÍSTICAS Y RENDIMIENTO (PRIORIDAD: 3ER)

### 5.1 Calcular tiempo de retorno, espera y promedio por proceso ✅ (COMPLETO)
- [x] Cálculo de tiempo de retorno: `tiempo_finalizacion - tiempo_arribo`
- [x] Cálculo de tiempo de espera: `tiempo_inicio - tiempo_arribo`
- [x] Cálculo de promedios
- [x] Mostrar en tabla tabulada con tabulate
- **Estado**: ✅ COMPLETADO

### 5.2 Calcular rendimiento del sistema ✅ (COMPLETO)
- [x] Implementar cálculo: `procesos_terminados / tiempo_total_simulacion`
- [x] Agregar al informe estadístico final
- [x] Unidad de medida: procesos/unidad_tiempo
- [x] Incluido en resumen general del informe
- **Estado**: ✅ COMPLETADO

---

## FASE 6: MEJORAS Y CORRECCIONES (PRIORIDAD: TODAS)

### 6.1 Mejorar formato de salidas (tablas tabuladas) ✅ (COMPLETO)
- [x] Revisar todas las salidas para usar formato de tabla tabulada
- [x] Aplicar formato consistente en:
  - Tabla de particiones
  - Estado del procesador
  - Cola de listos
  - Cola de suspendidos
  - Estadísticas finales
- [x] Usar librería `tabulate` con formato `grid` para consistencia
- **Estado**: ✅ COMPLETADO

### 6.2 Revisar sincronización de estados ✅ (COMPLETO)
- [x] Asegurar que proceso en cola de listos no pueda estar en ejecución
- [x] Validar que procesos no estén en múltiples estados simultáneamente
- [x] Revisar todas las transiciones de estado
- [x] Estados controlados correctamente en cada transición
- **Estado**: ✅ COMPLETADO

### 6.3 Revisar problemas ortográficos ✅ (COMPLETO)
- [x] Revisar todos los mensajes y salidas
- [x] Correcciones ortográficas aplicadas
- [x] Consistencia en nomenclatura mantenida
- **Estado**: ✅ COMPLETADO

### 6.4 Eliminar redundancias ✅ (COMPLETO)
- [x] Revisar código y salidas para eliminar repeticiones innecesarias
- [x] Información mostrada de forma organizada
- [x] Eventos destacados solo cuando hay cambios significativos
- **Estado**: ✅ COMPLETADO

---

## ORDEN SUGERIDO DE EJECUCIÓN

### Sprint 1: Correcciones Fundamentales
1. **Corregir grado de multiprogramación** (según aclaraciones: máximo 3 en RAM)
2. **Completar apropiación SRTF** (interrupción cuando llega proceso más corto)
3. **Validar sincronización de estados** (proceso no en múltiples estados)

### Sprint 2: Visualización y Salidas
4. **Mejorar formato de tablas** (formato tabulado consistente)
5. **Agregar salidas al arribo y finalización** de procesos
6. **Revisar y mejorar todas las funciones de visualización**

### Sprint 3: Estadísticas y Validaciones Finales
7. **Implementar cálculo de rendimiento del sistema**
8. **Revisar ortografía y eliminar redundancias**
9. **Pruebas finales con archivo `procesos.txt`**

---

## ARCHIVOS A MODIFICAR

- `simulador_memoria_procesos.py`: Archivo principal del simulador

---

## NOTAS IMPORTANTES

1. **Multiprogramación**: Según aclaraciones.md, debe ser máximo 3 procesos en RAM (Listo o Ejecutando), los otros en "Suspendido-Listo" en disco. **Necesita corrección**.

2. **Formato de Salida**: Todo debe mostrarse en formato de tabla tabulada según aclaraciones.

3. **Sincronización**: Un proceso no puede estar en múltiples estados simultáneamente (ej: en cola de listos Y en ejecución).

4. **Particiones**: Mostrar TODAS las particiones, inclusive la del SO (ya está implementado).

5. **Rendimiento**: Agregar cálculo de rendimiento al informe estadístico final.

---

## ACLARACIONES RECIBIDAS ✅

1. **Multiprogramación**: Máximo 5 procesos en total entre:
   - Procesos en memoria (en particiones)
   - Procesos en cola de listos
   - Procesos en ejecución
   - Procesos en lista de listos-suspendidos
   - Solo 3 pueden estar en RAM (Listo o Ejecutando), otros 2 en suspendido

2. **Rendimiento**: Cantidad de procesos terminados / tiempo total de simulación

3. **Salidas**: Mostrar en cada iteración de tiempo cuando haya cambios:
   - Estado del procesador (ocupado/libre y por quién)
   - Tabla de particiones (tabulada con tabulate)
   - Cuando cambia grado de multiprogramación
   - Cuando llega nuevo proceso
   - Cuando cambia cola de listos-suspendidos
   - Cuando cambia cola de listos

4. **Tablas**: Usar librería `tabulate` para formato tabulado

5. **SRTF**: Debe apropiarse inmediatamente cuando:
   - Llega un proceso más corto que el actual
   - O cuando un proceso suspendido es más corto que el actual
   - Siempre respetando grado de multiprogramación

6. **Iteraciones**: Cada iteración avanza una unidad de tiempo simulada (no tiempo real), controlado por clicks/entrada del usuario

