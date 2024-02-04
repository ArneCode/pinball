class Material:
    """
    Material of a form. This class is used to define the material of a form, which is used to calculate the result direction of a collision.

    Attributes:
        - factor_ort (float): The factor by which the velocity orthagonal to the surface is multiplied.
        - factor_par (float): The factor by which the velocity parallel to the surface is multiplied.
        - min_ort (float): The minimum velocity orthagonal to the surface.
        - min_par (float): The minimum velocity parallel to the surface.
    """
    factor_ort: float
    factor_par: float
    min_ort: float
    min_par: float

    def __init__(self, factor_ort: float, factor_par: float, min_ort: float, min_par: float):
        """
        Initialize the Material.

        Args:
            - factor_ort: The factor by which the velocity orthagonal to the surface is multiplied.
            - factor_par: The factor by which the velocity parallel to the surface is multiplied.
            - min_ort: The minimum velocity orthagonal to the surface.
            - min_par: The minimum velocity parallel to the surface.
        """
        self.factor_ort = factor_ort
        self.factor_par = factor_par
        self.min_ort = min_ort
        self.min_par = min_par
