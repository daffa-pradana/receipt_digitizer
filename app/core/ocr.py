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


def read_best(images: list[np.ndarray]) -> tuple[str, list[tuple[str, float]]]:
    """Run read() on each preprocessing variant, keep the highest mean-confidence result.

    Binarization helps faded receipts but can hurt clean ones by discarding
    information a deep-learning OCR model could otherwise use - so instead of
    committing to one preprocessing choice, try a few and pick the winner.
    """
    candidates = [read(image) for image in images]
    return max(candidates, key=_mean_confidence)


def _mean_confidence(result: tuple[str, list[tuple[str, float]]]) -> float:
    _full_text, lines_with_conf = result
    if not lines_with_conf:
        return 0.0
    return sum(confidence for _text, confidence in lines_with_conf) / len(lines_with_conf)
