# OCR

## Fase 4

La Fase 4 agrega una interfaz `OCREngine` y un adaptador `PaddleOCREngine`.

```text
Frame
  -> PaddleOCR
  -> PerceptionElement(type="text", source="ocr")
```

## Dependencia

PaddleOCR requiere PaddlePaddle. La documentacion oficial indica instalar PaddlePaddle 3.0+ y luego `paddleocr`.

En este equipo, con Python 3.14, `pip` no encontro wheel para `paddlepaddle`, ni en PyPI ni en el indice CPU oficial de Paddle. Por eso el backend real queda opcional:

```powershell
python -m pip install -e ".[ocr]"
```

en un Python compatible con PaddlePaddle.

## Estado

- Interfaz implementada.
- Adaptador PaddleOCR implementado.
- Parser probado para formato clasico `[[box, (text, score)]]`.
- No se guarda ninguna imagen a disco.
