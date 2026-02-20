"""
Serviço de consulta de demonstrativo CAR.

Consulta dados detalhados de um registro CAR diretamente
do sistema car.gov.br e gera PDF do demonstrativo.
"""

import ssl
import io
from typing import Dict, Any, Optional

import httpx

from src.core.logging import get_logger

logger = get_logger(__name__)

# URL base do sistema CAR
_CAR_BASE = "https://car.gov.br"
_DEMONSTRATIVO_URL = f"{_CAR_BASE}/imovel/demonstrativo/{{car_code}}/gerarComRecaptcha"


class CarConsultaError(Exception):
    """Erro ao consultar dados do CAR."""
    pass


class CarConsultaService:
    """
    Serviço para consulta de dados do demonstrativo CAR.
    
    Acessa a API pública do car.gov.br para obter informações
    detalhadas de um registro CAR.
    """

    def __init__(self):
        """Inicializa o serviço com sessão HTTP configurada para TLS do car.gov.br."""
        self._session: Optional[httpx.Client] = None

    def _get_session(self) -> httpx.Client:
        """Cria ou retorna sessão HTTP com TLS configurado."""
        if self._session is None:
            context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
            context.set_ciphers("RSA+AESGCM:RSA+AES:!aNULL:!MD5:!DSS")

            self._session = httpx.Client(
                verify=context,
                timeout=httpx.Timeout(60.0, connect=15.0),
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "close",
                },
            )
        return self._session

    def consultar_demonstrativo(self, car_code: str) -> Dict[str, Any]:
        """
        Consulta dados do demonstrativo de um registro CAR.
        
        Args:
            car_code: Código do registro CAR (ex: SP-3522307-B4A8A1B13D664F0981FB59901F2871CD)
            
        Returns:
            Dicionário com todos os dados do demonstrativo CAR.
            
        Raises:
            CarConsultaError: Se a consulta falhar.
        """
        car_code = car_code.strip()
        url = _DEMONSTRATIVO_URL.format(car_code=car_code)

        logger.info(f"Consultando demonstrativo CAR: {car_code}")

        try:
            session = self._get_session()
            response = session.get(url)

            if response.status_code != 200:
                raise CarConsultaError(
                    f"Erro HTTP {response.status_code} ao consultar CAR {car_code}"
                )

            data = response.json()

            if data.get("status") != "s":
                mensagem = data.get("mensagem", "Erro desconhecido")
                raise CarConsultaError(
                    f"Erro ao consultar CAR {car_code}: {mensagem}"
                )

            dados = data.get("dados", {})
            if not dados:
                raise CarConsultaError(
                    f"Sem dados retornados para CAR {car_code}"
                )

            logger.info(f"Demonstrativo CAR consultado com sucesso: {car_code}")
            return self._formatar_resposta(dados)

        except httpx.HTTPError as e:
            logger.error(f"Erro HTTP ao consultar CAR {car_code}: {e}")
            raise CarConsultaError(f"Erro de comunicação com car.gov.br: {e}") from e
        except CarConsultaError:
            raise
        except Exception as e:
            logger.error(f"Erro inesperado ao consultar CAR {car_code}: {e}")
            raise CarConsultaError(f"Erro inesperado: {e}") from e

    def _formatar_resposta(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formata os dados brutos do CAR em uma estrutura organizada.
        
        Args:
            dados: Dados brutos retornados pela API do car.gov.br
            
        Returns:
            Dados formatados e organizados por seção.
        """
        cabecalho = dados.get("cabecalho", {})
        areas = dados.get("areas", {})
        restricoes = dados.get("restricoes", [])
        tem_ti = dados.get("temTI", False)

        sobreposicoes = {
            "area_sobreposicao_outros_imoveis_ha": areas.get("areaSobreposicaoOutrosImoveis"),
            "area_sobreposicao_terra_indigena_ha": areas.get("areaSobreposicaoTI"),
            "area_sobreposicao_unidade_conservacao_ha": areas.get("areaSobreposicaoUC"),
            "area_sobreposicao_assentamento_ha": areas.get("areaSobreposicaoAssentamento"),
        }

        return {
            "situacao_cadastro": {
                "status": cabecalho.get("statusImovel"),
                "registro_car": cabecalho.get("codigo"),
                "condicao_externa": cabecalho.get("condicaoAnalise"),
                "data_analise": cabecalho.get("dataAnalise"),
                "aderiu_pra": cabecalho.get("aderiuPRA"),
                "condicao_pra": cabecalho.get("condicaoPRA"),
            },
            "dados_imovel": {
                "area_hectares": cabecalho.get("area"),
                "modulos_fiscais": cabecalho.get("modulosFiscais"),
                "municipio": cabecalho.get("municipio"),
                "estado": cabecalho.get("estado"),
                "municipio_uf": f"{cabecalho.get('municipio', '')} ({cabecalho.get('estado', '')})",
                "centroide": {
                    "latitude": cabecalho.get("latitude"),
                    "longitude": cabecalho.get("longitude"),
                    "lat_decimal": cabecalho.get("centroideY"),
                    "lon_decimal": cabecalho.get("centroideX"),
                },
                "data_inscricao": cabecalho.get("dataRegistro"),
                "data_ultima_retificacao": cabecalho.get("dataRetificacao"),
                "houve_retificacao": cabecalho.get("houveRetificacao"),
            },
            "cobertura_solo": {
                "remanescente_vegetacao_nativa_ha": areas.get("areaRVN"),
                "area_rural_consolidada_ha": areas.get("areaUsoConsolidado"),
                "area_pousio_ha": areas.get("areaAP"),
                "area_servidao_administrativa_ha": areas.get("areaServidaoAdministrativa"),
            },
            "reserva_legal": {
                "situacao": areas.get("situacaoRL"),
                "area_rl_averbada_ha": areas.get("areaRLA"),
                "area_rl_aprovada_nao_averbada_ha": areas.get("areaRLANA"),
                "area_rl_proposta_ha": areas.get("areaRLP"),
                "total_rl_declarada_ha": (
                    (areas.get("areaRLA") or 0.0)
                    + (areas.get("areaRLANA") or 0.0)
                    + (areas.get("areaRLP") or 0.0)
                ),
                "area_rl_vetorizada_sobreposta_rvn_ha": areas.get("areaRLVetorizadaSobrepostaRVN"),
                "area_rl_em_app_ha": areas.get("areaRLEmAPP"),
                "area_rl_minima_exigida_lei_ha": areas.get("areaRLMinimaExigidaLei"),
                "area_rl_compensada_de_terceiros_ha": areas.get("areaRLCompensadaDeTerceirosNoIR"),
                "area_rl_compensada_em_terceiros_ha": areas.get("areaRLCompensadaDoIREmTerceiros"),
            },
            "app": {
                "area_app_ha": areas.get("areaAPP"),
                "app_em_area_consolidada_ha": areas.get("areaAPPEmAC"),
                "app_sobreposta_rvn_ha": areas.get("areaAPPSobrepostaRVN"),
            },
            "uso_restrito": {
                "area_uso_restrito_ha": areas.get("areaUsoRestrito"),
                "uso_restrito_sobreposta_rvn_ha": areas.get("areaUsoRestritoSobrepostaRVN"),
            },
            "regularidade_ambiental": {
                "passivo_excedente_rl_ha": areas.get("areaRLExcedentePassivo"),
                "area_rl_recompor_ha": areas.get("areaRLRecompor", 0.0),
                "area_app_recompor_ha": areas.get("areaAPPRecompor"),
                "area_uso_restrito_recompor_ha": areas.get("areaUsoRestritoRecompor", 0.0),
            },
            "informacoes_adicionais": {
                "area_liquida_ha": areas.get("areaLiquida"),
                "sobreposicoes": sobreposicoes,
                "restricoes": restricoes,
                "tem_terra_indigena": tem_ti,
                "data_demonstrativo": cabecalho.get("dataDemonstrativo"),
            },
            "sobreposicoes": sobreposicoes,
            "_dados_brutos": dados,
        }

    def gerar_pdf_demonstrativo(self, car_code: str) -> bytes:
        """
        Gera PDF do demonstrativo CAR no formato oficial.
        
        Args:
            car_code: Código do registro CAR
            
        Returns:
            Bytes do PDF gerado.
            
        Raises:
            CarConsultaError: Se a consulta ou geração falhar.
        """
        dados = self.consultar_demonstrativo(car_code)
        return _gerar_pdf(dados)

    def gerar_pdf_demonstrativo_from_data(self, dados: Dict[str, Any]) -> bytes:
        """
        Gera PDF do demonstrativo a partir de dados já consultados.
        
        Args:
            dados: Dados formatados do demonstrativo.
            
        Returns:
            Bytes do PDF gerado.
        """
        return _gerar_pdf(dados)

    def __del__(self):
        """Fecha sessão HTTP."""
        if self._session:
            try:
                self._session.close()
            except Exception:
                pass


# ====================================================================
# GERAÇÃO DE PDF
# ====================================================================

def _fmt_area(valor) -> str:
    """Formata valor de área para exibição."""
    if valor is None:
        return "-"
    if isinstance(valor, (int, float)):
        if valor == 0.0:
            return "-"
        return f"{valor:,.4f} ha".replace(",", "X").replace(".", ",").replace("X", ".")
    return str(valor)


def _fmt_area_passivo(valor) -> str:
    """Formata valor de passivo/excedente."""
    if valor is None:
        return "-"
    if isinstance(valor, (int, float)):
        if valor == 0.0:
            return "0,00 ha"
        prefix = "(passivo) - " if valor < 0 else "(excedente) "
        return f"{prefix}{abs(valor):,.4f} ha".replace(",", "X").replace(".", ",").replace("X", ".")
    return str(valor)


def _gerar_pdf(dados: Dict[str, Any]) -> bytes:
    """
    Gera PDF do demonstrativo CAR seguindo o layout oficial.
    
    Args:
        dados: Dados formatados do demonstrativo.
        
    Returns:
        Bytes do PDF.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, cm
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
        HRFlowable, KeepTogether,
    )

    buffer = io.BytesIO()
    
    registro = dados.get("situacao_cadastro", {}).get("registro_car", "CAR")
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=f"Demonstrativo CAR - {registro}",
        author="Sistema de Cadastro Ambiental Rural",
        subject="Demonstrativo da Situação das Informações Declaradas no CAR",
        creator="DataGeoPlan",
    )

    # Estilos
    styles = getSampleStyleSheet()
    
    style_titulo = ParagraphStyle(
        "Titulo",
        parent=styles["Heading1"],
        fontSize=14,
        textColor=colors.HexColor("#1B5E20"),
        alignment=TA_CENTER,
        spaceAfter=6,
        spaceBefore=2,
    )
    
    style_secao = ParagraphStyle(
        "Secao",
        parent=styles["Heading2"],
        fontSize=11,
        textColor=colors.white,
        alignment=TA_LEFT,
        spaceBefore=10,
        spaceAfter=4,
        backColor=colors.HexColor("#2E7D32"),
        borderPadding=(4, 6, 4, 6),
    )

    style_subsecao = ParagraphStyle(
        "SubSecao",
        parent=styles["Heading3"],
        fontSize=10,
        textColor=colors.HexColor("#2E7D32"),
        alignment=TA_LEFT,
        spaceBefore=6,
        spaceAfter=2,
    )

    style_label = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#555555"),
    )

    style_valor = ParagraphStyle(
        "Valor",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#222222"),
        fontName="Helvetica-Bold",
    )

    style_info = ParagraphStyle(
        "Info",
        parent=styles["Normal"],
        fontSize=7.5,
        textColor=colors.HexColor("#666666"),
        alignment=TA_JUSTIFY,
        spaceBefore=4,
        spaceAfter=2,
        leading=10,
    )

    style_rodape = ParagraphStyle(
        "Rodape",
        parent=styles["Normal"],
        fontSize=7,
        textColor=colors.HexColor("#999999"),
        alignment=TA_CENTER,
    )

    elements = []

    # ---- Cabeçalho ----
    sit = dados.get("situacao_cadastro", {})
    imovel = dados.get("dados_imovel", {})
    centroide = imovel.get("centroide", {})

    elements.append(Paragraph(
        "Demonstrativo da Situação das Informações<br/>Declaradas no CAR",
        style_titulo,
    ))
    elements.append(Spacer(1, 2 * mm))

    # ---- Seção: Situação do Cadastro ----
    elements.append(_secao_header("Situação do Cadastro", style_secao))
    elements.append(_tabela_dados([
        ("Situação do Cadastro:", sit.get("status", "-")),
        ("Registro de Inscrição no CAR:", sit.get("registro_car", "-")),
        ("Condição Externa:", sit.get("condicao_externa", "-")),
    ], style_label, style_valor))

    # ---- Seção: Dados do Imóvel Rural ----
    elements.append(_secao_header("Dados do Imóvel Rural", style_secao))
    elements.append(_tabela_dados([
        ("Área do Imóvel Rural:", _fmt_area(imovel.get("area_hectares"))),
        ("Módulos Fiscais:", f"{imovel.get('modulos_fiscais', '-')}"),
        ("Município / UF:", imovel.get("municipio_uf", "-")),
        (
            "Coordenadas Geográficas do Centróide:",
            f"Lat: {centroide.get('latitude', '-')}  Long: {centroide.get('longitude', '-')}",
        ),
        ("Data da Inscrição:", imovel.get("data_inscricao", "-")),
        ("Data da Última Retificação:", imovel.get("data_ultima_retificacao", "-")),
    ], style_label, style_valor))

    # ---- Seção: Cobertura do Solo ----
    cobertura = dados.get("cobertura_solo", {})
    elements.append(_secao_header("Cobertura do Solo", style_secao))
    elements.append(_tabela_dados([
        ("Área de Remanescente de Vegetação Nativa:", _fmt_area(cobertura.get("remanescente_vegetacao_nativa_ha"))),
        ("Área Rural Consolidada:", _fmt_area(cobertura.get("area_rural_consolidada_ha"))),
        ("Área de Pousio:", _fmt_area(cobertura.get("area_pousio_ha"))),
        ("Área de Servidão Administrativa:", _fmt_area(cobertura.get("area_servidao_administrativa_ha"))),
    ], style_label, style_valor))

    # ---- Seção: Reserva Legal ----
    rl = dados.get("reserva_legal", {})
    elements.append(_secao_header("Reserva Legal", style_secao))
    elements.append(_tabela_dados([
        ("Localização da Reserva Legal:", rl.get("situacao", "-")),
    ], style_label, style_valor))

    elements.append(Paragraph("Informação Georreferenciada", style_subsecao))
    elements.append(_tabela_dados([
        ("Área de Reserva Legal Averbada:", _fmt_area(rl.get("area_rl_averbada_ha"))),
        ("Área de Reserva Legal Aprovada não Averbada:", _fmt_area(rl.get("area_rl_aprovada_nao_averbada_ha"))),
        ("Área de Reserva Legal Proposta:", _fmt_area(rl.get("area_rl_proposta_ha"))),
        ("Total de Reserva Legal Declarada pelo Proprietário/Possuidor:", _fmt_area(rl.get("total_rl_declarada_ha"))),
    ], style_label, style_valor))

    # ---- Seção: APP ----
    app = dados.get("app", {})
    elements.append(_secao_header("Áreas de Preservação Permanente (APP)", style_secao))
    elements.append(_tabela_dados([
        ("APP:", _fmt_area(app.get("area_app_ha"))),
        ("APP em Área Rural Consolidada:", _fmt_area(app.get("app_em_area_consolidada_ha"))),
        ("APP em Área de Remanescente de Vegetação Nativa:", _fmt_area(app.get("app_sobreposta_rvn_ha"))),
    ], style_label, style_valor))

    # ---- Seção: Uso Restrito ----
    ur = dados.get("uso_restrito", {})
    elements.append(_secao_header("Uso Restrito", style_secao))
    elements.append(_tabela_dados([
        ("Área de Uso Restrito:", _fmt_area(ur.get("area_uso_restrito_ha"))),
        ("Uso Restrito em Remanescente de Vegetação Nativa:", _fmt_area(ur.get("uso_restrito_sobreposta_rvn_ha"))),
    ], style_label, style_valor))

    # ---- Seção: Sobreposições ----
    sobr = dados.get("sobreposicoes", {})
    sobr_items = [
        ("Sobreposição com Outros Imóveis:", _fmt_area(sobr.get("area_sobreposicao_outros_imoveis_ha"))),
        ("Sobreposição com Terra Indígena:", _fmt_area(sobr.get("area_sobreposicao_terra_indigena_ha"))),
        ("Sobreposição com Unidade de Conservação:", _fmt_area(sobr.get("area_sobreposicao_unidade_conservacao_ha"))),
        ("Sobreposição com Assentamento:", _fmt_area(sobr.get("area_sobreposicao_assentamento_ha"))),
    ]
    # Só inclui seção se houver algum valor > 0
    has_sobreposicao = any(
        (sobr.get(k) or 0) > 0
        for k in sobr
    )
    if has_sobreposicao:
        elements.append(_secao_header("Sobreposições", style_secao))
        elements.append(_tabela_dados(sobr_items, style_label, style_valor))
    else:
        elements.append(_secao_header("Sobreposições", style_secao))
        elements.append(Paragraph("&nbsp;&nbsp;Nenhuma sobreposição encontrada.", style_label))

    # ---- Seção: Regularidade Ambiental ----
    reg = dados.get("regularidade_ambiental", {})
    elements.append(_secao_header("Regularidade Ambiental", style_secao))
    elements.append(_tabela_dados([
        ("Passivo / Excedente de Reserva Legal:", _fmt_area_passivo(reg.get("passivo_excedente_rl_ha"))),
        ("Área de Reserva Legal a Recompor:", _fmt_area(reg.get("area_rl_recompor_ha"))),
        ("Área de Preservação Permanente a Recompor:", _fmt_area(reg.get("area_app_recompor_ha"))),
        ("Área de Uso Restrito a Recompor:", _fmt_area(reg.get("area_uso_restrito_recompor_ha"))),
    ], style_label, style_valor))

    # ---- Informações Gerais (disclaimer) ----
    elements.append(Spacer(1, 6 * mm))
    elements.append(_secao_header("Informações Gerais", style_secao))
    
    disclaimers = [
        "1. Este documento apresenta a situação das informações declaradas no CAR relativas "
        "às Áreas de Preservação Permanente, de Reserva Legal e de Uso Restrito, para os fins "
        "do disposto no inciso II do caput do art. 3º do Decreto nº 7.830, de 2012, do art. 51 "
        "da Instrução Normativa MMA nº 02, de 06 de maio de 2014, e da Resolução SFB nº 03, "
        "de 27 de agosto de 2018;",
        "2. As informações prestadas no Cadastro Ambiental Rural são de caráter declaratório "
        "e estão sujeitas à análise pelo órgão competente;",
        "3. As informações constantes neste documento são de natureza pública, nos termos "
        "do artigo 12 da Instrução Normativa MMA nº 02, de 06 de maio de 2014;",
        "4. Este documento não será considerado título para fins de reconhecimento de direito "
        "de propriedade ou posse;",
        "5. Este documento não substitui qualquer licença ou autorização ambiental para "
        "exploração florestal ou supressão de vegetação, como também não dispensa as autorizações "
        "necessárias ao exercício da atividade econômica no imóvel rural.",
    ]
    for d in disclaimers:
        elements.append(Paragraph(d, style_info))

    # ---- Rodapé ----
    adicionais = dados.get("informacoes_adicionais", {})
    data_demo = adicionais.get("data_demonstrativo", "")
    elements.append(Spacer(1, 8 * mm))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CCCCCC")))
    elements.append(Spacer(1, 2 * mm))
    elements.append(Paragraph(
        f"Sistema de Cadastro Ambiental Rural — Documento gerado via DataGeoPlan"
        f"{' — ' + data_demo if data_demo else ''}",
        style_rodape,
    ))

    doc.build(elements)
    return buffer.getvalue()


def _secao_header(texto: str, style):
    """Cria cabeçalho de seção com fundo verde."""
    from reportlab.platypus import Paragraph
    return Paragraph(f"&nbsp;&nbsp;{texto}", style)


def _tabela_dados(items: list, style_label, style_valor):
    """
    Cria tabela com pares label/valor.
    
    Args:
        items: Lista de tuplas (label, valor)
        style_label: Estilo do label
        style_valor: Estilo do valor
        
    Returns:
        Table formatada.
    """
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import Table, TableStyle, Paragraph

    table_data = []
    for label, valor in items:
        table_data.append([
            Paragraph(label, style_label),
            Paragraph(str(valor), style_valor),
        ])

    col_widths = [95 * mm, 85 * mm]
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (0, -1), 8),
        ("LEFTPADDING", (1, 0), (1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#E0E0E0")),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFAFA")),
    ]))
    return table
