# Guía maestra de navegación de FV Engine

## 1. Para qué sirve esta guía

FV Engine contiene 143 archivos y 612 funciones o métodos. Esta guía no intenta documentar cada línea. Su propósito es responder rápidamente:

- dónde comienza cada proceso;
- qué archivo coordina y cuál calcula;
- dónde modificar una regla concreta;
- qué archivos son contratos centrales;
- qué módulos parecen rutas alternativas y requieren auditoría;
- qué partes no deben eliminarse solo porque el analizador no detecte llamadas.

La guía está basada en `arquitectura_detallada.json`. El análisis es estático: callbacks, aliases, funciones almacenadas en listas y llamadas dinámicas pueden no quedar resueltos completamente.

## 2. Mapa general del sistema

```text
app.py
  -> ui.router / pasos del wizard
  -> UI captura datos
  -> core.aplicacion.orquestador_estudio.ejecutar_estudio()
       -> sizing
       -> builder_paneles
       -> paneles / strings / MPPT
       -> energía
       -> optimización FV
       -> electricidad
       -> finanzas
       -> layout preliminar
  -> ui.resultados
       -> generación de imágenes
       -> generación del PDF
```

La regla mental más útil es:

| Capa | Responsabilidad |
|---|---|
| `ui/` | Captura información, muestra resultados y dispara procesos |
| `core/aplicacion/` | Coordina el caso de uso completo y adapta datos |
| `core/dominio/` | Contratos y modelos compartidos |
| `core/servicios/` | Dimensionamiento, optimización y finanzas |
| `electrical/paneles/` | Cantidad de módulos, strings y uso de MPPT |
| `electrical/inversor/` | Selección y comparación de inversores |
| `electrical/conductores/` | Corrientes, conductores y caída de tensión |
| `electrical/protecciones/` | Protecciones eléctricas |
| `energy/` | Recurso solar, producción, pérdidas y batería |
| `reportes/` | Presentación de resultados ya calculados |

## 3. Recorrido principal de una evaluación

### Paso 1: arranque y navegación

- Entrada: `app.py: main()`.
- Construye los pasos mediante `ui.router`.
- Las pantallas principales son `ui.datos_cliente`, `ui.consumo_energetico`, `ui.sistema_fv`, `ui.seleccion_equipos`, `ui.ingenieria_electrica` y `ui.resultados`.

### Paso 2: construcción del proyecto

- `core/aplicacion/datos_proyecto.py` traduce el estado de la interfaz al modelo `Datosproyecto`.
- `core/dominio/modelo.py` contiene el contrato central de entrada.
- `core/aplicacion/builder_paneles.py` convierte la configuración del usuario en `EntradaPaneles` y resuelve panel e inversor desde catálogo.

### Paso 3: coordinación del estudio

- Centro del pipeline: `core/aplicacion/orquestador_estudio.py: ejecutar_estudio()`.
- Ejecuta sizing, paneles, energía, optimización, electricidad, finanzas y layout.
- `core/aplicacion/dependencias.py` conecta los adaptadores con las implementaciones reales.

### Paso 4: paneles, strings e inversores

- `electrical/paneles/orquestador_paneles.py: ejecutar_paneles()` es el coordinador vigente del cálculo de paneles.
- Llama directamente a:
  - `dimensionado_paneles.py: dimensionar_paneles()`;
  - `calculo_de_strings.py: calcular_strings_fv()`;
  - `validacion_strings.py`;
  - modelos de `entrada_panel.py` y `resultado_paneles.py`.
- `electrical/inversor/orquestador_inversor.py` genera comparativas, configuraciones mixtas y la opción recomendada.

### Paso 5: producción energética

- `energy/orquestador_energia.py: ejecutar_energia()` coordina clima, POA, temperatura, potencia del panel, string, arreglo, pérdidas DC, inversor y pérdidas AC.
- Es el módulo con más dependencias salientes; cualquier refactor aquí debe hacerse con pruebas energéticas antes y después.

### Paso 6: ingeniería eléctrica

- `electrical/orquestador_electrical.py: ejecutar_electrical()` coordina:
  - validación del sistema;
  - corrientes;
  - conductores;
  - caída de tensión;
  - protecciones;
  - construcción de `ResultadoElectrico`.

### Paso 7: finanzas

- `core/servicios/finanzas.py: ejecutar_finanzas()` calcula CAPEX, cuota, O&M, evaluación mensual, TIR y escenarios de batería.
- Este archivo es grande y sensible. Conviene modificar funciones pequeñas, no reescribirlo completo sin pruebas de regresión.

