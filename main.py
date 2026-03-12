import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Dashboard Analítico", layout="wide")
st.title("Análise de Desempenho Real: 2025 vs 2026")

# ==========================================
# 2. LEITURA E TRATAMENTO DOS DADOS
# ==========================================
try:
    # Insira aqui os nomes exatos dos seus ficheiros CSV
    df_fat = pd.read_csv('faturamento.csv')
    df_prod = pd.read_csv('produto.csv')
except FileNotFoundError:
    st.error("Arquivos CSV não encontrados na pasta. Verifique os nomes exatos!")
    st.stop()

# --- DETETOR INTELIGENTE DE COLUNAS ---
FAT_COL_ANT = 'Valor Ano Anterior' if 'Valor Ano Anterior' in df_fat.columns else 'Valor Ano Ant'
FAT_COL_ATUAL = 'Valor Atual'

PROD_COL_ANT = 'Valor Ano Ant' if 'Valor Ano Ant' in df_prod.columns else 'Valor Ano Anterior'
PROD_COL_ATUAL = 'Valor Atual'

# Converte para números MANTENDO os sinais negativos
colunas_financeiras_fat = [FAT_COL_ANT, FAT_COL_ATUAL]
for col in colunas_financeiras_fat:
    if col in df_fat.columns:
        df_fat[col] = pd.to_numeric(df_fat[col], errors='coerce').fillna(0)

colunas_prod_fin = ['Qtd Ano Ant', PROD_COL_ANT, 'Qtd Atual', PROD_COL_ATUAL]
for col in colunas_prod_fin:
    if col in df_prod.columns:
        df_prod[col] = pd.to_numeric(df_prod[col], errors='coerce').fillna(0)

# ==========================================
# CÁLCULO INTELIGENTE DE VARIAÇÃO (%)
# ==========================================
def calcular_variacao_inteligente(ant, atual):
    if ant == 0:
        if atual > 0:
            return 100.0  
        elif atual < 0:
            return -100.0 
        else:
            return 0.0
    return ((atual - ant) / abs(ant)) * 100

# Aplica a matemática correta nas colunas
if FAT_COL_ANT in df_fat.columns and FAT_COL_ATUAL in df_fat.columns:
    df_fat['Variacao (%)'] = df_fat.apply(lambda row: calcular_variacao_inteligente(row[FAT_COL_ANT], row[FAT_COL_ATUAL]), axis=1)

if PROD_COL_ANT in df_prod.columns and PROD_COL_ATUAL in df_prod.columns:
    df_prod['Variacao (%)'] = df_prod.apply(lambda row: calcular_variacao_inteligente(row[PROD_COL_ANT], row[PROD_COL_ATUAL]), axis=1)

# Formatação limpa para os Códigos de Produto
if 'COD_PRODUTO' in df_prod.columns:
    df_prod['COD_PRODUTO'] = df_prod['COD_PRODUTO'].fillna("").astype(str)
    df_prod['COD_PRODUTO'] = df_prod['COD_PRODUTO'].apply(lambda x: x.replace('.0', '') if x.endswith('.0') else x)

if 'NOME_PRODUTO' in df_prod.columns:
    df_prod['NOME_PRODUTO'] = df_prod['NOME_PRODUTO'].fillna("").astype(str)

# Limpeza de qualquer subtotal residual (caso os CSVs antigos ainda sejam carregados)
df_prod = df_prod[df_prod['NOME_PRODUTO'] != ">> SUBTOTAL DA LOJA <<"].copy()

# ==========================================
# 3. CÁLCULO DE MÉTRICAS GERAIS
# ==========================================
total_2025 = df_fat[FAT_COL_ANT].sum() if FAT_COL_ANT in df_fat.columns else 0
total_2026 = df_fat[FAT_COL_ATUAL].sum() if FAT_COL_ATUAL in df_fat.columns else 0

variacao_real = calcular_variacao_inteligente(total_2025, total_2026)

st.info("Insight Baseado em Dados: Os indicadores abaixo e os gráficos refletem a consolidação real extraída diretamente da base (devoluções são exibidas como valores negativos e devidamente subtraídas).")

col1, col2, col3 = st.columns(3)
col1.metric("Faturamento (Ano Anterior)", f"R$ {total_2025:,.2f}")
col2.metric("Faturamento (Atual)", f"R$ {total_2026:,.2f}", f"{variacao_real:.2f}%")

st.markdown("---")

# ==========================================
# 4. GRÁFICOS INTERATIVOS
# ==========================================
col_grafico1, col_grafico2 = st.columns(2)

with col_grafico1:
    st.subheader("Evolução de Faturamento")
    fig1 = go.Figure(data=[
        go.Bar(name='Ano Anterior', x=['Total da Base'], y=[total_2025], marker_color='gray', text=[f"R$ {total_2025:,.2f}"], textposition='auto'),
        go.Bar(name='Ano Atual', x=['Total da Base'], y=[total_2026], marker_color='#e74c3c' if variacao_real < 0 else '#2ecc71', text=[f"R$ {total_2026:,.2f}"], textposition='auto')
    ])
    fig1.update_layout(barmode='group', template="plotly_white", yaxis_title="Faturamento Bruto Líquido (R$)")
    st.plotly_chart(fig1, use_container_width=True)

with col_grafico2:
    st.subheader("Venda de Produtos por Loja (Top 10)")
    
    top_10_lojas = df_prod.groupby('NOME_LOJA')[PROD_COL_ATUAL].sum().nlargest(10).index
    df_top = df_prod[df_prod['NOME_LOJA'].isin(top_10_lojas)]
    
    fig2 = px.bar(
        df_top, x='NOME_LOJA', y=PROD_COL_ATUAL, color='NOME_PRODUTO', 
        labels={'NOME_LOJA': 'Lojas', PROD_COL_ATUAL: 'Faturamento (R$)', 'NOME_PRODUTO': 'Produto'},
        template="plotly_white"
    )
    fig2.update_layout(xaxis={'categoryorder':'total descending', 'showticklabels': False})
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")

# ==========================================
# 5. TABELAS DE DADOS 
# ==========================================
st.subheader("Detalhamento Base de Dados")

def cor_variacao(val):
    try:
        val = float(val)
        cor = 'green' if val > 0 else 'red' if val < 0 else 'black'
        return f'color: {cor}; font-weight: bold'
    except:
        return 'color: black'

tab1, tab2 = st.tabs(["Resumo por Loja", "Detalhamento por Produto"])

with tab1:
    st.dataframe(
        df_fat.style.map(cor_variacao, subset=['Variacao (%)']).format({
            FAT_COL_ANT: "R$ {:,.2f}", 
            FAT_COL_ATUAL: "R$ {:,.2f}", 
            "Variacao (%)": "{:.2f}%"
        }),
        use_container_width=True, height=400
    )

with tab2:
    st.dataframe(
        df_prod.style.map(cor_variacao, subset=['Variacao (%)']).format({
            "Qtd Ano Ant": "{:,.2f}", 
            PROD_COL_ANT: "R$ {:,.2f}", 
            "Qtd Atual": "{:,.2f}", 
            PROD_COL_ATUAL: "R$ {:,.2f}", 
            "Variacao (%)": "{:.2f}%"
        }),
        use_container_width=True, height=500
    )