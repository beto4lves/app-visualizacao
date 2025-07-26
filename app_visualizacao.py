import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Painel de Entregas", layout="wide")

st.markdown("""
    <style>
    .dataframe tbody td {
        font-size: 12px !important;
        white-space: nowrap;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def carregar_dados():
    df = pd.read_excel("Atendimento.xlsx", sheet_name="base_dados")
    df.columns = df.columns.str.upper()
    df = df.fillna("--")
    df["PREVISÃO DE ENTREGA"] = pd.to_datetime(df["PREVISÃO DE ENTREGA"], errors='coerce')
    for col in ["SC", "SETOR", "REQUISITANTE", "STATUS"]:
        df[col] = df[col].astype(str).str.strip().str.upper()
    return df

df = carregar_dados()
hoje = pd.Timestamp.today().normalize()
proximos_7 = pd.date_range(start=hoje, periods=8, freq='D')
data_hoje_str = datetime.today().strftime("%d/%m/%Y")

# Última modificação do arquivo
try:
    timestamp_mod = os.path.getmtime("Atendimento.xlsx")
    data_modificacao = datetime.fromtimestamp(timestamp_mod).strftime("%d/%m/%Y %H:%M")
except:
    data_modificacao = "--"

st.markdown(f"📅 **Data atual:** {data_hoje_str}")
st.title("📦 Painel de Entregas")

with st.sidebar:
    st.markdown("### 🎛️ Filtros", unsafe_allow_html=True)
    filtro_sc = st.text_input("Número da SC:")
    desabilitar = bool(filtro_sc.strip())
    filtro_setor = st.selectbox("Departamento", ["Todos"] + sorted(df["SETOR"].unique()), disabled=desabilitar)
    opcoes_req = [r for r in df["REQUISITANTE"].unique() if r not in ["", "--", "-"]]
    filtro_req = st.selectbox("Solicitante", ["Todos"] + sorted(opcoes_req), disabled=desabilitar)

filtrado = df.copy()
if filtro_sc:
    filtrado = filtrado[filtrado["SC"].str.contains(filtro_sc, case=False)]
if filtro_setor != "Todos":
    filtrado = filtrado[filtrado["SETOR"] == filtro_setor]
if filtro_req != "Todos":
    filtrado = filtrado[filtrado["REQUISITANTE"] == filtro_req]

filtrado = filtrado[~filtrado["REQUISITANTE"].isin(["", "--", "-"])]
filtrado["ATRASADO_BOOL"] = (
    filtrado["PREVISÃO DE ENTREGA"].notna() &
    (filtrado["PREVISÃO DE ENTREGA"] < hoje) &
    (~filtrado["STATUS"].isin(["ENTREGUE", "FINALIZADO"]))
)
filtrado["SITUAÇÃO DA ENTREGA"] = filtrado["ATRASADO_BOOL"].apply(lambda x: "⚠️ Atrasado" if x else "✅ No prazo")
filtrado_visivel = filtrado[~filtrado["STATUS"].isin(["ENTREGUE", "FINALIZADO"])]

if not filtrado.empty:
    total = len(filtrado)
    final = (filtrado["STATUS"] == "ENTREGUE").sum()
    pend = (filtrado["STATUS"] == "AGUARDANDO ENTREGA").sum()
    atras = filtrado["ATRASADO_BOOL"].sum()
    hoje_qtd = (filtrado["PREVISÃO DE ENTREGA"] == hoje).sum()
    prox_qtd = filtrado["PREVISÃO DE ENTREGA"].isin(proximos_7).sum()
else:
    total = final = pend = atras = hoje_qtd = prox_qtd = 0

st.markdown("### 📊 Resumo dos Resultados")
estilo_card = """
    background-color: #1e1e1e;
    border-radius: 12px;
    padding: 18px;
    text-align: center;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.5);
    font-family: sans-serif;
"""
estilo_icone = "font-size:36px; margin-bottom:6px; color:#f0f0f0;"
estilo_valor = "font-size:26px; font-weight:bold; color:#ffffff;"
estilo_titulo = "font-size:14px; color:#cccccc; margin-top:4px;"
c1, c2, c3, c4, c5, c6 = st.columns(6)
for col, val, icone, titulo in zip(
    [c1, c2, c3, c4, c5, c6],
    [total, final, pend, atras, hoje_qtd, prox_qtd],
    ["📦", "✅", "🚚", "⚠️", "📅", "🗓️"],
    ["Total de Entregas", "Entregues", "Pendentes", "Atrasados", "Hoje", "Entrega Próx. 7 dias"]
):
    with col:
        st.markdown(f"""
            <div style="{estilo_card}">
                <div style="{estilo_icone}">{icone}</div>
                <div style="{estilo_valor}">{val}</div>
                <div style="{estilo_titulo}">{titulo}</div>
            </div>
        """, unsafe_allow_html=True)

# Espaço entre indicadores e filtro de data
st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)

# Tabela
datas_disponiveis = filtrado_visivel["PREVISÃO DE ENTREGA"].dropna().dt.normalize().drop_duplicates().sort_values()
opcoes_datas = ["Todas"] + datas_disponiveis.dt.strftime("%d/%m/%Y").tolist()
data_selecionada = st.selectbox("📅 Filtrar por data de entrega:", opcoes_datas, disabled=desabilitar)
if data_selecionada != "Todas":
    data_dt = datetime.strptime(data_selecionada, "%d/%m/%Y").date()
    filtrado_visivel = filtrado_visivel[filtrado_visivel["PREVISÃO DE ENTREGA"].dt.date == data_dt]

colunas = ["REQUISITANTE", "SETOR", "SC", "PC", "RAZAO SOCIAL", "PREVISÃO DE ENTREGA", "SITUAÇÃO DA ENTREGA"]
df_tabela = filtrado_visivel[colunas].copy()
df_tabela = df_tabela.rename(columns={
    "REQUISITANTE": "🙋 REQUISITANTE",
    "SETOR": "🏢 SETOR",
    "SC": "🧾 SC",
    "PC": "📄 PC",
    "RAZAO SOCIAL": "🏭 FORNECEDOR",
    "PREVISÃO DE ENTREGA": "📅 ENTREGA PREVISTA",
    "SITUAÇÃO DA ENTREGA": "📌 SITUAÇÃO DA ENTREGA"
})
df_tabela["📅 ENTREGA PREVISTA"] = pd.to_datetime(df_tabela["📅 ENTREGA PREVISTA"], errors='coerce').dt.strftime("%d/%m/%Y")

def highlight_row(row):
    if "📌 SITUAÇÃO DA ENTREGA" in row:
        if "Atrasado" in row["📌 SITUAÇÃO DA ENTREGA"]:
            return ['background-color: #f8d7da; color: black'] * len(row)
        else:
            return ['background-color: #d4edda; color: black'] * len(row)
    return [''] * len(row)

st.markdown("### 📋 Lista de Pedidos em Andamento")
if df_tabela.empty:
    st.warning("Nenhum resultado encontrado com os filtros selecionados.")
else:
    st.dataframe(df_tabela.style.apply(highlight_row, axis=1), use_container_width=True)

st.markdown("<span style='font-size:13px;'>🟩 Verde = No prazo &nbsp;&nbsp;&nbsp;&nbsp; 🟥 Vermelho = Atrasado</span>", unsafe_allow_html=True)

# Rodapé com última atualização
st.markdown("<hr style='margin-top:30px; margin-bottom:10px;'>", unsafe_allow_html=True)
st.markdown(f"<span style='font-size:13px;'>📁 Última atualização da base: <strong>{data_modificacao}</strong></span>", unsafe_allow_html=True)