### Paso 8: resultados y PDF

- `ui/resultados.py` dispara `generar_artefactos()` y `generar_pdf_profesional()`.
- `reportes/generar_pdf_profesional.py` arma el documento a partir de bloques.
- `reportes/bloques/ingenieria_electrica.py` controla la mayor parte del informe técnico.
- `reportes/secciones_tecnicas/` contiene tablas y conclusiones específicas.

## 4. Dónde cambiar cada cosa

| Quiero cambiar... | Comenzar en | Revisar también |
|---|---|---|
| Datos capturados del cliente | `ui/datos_cliente.py` | `core/aplicacion/datos_proyecto.py`, `core/dominio/modelo.py` |
| Perfil o consumo energético | `ui/consumo_energetico.py` | `core/servicios/consumo.py`, `energy/` |
| Modos de dimensionamiento FV | `ui/sistema_fv.py` | `core/servicios/sizing.py`, `core/aplicacion/builder_paneles.py` |
| Cantidad de paneles | `electrical/paneles/dimensionado_paneles.py` | `orquestador_paneles.py`, `resultado_paneles.py` |
| Longitud o distribución de strings | `electrical/paneles/calculo_de_strings.py` | `orquestador_paneles.py`, `validacion_strings.py` |
| Distribución de MPPT | `electrical/paneles/calculo_de_strings.py` | `mppt_global.py`, `resultado_paneles.py` |
| Selección automática de inversor | `electrical/inversor/orquestador_inversor.py` | catálogo YAML, `builder_paneles.py` |
| Rango DC/AC y criterio de selección | `electrical/inversor/orquestador_inversor.py` | UI de equipos y comparativa PDF |
| Parámetros de panel o inversor | catálogo YAML correspondiente | `electrical/modelos/paneles.py`, `electrical/modelos/inversor.py` |
| Producción anual | `energy/orquestador_energia.py` | clima, solar, modelo térmico, pérdidas e inversor |
| Batería | `energy/baterias/` | `core/servicios/finanzas.py`, bloque PDF de batería |
| Corriente DC o AC | `electrical/conductores/corrientes.py` | `orquestador_electrical.py`, tabla NEC |
| Calibre de conductor | `electrical/conductores/calculo_conductores.py` | tablas, factores NEC y caída de voltaje |
| Protección | `electrical/protecciones/protecciones.py` | resultados de protecciones y tabla NEC |
| Tabla NEC del PDF | `reportes/secciones_tecnicas/tabla_nec.py` | resultado eléctrico de origen |
| Resumen técnico del PDF | `reportes/secciones_tecnicas/resumen_tecnico.py` | `reportes/bloques/ingenieria_electrica.py` |
| Conclusiones ejecutivas | `reportes/secciones_tecnicas/conclusiones.py` | resumen ejecutivo y finanzas |
| Portada/resumen ejecutivo | `reportes/bloques/resumen_ejecutivo.py` | `pdf_utils.py`, `styles.py` |
| Cortes y orden de páginas | bloque correspondiente en `reportes/bloques/` | `generar_pdf_profesional.py` |
| Gráficos | `reportes/generar_charts.py` | `reportes/imagenes.py` |
| Layout de módulos | `reportes/generar_layout_paneles.py` | sección técnica de layout |

## 5. Archivos centrales: modificar con precaución

Estos contratos tienen varias dependencias entrantes. Un cambio puede romper muchas capas:

- `core/dominio/modelo.py`;
- `core/dominio/contrato.py`;
- `electrical/paneles/entrada_panel.py`;
- `electrical/paneles/resultado_paneles.py`;
- `electrical/modelos/paneles.py`;
- `electrical/modelos/inversor.py`;
- `energy/resultado_energia.py`;
- `electrical/resultado_electrical.py`.

Antes de renombrar un campo en ellos:

1. buscar todas sus referencias;
2. mantener compatibilidad temporal si el PDF o la UI todavía usa el nombre anterior;
3. ejecutar un caso conocido;
4. comparar potencia, paneles, strings, energía, corriente, CAPEX y PDF.

## 6. Auditoría especial de `electrical/paneles`

El flujo principal confirmado es:

```text
orquestador_paneles.py
  -> dimensionado_paneles.py
  -> calculo_de_strings.py
  -> validacion_strings.py
  -> resultado_paneles.py
```

Los siguientes módulos no aparecen como dependencias directas del orquestador principal y deben revisarse antes de seguir modificándolos:

