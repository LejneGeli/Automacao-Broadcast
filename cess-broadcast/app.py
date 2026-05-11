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

BRASILIA = ZoneInfo("America/Sao_Paulo")

# ─── CONFIG DA PÁGINA ────────────────────────────────────────────────
st.set_page_config(
    page_title="CESS · Gerador de Broadcast",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ─── ESTILO CUSTOMIZADO ───────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    .stApp {
        background: #0d0d0d;
        color: #f0f0f0;
    }

    .main-header {
        font-family: 'Space Mono', monospace;
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -1px;
        color: #f0f0f0;
        border-bottom: 2px solid #1e5fad;
        padding-bottom: 0.5rem;
        margin-bottom: 0.25rem;
    }

    .sub-header {
        color: #888;
        font-size: 0.9rem;
        margin-bottom: 2rem;
        font-family: 'Space Mono', monospace;
    }

    .horario-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.5rem;
        margin: 1rem 0;
    }

    .horario-card {
        background: #0f1e35;
        border: 1px solid #1a3a5c;
        border-radius: 6px;
        padding: 0.6rem 0.8rem;
        font-family: 'Space Mono', monospace;
        font-size: 0.75rem;
    }

    .horario-card .dia { color: #4d9de0; font-weight: 700; }
    .horario-card .hora { color: #f0f0f0; font-size: 1rem; margin: 0.1rem 0; }
    .horario-card .fluxo { color: #fff; font-weight: 700; font-size: 0.85rem; background: #1e5fad; display: inline-block; padding: 0.1rem 0.45rem; border-radius: 4px; margin-bottom: 0.3rem; }

    div[data-testid="stButton"] > button {
        background: #1e5fad !important;
        color: #fff !important;
        font-family: 'Space Mono', monospace !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.6rem 1.5rem !important;
        width: 100%;
        font-size: 0.9rem !important;
        letter-spacing: 0.5px !important;
        transition: opacity 0.2s !important;
    }

    div[data-testid="stButton"] > button:hover {
        opacity: 0.85 !important;
    }

    div[data-testid="stDownloadButton"] > button {
        background: #0f1e35 !important;
        color: #4d9de0 !important;
        border: 1px solid #1e5fad !important;
        font-family: 'Space Mono', monospace !important;
        font-weight: 700 !important;
        border-radius: 6px !important;
        padding: 0.6rem 1.5rem !important;
        width: 100%;
    }

    .stTextInput > div > div > input {
        background: #0f1e35 !important;
        border: 1px solid #1a3a5c !important;
        color: #f0f0f0 !important;
        border-radius: 6px !important;
        font-family: 'Space Mono', monospace !important;
    }

    .stTextInput > div > div > input:focus {
        border-color: #1e5fad !important;
        box-shadow: 0 0 0 1px #1e5fad !important;
    }

    .stMultiSelect > div, .stSelectbox > div {
        background: #0f1e35 !important;
    }

    .stSuccess {
        background: #0a1a2e !important;
        border-color: #1e5fad !important;
    }

    label { color: #aaa !important; font-size: 0.85rem !important; }

    .steps-bar {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin: 1rem 0 1.5rem 0;
        flex-wrap: wrap;
    }

    .step {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        background: #0f1e35;
        border: 1px solid #1a3a5c;
        border-radius: 6px;
        padding: 0.4rem 0.8rem;
    }

    .step-num {
        background: #1e5fad;
        color: #fff;
        font-family: 'Space Mono', monospace;
        font-size: 0.7rem;
        font-weight: 700;
        width: 1.3rem;
        height: 1.3rem;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
    }

    .step-label {
        color: #aaa;
        font-size: 0.78rem;
        font-family: 'DM Sans', sans-serif;
    }

    .step-arrow {
        color: #1a3a5c;
        font-size: 1rem;
        font-weight: 700;
    }

    .badge {
        display: inline-block;
        background: #0f1e35;
        border: 1px solid #1e5fad;
        color: #4d9de0;
        font-family: 'Space Mono', monospace;
        font-size: 0.7rem;
        padding: 0.15rem 0.5rem;
        border-radius: 20px;
        margin-right: 0.3rem;
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


def montar_json_sc(nome: str, timestamp: int) -> dict:
    """Estrutura para fluxos SC (SC1, SC2, SC3): sem tag, apenas broadcast."""
    id_root = gerar_id_aleatorio()
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
                "sonId": "",
                "pos": "{\"x\":-84.52275666567903,\"y\":2.315691963443271}",
                "triggers": [{"interaction": "broadcast"}],
                "nodes": []
            }
        }
    }


def montar_json_foward(nome: str, timestamp: int) -> dict:
    """Estrutura para fluxos de Foward (F2.1, F5.1)."""
    id_root = gerar_id_aleatorio()
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
                "sonId": "",
                "pos": "{\"x\":-84.52275666567903,\"y\":2.315691963443271}",
                "triggers": [{"interaction": "broadcast"}],
                "nodes": []
            }
        }
    }


