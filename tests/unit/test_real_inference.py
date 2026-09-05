from app.detection.real_inference import RealDetector


class FakeBoxes:
    def __init__(self, cls, conf, xyxy):
        self.cls = cls
        self.conf = conf
        self.xyxy = xyxy


class FakeResult:
    def __init__(self, boxes, orig_shape):
        self.boxes = boxes
        self.orig_shape = orig_shape


class FakeModel:
    def __init__(self):
        self.prompts = None

    def to(self, device):
        return self

    def set_classes(self, prompts):
        self.prompts = prompts

    def predict(self, source, conf=0.25, verbose=False):
        return [FakeResult(FakeBoxes([0, 1, 2], [0.82, 0.71, 0.64], [[10, 10, 60, 80], [100, 20, 150, 70], [200, 30, 260, 90]]), (100, 200))]


def test_conversion_normalizada_a_pixeles():
    bbox = RealDetector._a_pixeles([0.25, 0.1, 0.5, 0.3], ancho=200, alto=100)
    assert bbox == [50.0, 10.0, 100.0, 30.0]


def test_conversion_pixeles_sin_cambios():
    bbox = RealDetector._a_pixeles([25.0, 10.0, 100.0, 30.0], ancho=200, alto=100)
    assert bbox == [25.0, 10.0, 100.0, 30.0]


def test_detectar_mapea_indices_a_productos(tmp_path):
    imagen = tmp_path / "prueba.jpg"
    imagen.write_bytes(b"fake")
    detector = RealDetector(modelo="yolov8s-worldv2.pt", device="cpu")
    detector._model = FakeModel()

    prompts = {
        "caja_carton_chica": ["small cardboard box", "small brown carton box"],
        "botella_plastica": ["plastic bottle"],
    }
    detecciones = detector.detectar(imagen, prompts, confianza=0.5)

    assert len(detecciones) == 3
    assert detecciones[0].producto_id == "caja_carton_chica"
    assert detecciones[0].confianza == 0.82
    assert detecciones[0].bbox == [10.0, 10.0, 60.0, 80.0]
    assert detecciones[0].label == "small cardboard box"
    assert detecciones[1].producto_id == "caja_carton_chica"
    assert detecciones[1].label == "small brown carton box"
    assert detecciones[2].producto_id == "botella_plastica"
    assert detecciones[2].label == "plastic bottle"


def test_detectar_sin_prompts_devuelve_vacio(tmp_path):
    imagen = tmp_path / "prueba.jpg"
    imagen.write_bytes(b"fake")
    detector = RealDetector(device="cpu")
    assert detector.detectar(imagen, {}) == []


def test_detectar_imagen_inexistente():
    detector = RealDetector(device="cpu")
    try:
        detector.detectar("no_existe.jpg", {"caja_carton_chica": ["a box"]})
    except FileNotFoundError:
        return
    raise AssertionError("Deberia lanzar FileNotFoundError")


def test_detectar_ndarray_mapea_indices_a_productos():
    import numpy as np

    from app.detection.real_inference import RealDetector

    frame = np.zeros((100, 200, 3), dtype=np.uint8)
    detector = RealDetector(device="cpu")
    detector._model = FakeModel()

    prompts = {
        "caja_carton_chica": ["small cardboard box", "small brown carton box"],
        "botella_plastica": ["plastic bottle"],
    }
    detecciones = detector.detectar_ndarray(frame, prompts, confianza=0.5)

    assert len(detecciones) == 3
    assert detecciones[0].producto_id == "caja_carton_chica"
    assert detecciones[0].bbox == [10.0, 10.0, 60.0, 80.0]
    assert detecciones[1].producto_id == "caja_carton_chica"
    assert detecciones[2].producto_id == "botella_plastica"


def test_detectar_sin_prompts_ndarray_devuelve_vacio():
    import numpy as np

    detector = RealDetector(device="cpu")
    frame = np.zeros((10, 10, 3), dtype=np.uint8)
    assert detector.detectar_ndarray(frame, {}) == []


class FakeModelConContador(FakeModel):
    def __init__(self):
        super().__init__()
        self.set_calls = 0

    def set_classes(self, prompts):
        self.set_calls += 1
        super().set_classes(prompts)


def test_prompts_se_activan_solo_cuando_cambian(tmp_path):
    import numpy as np

    imagen = tmp_path / "prueba.jpg"
    imagen.write_bytes(b"fake")
    detector = RealDetector(device="cpu")
    detector._model = FakeModelConContador()
    prompts_a = {"botella_plastica": ["plastic bottle", "transparent plastic container", "botella plastica"]}
    prompts_b = {"caja_carton_chica": ["small cardboard box", "small brown carton box", "caja de carton pequena"]}

    detector.detectar(imagen, prompts_a)
    detector.detectar_ndarray(np.zeros((8, 8, 3), dtype=np.uint8), prompts_a)
    assert detector._model.set_calls == 1  # mismos prompts -> set_classes una sola vez

    detector.detectar(imagen, prompts_b)
    assert detector._model.set_calls == 2  # prompts distintos -> se reactiva


def test_obtener_detector_compartido_devuelve_singleton():
    from app.detection.real_inference import obtener_detector_compartido

    a = obtener_detector_compartido()
    b = obtener_detector_compartido()
    assert a is b