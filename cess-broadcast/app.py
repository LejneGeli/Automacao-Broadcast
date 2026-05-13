import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json
import zipfile
import io
import random
import string
import os
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(BASE_DIR, "logo-broadcast.png")
FAVICON = Image.open(LOGO_PATH) if os.path.exists(LOGO_PATH) else "📦"

BRASILIA = ZoneInfo("America/Sao_Paulo")

# ─── CONFIG DA PÁGINA ────────────────────────────────────────────────
st.set_page_config(
    page_title="CESS · Gerador de Broadcast",
    page_icon=FAVICON,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── ESTILO CUSTOMIZADO ───────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --bg:#05080f;
        --panel:rgba(10,26,48,.84);
        --line:rgba(61,151,255,.28);
        --text:#f3f7ff;
        --muted:#a8b8d8;
        --blue:#2f9bff;
        --purple:#6757ff;
    }

    html, body, [data-testid="stAppViewContainer"] {
        background:
            radial-gradient(circle at 10% 88%, rgba(0,78,190,.34), transparent 19rem),
            radial-gradient(circle at 55% 0%, rgba(27,102,255,.22), transparent 18rem),
            radial-gradient(circle at 88% 12%, rgba(103,87,255,.20), transparent 20rem),
            linear-gradient(135deg,#030508 0%,#07101f 42%,#020409 100%) !important;
        color:var(--text);
        font-family:'Inter',sans-serif;
    }

    [data-testid="stHeader"], [data-testid="stToolbar"] { background:transparent !important; }

    .block-container,
    [data-testid="stMainBlockContainer"] {
        max-width:1560px !important;
        width: calc(100% - 5rem) !important;
        padding:2.6rem 2.2rem 2.4rem !important;
        margin:3.2rem auto 2.5rem auto !important;
        position:relative;
        z-index:1;
        border:1px solid rgba(28,113,255,.35);
        border-radius:22px;
        background:rgba(3,10,22,.28);
        box-shadow:0 0 46px rgba(0,91,255,.18), inset 0 0 70px rgba(10,88,180,.08);
    }

    .broadcast-panel {
        width:100%;
        padding:34px 40px 32px;
        border:1px solid var(--line);
        border-radius:20px;
        background:
            linear-gradient(180deg,rgba(15,41,73,.90),rgba(8,20,36,.84)),
            repeating-linear-gradient(90deg,rgba(255,255,255,.018) 0 1px,transparent 1px 8px);
        box-shadow:0 30px 90px rgba(0,0,0,.52), inset 0 1px 0 rgba(255,255,255,.06);
        backdrop-filter:blur(14px);
        margin-bottom:26px;
    }

    .broadcast-top {
        display:flex;
        align-items:center;
        justify-content:space-between;
        gap:22px;
        margin-bottom:24px;
    }

    .broadcast-brand { display:flex; align-items:center; gap:18px; }
    .broadcast-logo-wrap {
        width:72px; height:72px; flex:0 0 72px;
        display:flex; align-items:center; justify-content:center;
        border-radius:14px;
        background:rgba(255,255,255,.96);
        box-shadow:0 0 24px rgba(47,155,255,.22);
        overflow:hidden;
    }
    .broadcast-logo-wrap img {
        width:58px; height:58px; object-fit:contain; display:block;
    }

    .broadcast-title {
        font-size:2.28rem;
        font-weight:800;
        letter-spacing:-.045em;
        margin:0;
        line-height:1.05;
        color:#f7fbff;
    }

    .broadcast-subtitle { color:var(--muted); font-size:.94rem; margin-top:9px; }
    .broadcast-badge {
        border:1px solid rgba(77,159,255,.24);
        background:rgba(5,12,25,.55);
        color:#dceaff;
        padding:8px 14px;
        border-radius:999px;
        font-size:.76rem;
        font-weight:700;
        white-space:nowrap;
    }

    .steps-bar {
        display:grid;
        grid-template-columns:1fr auto 1fr auto 1fr auto 1fr;
        align-items:center;
        gap:12px;
        padding:18px 20px;
        border:1px solid rgba(73,150,255,.22);
        border-radius:18px;
        background:rgba(4,12,28,.38);
        margin:1rem 0 0;
    }
    .step {
        display:flex;
        align-items:center;
        gap:12px;
        background:transparent;
        border:0;
        padding:0;
        min-width:0;
    }
    .step-num {
        background:linear-gradient(135deg,#2f9bff,#1749d7);
        color:#fff;
        font-size:.84rem;
        font-weight:800;
        width:34px;
        height:34px;
        border-radius:50%;
        display:flex;
        align-items:center;
        justify-content:center;
        flex-shrink:0;
        box-shadow:0 0 20px rgba(47,155,255,.38);
    }
    .step-label { color:#c5d5ef; font-size:.86rem; font-weight:600; }
    .step-arrow { color:rgba(132,169,232,.45); font-size:1.35rem; font-weight:700; }

    .schedule-shell {
        border:1px solid rgba(73,150,255,.18);
        border-radius:20px;
        background:rgba(4,12,28,.34);
        padding:26px 24px 22px;
        margin:20px 0 24px;
    }
    .schedule-title {
        color:#f2f7ff;
        font-size:1.05rem;
        font-weight:800;
        margin-bottom:18px;
        display:flex;
        gap:10px;
        align-items:center;
    }
    .horario-grid {
        display:grid;
        grid-template-columns:repeat(14, minmax(82px, 1fr));
        gap:12px;
        margin:0;
    }
    .horario-card {
        min-height:122px;
        background:rgba(10,24,49,.72);
        border:1px solid rgba(98,149,228,.22);
        border-radius:12px;
        padding:14px 12px;
        box-shadow:inset 0 1px 0 rgba(255,255,255,.05);
        display:flex;
        flex-direction:column;
        justify-content:space-between;
    }
    .horario-card .fluxo {
        color:#fff;
        font-weight:800;
        font-size:.98rem;
        background:linear-gradient(135deg,#2f9bff,#2530d0);
        display:inline-block;
        padding:5px 9px;
        border-radius:7px;
        width:max-content;
        box-shadow:0 0 16px rgba(47,155,255,.18);
    }
    .horario-card .hora { color:#eef5ff; font-size:1.02rem; font-weight:800; margin-top:12px; }
    .horario-card .dia { color:#4da9ff; font-weight:800; font-size:.77rem; margin-top:6px; }
    .mini-line { height:5px; width:54px; border-radius:99px; background:rgba(160,181,222,.22); margin-top:10px; overflow:hidden; }
    .mini-line span { display:block; width:22%; height:100%; background:#2f9bff; border-radius:99px; }

    label, [data-testid="stWidgetLabel"] p { color:#eef5ff !important; font-weight:700 !important; }

    [data-testid="stTextInput"] input,
    [data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
    [data-baseweb="select"] > div {
        background:rgba(8,15,32,.78) !important;
        border:1px solid rgba(109,154,220,.34) !important;
        border-radius:10px !important;
        color:white !important;
        min-height:48px;
        box-shadow:inset 0 0 0 1px rgba(255,255,255,.02);
    }
    [data-testid="stTextInput"] input:focus {
        border-color:rgba(58,156,255,.85) !important;
        box-shadow:0 0 0 3px rgba(58,156,255,.18) !important;
    }

    div[data-testid="stButton"] > button,
    div[data-testid="stDownloadButton"] > button {
        min-height:54px;
        border-radius:12px !important;
        border:1px solid rgba(91,84,255,.65) !important;
        background:linear-gradient(90deg,rgba(44,28,127,.96),rgba(21,55,137,.95)) !important;
        color:#fff !important;
        font-weight:800 !important;
        box-shadow:0 0 26px rgba(65,60,255,.22), inset 0 1px 0 rgba(255,255,255,.10);
        transition:transform .18s ease, box-shadow .18s ease, border-color .18s ease;
    }
    div[data-testid="stButton"] > button:hover,
    div[data-testid="stDownloadButton"] > button:hover {
        transform:translateY(-2px);
        border-color:rgba(81,171,255,.85) !important;
        box-shadow:0 0 34px rgba(50,145,255,.30), inset 0 1px 0 rgba(255,255,255,.14);
    }

    .retroativo-btn > div[data-testid="stButton"] > button {
        width:auto !important;
        min-height:44px !important;
        padding:.45rem 1.2rem !important;
        background:rgba(16,55,111,.72) !important;
        color:#dceaff !important;
        border:1px solid rgba(77,159,255,.32) !important;
    }

    [data-testid="stAlert"] {
        border-radius:12px !important;
        border:1px solid rgba(75,151,255,.20) !important;
        background:rgba(8,25,49,.46) !important;
        box-shadow:none !important;
    }

    hr { border-color:rgba(75,151,255,.24) !important; margin:1.8rem 0 !important; }

    .section-card {
        border:1px solid rgba(73,150,255,.18);
        border-radius:20px;
        background:rgba(4,12,28,.34);
        padding:24px;
        margin:20px 0 24px;
    }

    .broadcast-footer {
        display:flex;
        justify-content:flex-end;
        align-items:center;
        gap:10px;
        color:#eef4ff;
        font-size:.84rem;
        margin-top:24px;
    }
    .broadcast-footer span {
        background:rgba(255,255,255,.08);
        border-radius:999px;
        padding:5px 12px;
        font-weight:800;
    }

    @media (max-width:1100px) {
        .horario-grid { grid-template-columns:repeat(4, minmax(110px, 1fr)); }
        .steps-bar { grid-template-columns:1fr; }
        .step-arrow { display:none; }
    }
    @media (max-width:800px) {
        .block-container,[data-testid="stMainBlockContainer"] { width:calc(100% - 1rem) !important; padding:1rem !important; margin:1rem auto !important; }
        .broadcast-panel { padding:24px 20px; }
        .broadcast-top { display:grid; grid-template-columns:1fr; }
        .broadcast-title { font-size:1.55rem; }
        .horario-grid { grid-template-columns:repeat(2, minmax(110px, 1fr)); }
    }
</style>
""", unsafe_allow_html=True)

# ─── FUNÇÕES ──────────────────────────────────────────────────────────

def gerar_id_aleatorio(tamanho=20):
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(tamanho))


@st.cache_resource(show_spinner=False)
def conectar_sheets():
    """Conecta ao Google Sheets usando st.secrets (deploy seguro)."""
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    return gspread.authorize(creds)




def _rgb_para_hex(bg: dict) -> str:
    """Converte o RGB retornado pela API do Google Sheets para #RRGGBB."""
    r = round(bg.get("red", 1) * 255)
    g = round(bg.get("green", 1) * 255)
    b = round(bg.get("blue", 1) * 255)
    return f"#{r:02X}{g:02X}{b:02X}"


def _buscar_cores_api(client, spreadsheet_id: str, range_str: str) -> list:
    """Busca as cores de fundo de um intervalo usando a API v4 do Google Sheets."""
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"
    response = client.http_client.request(
        "GET",
        url,
        params={
            "ranges": range_str,
            "fields": "sheets.data.rowData.values.effectiveFormat.backgroundColor",
            "includeGridData": "true",
        },
    )
    try:
        return response.json()["sheets"][0]["data"][0].get("rowData", [])
    except (KeyError, IndexError, ValueError):
        return []


def buscar_mapeamento_contas(client, spreadsheet_name: str) -> dict:
    """
    Lê as cores de D2:D5 da aba 'Como funciona?' e monta:
    { '#RRGGBB': 'Conta_1', '#RRGGBB': 'Conta_2', ... }
    """
    spreadsheet = client.open(spreadsheet_name)
    row_data = _buscar_cores_api(client, spreadsheet.id, "'Como funciona?'!D2:D5")

    mapeamento = {}
    for i, row in enumerate(row_data, start=1):
        try:
            bg = row["values"][0]["effectiveFormat"]["backgroundColor"]
            hex_cor = _rgb_para_hex(bg)
            if hex_cor != "#FFFFFF":
                mapeamento[hex_cor] = f"Conta_{i}"
        except (KeyError, IndexError, TypeError):
            pass

    return mapeamento


def buscar_cores_linhas(client, spreadsheet_name: str, worksheet_name: str, linha_inicio_sheet: int, quantidade: int) -> list:
    """Retorna as cores da coluna A nas linhas dos cursos encontrados."""
    spreadsheet = client.open(spreadsheet_name)
    linha_fim = linha_inicio_sheet + quantidade - 1
    range_str = f"'{worksheet_name}'!A{linha_inicio_sheet}:A{linha_fim}"
    row_data = _buscar_cores_api(client, spreadsheet.id, range_str)

    cores = []
    for row in row_data:
        try:
            bg = row["values"][0]["effectiveFormat"]["backgroundColor"]
            hex_cor = _rgb_para_hex(bg)
        except (KeyError, IndexError, TypeError):
            hex_cor = "#FFFFFF"
        cores.append(hex_cor)

    while len(cores) < quantidade:
        cores.append("#FFFFFF")

    return cores[:quantidade]

def buscar_cursos_planilha(semana_alvo: str):
    try:
        client = conectar_sheets()
        aba = client.open("Informações Webhook").worksheet("Cursos 2026")
        dados = aba.get_all_values()

        linha_data = next(
            (i for i, l in enumerate(dados) if len(l) > 1 and semana_alvo in str(l[1])),
            None
        )
        if linha_data is None:
            return []

        cursos = []
        indices_linhas = []
        for i in range(linha_data + 2, len(dados)):
            linha = dados[i]
            if not linha or not linha[0].strip():
                break
            if len(linha) > 1 and "Semana" in str(linha[1]) and i > linha_data + 2:
                break
            cursos.append({
                "nome": linha[0].strip(),
                "tags": {f: linha[13 + f].strip() if len(linha) > 13 + f else "" for f in range(1, 9)}
            })
            indices_linhas.append(i)

        if cursos:
            mapeamento_contas = buscar_mapeamento_contas(client, "Informações Webhook")
            cores_linhas = buscar_cores_linhas(
                client,
                "Informações Webhook",
                "Cursos 2026",
                indices_linhas[0] + 1,
                len(cursos),
            )

            for curso, cor in zip(cursos, cores_linhas):
                curso["cor"] = cor
                curso["conta"] = mapeamento_contas.get(cor, "Sem_Conta")

        return cursos

    except Exception as e:
        st.error(f"❌ Erro ao ler planilha: {e}")
        return []


def montar_json_unnichat(nome: str, timestamp: int, tag_gatilho: str) -> dict:
    """Estrutura padrão (F1–F8): adiciona tag no perfil do aluno."""
    id_root = gerar_id_aleatorio()
    id_action = gerar_id_aleatorio()
    return {
        "status": "draft",
        "sendType": "scheduled",
        "name": nome,
        "templateId": "",
        "firstStepType": "node",
        "bodyParameters": [],
        "urlButtonParameters": [],
        "headerParameters": [],
        "audit": {
            "userId": "cess_manual_gen",
            "userEmail": "automacao@cess.com.br"
        },
        "sendAt": timestamp,
        "automation": {
            "name": nome,
            "category": "automation",
            "status": "idle",
            "connectionType": "whatsapp",
            "node": {
                "id": id_root,
                "type": {"id": id_root, "tag": "init", "color": "transparent", "icon": "init"},
                "sonId": id_action,
                "pos": "{\"x\":-84.52275666567903,\"y\":2.315691963443271}",
                "triggers": [{"interaction": "broadcast"}],
                "nodes": [{
                    "pos": "{\"x\":250.1006223932327,\"y\":16.522330585760557}",
                    "action": {
                        "userResourceGroupSendRandomic": False,
                        "unniiaAtributionOnly": False,
                        "keepChatActive": False,
                        "forceAttribution": False,
                        "type": "add_tag",
                        "tags": [tag_gatilho.strip()]
                    },
                    "id": id_action,
                    "type": {"color": "transparent", "tag": "action", "id": "action", "icon": ""}
                }]
            }
        }
    }


def montar_json_foward(nome: str, timestamp: int) -> dict:
    """Estrutura fowardAutomation (F2.1 e F5.1): encaminha para outra automação."""
    id_root = gerar_id_aleatorio()
    id_foward = gerar_id_aleatorio()
    return {
        "status": "draft",
        "sendType": "scheduled",
        "name": nome,
        "templateId": "",
        "firstStepType": "node",
        "bodyParameters": [],
        "urlButtonParameters": [],
        "headerParameters": [],
        "audit": {
            "userId": "cess_manual_gen",
            "userEmail": "automacao@cess.com.br"
        },
        "sendAt": timestamp,
        "automation": {
            "name": nome,
            "category": "automation",
            "status": "idle",
            "connectionType": "whatsapp",
            "node": {
                "id": id_root,
                "type": {"id": id_root, "tag": "init", "color": "transparent", "icon": "init"},
                "sonId": id_foward,
                "pos": "{\"x\":-84.52275666567903,\"y\":2.315691963443271}",
                "triggers": [{"interaction": "broadcast"}],
                "nodes": [{
                    "id": id_foward,
                    "pos": "{\"x\":226.38069856306106,\"y\":67.68179143894525}",
                    "type": {
                        "id": "fowardAutomation",
                        "tag": "fowardAutomation",
                        "color": "transparent",
                        "icon": ""
                    },
                    "fowardAutomation": {
                        "automationType": "whatsapp",
                        "automationId": "",
                        "automationName": ""
                    }
                }]
            },
            "customFieldsToCreate": {}
        }
    }


def intervalo_retroativo(total_cursos: int) -> int:
    """Retorna o intervalo em segundos entre disparos com base na quantidade de cursos."""
    if total_cursos <= 20:
        return 120   # 2min
    elif total_cursos <= 30:
        return 60    # 1min
    elif total_cursos <= 50:
        return 45    # 45s
    else:
        return 40    # 40s


def montar_json_retomada(nome: str, timestamp: int, data_disparo: str) -> dict:
    """Estrutura Retroativo: add_tag 'Super Chance - Retroativo DD/MM' → fowardAutomation."""
    id_root   = gerar_id_aleatorio()
    id_action = gerar_id_aleatorio()
    id_foward = gerar_id_aleatorio()
    tag = f"Super Chance - Retroativo {data_disparo}"
    return {
        "status": "draft",
        "sendType": "scheduled",
        "name": nome,
        "templateId": "",
        "firstStepType": "node",
        "bodyParameters": [],
        "urlButtonParameters": [],
        "headerParameters": [],
        "audit": {
            "userId": "cess_manual_gen",
            "userEmail": "automacao@cess.com.br"
        },
        "sendAt": timestamp,
        "automation": {
            "name": nome,
            "category": "automation",
            "status": "idle",
            "connectionType": "whatsapp",
            "node": {
                "id": id_root,
                "type": {"id": id_root, "tag": "init", "color": "transparent", "icon": "init"},
                "sonId": id_action,
                "pos": "{\"x\":-84.52275666567903,\"y\":2.315691963443271}",
                "triggers": [{"interaction": "broadcast"}],
                "nodes": [
                    {
                        "id": id_action,
                        "sonId": id_foward,
                        "pos": "{\"x\":226.38069856306106,\"y\":67.68179143894525}",
                        "type": {"id": "action", "tag": "action", "color": "transparent", "icon": ""},
                        "action": {
                            "userResourceGroupSendRandomic": False,
                            "unniiaAtributionOnly": False,
                            "keepChatActive": False,
                            "forceAttribution": False,
                            "type": "add_tag",
                            "tags": [tag]
                        }
                    },
                    {
                        "id": id_foward,
                        "pos": "{\"x\":550.0,\"y\":67.68179143894525}",
                        "type": {"id": "fowardAutomation", "tag": "fowardAutomation", "color": "transparent", "icon": ""},
                        "fowardAutomation": {
                            "automationType": "whatsapp",
                            "automationId": "",
                            "automationName": ""
                        }
                    }
                ]
            },
            "customFieldsToCreate": {}
        }
    }


def montar_json_sc(nome: str, timestamp: int) -> dict:
    """Estrutura SC (SC1, SC2, SC3): randomizer + delays + fowardAutomation."""
    id_root     = gerar_id_aleatorio()
    id_rand     = gerar_id_aleatorio()
    id_delay1   = gerar_id_aleatorio()  # delay 1s
    id_delay2   = gerar_id_aleatorio()  # delay 37s
    id_delay3   = gerar_id_aleatorio()  # delay 74s
    id_foward   = gerar_id_aleatorio()
    # IDs das variações do randomizer
    v_ids = [gerar_id_aleatorio() for _ in range(6)]

    return {
        "status": "draft",
        "sendType": "scheduled",
        "name": nome,
        "templateId": "",
        "firstStepType": "node",
        "bodyParameters": [],
        "urlButtonParameters": [],
        "headerParameters": [],
        "audit": {
            "userId": "cess_manual_gen",
            "userEmail": "automacao@cess.com.br"
        },
        "sendAt": timestamp,
        "automation": {
            "name": nome,
            "category": "automation",
            "status": "idle",
            "connectionType": "whatsapp",
            "node": {
                "id": id_root,
                "type": {"id": "FvqYATbUWkycagVBc7np", "tag": "init", "color": "transparent", "icon": "init"},
                "sonId": id_rand,
                "pos": "{\"x\":-142.85694973433232,\"y\":0}",
                "triggers": [{"interaction": "broadcast"}],
                "nodes": [
                    {
                        "id": id_rand,
                        "pos": "{\"x\":224.68482789256495,\"y\":-23.1596685596694}",
                        "type": {"id": "randomizer", "tag": "randomizer", "color": "transparent", "icon": ""},
                        "randomizer": {
                            "randomPathAlways": True,
                            "variations": [
                                {"id": v_ids[0], "value": 17, "sonId": id_delay1},
                                {"id": v_ids[1], "value": 17, "sonId": id_delay2},
                                {"id": v_ids[2], "value": 17, "sonId": id_delay3},
                                {"id": v_ids[3], "value": 17},
                                {"id": v_ids[4], "value": 17},
                                {"id": v_ids[5], "value": 15}
                            ]
                        }
                    },
                    {
                        "id": id_delay1,
                        "sonId": id_foward,
                        "pos": "{\"x\":635.0418438703014,\"y\":-318.0380288731563}",
                        "type": {"id": "delay", "tag": "delay", "color": "transparent", "icon": ""},
                        "delay": {
                            "type": "seconds", "time": 1,
                            "isComercialInterval": False,
                            "sendMessagesIntervalRangeType": "minutes",
                            "sendMessagesIntervalRange": [10, 201]
                        }
                    },
                    {
                        "id": id_delay2,
                        "sonId": id_foward,
                        "pos": "{\"x\":641.003547142757,\"y\":15.968382275369265}",
                        "type": {"id": "delay", "tag": "delay", "color": "transparent", "icon": ""},
                        "delay": {
                            "type": "seconds", "time": 37,
                            "isComercialInterval": False,
                            "commercialTimeRangeMinutes": False,
                            "sendMessagesIntervalRangeType": "minutes",
                            "sendMessagesIntervalRange": [10, 201]
                        }
                    },
                    {
                        "id": id_delay3,
                        "sonId": id_foward,
                        "pos": "{\"x\":647.493201624593,\"y\":376.41889199723454}",
                        "type": {"id": "delay", "tag": "delay", "color": "transparent", "icon": ""},
                        "delay": {
                            "type": "seconds", "time": 74,
                            "isComercialInterval": False,
                            "commercialTimeRangeMinutes": False,
                            "sendMessagesIntervalRangeType": "minutes",
                            "sendMessagesIntervalRange": [10, 201]
                        }
                    },
                    {
                        "id": id_foward,
                        "pos": "{\"x\":1154.1893313384387,\"y\":63.04434286060467}",
                        "type": {"id": "fowardAutomation", "tag": "fowardAutomation", "color": "transparent", "icon": ""},
                        "fowardAutomation": {
                            "automationType": "whatsapp",
                            "automationId": "",
                            "automationName": ""
                        }
                    }
                ]
            },
            "customFieldsToCreate": {}
        }
    }


# ─── CRONOGRAMA ───────────────────────────────────────────────────────
OFFSETS = {1: 0, 2: 1, "2.1": 1, 3: 1, 4: 2, 5: 2, "5.1": 2, 6: 2, 7: 2, 8: 3,
           "SC0": 3, "SC1": 8, "SC2": 17, "SC3": 24}
H_MAP = {
    1:     (10, 30, "Segunda"),
    2:     (8,  0,  "Terça"),
    "2.1": (16, 0,  "Terça"),
    3:     (19, 0,  "Terça"),
    4:     (7,  40, "Quarta"),
    5:     (12, 0,  "Quarta"),
    "5.1": (15, 0,  "Quarta"),
    6:     (18, 0,  "Quarta"),
    7:     (19, 50, "Quarta"),
    8:     (10, 30, "Quinta"),
    "SC0": (8, 0, "Quinta"),
    "SC1": (9,  0,  "Terça +1sem"),
    "SC2": (9,  0,  "Quinta +2sem"),
    "SC3": (9,  30, "Quinta +3sem"),
}


# ─── INTERFACE ────────────────────────────────────────────────────────

st.markdown(f"""
<div class="broadcast-panel">
    <div class="broadcast-top">
        <div class="broadcast-brand">
            <div class="broadcast-logo-wrap"><img src="data:image/png;base64,{__import__('base64').b64encode(open(LOGO_PATH, 'rb').read()).decode() if os.path.exists(LOGO_PATH) else ''}" alt="Logo Broadcast"></div>
            <div>
                <h1 class="broadcast-title">CESS · Gerador de Broadcast</h1>
                <div class="broadcast-subtitle">Crie e envie mensagens para seus cursos de forma rápida e eficiente.</div>
            </div>
        </div>
        <div class="broadcast-badge">CESS Broadcast System · 2026</div>
    </div>
    <div class="steps-bar">
      <div class="step"><span class="step-num">1</span><span class="step-label">Digite a data da segunda-feira</span></div>
      <div class="step-arrow">→</div>
      <div class="step"><span class="step-num">2</span><span class="step-label">Selecione os cursos e o fluxo</span></div>
      <div class="step-arrow">→</div>
      <div class="step"><span class="step-num">3</span><span class="step-label">Clique em Gerar Pacote ZIP</span></div>
      <div class="step-arrow">→</div>
      <div class="step"><span class="step-num">4</span><span class="step-label">Baixe e importe no UnniChat</span></div>
    </div>
</div>
""", unsafe_allow_html=True)

# Cronograma visual
cards_html = []
for f_num, (h, m, dia) in H_MAP.items():
    label_fluxo = 'F' + str(f_num) if isinstance(f_num, int) or f_num in ['2.1', '5.1'] else f_num
    cards_html.append(
        f'<div class="horario-card">'
        f'<div>'
        f'<div class="fluxo">{label_fluxo}</div>'
        f'<div class="hora">{h:02d}:{m:02d}</div>'
        f'<div class="dia">{dia}</div>'
        f'</div>'
        f'<div class="mini-line"><span></span></div>'
        f'</div>'
    )

st.markdown(f"""
<div class="schedule-shell">
    <div class="schedule-title">📅 Cronograma de Fluxos</div>
    <div class="horario-grid">{''.join(cards_html)}</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── Session state ─────────────────────────────────────────────────────
if "modo_retroativo" not in st.session_state:
    st.session_state.modo_retroativo = False

# ── Layout de entrada ───────────────────────────────────────────
col_in, col_cfg = st.columns([1, 2])

with col_in:
    # Campo de data — sempre presente
    if st.session_state.modo_retroativo:
        ret_busca = st.text_input(
            "Nome da semana na planilha",
            placeholder="ex: Retroativo - T 2025",
            help="Digite o nome exato da semana como aparece na coluna B da planilha."
        )
        ret_data = st.text_input(
            "Dia do disparo",
            placeholder="DD/MM  ex: 15/07",
            help="Data em que o Broadcast de Retroativo será disparado."
        )
        ret_hora = st.text_input(
            "Horário inicial de disparo",
            placeholder="HH:MM  ex: 12:00",
            help="Horário do primeiro disparo. Os demais serão +2 min por curso."
        )
    else:
        data_ref = st.text_input(
            "Segunda-feira da semana",
            placeholder="DD/MM  ex: 02/02",
            help="Digite a data da segunda-feira da semana que deseja gerar."
        )
        ret_busca = ret_data = ret_hora = None

    # Botão sempre por último na coluna esquerda
    st.markdown('<div class="retroativo-btn">', unsafe_allow_html=True)
    label_btn = "Cancelar Retroativo" if st.session_state.modo_retroativo else "Retroativo"
    if st.button(label_btn, key="btn_retroativo"):
        st.session_state.modo_retroativo = not st.session_state.modo_retroativo
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

with col_cfg:
    # ── MODO RETOMADA ──────────────────────────────────────────────────
    if st.session_state.modo_retroativo:
        if ret_busca:
            with st.spinner("Buscando cursos na planilha..."):
                lista_ret = buscar_cursos_planilha(ret_busca)

            if lista_ret:
                st.success(f"✅ {len(lista_ret)} curso(s) encontrado(s) para **{ret_busca}**")
                nomes_ret = [c["nome"] for c in lista_ret]
                cursos_ret_sel = st.multiselect(
                    "Cursos (vazio = todos)",
                    nomes_ret,
                    help="Deixe em branco para incluir todos os cursos."
                )

                campos_ok = ret_data and ret_hora
                if not campos_ok:
                    st.info("Preencha o dia e o horário de disparo para gerar.")

                if campos_ok and st.button("Gerar Pacote ZIP — Retroativo"):
                    try:
                        d_ret, m_ret = map(int, ret_data.strip().split("/"))
                        h_ret, min_ret = map(int, ret_hora.strip().split(":"))
                    except ValueError:
                        st.error("Formato inválido. Use DD/MM para a data e HH:MM para o horário.")
                        st.stop()

                    cursos_alvo = [c for c in lista_ret if c["nome"] in cursos_ret_sel] if cursos_ret_sel else lista_ret
                    total = len(cursos_alvo)
                    intervalo_s = intervalo_retroativo(total)

                    # Info do intervalo aplicado
                    if intervalo_s == 120:
                        info_intervalo = "2min por curso (até 20 cursos)"
                    elif intervalo_s == 60:
                        info_intervalo = "1min por curso (21–30 cursos)"
                    elif intervalo_s == 45:
                        info_intervalo = "45s por curso (31–50 cursos)"
                    else:
                        info_intervalo = "40s por curso (mais de 50 cursos)"
                    st.info(f"⏱ {total} curso(s) detectado(s) — intervalo aplicado: **{info_intervalo}**")

                    progresso = st.progress(0, text="Gerando arquivos...")
                    counter = 0
                    zip_buffer = io.BytesIO()

                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                        contadores_por_conta = {}
                        for c_data in cursos_alvo:
                            conta_pasta = c_data.get("conta", "Sem_Conta")
                            contador_delay_conta = contadores_por_conta.get(conta_pasta, 0)

                            dt = datetime(2026, m_ret, d_ret, h_ret, min_ret, tzinfo=BRASILIA) + timedelta(seconds=(contador_delay_conta * intervalo_s))
                            nome_final = f"Retroativo {ret_data} - {c_data['nome']}"
                            json_obj = montar_json_retomada(nome_final, int(dt.timestamp() * 1000), ret_data)
                            nome_arq = nome_final.replace("/", "_")
                            zf.writestr(f"Retroativo/{conta_pasta}/{nome_arq}.json", json.dumps(json_obj, indent=2, ensure_ascii=False))

                            contadores_por_conta[conta_pasta] = contador_delay_conta + 1
                            counter += 1
                            progresso.progress(counter / total, text=f"Gerando: {nome_final}")

                    progresso.empty()
                    st.success(f"✅ {counter} arquivo(s) de Retroativo gerado(s) com sucesso!")
                    st.download_button(
                        label="Baixar ZIP para Importação",
                        data=zip_buffer.getvalue(),
                        file_name=f"Import_CESS_Retroativo_{ret_data.replace('/', '_')}.zip",
                        mime="application/zip"
                    )
            else:
                st.warning(f"⚠️ Nenhum curso encontrado para **{ret_busca}**. Verifique o nome na planilha.")

    # ── MODO FLUXO NORMAL ──────────────────────────────────────────────
    else:
        if data_ref:
            with st.spinner("Buscando cursos na planilha..."):
                lista = buscar_cursos_planilha(data_ref)

            if lista:
                st.success(f"✅ {len(lista)} curso(s) encontrado(s) para a semana de **{data_ref}**")

                col_a, col_b = st.columns(2)
                with col_a:
                    nomes = [c["nome"] for c in lista]
                    cursos_sel = st.multiselect(
                        "Cursos (vazio = todos)",
                        nomes,
                        help="Deixe em branco para incluir todos os cursos."
                    )
                with col_b:
                    fluxo_sel = st.selectbox(
                        "Fluxo",
                        ["Todos", "F1", "F2", "F2.1", "F3", "F4", "F5", "F5.1", "F6", "F7", "F8", "SC0", "SC1", "SC2", "SC3"]
                    )

                if st.button("Gerar Pacote ZIP"):
                    cursos_alvo = [c for c in lista if c["nome"] in cursos_sel] if cursos_sel else lista

                    if fluxo_sel == "Todos":
                        fluxos_alvo = list(H_MAP.keys())
                    elif fluxo_sel.startswith("SC"):
                        fluxos_alvo = [fluxo_sel]
                    elif "." in fluxo_sel:
                        fluxos_alvo = [fluxo_sel[1:]]
                    else:
                        fluxos_alvo = [int(fluxo_sel[1])]

                    total = len(cursos_alvo) * len(list(fluxos_alvo))
                    progresso = st.progress(0, text="Gerando arquivos...")
                    counter = 0
                    zip_buffer = io.BytesIO()

                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                        contadores_por_fluxo_conta = {f_num: {} for f_num in fluxos_alvo}

                        for c_data in cursos_alvo:
                            conta_pasta = c_data.get("conta", "Sem_Conta")

                            for f_num in fluxos_alvo:
                                contadores_conta = contadores_por_fluxo_conta[f_num]
                                contador_delay_conta = contadores_conta.get(conta_pasta, 0)

                                h, m, _ = H_MAP[f_num]
                                d_ref, m_ref = map(int, data_ref.split("/"))
                                dt = datetime(2026, m_ref, d_ref, h, m, tzinfo=BRASILIA) + timedelta(days=OFFSETS[f_num])
                                dt += timedelta(minutes=(contador_delay_conta * 2))

                                nome_final = f"{data_ref} - F{f_num} - {c_data['nome']}"
                                if f_num in ("SC0", "SC1", "SC2", "SC3"):
                                    nome_final = f"{f_num} {data_ref} - {c_data['nome']}"
                                    json_obj = montar_json_sc(nome_final, int(dt.timestamp() * 1000))
                                elif f_num in ("2.1", "5.1"):
                                    json_obj = montar_json_foward(nome_final, int(dt.timestamp() * 1000))
                                else:
                                    tag = c_data["tags"].get(f_num, "")
                                    json_obj = montar_json_unnichat(nome_final, int(dt.timestamp() * 1000), tag)

                                nome_arq = nome_final.replace("/", "_")
                                zf.writestr(f"Fluxo_{f_num}/{conta_pasta}/{nome_arq}.json", json.dumps(json_obj, indent=2, ensure_ascii=False))

                                contadores_conta[conta_pasta] = contador_delay_conta + 1
                                counter += 1
                                progresso.progress(counter / total, text=f"Gerando: {nome_final}")

                    progresso.empty()
                    st.success(f"✅ {counter} arquivo(s) gerado(s) com sucesso!")
                    st.download_button(
                        label="Baixar ZIP para Importação",
                        data=zip_buffer.getvalue(),
                        file_name=f"Import_CESS_{data_ref.replace('/', '_')}.zip",
                        mime="application/zip"
                    )
            else:
                st.warning(f"⚠️ Nenhum curso encontrado para a semana de **{data_ref}**. Verifique a data e a planilha.")
st.markdown("""<div class="broadcast-footer"><strong>CESS Broadcast System</strong><span>2026</span><div>Versão Web Estável</div></div>""", unsafe_allow_html=True)
