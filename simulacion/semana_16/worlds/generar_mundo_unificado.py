#!/usr/bin/env python3
"""Genera el mundo unificado: edificio Calatayud + Unitree G1 rigido con LiDAR.

Lee, sin modificarlos, los archivos de la semana 15 y escribe un mundo nuevo
en simulacion/semana_16/worlds/. El robot se simplifica segun el alcance del
anteproyecto: articulaciones fijas, colision cilindrica y movimiento por
velocidad (sin dinamica de marcha biped).

Uso (desde la raiz del repositorio):
    python3 simulacion/semana_16/worlds/generar_mundo_unificado.py
"""
import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

S15 = Path(__file__).resolve().parents[2] / "semana_15" / "worlds"
S16 = Path(__file__).resolve().parent

BARRA_JUEGO = """<plugin filename="WorldControl" name="World control">
  <ignition-gui>
    <title>World control</title>
    <property type="bool" key="showTitleBar">false</property>
    <property type="bool" key="resizable">false</property>
    <property type="double" key="height">72</property>
    <property type="double" key="width">121</property>
    <property type="double" key="z">1</property>
    <property type="string" key="state">floating</property>
    <anchors target="3D View">
      <line own="left" target="left"/>
      <line own="bottom" target="bottom"/>
    </anchors>
  </ignition-gui>
  <play_pause>true</play_pause>
  <step>true</step>
  <start_paused>true</start_paused>
</plugin>"""

BARRA_ESTADO = """<plugin filename="WorldStats" name="World stats">
  <ignition-gui>
    <title>World stats</title>
    <property type="bool" key="showTitleBar">false</property>
    <property type="bool" key="resizable">false</property>
    <property type="double" key="height">110</property>
    <property type="double" key="width">290</property>
    <property type="double" key="z">1</property>
    <property type="string" key="state">floating</property>
    <anchors target="3D View">
      <line own="right" target="right"/>
      <line own="bottom" target="bottom"/>
    </anchors>
  </ignition-gui>
  <sim_time>true</sim_time>
  <real_time>true</real_time>
  <real_time_factor>true</real_time_factor>
  <iterations>true</iterations>
</plugin>"""


def leer(ruta):
    parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
    return ET.parse(str(ruta), parser=parser)


def texto(padre, etiqueta, valor):
    """Crea <etiqueta>valor</etiqueta> dentro de padre y lo devuelve."""
    nodo = ET.SubElement(padre, etiqueta)
    nodo.text = str(valor)
    return nodo


