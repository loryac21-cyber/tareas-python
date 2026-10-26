"""Verifica guion.json contra el texto fuente.

Marca con ¡¡ toda cifra (en "cifra" y "etiqueta") que no aparece tal cual en la fuente.
Los números de "frase" van en palabras; se revisan a mano (una persona lee el guion
completo contra la fuente: los números se verifican con código, las afirmaciones no).

Uso (Windows):
    .venv\\Scripts\\python verificar_guion.py --guion guion.json --fuente fuente_incendios.md
"""
import argparse
import json
import re
import sys
from pathlib import Path

NUM = re.compile(r"\d+(?:[.,]\d+)*")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--guion", default="guion.json")
    ap.add_argument("--fuente", default="fuente_incendios.md")
    a = ap.parse_args()

    fuente = Path(a.fuente).read_text(encoding="utf-8")
    nums_fuente = set(NUM.findall(fuente))
    escenas = json.loads(Path(a.guion).read_text(encoding="utf-8"))["escenas"]

    malas = 0
    palabras = 0
    for k, e in enumerate(escenas, 1):
        palabras += len(e["frase"].split())
        print(f"\nEscena {k}: {e['frase']}")
        for campo in ("cifra", "etiqueta"):
            texto = e.get(campo, "")
            marcas = []
            for n in NUM.findall(texto):
                if n in nums_fuente:
                    marcas.append(n)
                else:
                    marcas.append(f"¡¡{n}!!")
                    malas += 1
            print(f"   {campo:8s}: {texto}   ->  {' '.join(marcas) or '(sin números)'}")
        if re.search(r"\d", e["frase"]):
            print("   ¡¡ la frase tiene dígitos: escríbalos en palabras para que la voz los lea bien")
            malas += 1

    seg = palabras / 2.5
    print(f"\n{len(escenas)} escenas · {palabras} palabras · ~{seg:.0f} s de voz (a 2.5 palabras/s)")
    print("OK: todas las cifras aparecen en la fuente" if malas == 0 else f"{malas} cifra(s) marcadas con ¡¡: revíselas")
    return 1 if malas else 0


if __name__ == "__main__":
    sys.exit(main())
