@dataclass(frozen=True)
class EntradaSolar:

    # ubicación
    lat: float
    lon: float

    # tiempo
    fecha_hora: datetime

    # radiación completa
    ghi_wm2: float
    dni_wm2: float
    dhi_wm2: float

    # geometría
    tilt_deg: float
    azimuth_panel_deg: float
