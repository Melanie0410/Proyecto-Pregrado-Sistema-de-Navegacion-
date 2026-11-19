#!/usr/bin/env python3
"""Calcula la altura de la pelvis para que los pies queden en z = 0 (el piso).

Usa la cinematica directa del URDF del G1 con todas las articulaciones en cero
(la postura que muestra el modelo estatico) y busca el punto mas bajo de las
mallas visuales de los pies (eslabones *ankle_roll_link*).

Uso:
    python3 simulacion/semana_16/worlds/calcular_altura_pelvis.py
"""
import argparse
import math
import re
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

DESC = Path.home() / "unitree_referencias/unitree_ros/robots/g1_description"


def matriz_rpy(r, p, y):
    cr, sr, cp, sp, cy, sy = (math.cos(r), math.sin(r), math.cos(p),
                              math.sin(p), math.cos(y), math.sin(y))
    return [[cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
            [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
            [-sp, cp * sr, cp * cr]]


def componer(a, b):
    ra, ta = a
    rb, tb = b
    r = [[sum(ra[i][k] * rb[k][j] for k in range(3)) for j in range(3)]
         for i in range(3)]
    t = [sum(ra[i][k] * tb[k] for k in range(3)) + ta[i] for i in range(3)]
    return r, t


def origen(elem):
    o = elem.find("origin") if elem is not None else None
    xyz = [float(v) for v in (o.get("xyz", "0 0 0") if o is not None else "0 0 0").split()]
    rpy = [float(v) for v in (o.get("rpy", "0 0 0") if o is not None else "0 0 0").split()]
    return matriz_rpy(*rpy), xyz


def cargar_stl(ruta):
    datos = Path(ruta).read_bytes()
    if len(datos) >= 84:
        n = struct.unpack("<I", datos[80:84])[0]
        if len(datos) == 84 + 50 * n:
            for i in range(n):
                base = 84 + 50 * i + 12
                for v in range(3):
                    yield struct.unpack("<3f", datos[base + 12 * v: base + 12 * v + 12])
            return
    for m in re.finditer(r"vertex\s+(\S+)\s+(\S+)\s+(\S+)", datos.decode("utf-8", "ignore")):
        yield tuple(float(g) for g in m.groups())


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--urdf", default=str(DESC / "g1_29dof_rev_1_0.urdf"))
    ap.add_argument("--mallas", default=str(DESC / "meshes"))
    ap.add_argument("--pies", default="ankle_roll", help="texto en el nombre de los eslabones del pie")
    a = ap.parse_args()

    raiz = ET.parse(a.urdf).getroot()
    padre = {}
    for j in raiz.findall("joint"):
        padre[j.find("child").get("link")] = (j.find("parent").get("link"), origen(j))

    def pose_enlace(nombre):
        if nombre not in padre:
            return ([[1, 0, 0], [0, 1, 0], [0, 0, 1]], [0.0, 0.0, 0.0])
        p, t = padre[nombre]
        return componer(pose_enlace(p), t)

    raices = [l.get("name") for l in raiz.findall("link") if l.get("name") not in padre]
    print(f"Enlace raiz del URDF: {raices}")

    resultados = {}
    for enlace in raiz.findall("link"):
        nombre = enlace.get("name")
        if a.pies not in nombre:
            continue
        t_enlace = pose_enlace(nombre)
        for vis in enlace.findall("visual"):
            malla = vis.find("geometry/mesh")
            if malla is None:
                continue
            archivo = Path(a.mallas) / Path(malla.get("filename")).name
            if not archivo.exists():
                print(f"AVISO: no existe {archivo}")
                continue
            esc = [float(v) for v in malla.get("scale", "1 1 1").split()]
            r, t = componer(t_enlace, origen(vis))
            zmin = min(r[2][0] * x * esc[0] + r[2][1] * y * esc[1] + r[2][2] * z * esc[2] + t[2]
                       for x, y, z in cargar_stl(archivo))
            resultados[nombre] = min(zmin, resultados.get(nombre, zmin))
            print(f"  {nombre}: punto mas bajo = {zmin:.4f} m respecto a la pelvis")

    if not resultados:
        sys.exit("ERROR: no se encontraron mallas de pies. Medir z a mano en Gazebo.")
    z = -min(resultados.values())
    print(f"\nAltura de la pelvis para que el pie mas bajo toque el piso: {z:.4f} m")
    print("Regenerar el mundo con:")
    print(f"  python3 simulacion/semana_16/worlds/generar_mundo_unificado.py --z {z:.3f}")


if __name__ == "__main__":
    main()
