#!/usr/bin/env python3
"""Mide las dimensiones del G1 a partir de sus mallas (postura con articulaciones en cero).

Calcula, respecto a la pelvis, el punto mas bajo (pies), el mas alto y el radio
horizontal maximo (brazos incluidos). Con eso propone los parametros de la
colision simplificada del generador del mundo.

Uso:
    python3 simulacion/semana_16/worlds/medir_dimensiones_robot.py
"""
import argparse
import math
import re
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from calcular_altura_pelvis import DESC, componer, origen


def vertices(ruta):
    datos = Path(ruta).read_bytes()
    if len(datos) >= 84:
        n = struct.unpack("<I", datos[80:84])[0]
        if len(datos) == 84 + 50 * n:
            for reg in struct.iter_unpack("<12fH", datos[84:]):
                yield reg[3:6]
                yield reg[6:9]
                yield reg[9:12]
            return
    for m in re.finditer(r"vertex\s+(\S+)\s+(\S+)\s+(\S+)", datos.decode("utf-8", "ignore")):
        yield tuple(float(g) for g in m.groups())


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--urdf", default=str(DESC / "g1_29dof_rev_1_0.urdf"))
    ap.add_argument("--mallas", default=str(DESC / "meshes"))
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

    inf = float("inf")
    xmin = ymin = zmin = inf
    xmax = ymax = zmax = -inf
    r2max = 0.0
    n_mallas = 0
    for enlace in raiz.findall("link"):
        for vis in enlace.findall("visual"):
            malla = vis.find("geometry/mesh")
            if malla is None:
                continue
            archivo = Path(a.mallas) / Path(malla.get("filename")).name
            if not archivo.exists():
                print(f"AVISO: no existe {archivo}")
                continue
            esc = [float(v) for v in malla.get("scale", "1 1 1").split()]
            (r, t) = componer(pose_enlace(enlace.get("name")), origen(vis))
            (r00, r01, r02), (r10, r11, r12), (r20, r21, r22) = r
            sx, sy, sz = esc
            for x, y, z in vertices(archivo):
                x *= sx; y *= sy; z *= sz
                px = r00 * x + r01 * y + r02 * z + t[0]
                py = r10 * x + r11 * y + r12 * z + t[1]
                pz = r20 * x + r21 * y + r22 * z + t[2]
                if px < xmin: xmin = px
                if px > xmax: xmax = px
                if py < ymin: ymin = py
                if py > ymax: ymax = py
                if pz < zmin: zmin = pz
                if pz > zmax: zmax = pz
                d = px * px + py * py
                if d > r2max: r2max = d
            n_mallas += 1

    if n_mallas == 0:
        sys.exit("ERROR: no se leyo ninguna malla.")
    radio = math.sqrt(r2max)
    z_pelvis = -zmin
    altura = zmax - zmin
    print(f"Mallas leidas: {n_mallas}")
    print(f"Extension en x (adelante/atras): {xmin:.3f} a {xmax:.3f} m -> {xmax - xmin:.3f} m")
    print(f"Extension en y (lateral)       : {ymin:.3f} a {ymax:.3f} m -> {ymax - ymin:.3f} m")
    print(f"Extension en z                 : {zmin:.3f} a {zmax:.3f} m -> {altura:.3f} m")
    print(f"Radio horizontal maximo desde la pelvis: {radio:.3f} m")
    print("\nParametros sugeridos (radio redondeado hacia arriba al centimetro):")
    print("  python3 simulacion/semana_16/worlds/generar_mundo_unificado.py "
          f"--z {z_pelvis:.3f} --radio {math.ceil(radio * 100) / 100:.2f} --altura {altura:.2f}")


if __name__ == "__main__":
    main()
