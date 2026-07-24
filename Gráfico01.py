import unicodedata
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def normalize_text(value):
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text


def find_column(df, aliases):
    for alias in aliases:
        key = normalize_text(alias)
        for col in df.columns:
            if normalize_text(col) == key:
                return col
    return None


def load_data():
    base_dir = Path(__file__).resolve().parent

    candidates = [
        "vendas.xlsx", "vendas.xls", "planilha.xlsx", "planilha.xls",
        "dados.xlsx", "dados.xls", "vendas.csv", "planilha.csv", "dados.csv"
    ]

    for name in candidates:
        path = base_dir / name
        if path.exists():
            if path.suffix.lower() == ".csv":
                return pd.read_csv(path), path
            return pd.read_excel(path), path

    return pd.DataFrame(
        {
            "Estado": [
                "São Paulo", "Rio de Janeiro", "Minas Gerais", "Bahia",
                "Paraná", "Rio Grande do Sul", "Santa Catarina", "Pernambuco",
                "Ceará", "Goiás"
            ],
            "Vendas": [3200000, 1800000, 1400000, 900000, 850000, 800000, 750000, 650000, 620000, 600000]
        }
    ), None


df, arquivo = load_data()

if df.empty:
    raise ValueError("A planilha não contém dados.")

estado_col = find_column(df, ["estado", "estado_", "state", "uf", "sigla", "sigla_estado", "nome_do_estado", "nome_estado"])
vendas_col = find_column(df, ["vendas", "valor", "receita", "total", "sales", "valor_vendas", "valor_venda", "montante"])

if estado_col is None or vendas_col is None:
    raise ValueError("Não foi possível encontrar as colunas de estado e vendas. Ajuste os nomes das colunas na planilha.")

df = df[[estado_col, vendas_col]].copy()
df.columns = ["estado", "vendas"]

df["estado"] = df["estado"].astype(str).str.strip()
df["vendas"] = pd.to_numeric(df["vendas"], errors="coerce")
df = df.dropna(subset=["vendas"])
df = df[df["vendas"] > 0]

sigla_to_estado = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AP": "Amapá",
    "AM": "Amazonas",
    "BA": "Bahia",
    "CE": "Ceará",
    "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    "GO": "Goiás",
    "MA": "Maranhão",
    "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais",
    "PA": "Pará",
    "PB": "Paraíba",
    "PR": "Paraná",
    "PE": "Pernambuco",
    "PI": "Piauí",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul",
    "RO": "Rondônia",
    "RR": "Roraima",
    "SC": "Santa Catarina",
    "SP": "São Paulo",
    "SE": "Sergipe",
    "TO": "Tocantins",
}

def canonical_estado(value):
    text = str(value).strip()
    if text.upper() in sigla_to_estado:
        return sigla_to_estado[text.upper()]
    return text

df["estado"] = df["estado"].apply(canonical_estado)

df = df.groupby("estado", as_index=False)["vendas"].sum().sort_values("vendas", ascending=False)

coords = {
    "Acre": (-9.97498, -67.8243),
    "Alagoas": (-9.66599, -35.7350),
    "Amapá": (0.03490, -51.0694),
    "Amazonas": (-3.10190, -60.0250),
    "Bahia": (-12.9711, -38.5108),
    "Ceará": (-3.71722, -38.5433),
    "Distrito Federal": (-15.7801, -47.9292),
    "Espírito Santo": (-20.3155, -40.3128),
    "Goiás": (-16.6809, -49.2568),
    "Maranhão": (-2.53070, -44.3068),
    "Mato Grosso": (-15.5961, -56.0969),
    "Mato Grosso do Sul": (-20.4697, -54.6201),
    "Minas Gerais": (-19.9167, -43.9345),
    "Pará": (-1.45580, -48.5037),
    "Paraíba": (-7.11500, -34.8631),
    "Paraná": (-25.4284, -49.2658),
    "Pernambuco": (-8.04756, -34.8770),
    "Piauí": (-5.08920, -42.8090),
    "Rio de Janeiro": (-22.9068, -43.1729),
    "Rio Grande do Norte": (-5.77930, -35.2009),
    "Rio Grande do Sul": (-30.0346, -51.2177),
    "Rondônia": (-8.76190, -63.9039),
    "Roraima": (2.81910, -60.6711),
    "Santa Catarina": (-27.5949, -48.5480),
    "São Paulo": (-23.5505, -46.6333),
    "Sergipe": (-10.9472, -37.0765),
    "Tocantins": (-10.1750, -48.3336),
}

coords_norm = {normalize_text(k): v for k, v in coords.items()}

fig_bar = px.bar(
    df,
    x="estado",
    y="vendas",
    text="vendas",
    title="Vendas por estado do Brasil",
    labels={"estado": "Estado", "vendas": "Vendas (R$)"},
    color_discrete_sequence=["#1f77b4"],
)

fig_bar.update_traces(
    texttemplate="R$ %{text:,.0f}",
    textposition="outside",
)

fig_bar.update_layout(
    xaxis_tickangle=-45,
    template="plotly_white",
    margin=dict(l=20, r=20, t=60, b=90),
)

origem = (-15.7801, -47.9292)  
fig_flow = go.Figure()

for i, row in df.iterrows():
    estado = row["estado"]
    vendas = row["vendas"]
    key = normalize_text(estado)

    if key not in coords_norm:
        continue

    lat0, lon0 = origem
    lat1, lon1 = coords_norm[key]

    cor = px.colors.qualitative.Set3[i % len(px.colors.qualitative.Set3)]

    fig_flow.add_trace(
        go.Scattergeo(
            lon=[lon0, lon1],
            lat=[lat0, lat1],
            mode="lines",
            line=dict(width=1.5, color=cor),
            hoverinfo="skip",
            showlegend=False,
        )
    )

    fig_flow.add_trace(
        go.Scattergeo(
            lon=[lon1],
            lat=[lat1],
            mode="markers",
            marker=dict(size=8 + min(10, vendas / 500000), color=cor),
            text=[f"{estado}<br>Vendas: R$ {vendas:,.0f}"],
            hovertemplate="<b>%{text}</b><extra></extra>",
            showlegend=False,
        )
    )

fig_flow.update_layout(
    title="Fluxo de vendas por estado do Brasil",
    template="plotly_white",
    geo=dict(
        scope="south america",
        projection_type="natural earth",
        showland=True,
        landcolor="#f2f2f2",
        showcountries=True,
        countrycolor="#cccccc",
        showcoastlines=True,
        coastlinecolor="#cccccc",
        bgcolor="white",
    ),
    margin=dict(l=0, r=0, t=50, b=0),
)

fig_flow.update_geos(fitbounds="locations")

base_dir = Path(__file__).resolve().parent
fig_bar.write_html(str(base_dir / "vendas_por_estado.html"))
fig_flow.write_html(str(base_dir / "fluxo_vendas_brasil.html"))

fig_bar.show()
fig_flow.show()