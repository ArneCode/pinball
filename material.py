class Material:
    factor_ort: float
    factor_par: float
    min_ort: float
    min_par: float

    def __init__(self, factor_ort: float, factor_par: float, min_ort: float, min_par: float):
        self.factor_ort = factor_ort
        self.factor_par = factor_par
        self.min_ort = min_ort
        self.min_par = min_par