def montar_json_retomada(nome: str, timestamp: int, semana: str) -> dict:
    """Estrutura para fluxo de Retomada."""
    id_root = gerar_id_aleatorio()
    id_action = gerar_id_aleatorio()
    tag_limpeza = f"RETOMADA {semana}"
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
                        "tags": [tag_limpeza]
                    },
                    "id": id_action,
                    "type": {"color": "transparent", "tag": "action", "id": "action", "icon": ""}
                }]
            }
        }
    }


def intervalo_retroativo(total_cursos: int) -> int:
    """Define o intervalo em segundos baseado na quantidade de cursos."""
    if total_cursos <= 20:
        return 120  # 2 min
    elif total_cursos <= 30:
        return 60   # 1 min
    elif total_cursos <= 50:
        return 45   # 45 seg
    else:
        return 40   # 40 seg


# ─── CONSTANTES DE HORÁRIOS ───────────────────────────────────────────
H_MAP = {
    1: (12, 0, "Seg"),
    2: (12, 0, "Ter"),
    "2.1": (18, 0, "Ter"),
    3: (12, 0, "Qua"),
    4: (12, 0, "Qui"),
    5: (12, 0, "Sex"),
    "5.1": (18, 0, "Sex"),
    6: (12, 0, "Sáb"),
    7: (12, 0, "Dom"),
    8: (12, 0, "Seg+1"),
    "SC1": (18, 0, "Seg"),
    "SC2": (18, 0, "Ter"),
    "SC3": (18, 0, "Qua"),
}

OFFSETS = {
    1: 0, 2: 1, "2.1": 1, 3: 2, 4: 3, 5: 4, "5.1": 4, 6: 5, 7: 6, 8: 7,
    "SC1": 0, "SC2": 1, "SC3": 2
}


# ─── INTERFACE ────────────────────────────────────────────────────────

st.markdown('<div class="main-header">CESS · Gerador de Broadcast</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Geração automatizada de arquivos JSON para o UnniChat</div>', unsafe_allow_html=True)

# Estado para alternar entre modo normal e retroativo
if "modo_retroativo" not in st.session_state:
    st.session_state.modo_retroativo = False

# Sidebar / Info rápida
with st.sidebar:
    st.write("### 📅 Grade de Horários")
    for f, (h, m, d) in H_MAP.items():
        st.write(f"**F{f}**: {d} às {h:02d}:{m:02d}")