- `string_auto.py`;
- `strings_global.py`;
- `mppt_global.py`;
- `consolidacion_string.py`;
- `adapter_multizona.py`.

No deben borrarse todavía. Pueden pertenecer al flujo multizona o ser una generación anterior. Para clasificarlos hay que buscar quién importa cada función y ejecutar pruebas normal/multizona.

### Clasificación provisional

| Archivo | Clasificación provisional |
|---|---|
| `orquestador_paneles.py` | Coordinador vigente |
| `calculo_de_strings.py` | Motor vigente de strings |
| `dimensionado_paneles.py` | Motor vigente de cantidad de paneles |
| `validacion_strings.py` | Validación vigente |
| `entrada_panel.py` | Contrato central de entrada |
| `resultado_paneles.py` | Contrato central de salida |
| `adapter_multizona.py` | Adaptador especializado; conservar |
| `strings_global.py` | Especializado/multizona; auditar |
| `mppt_global.py` | Especializado/multizona; auditar |
| `consolidacion_string.py` | Posible consolidación anterior o multizona; auditar |
| `string_auto.py` | Posible motor alternativo anterior; auditar primero |

## 7. Hallazgos del analizador que no implican errores inmediatos

### Ciclos

Los ciclos `electrical.canalizacion -> electrical.canalizacion` y `electrical.catalogos -> electrical.catalogos` son probablemente falsos positivos producidos por paquetes y módulos homónimos. No justifican una refactorización.

### Violación entre energía y catálogo eléctrico

`energy.orquestador_energia` importa `electrical.catalogos.catalogos`. Es una dependencia arquitectónica discutible, pero funcionalmente comprensible porque energía necesita datos del panel. No moverla hasta definir un contrato compartido estable.

### Posibles funciones no llamadas

No borrar funciones usando solo esa lista. Contiene puntos de entrada, propiedades, callbacks y funciones llamadas dinámicamente. Cada candidato necesita búsqueda textual, búsqueda de imports y prueba de ejecución.

## 8. Reglas para continuar sin romper avances

1. No hacer refactorizaciones masivas mientras se corrige una falla funcional.
2. Cambiar primero el módulo dueño del cálculo, no la tabla PDF.
3. El PDF presenta resultados; no debe recalcular ingeniería.
4. Mantener nombres de campos existentes hasta actualizar todos los consumidores.
5. No borrar rutas alternativas sin probar modo normal y multizona.
6. Crear un caso de regresión estable con datos conocidos.
7. Comparar antes/después al menos:
   - kWp DC;
   - kW AC y DC/AC;
   - número de módulos;
   - strings y MPPT;
   - producción anual;
   - cobertura;
   - corrientes y calibres;
   - CAPEX, ahorro y retorno;
   - páginas y tablas del PDF.
8. Hacer commits pequeños por problema resuelto.

## 9. Orden recomendado para estabilizar el proyecto

1. Congelar temporalmente las refactorizaciones estructurales.
2. Corregir las inconsistencias técnicas detectadas en el PDF.
3. Crear casos de regresión para paneles/strings, energía, eléctrico y finanzas.
4. Auditar `electrical/paneles` y clasificar las rutas alternativas.
5. Auditar dependencias entre `energy` y `electrical`.
6. Mejorar el analizador para resolver imports por símbolo y falsos ciclos de paquetes.
7. Solo después consolidar o retirar archivos duplicados.

## 10. Ruta rápida para el problema actual del informe

Para las correcciones ya identificadas:

| Corrección | Archivo inicial |
|---|---|
| Compatibilidad fase/tensión del inversor | `electrical/modelos/inversor.py` y catálogo YAML |
| Corriente `Imp` frente a `Isc` | `electrical/conductores/corrientes.py` |
| Conductor MPPT #14 frente a #10 | `electrical/conductores/calculo_conductores.py` |
| Presentación NEC consistente | `reportes/secciones_tecnicas/tabla_nec.py` |
| Cobertura solicitada frente a recomendada | `reportes/bloques/resumen_ejecutivo.py` y `conclusiones.py` |
| Batería recomendada de 0 kWh | `reportes/bloques/ingenieria_electrica.py` |
| Cortes de tablas entre páginas | bloques y secciones correspondientes de `reportes/` |

La corrección debe comenzar en el cálculo o contrato propietario y terminar en la presentación. Nunca debe corregirse una inconsistencia técnica únicamente ocultándola en el PDF.
