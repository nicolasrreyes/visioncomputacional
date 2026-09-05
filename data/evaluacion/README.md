# Evaluacion de deteccion

Harness `scripts/evaluar.py` para medir calidad de deteccion contra ground
truth (GT). Permite decidir prompts, umbrales y si alcanza el zero-shot o hace
falta un modelo entrenado. SIEMPRE sin GPU: la inferencia usa el detector
compartido ya cargado en memoria.

## Formato de etiquetas

Un JSON por conjunto de evaluacion. Cada imagen es una clave; el valor indica
la zona (para activar el vocabulario correcto) y el modo:

### Modo bbox (mAP / P / R / F1 por IoU >= 0.5)

```json
{
  "estante_gaseosas.jpg": {
    "zona": "estanteria_b",
    "cajas": {
      "botella_plastica": [[120, 180, 240, 420], [260, 180, 380, 420]]
    }
  }
}
```

Requiere anotar cada objeto con su caja. Herramientas gratuitas: CVAT
(self-host), Roboflow o make sense. Exportar en YOLO/PASCAL y convertir a este
formato o anotar directo con un script.

### Modo conteo (comparacion de recuentos, sin anotar cajas)

```json
{
  "estante_gaseosas.jpg": {
    "zona": "estanteria_b",
    "conteos": { "botella_plastica": 41 }
  }
}
```

Sirve para calibracion rapida cuando se conoce cuantos objetos hay (p. ej. los
recuentos documentados en `docs/DEMO.md`).

## Uso

```bash
# Modo conteo con sweep de umbral para calibrar cada producto
python scripts/evaluar.py --etiquetas data/evaluacion/etiquetas_conteo.json \
    --dir data/demo_images --conf 0.1 --sweep "0.2 0.3 0.4 0.5 0.6 0.7"

# Modo bbox (con GT anotada)
python scripts/evaluar.py --etiquetas data/evaluacion/mi_set.json \
    --dir data/mis_fotos --iou 0.5 --json outputs/evaluacion.json

# Comparar cero-shot con y sin clases negativas
python scripts/evaluar.py ... --no-background
```

Flags utiles: `--conf` (confianza cruda de inferencia, usar ~0.1 para el motor
de evaluacion), `--iou` (umbral de emparejamiento bbox), `--nms` (IoU NMS del
conteo), `--sweep` (umbrales a probar por producto), `--no-background` (apagar
clases negativas), `--json` (guardar reporte).

## Que mirar

- **mAP@0.5 / F1 por producto** en modo bbox: la calidad real por objeto.
- **Umbral optimo por F1** en modo conteo: alimenta `umbral_confianza` en
  `data/productos_objetivo.json`.
- **comparar --background vs --no-background**: mide si las clases negativas
  suben precision sin bajar recall.

## Limite conocido

Los recuentos del seed (`etiquetas_conteo.json`) provienen de la documentacion
de la demo y son aproximados; son para calibracion, no para certificar mAP.
Para metricas definitivas anotar bboxes (modo bbox).