# Desafio Trainee - Mini Ifood

API REST desenvolvida para um serviço de venda de comida, contendo as funcionalidades básicas de um mini-ifood.

## 🛠 Tecnologias Utilizadas

| Biblioteca | Versão | Função Principal no Projeto |
| :--- | :--- | :--- |
| **Django** | `5.2.6` | **Framework Web Core**. |
| **Django REST Framework** | `3.16.1` | Criação de Endpoints RESTful. |
| **drf-yasg** | `1.21.11` | Geração da **Documentação Swagger/OpenAPI**. |
| **djangorestframework_simplejwt** | `5.5.1` | **Autenticação JWT** (usado via Cookies customizados). |
| **django-filter** | `25.2` | Implementação de filtros em Views. |
| **PyJWT** | `2.10.1` | Manipulação de tokens JSON Web Token. |

## ⚡ Instalação e Execução

Siga o passo a passo abaixo para configurar e rodar a API localmente no ambiente de desenvolvimento.

#### 1. Clonar o repositório
```
git clone [https://github.com/rafaelafariasm56-blip/Desafio-Trainee.git](https://github.com/rafaelafariasm56-blip/Desafio-Trainee.git)
cd Desafio-Trainee
```
### 2. Criar e ativar Ambiente Virtual
```
# Cria o ambiente
python -m venv venv

# Ativação (Linux/Mac)
source venv/bin/activate
```

### 3. Instalar as dependências
```
pip install -r requirements.txt
```

### 4. Configurar o Banco de Dados
Comando para aplicar as migrações:
```
python manage.py migrate
```

### 5. Iniciar o servidor
```
python manage.py runserver
```
A API estará acessível em: `http://localhost:8000/`

## 🔒 Acessando a Documentação

Com o servidor rodando, a documentação está disponível nos seguintes formatos:

| Formato | URL | Uso |
| :--- | :--- | :--- |
| **Swagger UI** | `http://127.0.0.1:8000/swagger/` | **Visualização interativa** e envio de requisições. |
| **Schema JSON** | `http://127.0.0.1:8000/swagger.json` | Download do arquivo de definição da API (para ferramentas como Postman, Insomnia ou clientes geradores de código). |
| **Schema YAML** | `http://127.0.0.1:8000/swagger.yaml` | Download do arquivo de definição no formato YAML. |

### Mecanismo de autenticação (JWT via Cookie)

Esta API usa um mecanismo de autenticação seguro para clientes Web:

1. O endpoint de login define o access_token como um Cookie HTTP Only.
2. O JWTHeaderMiddleware (customizado) intercepta o cookie a cada requisição e o move para o cabeçalho Authorization: Bearer <token>, permitindo que o DRF o valide.

###ENDPOINTS
### 🛍️ Cliente (Consumidor)

#### 🔑 Autenticação e Perfil
* `POST /api/users/register/`: Registrar novo usuário/cliente
* `POST /api/users/login/`: Autenticar-se e obter token
* `GET /api/users/painel/usuario/`: Ver painel do usuário

#### 🏡 Endereço e Pagamento
* `GET /api/pedidos/endereco/`: Listar endereços cadastrados
* `POST /api/pedidos/endereco/`: Cadastrar novo endereço
* `PUT/DELETE /api/pedidos/endereco/{id}/`: Atualizar/Excluir um endereço
* `POST /api/pedidos/pagamento/`: Cadastrar novo método de pagamento
* `DELETE /api/pedidos/pagamento/{id}/`: Excluir método de pagamento

#### 🛒 Compras e Pedidos
* `GET /api/core/produtos/`: Listar todos os produtos disponíveis
* `GET /api/pedidos/carrinho/`: Visualizar itens do carrinho
* `POST /api/pedidos/carrinho/`: Adicionar item ao carrinho ou atualizar quantidade
* `DELETE /api/pedidos/carrinho/{id}/`: Remover um item do carrinho
* `POST /api/pedidos/pagamento/pagar/`: **Finalizar compra** (Converter carrinho em pedido)
* `GET /api/pedidos/historico-pedidos/`: Listar histórico de pedidos realizados
* `GET /api/pedidos/historico-pedidos/{id}/`: Ver detalhes e status de um pedido

---

### 🏪 Loja 

#### 🔑 Autenticação e Perfil
* `POST /api/users/register/`: Registrar nova loja/usuário comerciante
* `POST /api/users/login/`: Autenticar-se e obter token
* `GET /api/users/painel/loja/`: Ver painel de lojas

#### 🍕 Gestão de Produtos e Catálogo
* `GET /api/core/cardapio/`: Listar produtos do cardápio da própria loja
* `POST /api/core/produtos/`: Cadastrar novo produto
* `GET /api/core/produtos/{id}/`: Ver detalhes de um produto
* `PUT/PATCH /api/core/produtos/{id}/`: Atualizar/Modificar dados ou estoque de um produto
* `DELETE /api/core/produtos/{id}/`: Excluir um produto

#### 💰 Vendas e Finanças
* `GET /api/pedidos/historico-loja/`: Listar todos os pedidos recebidos pela loja
* `PATCH /api/pedidos/{id}/`: **Atualizar status** do pedido (e.g., `preparando`, `entregue`)
* `GET /api/pedidos/faturamento/`: Ver relatórios de faturamento por período