def quitar(padre, etiqueta):
    n = 0
    for hijo in padre.findall(etiqueta):
        padre.remove(hijo)
        n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--robot", default=str(S15 / "g1_lidar.sdf"))
    ap.add_argument("--edificio", default=str(S15 / "edificio_calatayud.sdf"))
    ap.add_argument("--salida", default=str(S16 / "calatayud_g1.sdf"))
    ap.add_argument("--modelo-origen", default="g1_29dof_rev_1_0")
    ap.add_argument("--nombre", default="g1", help="nombre del modelo en el mundo")
    ap.add_argument("--x", type=float, default=1.195, help="posicion inicial x (m)")
    ap.add_argument("--y", type=float, default=1.0, help="posicion inicial y (m)")
    ap.add_argument("--yaw", type=float, default=90.0, help="orientacion inicial (grados)")
    ap.add_argument("--z", type=float, default=None,
                    help="altura de la pelvis sobre el piso (m); provisional si no se da")
    ap.add_argument("--altura", type=float, default=1.3, help="altura de la colision (m)")
    ap.add_argument("--radio", type=float, default=0.25, help="radio de la colision (m)")
    ap.add_argument("--holgura", type=float, default=0.02, help="separacion colision-piso (m)")
    a = ap.parse_args()

    # --- Lectura -----------------------------------------------------------
    mundo_r = leer(a.robot).getroot().find("world")
    arbol_e = leer(a.edificio)
    mundo_e = arbol_e.getroot().find("world")
    if mundo_r is None or mundo_e is None:
        sys.exit("ERROR: no se encontro <world> en alguno de los archivos.")

    modelo = None
    for m in mundo_r.findall("model"):
        if m.get("name") == a.modelo_origen:
            modelo = m
    if modelo is None:
        sys.exit(f"ERROR: no existe el modelo '{a.modelo_origen}' en {a.robot}")
    if any(m.get("name") == a.nombre for m in mundo_e.findall("model")):
        sys.exit(f"ERROR: el edificio ya tiene un modelo llamado '{a.nombre}'.")

    print(f"Mundo del edificio : {mundo_e.get('name')}")
    print(f"Modelo del robot   : {a.modelo_origen} -> '{a.nombre}'")

    # --- Pose inicial ------------------------------------------------------
    pose_vieja = modelo.find("pose")
    z = a.z
    if z is None and pose_vieja is not None and pose_vieja.text:
        z = float(pose_vieja.text.split()[2])
        print(f"z tomada de la pose original del modelo: {z}")
    if z is None:
        z = 0.80
        print("AVISO: z = 0.80 m es PROVISIONAL. Calibrar viendo en Gazebo que "
              "los pies toquen el piso y repetir con --z.")
    print(f"Pose original      : {pose_vieja.text.strip() if pose_vieja is not None else 'ninguna'}")
    quitar(modelo, "pose")
    modelo.set("name", a.nombre)
    pose = ET.Element("pose")
    pose.text = f"{a.x} {a.y} {z} 0 0 {a.yaw * 3.141592653589793 / 180:.6f}"
    modelo.insert(0, pose)

    # --- Robot rigido ------------------------------------------------------
    quitar(modelo, "static")
    texto(modelo, "static", "false")

    n_art = 0
    for j in modelo.findall("joint"):
        j.set("type", "fixed")
        for etq in ("axis", "axis2", "physics", "sensor"):
            quitar(j, etq)
        n_art += 1

    enlaces = modelo.findall("link")
    n_col = 0
    for e in enlaces:
        n_col += quitar(e, "collision")
        quitar(e, "gravity")
        texto(e, "gravity", "false")

    raiz = enlaces[0]
    centro_z = a.altura / 2 + a.holgura - z
    col = ET.SubElement(raiz, "collision", name="colision_envolvente")
    texto(col, "pose", f"0 0 {centro_z:.4f} 0 0 0")
    geo = ET.SubElement(col, "geometry")
    cil = ET.SubElement(geo, "cylinder")
    texto(cil, "radius", a.radio)
    texto(cil, "length", a.altura)
    surf = ET.SubElement(col, "surface")
    fric = ET.SubElement(ET.SubElement(surf, "friction"), "ode")
    texto(fric, "mu", 0.0)
    texto(fric, "mu2", 0.0)

    # --- LiDAR -------------------------------------------------------------
    sensores = [s for s in modelo.iter("sensor") if s.get("type") == "gpu_lidar"]
    for s in sensores:
        quitar(s, "ignition_frame_id")
        texto(s, "ignition_frame_id", "mid360_link")

    # --- Plugins de movimiento y odometria ---------------------------------
    ET.SubElement(modelo, "plugin",
                  filename="ignition-gazebo-velocity-control-system",
                  name="ignition::gazebo::systems::VelocityControl")
    odo = ET.SubElement(modelo, "plugin",
                        filename="ignition-gazebo-odometry-publisher-system",
                        name="ignition::gazebo::systems::OdometryPublisher")
    texto(odo, "odom_frame", "odom")
    texto(odo, "robot_base_frame", "base_link")
    texto(odo, "odom_publish_frequency", 50)
    texto(odo, "dimensions", 2)

    # --- Ensamblado --------------------------------------------------------
    mundo_e.set("name", "calatayud_g1")
    mundo_e.append(modelo)
    if mundo_e.find("light") is None and mundo_r.find("light") is not None:
        mundo_e.append(mundo_r.find("light"))
        print("Se copio la luz del archivo del robot (el edificio no tenia).")
    for p in mundo_e.findall("plugin"):
        if p.get("name", "").endswith("Sensors") and p.find("render_engine") is None:
            texto(p, "render_engine", "ogre2")
            print("Se agrego render_engine=ogre2 al plugin de sensores.")

    gui = mundo_e.find("gui")
    if gui is not None and not any(p.get("filename") == "WorldControl" for p in gui.findall("plugin")):
        for xml in (BARRA_JUEGO, BARRA_ESTADO):
            gui.append(ET.fromstring(xml))
        print("Se agregaron los plugins de la GUI: boton Play/Pausa y estadisticas.")

    ET.indent(arbol_e, space="  ")
    salida = Path(a.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    arbol_e.write(str(salida), encoding="utf-8", xml_declaration=True)

    print("--- Resumen ---")
    print(f"Articulaciones convertidas a fijas : {n_art}")
    print(f"Colisiones originales eliminadas   : {n_col}")
    print(f"Colision nueva (cilindro)          : radio {a.radio} m, altura {a.altura} m")
    print(f"Enlace raiz                        : {raiz.get('name')}")
    print(f"Sensores LiDAR encontrados         : {len(sensores)}")
    print(f"Pose inicial (x y z yaw)           : {a.x} {a.y} {z} {a.yaw} grados")
    print(f"Archivo generado                   : {salida}")


if __name__ == "__main__":
    main()
