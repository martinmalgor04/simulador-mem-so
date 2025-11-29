echo "Generando todos los archivos de auditoría..."
echo ""

./generar_info_sistema.sh
./generar_listado_procesos.sh
./generar_usuarios_nomina.sh
./generar_grupos_nomina.sh
./generar_usuarios_logueados.sh
./generar_usuarios_fallos.sh
./generar_listado_permisos.sh

echo ""
echo "Todos los archivos generados. Verificando permisos..."
ls -l

echo ""
echo "¡Análisis de auditoría completado!"