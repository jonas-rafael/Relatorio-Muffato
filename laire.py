import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. CONFIGURAÇÃO GERAL DA PÁGINA
# ==========================================
st.set_page_config(page_title="Dashboard Executivo Master", layout="wide")

def calcular_variacao_inteligente(ant, atual):
    if ant == 0:
        if atual > 0: return 100.0  
        elif atual < 0: return -100.0 
        else: return 0.0
    return ((atual - ant) / abs(ant)) * 100

def cor_variacao(val):
    try:
        val = float(val)
        cor = 'green' if val > 0 else 'red' if val < 0 else 'black'
        return f'color: {cor}; font-weight: bold'
    except:
        return 'color: black'

# ==========================================
# 2. MENU LATERAL DE NAVEGAÇÃO
# ==========================================
st.sidebar.title("Navegação Executiva")
visao_selecionada = st.sidebar.radio(
    "Selecione o Painel:", 
    ["Comparativo YoY (25 vs 26)", "Evolução Mensal (2025/2026)"]
)

st.sidebar.markdown("---")
st.sidebar.info("Utilize as opções acima para alternar entre as análises de Ano vs Ano e a Curva Mensal do faturamento.")

# ==============================================================================
# PAINEL 1: COMPARATIVO YOY (2025 vs 2026)
# ==============================================================================
if visao_selecionada == "Comparativo YoY (25 vs 26)":
    st.title("Análise de Desempenho Real: 2025 vs 2026")
    
    try:
        # LÊ APENAS O ARQUIVO DE PRODUTOS
        df_prod = pd.read_csv('faturamento_laire_comparativo.csv')
    except FileNotFoundError:
        st.error("Arquivo não encontrado! Verifique se 'faturamento_laire_comparativo.csv' está na pasta.")
        st.stop()

    PROD_COL_ANT = 'Valor Ano Ant' if 'Valor Ano Ant' in df_prod.columns else 'Valor Ano Anterior'
    PROD_COL_ATUAL = 'Valor Atual'

    for col in ['Qtd Ano Ant', PROD_COL_ANT, 'Qtd Atual', PROD_COL_ATUAL]:
        if col in df_prod.columns: df_prod[col] = pd.to_numeric(df_prod[col], errors='coerce').fillna(0)

    # Limpeza brutal de linhas duplicadas (Subtotais e Resumos que vêm do SQL)
    df_prod = df_prod[
        (~df_prod['NOME_PRODUTO'].astype(str).str.contains("SUBTOTAL", na=False)) & 
        (~df_prod['NOME_LOJA'].astype(str).str.contains("TOTAL", na=False)) &
        (~df_prod['NOME_LOJA'].astype(str).str.contains("RESUMO", na=False))
    ].copy()

    # O PYTHON GERA A TABELA DE FATURAMENTO AUTOMATICAMENTE AQUI
    df_fat = df_prod.groupby(['COD_LOJA', 'NOME_LOJA'])[[PROD_COL_ANT, PROD_COL_ATUAL]].sum().reset_index()

    # Filtro Dinâmico de Cidade (se existir no arquivo)
    if 'CIDADE_LOJA' in df_prod.columns:
        cidades_validas = df_prod[~df_prod['CIDADE_LOJA'].isin(['---', 'NÃO INFORMADA'])]['CIDADE_LOJA'].dropna().unique().tolist()
        if len(cidades_validas) > 0:
            cidade_selecionada = st.selectbox("📍 Filtrar Análise por Cidade:", ["Todas as Cidades"] + sorted(cidades_validas))
            if cidade_selecionada != "Todas as Cidades":
                df_prod = df_prod[df_prod['CIDADE_LOJA'] == cidade_selecionada]
                df_fat = df_fat[df_fat['NOME_LOJA'].isin(df_prod['NOME_LOJA'].unique())]

    # Aplica matemática inteligente
    df_fat['Variacao (%)'] = df_fat.apply(lambda row: calcular_variacao_inteligente(row[PROD_COL_ANT], row[PROD_COL_ATUAL]), axis=1)
    df_prod['Variacao (%)'] = df_prod.apply(lambda row: calcular_variacao_inteligente(row[PROD_COL_ANT], row[PROD_COL_ATUAL]), axis=1)

    # Limpa código de produto
    if 'COD_PRODUTO' in df_prod.columns:
        df_prod['COD_PRODUTO'] = df_prod['COD_PRODUTO'].fillna("").astype(str).apply(lambda x: x.replace('.0', '') if x.endswith('.0') else x)

    # CÁLCULO TOTAL DOS CARDS
    total_2025 = df_fat[PROD_COL_ANT].sum()
    total_2026 = df_fat[PROD_COL_ATUAL].sum()
    variacao_real = calcular_variacao_inteligente(total_2025, total_2026)

    st.info("Insight Baseado em Dados: Os indicadores refletem a consolidação real extraída da base (devoluções são exibidas como valores negativos).")
    col1, col2, col3 = st.columns(3)
    col1.metric("Faturamento (Ano Anterior)", f"R$ {total_2025:,.2f}")
    col2.metric("Faturamento (Atual)", f"R$ {total_2026:,.2f}", f"{variacao_real:.2f}%")

    st.markdown("---")
    
    col_grafico1, col_grafico2 = st.columns(2)
    with col_grafico1:
        st.subheader("Evolução de Faturamento")
        fig1 = go.Figure(data=[
            go.Bar(name='Ano Anterior', x=['Total Selecionado'], y=[total_2025], marker_color='gray', text=[f"R$ {total_2025:,.2f}"], textposition='auto'),
            go.Bar(name='Ano Atual', x=['Total Selecionado'], y=[total_2026], marker_color='#e74c3c' if variacao_real < 0 else '#2ecc71', text=[f"R$ {total_2026:,.2f}"], textposition='auto')
        ])
        fig1.update_layout(barmode='group', template="plotly_white", yaxis_title="Faturamento Bruto (R$)")
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
    st.subheader("Detalhamento Base de Dados")
    tab1, tab2 = st.tabs(["Resumo por Loja", "Detalhamento por Produto"])

    with tab1:
        formato_fat = {PROD_COL_ANT: "R$ {:,.2f}", PROD_COL_ATUAL: "R$ {:,.2f}", "Variacao (%)": "{:.2f}%"}
        st.dataframe(df_fat.style.map(cor_variacao, subset=['Variacao (%)']).format(formato_fat), use_container_width=True, height=400)

    with tab2:
        formato_prod = {"Qtd Ano Ant": "{:,.2f}", PROD_COL_ANT: "R$ {:,.2f}", "Qtd Atual": "{:,.2f}", PROD_COL_ATUAL: "R$ {:,.2f}", "Variacao (%)": "{:.2f}%"}
        st.dataframe(df_prod.style.map(cor_variacao, subset=['Variacao (%)']).format(formato_prod), use_container_width=True, height=500)

