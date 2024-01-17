class Material:
    factor_ort: float
    factor_par: float

    def __init__(self, factor_ort: float, factor_par: float):
        self.factor_ort = factor_ort
        self.factor_par = factor_par