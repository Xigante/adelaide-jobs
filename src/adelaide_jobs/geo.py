"""Distância e janela de transporte.

Deliberadamente simples: haversine em linha reta. O estudo recomenda
GTFS do Adelaide Metro para tempo real de viagem — inclusive o trajeto
de VOLTA no horário de término do turno, que é o que decide se um night
fill em Elizabeth é alcançável sem carro. Isso fica para a v2; até lá o
raio em linha reta já derruba o que está claramente fora.
"""

from __future__ import annotations

import math

# 115 Grenfell St, Adelaide CBD (ILSC)
ILSC_LAT = -34.9235
ILSC_LON = 138.6055

EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distância em linha reta entre dois pontos, em quilômetros."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def distance_from_school(lat: float | None, lon: float | None) -> float | None:
    """Distância até o ILSC. `None` quando a vaga não traz coordenada."""
    if lat is None or lon is None:
        return None
    return haversine_km(ILSC_LAT, ILSC_LON, lat, lon)


# Subúrbios de Adelaide que aparecem com frequência em vaga casual.
# Serve para estimar distância quando o anúncio não traz coordenada —
# muito anúncio de agência só diz o nome do subúrbio.
SUBURB_COORDS: dict[str, tuple[float, float]] = {
    "adelaide": (-34.9285, 138.6007),
    "adelaide cbd": (-34.9285, 138.6007),
    "north adelaide": (-34.9066, 138.5936),
    "norwood": (-34.9200, 138.6300),
    "unley": (-34.9500, 138.6050),
    "glenelg": (-34.9800, 138.5150),
    "port adelaide": (-34.8480, 138.5030),
    "prospect": (-34.8830, 138.5940),
    "mile end": (-34.9250, 138.5710),
    "keswick": (-34.9450, 138.5800),
    "marion": (-35.0170, 138.5570),
    "modbury": (-34.8330, 138.6830),
    "elizabeth": (-34.7180, 138.6710),
    "salisbury": (-34.7580, 138.6400),
    "gawler": (-34.5980, 138.7450),
    "mawson lakes": (-34.8100, 138.6100),
    "west lakes": (-34.8760, 138.4930),
    "burnside": (-34.9350, 138.6560),
    "campbelltown": (-34.8830, 138.6650),
    "kent town": (-34.9210, 138.6180),
    "thebarton": (-34.9160, 138.5670),
    "hindmarsh": (-34.9080, 138.5720),
    "richmond": (-34.9370, 138.5620),
    "torrensville": (-34.9200, 138.5580),
    "st peters": (-34.9060, 138.6250),
    "parkside": (-34.9450, 138.6150),
    "goodwood": (-34.9520, 138.5930),
    "hilton": (-34.9280, 138.5620),
    "woodville": (-34.8790, 138.5390),
    "seaton": (-34.8890, 138.5150),
    "henley beach": (-34.9190, 138.4950),
    "brighton": (-35.0180, 138.5220),
    "aldinga": (-35.2700, 138.4640),
    "noarlunga": (-35.1400, 138.4970),
    "golden grove": (-34.7880, 138.7130),
    "tea tree gully": (-34.8220, 138.7150),
    "edwardstown": (-34.9750, 138.5710),
    "melrose park": (-34.9820, 138.5810),
    "netley": (-34.9420, 138.5480),
    "wingfield": (-34.8410, 138.5620),
    "regency park": (-34.8620, 138.5720),
    "dry creek": (-34.8280, 138.5760),
    "pooraka": (-34.8300, 138.6060),
    "athol park": (-34.8580, 138.5460),
}


def guess_coords(suburb: str | None) -> tuple[float, float] | None:
    """Coordenada aproximada a partir do nome do subúrbio."""
    if not suburb:
        return None
    return SUBURB_COORDS.get(suburb.strip().lower())
