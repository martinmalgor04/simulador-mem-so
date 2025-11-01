##SIMULADOR DE ADMINISTRADOR DE MEMORIA##

1.1 Simular la administración en la asignación de memoria con particiones fijas de DIFERENTES tamaños
para un sistema con 3 procesos P1, P2 y P3. Se prevé asignar 150 b de memoria al núcleo del
Sistema Operativo. Los procesos tendrán los siguientes tamaños P1= 100 b, P2= 150 b, P3= 250 b.
Luego de la asignación deberá imprimirse la información contenida en una tabla de particiones. La tabla
de particiones contendrá la siguiente información (id Proceso, dirección de comienzo de la partición
asignada, tamaño de la partición).
1.2 Modificar la propuesta anterior con la posibilidad de cargar N procesos. El programa debe permitir ingresar nuevos procesos, mientras haya memoria libre para asignar, por cada proceso se debe ingresar o leer de un archivo el Id de proceso, tamaño del proceso, tiempo de arribo y tiempo de irrupción. La tabla de particiones impresa deberá contener (Id de partición, dirección de comienzo de partición, tamaño de la partición, id de proceso asignado a la partición, fragmentación interna). Mostrar la información anterior por cada proceso ingresado en la tabla de particiones.


MEMORIA DE 750B
AMBIENTE
particion = reg
    proceso : entero
    tamano : entero
fr

parts : arreglo de [1..4] de particion
aux : entero

nodo = reg //cola de procesos
    tamano : entero
    prox : esp
fr

esp : lista de nodo
prim : esp

inicio ()
    while i < 4 do
        parts[i].proceso := 0
        i := i + 1
    fw
    parts[1].proceso = 150 //sistema operativo
    parts[1].tamano = 200
    parts[2].tamano = 300
    parts[3].tamano = 150
    parts[4].tamano = 100
finpr

addproceso (entero,entero)
    Print("Ingresa el tamaño del proceso")
    read(aux)

    if addmemoria(aux) = false
        addcola(aux)
    else
        print("memoria impresa correctamente")
    fif
fp

addmemoria(aux: entero): boolean
    i := 2
    b := false

    while i < 4 do
        if parts[i].proceso = 0
            if parts[i].tamano >= aux do
                parts[i].proceso := aux
                b := true
                i := 5 //para salir
            fif
        fif
        i := i + 1
    fw

    return b
fp

addcola(aux: entero)
    if prim = null do //lista vacia
        nuevo(p)
        p.tamano := aux
        p.prox := null
        prim := p
    else
        while p.prox <> null do 
            p := p.prox
        fw 
        nuevo(a)
        a.tamano := aux
        a.prox := null
        p.prox := a
    fif
fp

fueracola()

c : entero
            
PROCESO
inicio()
c := 0

while siga do
    Print("1. Ingresar proceso 2. Limpiar Memoria 3. Ver estado memoria")
