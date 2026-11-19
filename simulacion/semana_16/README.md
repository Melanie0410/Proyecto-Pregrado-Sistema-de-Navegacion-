# Semana 16 – Integración del entorno Calatayud con Unitree G1 EDU

## 1. Descripción general

Durante la semana 16 se avanzó en la construcción y ajuste del entorno de simulación del proyecto de navegación asistida con el robot humanoide Unitree G1 EDU.

El trabajo se centró en integrar el modelo del robot con el escenario unificado del bloque Calatayud, ajustar sus dimensiones físicas, comprobar el comportamiento del movimiento y verificar la disponibilidad de odometría para los siguientes procesos de localización y navegación.

Las pruebas se realizaron en Gazebo Fortress, utilizando ROS 2 Humble.

## 2. Objetivos

- Consolidar el escenario unificado de simulación del bloque Calatayud.
- Ajustar las dimensiones y la posición del modelo del Unitree G1 EDU.
- Comprobar el desplazamiento del robot mediante comandos de velocidad.
- Verificar la publicación y continuidad de la odometría.
- Corregir problemas de colisión entre el modelo del robot y las paredes.
- Identificar los marcos de referencia necesarios para integrar el LiDAR con ROS 2.

## 3. Estructura de archivos

Los archivos desarrollados durante esta semana se encuentran organizados de la siguiente manera:

```text
simulacion/
└── semana_16/
    └── worlds/
        ├── generar_mundo_unificado.py
        ├── calcular_altura_pelvis.py
        ├── medir_dimensiones_robot.py
        └── calatayud_g1.sdf

evidencias/
└── semana_16/
    ├── 01_robot_corredor.png
    ├── 02_robot_colision_pared.png
    ├── 03_prueba_odometria.png
    ├── Screenshot from 2026-11-19 16-20-09.png
    ├── Screenshot from 2026-11-19 16-29-18.png
    └── Screenshot from 2026-11-19 16-41-19.png
```

### Descripción de los archivos

| Archivo | Función |
|---|---|
| `generar_mundo_unificado.py` | Generación del escenario unificado mediante parámetros geométricos. |
| `calcular_altura_pelvis.py` | Herramienta auxiliar para calcular la altura de la pelvis del modelo. |
| `medir_dimensiones_robot.py` | Herramienta auxiliar para medir dimensiones del robot. |
| `calatayud_g1.sdf` | Mundo SDF generado para la simulación del entorno Calatayud con el Unitree G1 EDU. |

## 4. Configuración geométrica

Para la generación del mundo se utilizaron los siguientes parámetros:

| Parámetro | Valor |
|---|---:|
| Posición vertical de referencia (`--z`) | 0,792 m |
| Radio del modelo (`--radio`) | 0,40 m |
| Altura del modelo (`--altura`) | 1,32 m |

El radio de 0,40 m se utilizó para ajustar el comportamiento de colisión del modelo, evitando que las manos atravesaran las paredes durante las pruebas.

El archivo `calatayud_g1.sdf` corresponde a la generación realizada con estos parámetros.

## 5. Pruebas realizadas

### 5.1. Generación del mundo

Se ejecutó el generador del escenario con los parámetros geométricos definidos.

**Resultado:**

- Radio: 0,40 m.
- Altura: 1,32 m.
- Validación del archivo SDF: `Valid.`

Esto permitió comprobar que el generador produjo un archivo de mundo válido con la configuración utilizada.

### 5.2. Prueba de desplazamiento

Se realizó una prueba de movimiento utilizando la tecla `i` para ordenar el avance del robot.

Se registraron los siguientes valores:

| Variable | Posición inicial | Posición final |
|---|---:|---:|
| X | 1,195 m | 1,195 m |
| Y | 1,000 m | 1,864 m |

Se observó que el desplazamiento ocurrió sobre el eje Y, mientras que la coordenada X permaneció constante.

**Conclusión:** se confirmó que la velocidad de desplazamiento se aplica en el marco propio del robot, permitiendo avanzar en la dirección hacia la que está orientado.

### 5.3. Verificación de odometría

Se evaluó la frecuencia de publicación del tópico:

```bash
ros2 topic hz /odom
```

**Resultado:**

- Frecuencia medida: aproximadamente 50 Hz.
- Periodo medio: aproximadamente 0,020 s.
- Desviación del periodo: aproximadamente 0,0002 s.

La prueba permitió verificar que la odometría se publica de manera continua y estable a la frecuencia configurada durante el ensayo.

### 5.4. Verificación de colisiones

Se realizaron pruebas de interacción entre el modelo del robot y las paredes del entorno.

Se identificó que las manos atravesaban las paredes con la configuración anterior. Después de ajustar el radio del modelo a 0,40 m, se comprobó que las manos dejaron de atravesarlas durante las pruebas realizadas.

**Conclusión:** el ajuste geométrico permitió mejorar el comportamiento de colisión del modelo rígido en el escenario simulado.

