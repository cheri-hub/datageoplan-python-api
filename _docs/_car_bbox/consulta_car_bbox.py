"""
Consulta CARs (Cadastro Ambiental Rural) dentro de um Bounding Box (BBOX)
usando o WFS público do GeoServer do SICAR.

Uso:
    python consulta_car_bbox.py --bbox "-47.1,-23.6,-47.0,-23.5" --uf sp
    python consulta_car_bbox.py --bbox "-47.1,-23.6,-47.0,-23.5" --uf sp --max 10 --com-geometria
    python consulta_car_bbox.py --bbox "-47.1,-23.6,-47.0,-23.5" --uf sp --output resultado.json
"""

import argparse
import json
import ssl
import sys
import urllib.request
import urllib.parse
import urllib.error

# Mapeamento UF -> layer name
UFS = [
    "ac", "al", "am", "ap", "ba", "ce", "df", "es", "go",
    "ma", "mg", "ms", "mt", "pa", "pb", "pe", "pi", "pr",
    "rj", "rn", "ro", "rr", "rs", "sc", "se", "sp", "to"
]

GEOSERVER_WFS = "https://geoserver.car.gov.br/geoserver/sicar/wfs"

STATUS_MAP = {
    "IN": "Inscrito",
    "RE": "Retificado",
    "AT": "Ativo",
    "PE": "Pendente",
    "CA": "Cancelado",
    "SU": "Suspenso",
}

TIPO_MAP = {
    "IRU": "Imóvel Rural",
    "PCT": "Povos e Comunidades Tradicionais",
    "AST": "Assentamento da Reforma Agrária",
}


def consultar_cars_bbox(
    bbox: str,
    uf: str,
    max_features: int = 50,
    com_geometria: bool = False,
    cql_filter: str | None = None,
) -> dict:
    """
    Consulta CARs dentro de um BBOX via WFS.

    Args:
        bbox: Bounding box no formato "minx,miny,maxx,maxy" (lon/lat em EPSG:4674/SIRGAS2000)
        uf: Sigla do estado (ex: "sp", "mg")
        max_features: Número máximo de features retornadas
        com_geometria: Se True, inclui a geometria MultiPolygon na resposta
        cql_filter: Filtro CQL opcional (ex: "status_imovel='AT'")

    Returns:
        dict: GeoJSON FeatureCollection
    """
    uf = uf.lower()
    if uf not in UFS:
        raise ValueError(f"UF inválida: {uf}. Válidas: {', '.join(UFS)}")

    layer = f"sicar_imoveis_{uf}"

    params = {
        "SERVICE": "WFS",
        "VERSION": "1.1.0",
        "REQUEST": "GetFeature",
        "TYPENAMES": layer,
        "BBOX": f"{bbox},EPSG:4674",
        "OUTPUTFORMAT": "application/json",
        "MAXFEATURES": str(max_features),
    }

    if not com_geometria:
        params["PROPERTYNAME"] = "cod_imovel,status_imovel,dat_criacao,area,condicao,uf,municipio,cod_municipio_ibge,m_fiscal,tipo_imovel"

    if cql_filter:
        # BBOX and CQL_FILTER are mutually exclusive in WFS, and the
        # server WAF blocks CQL_FILTER requests. So we fetch with BBOX
        # only and filter attributes client-side.
        # Increase max_features to compensate for client-side filtering
        params["MAXFEATURES"] = str(max_features * 10)

    url = f"{GEOSERVER_WFS}?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(url)
    req.add_header("User-Agent", "car-bbox-query/1.0")

    # Create SSL context that works with the GeoServer endpoint
    ctx = ssl.create_default_context()
    ctx.set_ciphers("DEFAULT@SECLEVEL=1")

    try:
        with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"Erro HTTP {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Erro de conexão: {e.reason}", file=sys.stderr)
        sys.exit(1)

    # Apply attribute filter client-side (WAF blocks CQL_FILTER)
    if cql_filter:
        # Parse simple filters like "status_imovel='AT'"
        import re
        match = re.match(r"(\w+)\s*=\s*'(\w+)'", cql_filter)
        if match:
            field, value = match.groups()
            data["features"] = [
                f for f in data.get("features", [])
                if f.get("properties", {}).get(field) == value
            ]
            data["numberReturned"] = len(data["features"])
            data["totalFeatures"] = f"{len(data['features'])} (filtrado client-side)"

    return data


def formatar_resultado(data: dict) -> str:
    """Formata o resultado para exibição no terminal."""
    total = data.get("totalFeatures", "?")
    retornados = data.get("numberReturned", len(data.get("features", [])))
    features = data.get("features", [])

    linhas = []
    linhas.append(f"Total de CARs no BBOX: {total}")
    linhas.append(f"Retornados: {retornados}")
    linhas.append("-" * 100)
    linhas.append(
        f"{'#':<4} {'Código CAR':<52} {'Status':<12} {'Tipo':<8} {'Área (ha)':<12} {'Município':<20}"
    )
    linhas.append("-" * 100)

    for i, f in enumerate(features, 1):
        props = f.get("properties", {})
        cod = props.get("cod_imovel", "?")
        status = props.get("status_imovel", "?")
        tipo = props.get("tipo_imovel", "?")
        area = props.get("area", 0)
        municipio = props.get("municipio", "?")

        linhas.append(
            f"{i:<4} {cod:<52} {status:<12} {tipo:<8} {area:<12.4f} {municipio:<20}"
        )

    linhas.append("-" * 100)
    return "\n".join(linhas)


def main():
    parser = argparse.ArgumentParser(
        description="Consulta CARs dentro de um Bounding Box via WFS do SICAR/GeoServer"
    )
    parser.add_argument(
        "--bbox",
        required=True,
        help='BBOX no formato "minLon,minLat,maxLon,maxLat" (EPSG:4674). Ex: "-47.1,-23.6,-47.0,-23.5"',
    )
    parser.add_argument(
        "--uf",
        required=True,
        help="Sigla do estado (ex: sp, mg, ba)",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=50,
        help="Número máximo de resultados (padrão: 50)",
    )
    parser.add_argument(
        "--com-geometria",
        action="store_true",
        help="Incluir geometria MultiPolygon na resposta",
    )
    parser.add_argument(
        "--status",
        help="Filtrar por status (AT=Ativo, PE=Pendente, CA=Cancelado, IN=Inscrito, RE=Retificado)",
    )
    parser.add_argument(
        "--output",
        help="Salvar resultado GeoJSON em arquivo",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Exibir saída em JSON em vez de tabela",
    )

    args = parser.parse_args()

    cql = None
    if args.status:
        cql = f"status_imovel='{args.status.upper()}'"

    print(f"Consultando CARs no BBOX [{args.bbox}] para UF={args.uf.upper()}...\n")

    data = consultar_cars_bbox(
        bbox=args.bbox,
        uf=args.uf,
        max_features=args.max,
        com_geometria=args.com_geometria,
        cql_filter=cql,
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Resultado salvo em: {args.output}")

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(formatar_resultado(data))


if __name__ == "__main__":
    main()
