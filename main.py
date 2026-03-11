import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="Dashboard Analítico - Muffato", layout="wide")
st.title("Análise de Desempenho Real: 2025 vs 2026 (Rede Muffato)")

# ==========================================
# 2. LEITURA E LIMPEZA DOS DADOS REAIS
# ==========================================
try:
    df_fat = pd.read_csv('faturamento_muffato_25_26_jadson.csv')
    df_prod = pd.read_csv('muffato_analise_de_produtos_entre_jan-fev_de_25_e_jan-fev_de_26_jadson.csv')
except FileNotFoundError:
    st.error("Arquivos CSV não encontrados na pasta. Verifique os nomes!")
    st.stop()

# Preenchimento de Nulos no Faturamento
df_fat = df_fat.fillna(0)

# Limpeza e tipagem forte nos Produtos para evitar erros do PyArrow no terminal
if 'COD_PRODUTO' in df_prod.columns:
    # Transforma em texto puro e remove o ".0" caso o pandas tenha lido como número decimal
    df_prod['COD_PRODUTO'] = df_prod['COD_PRODUTO'].fillna("").astype(str)
    df_prod['COD_PRODUTO'] = df_prod['COD_PRODUTO'].apply(lambda x: x.replace('.0', '') if x.endswith('.0') else x)

if 'NOME_PRODUTO' in df_prod.columns:
    df_prod['NOME_PRODUTO'] = df_prod['NOME_PRODUTO'].fillna("").astype(str)

# Preenche o resto (valores numéricos) com zero
df_prod = df_prod.fillna(0)

# ==========================================
# 3. CÁLCULO DE MÉTRICAS 100% DINÂMICAS
# ==========================================
total_2025 = df_fat['Valor Ano Anterior'].sum()
total_2026 = df_fat['Valor Atual'].sum()

if total_2025 > 0:
    variacao_real = ((total_2026 - total_2025) / total_2025) * 100
else:
    variacao_real = 100.0

st.info("**Insight Baseado em Dados:** Os indicadores abaixo e os gráficos refletem exclusivamente a consolidação real dos meses de Janeiro e Fevereiro, extraídos diretamente da base.")

col1, col2, col3 = st.columns(3)
col1.metric("Faturamento Jan-Fev (2025)", f"R$ {total_2025:,.2f}")
col2.metric("Faturamento Jan-Fev (2026)", f"R$ {total_2026:,.2f}", f"{variacao_real:.2f}%")

st.markdown("---")

# ==========================================
# 4. GRÁFICOS INTERATIVOS
# ==========================================
col_grafico1, col_grafico2 = st.columns(2)

with col_grafico1:
    st.subheader("Evolução de Faturamento (Jan-Fev)")
    fig1 = go.Figure(data=[
        go.Bar(name='2025 (Baseline)', x=['Total Rede Muffato'], y=[total_2025], marker_color='gray', text=[f"R$ {total_2025:,.2f}"], textposition='auto'),
        go.Bar(name='2026 (Atual)', x=['Total Rede Muffato'], y=[total_2026], marker_color='#e74c3c' if variacao_real < 0 else '#2ecc71', text=[f"R$ {total_2026:,.2f}"], textposition='auto')
    ])
    fig1.update_layout(barmode='group', template="plotly_white", yaxis_title="Faturamento Bruto (R$)")
    st.plotly_chart(fig1, use_container_width=True)

with col_grafico2:
    st.subheader("Venda de Produtos por Loja (Top 10)")
    
    # Remove as linhas de Subtotal para o gráfico não distorcer
    df_prod_grafico = df_prod[df_prod['NOME_PRODUTO'] != ">> SUBTOTAL DA LOJA <<"].copy()
    
    # Pega apenas as 10 lojas que mais venderam
    top_10_lojas = df_prod_grafico.groupby('NOME_LOJA')['Valor Atual'].sum().nlargest(10).index
    df_top = df_prod_grafico[df_prod_grafico['NOME_LOJA'].isin(top_10_lojas)]
    
    fig2 = px.bar(
        df_top, x='NOME_LOJA', y='Valor Atual', color='NOME_PRODUTO', 
        labels={'NOME_LOJA': 'Lojas', 'Valor Atual': 'Faturamento (R$)', 'NOME_PRODUTO': 'Produto'},
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
    cor = 'green' if val > 0 else 'red' if val < 0 else 'black'
    return f'color: {cor}; font-weight: bold'

tab1, tab2 = st.tabs(["Resumo por Loja", "Detalhamento por Produto"])

with tab1:
    st.dataframe(
        df_fat.style.map(cor_variacao, subset=['Variacao (%)']).format({
            "Valor Ano Anterior": "R$ {:,.2f}", 
            "Valor Atual": "R$ {:,.2f}", 
            "Variacao (%)": "{:.2f}%"
        }),
        use_container_width=True, height=400
    )

with tab2:
    st.dataframe(
        df_prod.style.map(cor_variacao, subset=['Variacao (%)']).format({
            "Valor Ano Ant": "R$ {:,.2f}", 
            "Valor Atual": "R$ {:,.2f}", 
            "Variacao (%)": "{:.2f}%"
        }),
        use_container_width=True, height=500
    )