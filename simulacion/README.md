# Simulación preliminar del pasillo

Prueba del 4 de noviembre de 2026 con ROS 2 Humble y Gazebo Fortress 6.18.0.
El escenario tiene un LiDAR simulado fijo. Se comprobó que la nube de
puntos llega a ROS 2 y se visualiza en RViz.

Ejecutar desde la raíz del repositorio, en tres terminales separadas.

## Terminal 1 — Gazebo

```bash
ign gazebo --force-version 6 simulacion/worlds/pasillo_lidar.sdf
```

Pulsa ▶ en Gazebo para iniciar la simulación.

## Terminal 2 — Puente del LiDAR

```bash
source /opt/ros/humble/setup.bash
ros2 run ros_gz_bridge parameter_bridge \
  '/lidar/points@sensor_msgs/msg/PointCloud2[ignition.msgs.PointCloudPacked'
```

## Terminal 3 — RViz

```bash
source /opt/ros/humble/setup.bash
rviz2 -d simulacion/rviz/pasillo_lidar.rviz
```

En RViz, la visualización PointCloud2 usa el tópico `/lidar/points`.
La prueba del reloj `/clock` se realizó por separado. Quedan pendientes
las transformaciones TF, el movimiento, la odometría y el mapeo.
