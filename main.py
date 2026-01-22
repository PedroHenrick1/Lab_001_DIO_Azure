import streamlit as st
from azure.storage.blob import BlobServiceClient
import os
import pymssql
import uuid
import json
from dotenv import load_dotenv

load_dotenv()

BlobConnectionString = os.getenv("BLOB_CONNECTION_STRING")
blobContainerName = os.getenv("BLOB_CONTAINER_NAME")
blobAccountName = os.getenv("BLOB_ACCOUNT_NAME")

SQL_SERVER = os.getenv("SQL_SERVER")
SQL_DATABASE = os.getenv("SQL_DATABASE")
SQL_USER = os.getenv("SQL_USER")
SQL_PASSWORD = os.getenv("SQL_PASSWORD")

st.title("Cadastro de Produtos")

# formulário de cadastro de produtos
product_name = st.text_input("Nome do Produto")
product_price = st.number_input("Preço do Produto", min_value=0.0, format="%.2f")
product_description = st.text_area("Descrição do Produto")
product_image = st.file_uploader("Imagem do Produto", type=["jpg", "jpeg", "png"])

# Save image on Azure Blob Storage

def upload_blob(file):
    blobservice_client = BlobServiceClient.from_connection_string(BlobConnectionString)
    container_client = blobservice_client.get_container_client(blobContainerName)
    blob_name = str(uuid.uuid4()) + file.name
    blob_client =  container_client.get_blob_client(blob_name)
    blob_client.upload_blob(file.read(), overwrite=True)
    image_url = f"https://{blobAccountName}.blob.core.windows.net/{blobContainerName}/{blob_name}"
    return image_url

def insert_product(product_name, product_description, product_price, product_image_url):
    try:
        conn = pymssql.connect(server=SQL_SERVER, user=SQL_USER, password=SQL_PASSWORD, database=SQL_DATABASE)
        cursor = conn.cursor()
        insert_query = "INSERT INTO Produtos (nome, descricao, preco, imagem_url) VALUES (%s, %s, %s, %s)"
        cursor.execute(insert_query, (product_name, product_description, product_price, product_image_url))
        conn.commit()
        cursor.close()
        conn.close()
    
        return True
    
    except Exception as e:
        st.error(f"Erro ao inserir produto no banco de dados: {e}")
        return False
    
def list_products():
    try:
        conn = pymssql.connect(server=SQL_SERVER, user=SQL_USER, password=SQL_PASSWORD, database=SQL_DATABASE)
        cursor = conn.cursor(as_dict=True)
        select_query = "SELECT * FROM Produtos"
        cursor.execute(select_query)
        products = cursor.fetchall()
        cursor.close()
        conn.close()
    
        for product in products:
            st.subheader(product['nome'])
            st.write(f"Descrição: {product['descricao']}")
            st.write(f"Preço: R$ {product['preco']:.2f}")
            st.image(product['imagem_url'], width=200)
    
    except Exception as e:
        st.error(f"Erro ao listar produtos do banco de dados: {e}")

def list_products_screen():
    products = list_products()
    if products:
        # define o numero de cards por linha
        cards_for_row = 3
        # cria as colunas iniciais
        cols = st.columns(cards_for_row)
        for index, product in enumerate(products):
            col = cols[index % cards_for_row]
            with col:
                st.markdown(f"### {product['nome']}")
                st.write(f"Descrição: {product['descricao']}")
                st.write(f"Preço: R$ {product['preco']:.2f}")
                if product['imagem_url']:
                    html_img = f'<img src="{product["imagem_url"]}" width="150"/>'
                    st.markdown(html_img, unsafe_allow_html=True)
                st.markdown("---")

            # cria novas colunas a cada 'cards_for_row' produtos
            if(index + 1) % cards_for_row == 0 and (index + 1) < len(products):
                cols = st.columns(cards_for_row)
    else:
        st.info("Nenhum produto cadastrado.")



if st.button("Salvar Produto"):
    insert_product(product_name, product_description, product_price, upload_blob(product_image))
    list_products_screen()
    return_massage = "Produto salvo com sucesso!"

st.header("Produtos Cadastrados")

if st.button("Listar Produtos"):
    list_products_screen()
    return_massage = "Produtos listados com sucesso!"

