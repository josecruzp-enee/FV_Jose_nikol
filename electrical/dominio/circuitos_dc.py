from dataclasses import dataclass


@dataclass
class MPPTCircuit:

    id_mppt: int
    strings: int

    imp_string: float
    isc_string: float

    corriente_operacion: float
    corriente_diseno: float
