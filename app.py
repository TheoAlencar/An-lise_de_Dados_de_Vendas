import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configurar o estilo dos gráficos
sns.set_style("whitegrid")

# Título do aplicativo no Streamlit
st.title("📊 Análise de Dados de Vendas - ModaOnline")

# Carregar os arquivos
@st.cache_data
def load_data():
    df_vendas_2020 = pd.read_excel("Base Vendas - 2020.xlsx")
    df_vendas_2021 = pd.read_excel("Base Vendas - 2021.xlsx")
    df_vendas_2022 = pd.read_excel("Base Vendas - 2022.xlsx")
    df_produtos = pd.read_excel("Cadastro Produtos.xlsx")
    df_devolucoes = pd.read_excel("Base Devol.xlsx")

    df_vendas = pd.concat([df_vendas_2020, df_vendas_2021, df_vendas_2022])
    return df_vendas, df_produtos, df_devolucoes

df_vendas, df_produtos, df_devolucoes = load_data()

# Criar um menu lateral
st.sidebar.header("📌 Filtros")

# Seleção de ano
anos = ["Todos", "2020", "2021", "2022"]
ano_selecionado = st.sidebar.selectbox("Selecione o ano:", anos)

# Filtrar dados pelo ano escolhido
if ano_selecionado != "Todos":
    df_vendas = df_vendas[df_vendas["Data da Venda"].astype(str).str.contains(ano_selecionado)]

# Exibir os primeiros dados
st.subheader("📋 Amostra dos Dados de Vendas")
st.dataframe(df_vendas.head())

# Produtos mais vendidos
produtos_mais_vendidos = df_vendas.groupby("SKU")["Qtd Vendida"].sum().reset_index()
produtos_mais_vendidos = produtos_mais_vendidos.merge(df_produtos, on="SKU", how="left")
produtos_mais_vendidos = produtos_mais_vendidos.sort_values(by="Qtd Vendida", ascending=False)

# Produtos menos vendidos
produtos_menos_vendidos = produtos_mais_vendidos.sort_values(by="Qtd Vendida", ascending=True)

# Exibir tabelas corretamente filtradas
st.subheader("📌 Top 10 Produtos Mais Vendidos")
st.dataframe(produtos_mais_vendidos.head(10))

st.subheader("📌 Top 10 Produtos Menos Vendidos")
st.dataframe(produtos_menos_vendidos.head(10))

# Preço médio de venda
produtos_mais_vendidos["Valor Total Vendido"] = produtos_mais_vendidos["Qtd Vendida"] * produtos_mais_vendidos["Preço Unitario"]
preco_medio_geral = produtos_mais_vendidos["Valor Total Vendido"].sum() / produtos_mais_vendidos["Qtd Vendida"].sum()

st.subheader("💰 Preço Médio de Venda")
st.write(f"O preço médio de venda dos produtos é **R$ {preco_medio_geral:.2f}**")

# **Sugestões de Precificação**
st.sidebar.header("📌 Sugestões de Precificação")

# Calcular margem de lucro
produtos_mais_vendidos["Lucro Unitário"] = produtos_mais_vendidos["Preço Unitario"] - produtos_mais_vendidos["Custo Unitario"]
produtos_mais_vendidos["Lucro Total"] = produtos_mais_vendidos["Lucro Unitário"] * produtos_mais_vendidos["Qtd Vendida"]

# Criar filtro para selecionar produtos com baixa margem de lucro
limite_lucro = st.sidebar.slider("Defina o mínimo de lucro por unidade:", 0, 100, 20)
produtos_baixo_lucro = produtos_mais_vendidos[produtos_mais_vendidos["Lucro Unitário"] < limite_lucro]

st.subheader("📊 Produtos com Baixa Margem de Lucro")
st.dataframe(produtos_baixo_lucro.head(10))

# **Simulação de Precificação**
if not produtos_baixo_lucro.empty:
    produto_selecionado = st.sidebar.selectbox("Selecione um produto para simular:", produtos_baixo_lucro["Produto"].unique())

    produto_info = produtos_baixo_lucro[produtos_baixo_lucro["Produto"] == produto_selecionado]
    
    if not produto_info.empty:
        preco_atual = float(produto_info["Preço Unitario"].values[0])
        custo_produto = float(produto_info["Custo Unitario"].values[0])
        qtd_vendida = int(produto_info["Qtd Vendida"].values[0])
        lucro_atual = preco_atual - custo_produto
        lucro_total_atual = lucro_atual * qtd_vendida

        st.sidebar.write(f"💰 **Preço Atual:** R$ {preco_atual:.2f}")
        st.sidebar.write(f"📉 **Lucro Atual por unidade:** R$ {lucro_atual:.2f}")
        st.sidebar.write(f"💵 **Lucro Total Atual:** R$ {lucro_total_atual:.2f}")

        novo_preco = st.sidebar.slider("Novo Preço Unitário:", 
                                       min_value=float(custo_produto + 1), 
                                       max_value=float(preco_atual * 2), 
                                       value=float(preco_atual),
                                       step=0.01)  

        # Calcular novo lucro estimado
        novo_lucro = novo_preco - custo_produto
        novo_lucro_total = novo_lucro * qtd_vendida

        st.sidebar.write(f"📈 **Novo Lucro por unidade:** R$ {novo_lucro:.2f}")
        st.sidebar.write(f"💰 **Novo Lucro Total Estimado:** R$ {novo_lucro_total:.2f}")

        # Comparação gráfica do impacto da mudança
        st.subheader(f"📊 Impacto da Mudança de Preço no Lucro - {produto_selecionado}")
        fig, ax = plt.subplots(figsize=(8, 4))
        sns.barplot(x=["Lucro Atual", "Novo Lucro"], y=[lucro_total_atual, novo_lucro_total], palette=["red", "green"], ax=ax)
        plt.ylabel("Lucro Total")
        st.pyplot(fig)

# **Definição do DataFrame 'analise_estoque' para evitar erro**
devolucoes_por_produto = df_devolucoes.groupby("SKU")["Qtd Devolvida"].sum().reset_index()
analise_estoque = produtos_mais_vendidos.merge(devolucoes_por_produto, on="SKU", how="left").fillna(0)
analise_estoque["Taxa de Devolução (%)"] = (analise_estoque["Qtd Devolvida"] / analise_estoque["Qtd Vendida"]) * 100
analise_estoque = analise_estoque.sort_values(by="Taxa de Devolução (%)", ascending=False)

# **Otimização de Estoque**
st.sidebar.header("📌 Otimização de Estoque")

limite_devolucao = st.sidebar.slider("Filtrar produtos com taxa de devolução acima de:", 0, 100, 5)
produtos_alta_devolucao = analise_estoque[analise_estoque["Taxa de Devolução (%)"] > limite_devolucao]

st.subheader("📉 Produtos com Alta Taxa de Devolução")
st.dataframe(produtos_alta_devolucao.head(10))

# Finalização
st.sidebar.write("👨‍💻 Desenvolvido com Streamlit e Seaborn")
