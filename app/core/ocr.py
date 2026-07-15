import easyocr
import numpy as np

_reader: easyocr.Reader | None = None


def get_reader() -> easyocr.Reader:
    global _reader
    if _reader is None:
        _reader = easyocr.Reader(["en"], gpu=False)
    return _reader


def read(image: np.ndarray) -> tuple[str, list[tuple[str, float]]]:
    results = get_reader().readtext(image)
    lines_with_conf = [(text, float(conf)) for _bbox, text, conf in results]
    full_text = "\n".join(text for text, _conf in lines_with_conf)
    return full_text, lines_with_conf
