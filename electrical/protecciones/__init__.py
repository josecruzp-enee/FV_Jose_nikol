from __future__ import annotations

from typing import Any, Dict, Optional


def armar_ocpd(*, iac_nom_a: float, n_strings: int, isc_mod_a: float, has_combiner: Optional[bool] = None) -> Dict[str, object]:
    # Import diferido para evitar circular imports
    from .protecciones import armar_ocpd as _armar_ocpd
    return _armar_ocpd(iac_nom_a=float(iac_nom_a), n_strings=int(n_strings), isc_mod_a=float(isc_mod_a), has_combiner=has_combiner)


__all__ = ["armar_ocpd"]