# ── GRID DE PASSOS ───────────────────────────────────────────────────
st.markdown(f"""
<div class="steps-bar">
    <div class="step">
        <div class="step-num">1</div>
        <div class="step-label">Configurar Disparo</div>
    </div>
    <div class="step-arrow">→</div>
    <div class="step">
        <div class="step-num">2</div>
        <div class="step-label">Selecionar Cursos</div>
    </div>
    <div class="step-arrow">→</div>
    <div class="step">
        <div class="step-num">3</div>
        <div class="step-label">Gerar ZIP</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── LAYOUT PRINCIPAL ─────────────────────────────────────────────────
st.markdown("""
<style>
.retroativo-btn > div[data-testid="stButton"] > button {
    background: transparent !important;
    border: 1px solid #1a3a5c !important;
    color: #555 !important;
    font-size: 0.7rem !important;
    padding: 0.2rem 0.75rem !important;
    width: auto !important;
    min-height: unset !important;
    line-height: 1.4 !important;
    letter-spacing: 0.3px !important;
    margin-top: 0.25rem !important;
}
.retroativo-btn > div[data-testid="stButton"] > button:hover {
    background: #0f1e35 !important;
    opacity: 1 !important;
}
</style>
""", unsafe_allow_html=True)

col_in, col_cfg = st.columns([1, 2])

with col_in:
    # Campo de data — sempre presente
    if st.session_state.modo_retroativo:
        ret_busca = st.text_input(
            "Nome da semana na planilha",
            placeholder="ex: Retroativo - T 2025",
            help="Digite o nome exato da semana como aparece na coluna B da planilha.",
            key="input_ret_busca"
        )
        ret_data = st.text_input(
            "Dia do disparo",
            placeholder="DD/MM  ex: 15/07",
            help="Data em que o Broadcast de Retroativo será disparado.",
            key="input_ret_data"
        )
        ret_hora = st.text_input(
            "Horário inicial de disparo",
            placeholder="HH:MM  ex: 12:00",
            help="Horário do primeiro disparo. Os demais serão +2 min por curso.",
            key="input_ret_hora"
        )
        data_ref = None
    else:
        data_ref = st.text_input(
            "Segunda-feira da semana",
            placeholder="DD/MM  ex: 02/02",
            help="Digite a data da segunda-feira da semana que deseja gerar.",
            key="input_data_ref"
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
                    help="Deixe em branco para incluir todos os cursos.",
                    key="ms_cursos_ret"
                )

                campos_ok = ret_data and ret_hora
                if not campos_ok:
                    st.info("Preencha o dia e o horário de disparo para gerar.")

                if campos_ok and st.button("Gerar Pacote ZIP — Retroativo", key="btn_gerar_ret"):
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
                        for idx, c_data in enumerate(cursos_alvo):
                            dt = datetime(2026, m_ret, d_ret, h_ret, min_ret, tzinfo=BRASILIA) + timedelta(seconds=(idx * intervalo_s))
                            nome_final = f"Retroativo {ret_data} - {c_data['nome']}"
                            json_obj = montar_json_retomada(nome_final, int(dt.timestamp() * 1000), ret_data)
                            nome_arq = nome_final.replace("/", "_")
                            zf.writestr(f"Retroativo/{nome_arq}.json", json.dumps(json_obj, indent=2, ensure_ascii=False))
                            counter += 1
                            progresso.progress(counter / total, text=f"Gerando: {nome_final}")

                    progresso.empty()
                    st.success(f"✅ {counter} arquivo(s) de Retroativo gerado(s) com sucesso!")
                    st.download_button(
                        label="Baixar ZIP para Importação",
                        data=zip_buffer.getvalue(),
                        file_name=f"Import_CESS_Retroativo_{ret_data.replace('/', '_')}.zip",
                        mime="application/zip",
                        key="dl_btn_ret"
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
                        help="Deixe em branco para incluir todos os cursos.",
                        key="ms_cursos_normal"
                    )
                with col_b:
                    fluxo_sel = st.selectbox(
                        "Fluxo",
                        ["Todos", "F1", "F2", "F2.1", "F3", "F4", "F5", "F5.1", "F6", "F7", "F8", "SC1", "SC2", "SC3"],
                        key="sb_fluxo_normal"
                    )

                if st.button("Gerar Pacote ZIP", key="btn_gerar_normal"):
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
                        for idx, c_data in enumerate(cursos_alvo):
                            for f_num in fluxos_alvo:
                                h, m, _ = H_MAP[f_num]
                                d_ref, m_ref = map(int, data_ref.split("/"))
                                dt = datetime(2026, m_ref, d_ref, h, m, tzinfo=BRASILIA) + timedelta(days=OFFSETS[f_num])
                                dt += timedelta(minutes=(idx * 2))

                                nome_final = f"{data_ref} - F{f_num} - {c_data['nome']}"
                                if f_num in ("SC1", "SC2", "SC3"):
                                    nome_final = f"{f_num} {data_ref} - {c_data['nome']}"
                                    json_obj = montar_json_sc(nome_final, int(dt.timestamp() * 1000))
                                elif f_num in ("2.1", "5.1"):
                                    json_obj = montar_json_foward(nome_final, int(dt.timestamp() * 1000))
                                else:
                                    tag = c_data["tags"].get(f_num, "")
                                    json_obj = montar_json_unnichat(nome_final, int(dt.timestamp() * 1000), tag)

                                nome_arq = nome_final.replace("/", "_")
                                zf.writestr(f"Fluxo_{f_num}/{nome_arq}.json", json.dumps(json_obj, indent=2, ensure_ascii=False))
                                counter += 1
                                progresso.progress(counter / total, text=f"Gerando: {nome_final}")

                    progresso.empty()
                    st.success(f"✅ {counter} arquivo(s) gerado(s) com sucesso!")
                    st.download_button(
                        label="Baixar ZIP para Importação",
                        data=zip_buffer.getvalue(),
                        file_name=f"Import_CESS_{data_ref.replace('/', '_')}.zip",
                        mime="application/zip",
                        key="dl_btn_normal"
                    )
            else:
                st.warning(f"⚠️ Nenhum curso encontrado para a semana de **{data_ref}**. Verifique a data e a planilha.")