# ==============================================================================
# PAINEL 2: EVOLUÇÃO MENSAL
# ==============================================================================
elif visao_selecionada == "Evolução Mensal (2025/2026)":
    st.title("Evolução Mensal de Faturamento")
    
    try:
        df_fat_mes = pd.read_csv('faturamento_laire_2025-6.csv')
    except FileNotFoundError:
        st.error("Arquivo não encontrado! Verifique se 'faturamento_laire_2025-6.csv' está na pasta.")
        st.stop()

    df_fat_mes = df_fat_mes.dropna(subset=['MES'])
    df_fat_mes = df_fat_mes[~df_fat_mes['CLIENTE'].astype(str).str.contains("TOTAL GERAL", na=False)]

    df_fat_mes['MES'] = pd.to_numeric(df_fat_mes['MES'], errors='coerce').fillna(0).astype(int)
    if 'VALOR_FATURADO' in df_fat_mes.columns:
        df_fat_mes['VALOR_FATURADO'] = pd.to_numeric(df_fat_mes['VALOR_FATURADO'], errors='coerce').fillna(0)

    meses_pt = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
    df_fat_mes['NOME_MES'] = df_fat_mes['MES'].map(meses_pt)

    if 'CIDADE_LOJA' not in df_fat_mes.columns: df_fat_mes['CIDADE_LOJA'] = "NÃO INFORMADA"

    # Filtro Dinâmico de Cidade
    cidades_disponiveis = df_fat_mes['CIDADE_LOJA'].dropna().unique().tolist()
    if len(cidades_disponiveis) > 1:
        cidade_sel_mes = st.selectbox("📍 Filtrar Análise por Cidade:", ["Todas as Cidades"] + sorted(cidades_disponiveis))
        if cidade_sel_mes != "Todas as Cidades":
            df_fat_mes = df_fat_mes[df_fat_mes['CIDADE_LOJA'] == cidade_sel_mes]

    faturamento_total_mes = df_fat_mes['VALOR_FATURADO'].sum()

    st.info("Insight Baseado em Dados: A curva abaixo demonstra a evolução do faturamento bruto líquido ao longo dos meses.")
    st.metric("Faturamento Total Acumulado (Período Selecionado)", f"R$ {faturamento_total_mes:,.2f}")

    st.markdown("---")
    
    st.subheader("Curva de Faturamento Mensal")
    df_agrupado_mes = df_fat_mes.groupby(['ANO', 'MES', 'NOME_MES'])['VALOR_FATURADO'].sum().reset_index()
    df_agrupado_mes = df_agrupado_mes.sort_values(['ANO', 'MES'])
    df_agrupado_mes['EIXO_X'] = df_agrupado_mes['NOME_MES'] + "/" + df_agrupado_mes['ANO'].astype(str)
    df_agrupado_mes['TEXTO_VALOR'] = df_agrupado_mes['VALOR_FATURADO'].apply(lambda x: f"R$ {x:,.2f}")
    
    fig_linha = px.line(
        df_agrupado_mes, x='EIXO_X', y='VALOR_FATURADO', markers=True, text='TEXTO_VALOR',
        labels={'EIXO_X': 'Mês/Ano', 'VALOR_FATURADO': 'Faturamento (R$)'},
        template="plotly_white"
    )
    fig_linha.update_traces(line_color='#2980b9', line_width=4, marker_size=10, textposition='top center')
    fig_linha.update_yaxes(rangemode="tozero")
    st.plotly_chart(fig_linha, use_container_width=True)

    st.markdown("---")
    st.subheader("Detalhamento Base de Dados (Mensal)")
    
    colunas_fat_exibicao = ['ANO', 'NOME_MES', 'COD_CLIENTE', 'CLIENTE', 'CIDADE_LOJA', 'VALOR_FATURADO']
    colunas_fat = [col for col in colunas_fat_exibicao if col in df_fat_mes.columns]
    
    st.dataframe(df_fat_mes[colunas_fat].style.format({"VALOR_FATURADO": "R$ {:,.2f}"}), use_container_width=True, height=400)