Estas pruebas no constituyen una validación de la dinámica bípeda ni del comportamiento de navegación autónoma del robot físico.

## 6. Integración preliminar del LiDAR

Se inició la verificación de la información publicada por el LiDAR virtual para preparar su integración con los procesos de percepción, mapeo y localización.

Se consultó el tópico:

```bash
ros2 topic echo /g1/lidar/points --once --field header.frame_id
```

**Resultado obtenido:**

```text
mid360_link
```

Con esto se identificó que la nube de puntos publicada en `/g1/lidar/points` utiliza el marco de referencia `mid360_link`.

También se inició la visualización mediante RViz utilizando la configuración disponible:

```bash
cd ~/navegacion-g1-github
source /opt/ros/humble/setup.bash
rviz2 -d simulacion/semana_15/rviz/g1_lidar.rviz
```

Durante esta prueba se presentó el siguiente mensaje:

```text
Message Filter dropping message:
frame 'mid360_link'
reason 'discarding message because the queue is full'
```

Este mensaje indica que RViz está descartando mensajes porque su cola se encuentra llena. La visualización y la configuración de las transformaciones entre marcos todavía requieren revisión.

Por lo tanto, la identificación del marco LiDAR se considera verificada, pero la integración completa del sensor con los procesos de localización y mapeo continúa pendiente.

## 7. Resultados consolidados

| Prueba | Resultado | Estado |
|---|---|---|
| Generación del mundo | Archivo SDF validado | Verificado |
| Ajuste geométrico | Radio de 0,40 m y altura de 1,32 m | Verificado |
| Movimiento del robot | Desplazamiento según su orientación | Verificado |
| Odometría | Publicación estable a 50 Hz | Verificado |
| Colisiones | Las manos dejaron de atravesar las paredes | Verificado |
| Identificación del marco LiDAR | `mid360_link` | Verificado |
| Visualización LiDAR en RViz | Mensajes descartados por cola llena | Requiere revisión |
| Integración TF y escaneo 2D | Sin validación completa | Pendiente |

## 8. Aspectos pendientes

Para continuar con el desarrollo se identifican las siguientes actividades:

1. Revisar las transformaciones TF entre los marcos del robot y el sensor LiDAR.
2. Corregir la configuración de visualización del LiDAR en RViz.
3. Verificar la relación entre `mid360_link`, `base_link` y los demás marcos disponibles.
4. Evaluar la conversión de la nube de puntos 3D a un escaneo 2D mediante `PointCloudToLaserScan`, si resulta adecuada para el sensor y la aplicación.
5. Preparar la integración del sensor con `slam_toolbox` y los componentes de localización de Nav2.
6. Revisar el comportamiento del robot en la zona de escaleras, donde se han identificado problemas de estabilidad.
7. Documentar el origen y la licencia de los recursos del modelo `g1_description`.
8. Continuar con las pruebas de localización y construcción del mapa.

## 9. Evidencias de simulación

A continuación, se presentan las evidencias gráficas correspondientes a las pruebas realizadas durante la semana 16.

### 9.1. Evidencias del entorno y las pruebas

**Figura 1. Evidencia del entorno de simulación.**

![Evidencia del entorno](../../../evidencias/semana_16/Screenshot%20from%202026-11-19%2016-20-09.png)

**Figura 2. Evidencia complementaria del escenario.**

![Evidencia complementaria](../../../evidencias/semana_16/Screenshot%20from%202026-11-19%2016-29-18.png)

**Figura 3. Evidencia complementaria de las pruebas.**

![Evidencia de pruebas](../../../evidencias/semana_16/Screenshot%20from%202026-11-19%2016-41-19.png)

### 9.2. Pruebas principales

**Figura 4. Modelo Unitree G1 EDU en el corredor.**

![Robot en corredor](../../../evidencias/semana_16/01_robot_corredor.png)

**Figura 5. Verificación de colisiones entre el robot y las paredes.**

![Prueba de colisiones](../../../evidencias/semana_16/02_robot_colision_pared.png)

**Figura 6. Verificación de la publicación de odometría.**

![Prueba de odometría](../../../evidencias/semana_16/03_prueba_odometria.png)
## 10. Conclusión

Durante la semana 16 se consolidó un escenario unificado de simulación del bloque Calatayud con el modelo del Unitree G1 EDU. Se realizaron ajustes geométricos y pruebas preliminares que permitieron verificar la generación del mundo, el desplazamiento del modelo, el comportamiento de colisión con las paredes y la publicación estable de odometría a 50 Hz.

Adicionalmente, se identificó el marco de referencia asociado a la nube de puntos del LiDAR virtual, estableciendo un punto de partida para su integración con los procesos de percepción y localización.

Los resultados obtenidos corresponden a pruebas del modelo en simulación. La integración completa del LiDAR, las transformaciones TF, el mapeo y la navegación autónoma continúan como actividades de desarrollo.
