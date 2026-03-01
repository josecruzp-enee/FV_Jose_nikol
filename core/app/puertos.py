from typing import Protocol, Dict, Any


class PuertoSizing(Protocol):
    def ejecutar(self, datos: Any) -> Dict[str, Any]: ...


class PuertoPaneles(Protocol):
    def ejecutar(self, datos: Any, sizing: Dict[str, Any]) -> Dict[str, Any]: ...


class PuertoEnergia(Protocol):
    def ejecutar(self, datos: Any, sizing: Dict[str, Any], strings: Dict[str, Any]) -> Dict[str, Any]: ...


class PuertoNEC(Protocol):
    def ejecutar(self, datos: Any, sizing: Dict[str, Any], strings: Dict[str, Any]) -> Dict[str, Any]: ...


class PuertoFinanzas(Protocol):
    def ejecutar(self, datos: Any, sizing: Dict[str, Any], energia: Dict[str, Any]) -> Dict[str, Any]: ...
