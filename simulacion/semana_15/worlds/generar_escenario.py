"""Genera el escenario de Gazebo. Posiciones y medidas en metros, giros en radianes."""

import argparse
from pathlib import Path
import re
import xml.etree.ElementTree as ET


PISO = "0.55 0.52 0.47 1"
MURO = "0.80 0.78 0.72 1"
LADRILLO = "0.60 0.30 0.20 1"
METAL = "0.24 0.25 0.27 1"
PUERTA = "0.35 0.45 0.55 1"
PELDANO = "0.50 0.46 0.42 1"


def caja(enlace, nombre, medidas, color, pose=None):
    for tipo in ("collision", "visual"):
        identificador = f"{nombre}_{tipo}" if nombre else tipo
        pieza = ET.SubElement(enlace, tipo, name=identificador)
        if pose is not None:
            ET.SubElement(pieza, "pose").text = " ".join(map(str, pose))
        geometria = ET.SubElement(pieza, "geometry")
        ET.SubElement(ET.SubElement(geometria, "box"), "size").text = " ".join(map(str, medidas))
        if tipo == "visual":
            material = ET.SubElement(pieza, "material")
            ET.SubElement(material, "ambient").text = color
            ET.SubElement(material, "diffuse").text = color


def modelo(mundo, nombre, pose=None):
    pieza = ET.SubElement(mundo, "model", name=nombre)
    ET.SubElement(pieza, "static").text = "true"
    if pose is not None:
        ET.SubElement(pieza, "pose").text = " ".join(map(str, pose))
    return ET.SubElement(pieza, "link", name="link")


def piezas(mundo, nombre, pose, cajas):
    enlace = modelo(mundo, nombre, pose)
    for datos in cajas:
        caja(enlace, *datos)


def baranda(mundo, nombre, pose, eje, centro, largo, postes):
    enlace = modelo(mundo, nombre, pose)
    x, y = centro
    for pieza, grosor, alto, z, color in (
        ("murete", .13, .5, .25, LADRILLO),
        ("barra_1", .03, .02, .653333, METAL),
        ("barra_2", .03, .02, .816667, METAL),
        ("pasamanos", .05, .03, .985, METAL),
    ):
        ancho, fondo = (largo, grosor) if eje == "x" else (grosor, largo)
        caja(enlace, pieza, (ancho, fondo, alto), color, (x, y, z, 0, 0, 0))
    for numero, posicion in enumerate(postes, 1):
        px, py = (posicion, y) if eje == "x" else (x, posicion)
        caja(enlace, f"poste_{numero}", (.04, .04, .5), METAL, (px, py, .75, 0, 0, 0))


def escalera_lateral(mundo, nombre, pose, ancho, primer_z, incremento):
    enlace = modelo(mundo, nombre, pose)
    for i in range(5):
        x = round(.12 + i * .24, 6)
        z = round(primer_z + i * incremento, 6)
        caja(enlace, f"peldano_{i + 1}", (.24, ancho, .05), METAL, (x, 0, z, 0, 0, 0))


def escalera_en_u(mundo, nombre):
    enlace = modelo(mundo, nombre)
    huella, contrahuella = .532, .18
    for i in range(5):
        y = round(27.356 + i * huella, 6)
        z_izq = round(-.27 - i * contrahuella, 6)
        z_der = round(-1.89 + i * contrahuella, 6)
        caja(enlace, f"bajada_{i + 1:02d}", (1.02, huella, contrahuella), PELDANO,
             (.58, y, z_izq, 0, 0, 0))
        caja(enlace, f"bajada_tramo_2_{5 - i:02d}", (1.53, huella, contrahuella), PELDANO,
             (1.855, y, z_der, 0, 0, 0))
    caja(enlace, "descanso", (2.55, 1.02, contrahuella), PELDANO,
         (1.345, 30.26, -.99, 0, 0, 0))


def crear_mundo():
    raiz = ET.Element("sdf", version="1.9")
    raiz.append(ET.Comment(" Generado por generar_escenario.py "))
    mundo = ET.SubElement(raiz, "world", name="tramo_superior")
    configuracion = ET.fromstring("""
<configuracion>
  <plugin filename="ignition-gazebo-physics-system" name="ignition::gazebo::systems::Physics" />
  <plugin filename="ignition-gazebo-user-commands-system" name="ignition::gazebo::systems::UserCommands" />
  <plugin filename="ignition-gazebo-scene-broadcaster-system" name="ignition::gazebo::systems::SceneBroadcaster" />
  <plugin filename="ignition-gazebo-sensors-system" name="ignition::gazebo::systems::Sensors">
    <render_engine>ogre2</render_engine>
  </plugin>
  <light name="sol" type="directional">
    <pose>0 0 10 0 0 0</pose>
    <diffuse>0.8 0.8 0.8 1</diffuse>
    <specular>0.2 0.2 0.2 1</specular>
    <direction>-0.5 0.1 -0.9</direction>
  </light>
  <gui fullscreen="0">
    <plugin filename="MinimalScene" name="3D View">
      <gz-gui>
        <title>3D View</title>
        <property type="bool" key="showTitleBar">false</property>
        <property type="string" key="state">docked</property>
      </gz-gui>
      <engine>ogre2</engine>
      <scene>scene</scene>
      <ambient_light>0.4 0.4 0.4</ambient_light>
      <background_color>0.8 0.8 0.8</background_color>
      <camera_pose>6 -5 6 0 0.55 2.18</camera_pose>
      <camera_clip>
        <near>0.05</near>
        <far>100</far>
      </camera_clip>
    </plugin>
    <plugin filename="GzSceneManager" name="Scene Manager" />
    <plugin filename="InteractiveViewControl" name="View control" />
    <plugin filename="EntityTree" name="Entity tree" />
    <plugin filename="ComponentInspector" name="Component inspector" />
    <plugin filename="SelectEntities" name="Select entities">
      <gz-gui>
        <property type="string" key="state">floating</property>
        <property type="bool" key="showTitleBar">false</property>
        <property type="double" key="width">5</property>
        <property type="double" key="height">5</property>
      </gz-gui>
    </plugin>
  </gui>
</configuracion>
""")
    mundo.extend(n for n in configuracion if n.tag != "gui")

    mundo.append(ET.Comment(" Piso "))
    suelo = modelo(mundo, "suelo", (0, 0, 0, 0, 0, 0))
    for nombre, x, y, ancho, largo in (
        ("piso_reajustado_01", 1.195, 0.585, 2.95, 1.73),
        ("piso_reajustado_02", 1.12, 1.925, 2.8, 0.95),
        ("base_exterior_columna_1", 2.815, 2.54, 0.29, 0.28),
        ("piso_reajustado_03", 1.195, 2.54, 2.95, 0.28),
        ("piso_reajustado_04", 1.12, 3.195, 2.8, 1.03),
        ("base_exterior_columna_2", 2.815, 3.85, 0.29, 0.28),
        ("piso_reajustado_05", 1.195, 3.85, 2.95, 0.28),
        ("piso_reajustado_06", 1.12, 4.505, 2.8, 1.03),
        ("piso_reajustado_07", 1.195, 5.09, 2.95, 0.14),
        ("base_exterior_columna_3", 2.815, 5.16, 0.29, 0.28),
        ("piso_reajustado_08", 0.695, 5.23, 3.95, 0.14),
        ("piso_reajustado_09", 0.62, 5.82, 3.8, 1.04),
        ("piso_reajustado_10", 0.695, 7.795, 3.95, 2.91),
        ("piso_reajustado_11", 0.62, 9.76, 3.8, 1.02),
        ("piso_reajustado_12", 1.095, 10.29, 2.85, 0.04),
        ("base_exterior_columna_4", 2.815, 10.45, 0.29, 0.28),
        ("piso_reajustado_13", 1.17, 10.45, 3, 0.28),
        ("piso_reajustado_14", 1.095, 11.105, 2.85, 1.03),
        ("base_exterior_columna_5", 2.815, 11.76, 0.29, 0.28),
        ("piso_reajustado_15", 1.17, 11.76, 3, 0.28),
        ("piso_reajustado_16", 1.095, 12.41, 2.85, 1.02),
        ("base_exterior_columna_6", 2.815, 13.06, 0.29, 0.28),
        ("piso_reajustado_17", 1.17, 13.06, 3, 0.28),
        ("piso_reajustado_18", 1.095, 13.72, 2.85, 1.04),
        ("base_exterior_columna_7", 2.815, 14.38, 0.29, 0.28),
        ("piso_reajustado_19", 1.17, 14.38, 3, 0.28),
        ("piso_reajustado_20", 1.095, 15.055, 2.85, 1.07),
        ("acceso_ascensor", 2.815, 16.385, 0.29, 1.59),
        ("piso_reajustado_21", 1.17, 16.385, 3, 1.59),
        ("piso_reajustado_22", 1.095, 17.705, 2.85, 1.05),
        ("piso_reajustado_23", 1.17, 19.745, 3, 3.03),
        ("base_refuerzo_escaleras", 2.815, 21.12, 0.29, 0.28),
        ("piso_previo_escalera_subida", 2.67, 22.425, 0.56, 2.33),
        ("piso_reajustado_24", 1.03, 22.615, 2.72, 2.71),
        ("base_columna_escaleras", 2.675, 23.715, 0.57, 0.25),
        ("piso_union_zona_inferior", -3.115, 23.83, 5.57, 0.28),
        ("piso_previo_escalera_bajada", 2.67, 24.7, 0.56, 1.72),
        ("piso_reajustado_25", 1.17, 24.765, 2.44, 1.59),
        ("piso_reajustado_26_escalera_3", 1.285, 26.325, 2.67, 1.53),
        ("piso_zona_inferior", -2.9, 27.37, 5.7, 6.8),
        ("piso_reajustado_26_escalera_2", 4.2, 28.14, 3.16, 5.16),
        ("piso_reajustado_27_escalera_2", 3.955, 30.745, 2.67, 0.05),
        ("piso_reajustado_28", 4.02, 30.835, 2.54, 0.13),
        ("piso_bajo_transversal_fondo", -2.975, 30.91, 5.85, 0.28),
    ):
        caja(suelo, nombre, (ancho, largo, .1), PISO, (x, y, -.05, 0, 0, 0))

    mundo.append(ET.Comment(" Entrada y corredor izquierdo "))
    caja(modelo(mundo, "muro_entrada_transversal", (1.195, -0.14, 1.6, 0, 0, 0)), "",
         (2.95, 0.28, 3.2), MURO)
    caja(modelo(mundo, "muro_corredor_izquierdo_inicio", (-0.14, 2.72, 1.6, 0, 0, 0)), "",
         (0.28, 5.44, 3.2), MURO)
    caja(modelo(mundo, "muro_corredor_izquierdo_ensanche", (-0.64, 5.3, 1.6, 0, 0, 0)), "",
         (0.72, 0.28, 3.2), MURO)
    piezas(mundo, "muro_corredor_izquierdo_puertas_01_02", None, (
        ("union_esquina", (0.28, 0.28, 3.2), MURO, (-1.14, 5.3, 1.6, 0, 0, 0)),
        ("pared_inicial", (0.28, 0.25, 3.2), MURO, (-1.14, 5.565, 1.6, 0, 0, 0)),
        ("puerta_1", (0.04, 1, 2.6), PUERTA, (-1.02, 6.19, 1.3, 0, 0, 0)),
        ("sobre_puerta_1", (0.28, 1, 0.6), MURO, (-1.14, 6.19, 2.9, 0, 0, 0)),
        ("pared_intermedia", (0.28, 2.05, 3.2), MURO, (-1.14, 7.715, 1.6, 0, 0, 0)),
        ("puerta_2", (0.04, 1, 2.6), PUERTA, (-1.02, 9.24, 1.3, 0, 0, 0)),
        ("sobre_puerta_2", (0.28, 1, 0.6), MURO, (-1.14, 9.24, 2.9, 0, 0, 0)),
        ("pared_final", (0.28, 0.25, 3.2), MURO, (-1.14, 9.865, 1.6, 0, 0, 0)),
    ))
    caja(modelo(mundo, "muro_corredor_izquierdo_retorno", (-0.665, 10.13, 1.6, 0, 0, 0)), "",
         (1.23, 0.28, 3.2), MURO)
    caja(modelo(mundo, "muro_corredor_izquierdo_tramo_largo", (-0.19, 14.16, 1.6, 0, 0, 0)), "pared_larga",
         (0.28, 7.78, 3.2), MURO)
    caja(modelo(mundo, "puerta_corredor_izquierdo_03", (-0.07, 18.55, 1.3, 0, 0, 0)), "puerta_izquierda_3",
         (0.04, 1, 2.6), PUERTA)
    caja(modelo(mundo, "dintel_corredor_izquierdo_puerta_03", (-0.19, 18.55, 2.9, 0, 0, 0)), "pared_sobre_puerta_izquierda_3",
         (0.28, 1, 0.6), MURO)
    caja(modelo(mundo, "muro_corredor_izquierdo_entre_puertas_03_04", (-0.19, 19.11, 1.6, 0, 0, 0)), "separacion_puertas_izquierda_012",
         (0.28, 0.12, 3.2), MURO)
    caja(modelo(mundo, "puerta_corredor_izquierdo_04", (-0.07, 19.67, 1.3, 0, 0, 0)), "puerta_izquierda_4",
         (0.04, 1, 2.6), PUERTA)
    caja(modelo(mundo, "dintel_corredor_izquierdo_puerta_04", (-0.19, 19.67, 2.9, 0, 0, 0)), "pared_sobre_puerta_izquierda_4",
         (0.28, 1, 0.6), MURO)
    caja(modelo(mundo, "muro_corredor_izquierdo_hasta_zona_inferior", (-0.19, 22.07, 1.6, 0, 0, 0)), "pared_izquierda_380",
         (0.28, 3.8, 3.2), MURO)

    mundo.append(ET.Comment(" Corredor derecho y ascensor "))
    caja(modelo(mundo, "muro_corredor_derecho_inicio", (2.53, 0.725, 1.6, 0, 0, 0)), "",
         (0.28, 1.45, 3.2), MURO)
    caja(modelo(mundo, "murete_derecho_01", (2.455, 1.925, 0.615, 0, 0, 0)), "",
         (0.13, 0.95, 1.23), LADRILLO)
    caja(modelo(mundo, "columna_derecha_01", (2.675, 2.54, 1.6, 0, 0, 0)), "",
         (0.57, 0.28, 3.2), MURO)
    caja(modelo(mundo, "murete_derecho_02", (2.455, 3.195, 0.615, 0, 0, 0)), "",
         (0.13, 1.03, 1.23), LADRILLO)
    caja(modelo(mundo, "columna_derecha_02", (2.675, 3.85, 1.6, 0, 0, 0)), "",
         (0.57, 0.28, 3.2), MURO)
    caja(modelo(mundo, "murete_derecho_03", (2.455, 4.505, 0.615, 0, 0, 0)), "",
         (0.13, 1.03, 1.23), LADRILLO)
    caja(modelo(mundo, "columna_derecha_03", (2.675, 5.16, 1.6, 0, 0, 0)), "",
         (0.57, 0.28, 3.2), MURO)
    caja(modelo(mundo, "murete_derecho_04", (2.455, 5.82, 0.615, 0, 0, 0)), "",
         (0.13, 1.04, 1.23), LADRILLO)
    caja(modelo(mundo, "muro_corredor_derecho_entre_muretes_04_05", (2.53, 7.795, 1.6, 0, 0, 0)), "",
         (0.28, 2.91, 3.2), MURO)
    caja(modelo(mundo, "murete_derecho_05", (2.455, 9.78, 0.615, 0, 0, 0)), "",
         (0.13, 1.06, 1.23), LADRILLO)
    caja(modelo(mundo, "columna_derecha_04", (2.675, 10.45, 1.6, 0, 0, 0)), "",
         (0.57, 0.28, 3.2), MURO)
    caja(modelo(mundo, "murete_derecho_06", (2.455, 11.105, 0.615, 0, 0, 0)), "",
         (0.13, 1.03, 1.23), LADRILLO)
    caja(modelo(mundo, "columna_derecha_05", (2.675, 11.76, 1.6, 0, 0, 0)), "",
         (0.57, 0.28, 3.2), MURO)
    caja(modelo(mundo, "murete_derecho_07", (2.455, 12.41, 0.615, 0, 0, 0)), "",
         (0.13, 1.02, 1.23), LADRILLO)
    caja(modelo(mundo, "columna_derecha_06", (2.675, 13.06, 1.6, 0, 0, 0)), "",
         (0.57, 0.28, 3.2), MURO)
    caja(modelo(mundo, "murete_derecho_08", (2.455, 13.72, 0.615, 0, 0, 0)), "",
         (0.13, 1.04, 1.23), LADRILLO)
    caja(modelo(mundo, "columna_derecha_07", (2.675, 14.38, 1.6, 0, 0, 0)), "",
         (0.57, 0.28, 3.2), MURO)
    caja(modelo(mundo, "murete_derecho_09", (2.455, 15.055, 0.615, 0, 0, 0)), "",
         (0.13, 1.07, 1.23), LADRILLO)
    caja(modelo(mundo, "columna_derecha_08", (2.675, 15.73, 1.6, 0, 0, 0)), "",
         (0.57, 0.28, 3.2), MURO)
    caja(modelo(mundo, "puerta_ascensor", (2.98, 16.385, 1.135, 0, 0, 0)), "puerta_ascensor",
         (0.04, 1.03, 2.27), PUERTA)
    caja(modelo(mundo, "dintel_ascensor", (3.1, 16.385, 2.735, 0, 0, 0)), "pared_sobre_ascensor",
         (0.28, 1.59, 0.93), MURO)
    caja(modelo(mundo, "panel_ascensor_lado_columna_08", (3.1, 15.73, 1.135, 0, 0, 0)), "",
         (0.28, 0.28, 2.27), MURO)
    caja(modelo(mundo, "panel_ascensor_lado_columna_09", (3.1, 17.04, 1.135, 0, 0, 0)), "",
         (0.28, 0.28, 2.27), MURO)
    caja(modelo(mundo, "columna_derecha_09", (2.675, 17.04, 1.6, 0, 0, 0)), "columna_derecha_9",
         (0.57, 0.28, 3.2), MURO)
    caja(modelo(mundo, "murete_derecho_10", (2.455, 17.705, 0.615, 0, 0, 0)), "murete_derecho_10",
         (0.13, 1.05, 1.23), LADRILLO)
    caja(modelo(mundo, "muro_corredor_derecho_antes_escaleras", (2.53, 19.745, 1.6, 0, 0, 0)), "pared_derecha_289",
         (0.28, 3.03, 3.2), MURO)
    caja(modelo(mundo, "refuerzo_muro_antes_escaleras", (2.815, 21.12, 1.6, 0, 0, 0)), "refuerzo_final_pared_289",
         (0.29, 0.28, 3.2), MURO)

    mundo.append(ET.Comment(" Escaleras laterales "))
    caja(modelo(mundo, "columna_entre_escaleras_laterales", (2.675, 23.715, 1.6, 0, 0, 0)), "columna_entre_escaleras",
         (0.57, 0.25, 3.2), MURO)
    escalera_lateral(mundo, "escalera_lateral_subida", (2.95, 22.425, 0, 0, 0, 0), 2.17, 0.175, 0.2)
    escalera_lateral(mundo, "escalera_lateral_bajada", (2.95, 24.7, 0, 0, 0, 0), 1.56, -0.225, -0.2)
    baranda(mundo, "baranda_escalera_lateral_bajada", (4.085, 25.625, 0, 0, 0, -1.570796), "y",
            (0, 0), 3.39, (-1.675, -0.558333, 0.558333, 1.675))

    mundo.append(ET.Comment(" Zona inferior "))
    caja(modelo(mundo, "muro_zona_inferior_transversal_inicio", (-3.115, 23.83, 1.6, 0, 0, 0)), "pared_izquierda_380",
         (5.57, 0.28, 3.2), MURO)
    baranda(mundo, "baranda_zona_inferior_lateral_izquierda", (-5.685, 27.37, 0, 0, 0, 0), "y",
            (0, 0), 6.8, (-3.38, -1.12666667, 1.12666667, 3.38))
    caja(modelo(mundo, "muro_zona_inferior_transversal_izquierdo", (-2.975, 30.91, 1.6, 0, 0, 0)), "pared_izquierda_380",
         (5.85, 0.28, 3.2), MURO)
    caja(modelo(mundo, "muro_bajo_zona_inferior_lateral_derecho", (5.715, 28.075, 0.75, 0, 0, 0)), "pared_baja_continuacion_y",
         (0.13, 5.03, 1.5), LADRILLO)
    caja(modelo(mundo, "muro_bajo_zona_inferior_giro_derecho", (5.47, 30.655, 0.75, 0, 0, 0)), "pared_baja_primer_giro",
         (0.62, 0.13, 1.5), LADRILLO)
    caja(modelo(mundo, "muro_bajo_zona_inferior_entrante_derecho", (5.225, 30.745, 0.75, 0, 0, 0)), "pared_baja_entrante",
         (0.13, 0.05, 1.5), LADRILLO)
    caja(modelo(mundo, "muro_zona_inferior_fondo_derecho", (4.02, 30.835, 1.6, 0, 0, 0)), "pared_baja_final",
         (2.54, 0.13, 3.2), LADRILLO)

    mundo.append(ET.Comment(" Caja de la escalera en U "))
    caja(modelo(mundo, "muro_fondo_caja_escalera", (1.35, 30.835, 1.6, 0, 0, 0)), "pared_baja_final",
         (2.8, 0.13, 3.2), LADRILLO)
    baranda(mundo, "baranda_caja_escalera_lateral_izquierda", (-0.115, 29.07, 0, 0, 0, 0), "y",
            (0, -0.14), 3.68, (-1.96, -0.653333, 0.653333))
    baranda(mundo, "baranda_caja_escalera_lateral_derecha", (2.685, 29.07, 0, 0, 0, 0), "y",
            (0, -0.14), 3.68, (-1.96, -0.653333, 0.653333))
    baranda(mundo, "baranda_caja_escalera_frente_derecho", None, "x",
            (1.855, 27.155), 1.53, (1.11752525, 1.60917521, 2.10082479, 2.59247475))
    baranda(mundo, "baranda_caja_escalera_frente_izquierdo", None, "x",
            (0.01, 27.155), 0.12, (0.01,))
    escalera_en_u(mundo, "escalera_caja_fondo_en_u")

    mundo.append(configuracion.find("gui"))
    return raiz


def generar(destino):
    raiz = crear_mundo()
    ET.indent(raiz, space="  ")
    xml = ET.tostring(raiz, encoding="unicode")
    xml = re.sub(
        r"<geometry>\s*<box>\s*(<size>[^<]+</size>)\s*</box>\s*</geometry>",
        r"<geometry><box>\1</box></geometry>",
        xml,
    )
    destino.write_text('<?xml version="1.0" encoding="utf-8"?>\n' + xml + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("salida", type=Path, nargs="?",
                        default=Path(__file__).with_name("edificio_calatayud.sdf"))
    generar(parser.parse_args().salida)
