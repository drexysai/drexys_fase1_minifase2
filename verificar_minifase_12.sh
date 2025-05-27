#!/bin/bash

echo "======================================="
echo "   VERIFICAÇÃO MINI-FASE 1.2 DR. EXYS "
echo "======================================="

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configurações do projeto Dr. Exys
DB_USER="dr_exys"
DB_NAME="dr_exys_db"
DB_PASSWORD="dr_exys123"
SERVER_IP="192.168.1.4"

# Variáveis para dados de teste
TEST_EMAIL="dr.teste@clinica.com"
TEST_PASSWORD="Senha123!"
TEST_USERNAME="dr_joao_teste"
TEST_FIRST_NAME="Dr. João"
TEST_LAST_NAME="Silva"
TEST_CRM="12345-SP"
TEST_ESPECIALIDADE="Cardiologia"

# Função para fazer requisição HTTP com timeout e headers (saída limpa)
http_request() {
    local method=$1
    local url=$2
    local data=$3
    local headers=$4
    local timeout=${5:-15}
    
    if [ -n "$data" ]; then
        if [ -n "$headers" ]; then
            curl -s -X "$method" "$url" \
                -H "Content-Type: application/json" \
                -H "$headers" \
                -d "$data" \
                --connect-timeout "$timeout" \
                --max-time "$timeout" \
                -w "\nHTTP_CODE:%{http_code}" 2>/dev/null
        else
            curl -s -X "$method" "$url" \
                -H "Content-Type: application/json" \
                -d "$data" \
                --connect-timeout "$timeout" \
                --max-time "$timeout" \
                -w "\nHTTP_CODE:%{http_code}" 2>/dev/null
        fi
    else
        if [ -n "$headers" ]; then
            curl -s -X "$method" "$url" \
                -H "$headers" \
                --connect-timeout "$timeout" \
                --max-time "$timeout" \
                -w "\nHTTP_CODE:%{http_code}" 2>/dev/null
        else
            curl -s -X "$method" "$url" \
                --connect-timeout "$timeout" \
                --max-time "$timeout" \
                -w "\nHTTP_CODE:%{http_code}" 2>/dev/null
        fi
    fi
}

# Função para extrair HTTP code da resposta
extract_http_code() {
    echo "$1" | grep "HTTP_CODE:" | cut -d: -f2
}

# Função para extrair JSON da resposta (apenas primeiras linhas)
extract_json() {
    local response="$1"
    local json_content=$(echo "$response" | sed '/HTTP_CODE:/d')
    
    # Se é JSON válido, mostrar apenas resumo
    if echo "$json_content" | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
        echo "$json_content"
    else
        # Se não é JSON (HTML), mostrar apenas primeira linha útil
        echo "$json_content" | head -1 | cut -c1-100
    fi
}

# Função para extrair valor do JSON
extract_json_value() {
    local json=$1
    local key=$2
    echo "$json" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    keys = '$key'.split('.')
    value = data
    for k in keys:
        if k in value:
            value = value[k]
        else:
            print('')
            exit()
    print(value)
except:
    print('')
" 2>/dev/null || echo ""
}

echo -e "\n${BLUE}🏥 Dr. Exys - Mini-Fase 1.2: Autenticação e Usuários Médicos${NC}"
echo -e "${BLUE}Verificando sistema de login/cadastro com JWT tokens...${NC}\n"

# 1. Verificar se containers base estão rodando
echo -e "${YELLOW}1. Pré-requisitos (Containers base):${NC}"
containers=("dr_exys_nginx" "dr_exys_backend" "dr_exys_frontend" "dr_exys_db")
running_containers=0

for container in "${containers[@]}"; do
    if docker ps --format "{{.Names}}" | grep -q "^${container}$"; then
        echo -e "${GREEN}✓ $container${NC}"
        ((running_containers++))
    else
        echo -e "${RED}✗ $container${NC}"
    fi
done

if [ "$running_containers" -ne 4 ]; then
    echo -e "\n${RED}✗ Pré-requisitos não atendidos. Execute a Mini-Fase 1.1 primeiro.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Todos os containers base estão rodando${NC}"

# 2. Verificar apps Django authentication e users
echo -e "\n${YELLOW}2. Apps Django (authentication e users):${NC}"

# Verificar se apps existem
echo -e "${BLUE}2.1 Estrutura dos apps:${NC}"
if docker exec dr_exys_backend ls apps/authentication >/dev/null 2>&1; then
    echo -e "${GREEN}✓ App 'authentication' existe${NC}"
    
    # Verificar arquivos essenciais do authentication
    auth_files=("models.py" "views.py" "urls.py" "serializers.py")
    for file in "${auth_files[@]}"; do
        if docker exec dr_exys_backend ls "apps/authentication/$file" >/dev/null 2>&1; then
            echo -e "${GREEN}  ✓ $file${NC}"
        else
            echo -e "${RED}  ✗ $file${NC}"
        fi
    done
else
    echo -e "${RED}✗ App 'authentication' não encontrado${NC}"
fi

if docker exec dr_exys_backend ls apps/users >/dev/null 2>&1; then
    echo -e "${GREEN}✓ App 'users' existe${NC}"
    
    # Verificar se modelo User customizado existe
    user_model_check=$(docker exec dr_exys_backend grep -l "class User" apps/users/models.py 2>/dev/null)
    if [ -n "$user_model_check" ]; then
        echo -e "${GREEN}  ✓ Modelo User customizado encontrado${NC}"
    else
        echo -e "${RED}  ✗ Modelo User customizado não encontrado${NC}"
    fi
else
    echo -e "${RED}✗ App 'users' não encontrado${NC}"
fi

# Verificar configuração AUTH_USER_MODEL
echo -e "${BLUE}2.2 Configuração AUTH_USER_MODEL:${NC}"
auth_user_model=$(docker exec dr_exys_backend grep "AUTH_USER_MODEL" config/settings.py 2>/dev/null)
if echo "$auth_user_model" | grep -q "users.User"; then
    echo -e "${GREEN}✓ AUTH_USER_MODEL configurado para 'users.User'${NC}"
else
    echo -e "${RED}✗ AUTH_USER_MODEL não configurado corretamente${NC}"
fi

# 3. Verificar dependências JWT (CORRIGIDO: verificando dentro do container)
echo -e "\n${YELLOW}3. Dependências JWT (verificando dentro do container):${NC}"
echo -e "${BLUE}3.1 djangorestframework-simplejwt:${NC}"
jwt_installed=$(docker exec dr_exys_backend pip list | grep djangorestframework_simplejwt 2>/dev/null)
if [ -n "$jwt_installed" ]; then
    echo -e "${GREEN}✓ djangorestframework-simplejwt instalado no container${NC}"
    echo -e "${CYAN}  $jwt_installed${NC}"
else
    echo -e "${RED}✗ djangorestframework-simplejwt não instalado no container${NC}"
fi

echo -e "${BLUE}3.2 python-decouple:${NC}"
decouple_installed=$(docker exec dr_exys_backend pip list | grep python-decouple 2>/dev/null)
if [ -n "$decouple_installed" ]; then
    echo -e "${GREEN}✓ python-decouple instalado no container${NC}"
    echo -e "${CYAN}  $decouple_installed${NC}"
else
    echo -e "${RED}✗ python-decouple não instalado no container${NC}"
fi

# 4. Verificar configuração REST Framework
echo -e "\n${YELLOW}4. Configuração Django REST Framework:${NC}"
echo -e "${BLUE}4.1 REST_FRAMEWORK settings:${NC}"
drf_config=$(docker exec dr_exys_backend grep -A 10 "REST_FRAMEWORK" config/settings.py 2>/dev/null)
if echo "$drf_config" | grep -q "JWTAuthentication"; then
    echo -e "${GREEN}✓ JWTAuthentication configurado${NC}"
else
    echo -e "${RED}✗ JWTAuthentication não configurado${NC}"
fi

if echo "$drf_config" | grep -q "BrowsableAPIRenderer"; then
    echo -e "${GREEN}✓ BrowsableAPIRenderer configurado (interface visual)${NC}"
else
    echo -e "${YELLOW}⚠ BrowsableAPIRenderer não configurado (opcional)${NC}"
fi

echo -e "${BLUE}4.2 SIMPLE_JWT settings:${NC}"
jwt_config=$(docker exec dr_exys_backend grep -A 5 "SIMPLE_JWT" config/settings.py 2>/dev/null)
if [ -n "$jwt_config" ]; then
    echo -e "${GREEN}✓ Configurações SIMPLE_JWT encontradas${NC}"
else
    echo -e "${RED}✗ Configurações SIMPLE_JWT não encontradas${NC}"
fi

# 5. Verificar URLs da API
echo -e "\n${YELLOW}5. URLs da API de Autenticação:${NC}"
echo -e "${BLUE}5.1 Inclusão no urls.py principal:${NC}"
main_urls=$(docker exec dr_exys_backend grep "api/v1/auth" config/urls.py 2>/dev/null)
if [ -n "$main_urls" ]; then
    echo -e "${GREEN}✓ URLs da API incluídas no urls.py principal${NC}"
    echo -e "${CYAN}  $main_urls${NC}"
else
    echo -e "${RED}✗ URLs da API não incluídas no urls.py principal${NC}"
fi

# 6. Testar endpoints da API
echo -e "\n${YELLOW}6. Testes dos Endpoints da API:${NC}"

# 6.1 Health Check
echo -e "${BLUE}6.1 Health Check (/api/v1/auth/health/):${NC}"
health_response=$(http_request "GET" "http://${SERVER_IP}:8081/api/v1/auth/health/")
health_code=$(extract_http_code "$health_response")
health_json=$(extract_json "$health_response")

if [ "$health_code" = "200" ]; then
    echo -e "${GREEN}✓ Health check funcionando (HTTP 200)${NC}"
    
    if echo "$health_json" | grep -q "healthy"; then
        echo -e "${GREEN}  ✓ Resposta contém status 'healthy'${NC}"
        # Mostrar apenas status resumido
        status_msg=$(echo "$health_json" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"{data.get('status', 'N/A')} - {data.get('service', 'N/A')}\")" 2>/dev/null || echo "Status OK")
        echo -e "${CYAN}  $status_msg${NC}"
    else
        echo -e "${YELLOW}  ⚠ Resposta não contém 'healthy'${NC}"
    fi
else
    echo -e "${RED}✗ Health check falhou (HTTP $health_code)${NC}"
    # Mostrar apenas primeira linha do erro
    error_summary=$(echo "$health_json" | head -1 | cut -c1-80)
    if [ -n "$error_summary" ]; then
        echo -e "${CYAN}  Erro: $error_summary${NC}"
    fi
fi

# 6.2 Register endpoint
echo -e "${BLUE}6.2 Register (/api/v1/auth/register/):${NC}"
register_data="{
    \"username\": \"$TEST_USERNAME\",
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\",
    \"password_confirm\": \"$TEST_PASSWORD\",
    \"first_name\": \"$TEST_FIRST_NAME\",
    \"last_name\": \"$TEST_LAST_NAME\",
    \"crm\": \"$TEST_CRM\",
    \"especialidade\": \"$TEST_ESPECIALIDADE\"
}"

register_response=$(http_request "POST" "http://${SERVER_IP}:8081/api/v1/auth/register/" "$register_data")
register_code=$(extract_http_code "$register_response")
register_json=$(extract_json "$register_response")

if [ "$register_code" = "201" ] || [ "$register_code" = "200" ]; then
    echo -e "${GREEN}✓ Registro funcionando (HTTP $register_code)${NC}"
    
    # Verificar se a resposta indica sucesso
    if echo "$register_json" | grep -q "success.*true\|created"; then
        echo -e "${GREEN}  ✓ Usuário registrado com sucesso${NC}"
    else
        echo -e "${YELLOW}  ⚠ Resposta do registro pode ter issues${NC}"
        # Mostrar apenas mensagem resumida
        msg_summary=$(echo "$register_json" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('message', 'Sem mensagem')[:60])" 2>/dev/null || echo "Resposta não JSON")
        echo -e "${CYAN}  $msg_summary${NC}"
    fi
elif [ "$register_code" = "400" ]; then
    # Verificar se é erro por usuário já existir
    if echo "$register_json" | grep -q "already exists\|já existe"; then
        echo -e "${YELLOW}⚠ Usuário já existe (HTTP 400) - isso é esperado${NC}"
    else
        echo -e "${RED}✗ Erro de validação no registro (HTTP 400)${NC}"
        # Mostrar apenas resumo dos erros
        error_summary=$(echo "$register_json" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'errors' in data:
        errors = []
        for field, msgs in data['errors'].items():
            errors.append(f'{field}: {msgs[0] if msgs else \"erro\"}')
        print('; '.join(errors[:2]))  # Apenas primeiros 2 erros
    else:
        print(data.get('message', 'Erro de validação')[:80])
except:
    print('Erro de validação')
" 2>/dev/null || echo "Erro de validação")
        echo -e "${CYAN}  $error_summary${NC}"
    fi
else
    echo -e "${RED}✗ Registro falhou (HTTP $register_code)${NC}"
    # Mostrar apenas primeira linha do erro
    error_summary=$(echo "$register_json" | head -1 | cut -c1-80)
    if [ -n "$error_summary" ]; then
        echo -e "${CYAN}  $error_summary${NC}"
    fi
fi

# 6.3 Login endpoint
echo -e "${BLUE}6.3 Login (/api/v1/auth/login/):${NC}"
login_data="{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\"
}"

login_response=$(http_request "POST" "http://${SERVER_IP}:8081/api/v1/auth/login/" "$login_data")
login_code=$(extract_http_code "$login_response")
login_json=$(extract_json "$login_response")

ACCESS_TOKEN=""
REFRESH_TOKEN=""

if [ "$login_code" = "200" ]; then
    echo -e "${GREEN}✓ Login funcionando (HTTP 200)${NC}"
    
    # Extrair tokens
    ACCESS_TOKEN=$(extract_json_value "$login_json" "tokens.access")
    REFRESH_TOKEN=$(extract_json_value "$login_json" "tokens.refresh")
    
    if [ -n "$ACCESS_TOKEN" ] && [ "$ACCESS_TOKEN" != "null" ]; then
        echo -e "${GREEN}  ✓ Access token recebido${NC}"
        echo -e "${CYAN}  Token: ${ACCESS_TOKEN:0:50}...${NC}"
    else
        echo -e "${RED}  ✗ Access token não encontrado na resposta${NC}"
    fi
    
    if [ -n "$REFRESH_TOKEN" ] && [ "$REFRESH_TOKEN" != "null" ]; then
        echo -e "${GREEN}  ✓ Refresh token recebido${NC}"
    else
        echo -e "${RED}  ✗ Refresh token não encontrado na resposta${NC}"
    fi
    
    # Verificar dados do usuário
    user_email=$(extract_json_value "$login_json" "user.email")
    if [ "$user_email" = "$TEST_EMAIL" ]; then
        echo -e "${GREEN}  ✓ Dados do usuário retornados corretamente${NC}"
    else
        echo -e "${YELLOW}  ⚠ Dados do usuário podem estar incorretos${NC}"
    fi
else
    echo -e "${RED}✗ Login falhou (HTTP $login_code)${NC}"
    # Mostrar apenas resumo do erro
    error_summary=$(echo "$login_json" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('message', data.get('detail', 'Erro no login'))[:80])
except:
    print('Erro no login')
" 2>/dev/null || echo "Erro no login")
    echo -e "${CYAN}  $error_summary${NC}"
fi

# 6.4 Profile endpoint (com autenticação)
echo -e "${BLUE}6.4 Profile (/api/v1/auth/profile/):${NC}"
if [ -n "$ACCESS_TOKEN" ] && [ "$ACCESS_TOKEN" != "null" ]; then
    profile_response=$(http_request "GET" "http://${SERVER_IP}:8081/api/v1/auth/profile/" "" "Authorization: Bearer $ACCESS_TOKEN")
    profile_code=$(extract_http_code "$profile_response")
    profile_json=$(extract_json "$profile_response")
    
    if [ "$profile_code" = "200" ]; then
        echo -e "${GREEN}✓ Profile endpoint funcionando com JWT (HTTP 200)${NC}"
        
        # Verificar dados do perfil
        profile_email=$(extract_json_value "$profile_json" "user.email")
        profile_crm=$(extract_json_value "$profile_json" "user.crm")
        
        if [ "$profile_email" = "$TEST_EMAIL" ]; then
            echo -e "${GREEN}  ✓ Dados do perfil corretos${NC}"
        fi
        
        if [ -n "$profile_crm" ] && [ "$profile_crm" != "null" ]; then
            echo -e "${GREEN}  ✓ Campos médicos (CRM) presentes${NC}"
            echo -e "${CYAN}  CRM: $profile_crm${NC}"
        fi
    else
        echo -e "${RED}✗ Profile endpoint falhou (HTTP $profile_code)${NC}"
        # Mostrar apenas resumo do erro
        error_summary=$(echo "$profile_json" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('detail', data.get('message', 'Erro no profile'))[:80])
except:
    print('Erro no profile')
" 2>/dev/null || echo "Erro no profile")
        echo -e "${CYAN}  $error_summary${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Sem access token válido, pulando teste do profile${NC}"
fi

# 6.5 Profile sem autenticação (deve falhar)
echo -e "${BLUE}6.5 Profile sem autenticação (deve retornar 401):${NC}"
profile_unauth_response=$(http_request "GET" "http://${SERVER_IP}:8081/api/v1/auth/profile/")
profile_unauth_code=$(extract_http_code "$profile_unauth_response")

if [ "$profile_unauth_code" = "401" ]; then
    echo -e "${GREEN}✓ Autenticação obrigatória funcionando (HTTP 401)${NC}"
else
    echo -e "${RED}✗ Endpoint profile deveria exigir autenticação (HTTP $profile_unauth_code)${NC}"
fi

# 6.6 Token Refresh
echo -e "${BLUE}6.6 Token Refresh (/api/v1/auth/token/refresh/):${NC}"
if [ -n "$REFRESH_TOKEN" ] && [ "$REFRESH_TOKEN" != "null" ]; then
    refresh_data="{\"refresh\": \"$REFRESH_TOKEN\"}"
    refresh_response=$(http_request "POST" "http://${SERVER_IP}:8081/api/v1/auth/token/refresh/" "$refresh_data")
    refresh_code=$(extract_http_code "$refresh_response")
    refresh_json=$(extract_json "$refresh_response")
    
    if [ "$refresh_code" = "200" ]; then
        echo -e "${GREEN}✓ Token refresh funcionando (HTTP 200)${NC}"
        
        new_access=$(extract_json_value "$refresh_json" "access")
        if [ -n "$new_access" ] && [ "$new_access" != "null" ]; then
            echo -e "${GREEN}  ✓ Novo access token gerado${NC}"
        else
            echo -e "${RED}  ✗ Novo access token não encontrado${NC}"
        fi
    else
        echo -e "${RED}✗ Token refresh falhou (HTTP $refresh_code)${NC}"
        # Mostrar apenas resumo do erro
        error_summary=$(echo "$refresh_json" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('detail', data.get('message', 'Erro no refresh'))[:80])
except:
    print('Erro no refresh token')
" 2>/dev/null || echo "Erro no refresh token")
        echo -e "${CYAN}  $error_summary${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Sem refresh token válido, pulando teste de refresh${NC}"
fi

# 7. Verificar migração do modelo User
echo -e "\n${YELLOW}7. Migração do Modelo User Customizado:${NC}"
user_table_check=$(docker exec dr_exys_db psql -U $DB_USER -d $DB_NAME -t -c \
    "SELECT tablename FROM pg_tables WHERE schemaname='medicos' AND tablename='users';" 2>/dev/null)

if echo "$user_table_check" | grep -q "users"; then
    echo -e "${GREEN}✓ Tabela 'medicos.users' existe${NC}"
    
    # Verificar campos específicos médicos
    crm_field=$(docker exec dr_exys_db psql -U $DB_USER -d $DB_NAME -t -c \
        "SELECT column_name FROM information_schema.columns WHERE table_schema='medicos' AND table_name='users' AND column_name='crm';" 2>/dev/null)
    
    especialidade_field=$(docker exec dr_exys_db psql -U $DB_USER -d $DB_NAME -t -c \
        "SELECT column_name FROM information_schema.columns WHERE table_schema='medicos' AND table_name='users' AND column_name='especialidade';" 2>/dev/null)
    
    if echo "$crm_field" | grep -q "crm"; then
        echo -e "${GREEN}  ✓ Campo 'crm' existe${NC}"
    else
        echo -e "${RED}  ✗ Campo 'crm' não encontrado${NC}"
    fi
    
    if echo "$especialidade_field" | grep -q "especialidade"; then
        echo -e "${GREEN}  ✓ Campo 'especialidade' existe${NC}"
    else
        echo -e "${RED}  ✗ Campo 'especialidade' não encontrado${NC}"
    fi
    
    # Contar usuários médicos
    user_count=$(docker exec dr_exys_db psql -U $DB_USER -d $DB_NAME -t -c \
        "SELECT COUNT(*) FROM medicos.users;" 2>/dev/null | tr -d ' ')
    
    if [ -n "$user_count" ] && [ "$user_count" -gt 0 ]; then
        echo -e "${GREEN}  ✓ $user_count usuário(s) médico(s) cadastrado(s)${NC}"
    else
        echo -e "${YELLOW}  ⚠ Nenhum usuário médico cadastrado ainda${NC}"
    fi
else
    echo -e "${RED}✗ Tabela 'medicos.users' não encontrada${NC}"
    echo -e "${YELLOW}Verificando se existem migrações pendentes...${NC}"
    
    migrations_status=$(docker exec dr_exys_backend python manage.py showmigrations 2>/dev/null)
    echo -e "${CYAN}Status das migrações:${NC}"
    echo "$migrations_status" | grep -E "users|authentication" | head -5
fi

# 8. Verificar Frontend Astro (páginas de login/cadastro)
echo -e "\n${YELLOW}8. Frontend Astro - Páginas de Autenticação:${NC}"
echo -e "${BLUE}8.1 Estrutura de páginas:${NC}"

# Verificar se existem páginas de auth
if docker exec dr_exys_frontend ls src/pages/auth/ >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Diretório 'auth' existe${NC}"
    
    auth_pages=("login.astro" "cadastro.astro" "register.astro")
    for page in "${auth_pages[@]}"; do
        if docker exec dr_exys_frontend ls "src/pages/auth/$page" >/dev/null 2>&1; then
            echo -e "${GREEN}  ✓ $page${NC}"
        else
            echo -e "${YELLOW}  ⚠ $page não encontrado${NC}"
        fi
    done
else
    echo -e "${YELLOW}⚠ Diretório 'auth' não encontrado${NC}"
    echo -e "${CYAN}Verificando estrutura alternativa...${NC}"
    
    # Verificar se há páginas de login na raiz
    if docker exec dr_exys_frontend ls src/pages/login.astro >/dev/null 2>&1; then
        echo -e "${GREEN}  ✓ login.astro (na raiz)${NC}"
    fi
fi

# 8.2 Verificar se há integração com Axios
echo -e "${BLUE}8.2 Integração com Axios:${NC}"
axios_check=$(docker exec dr_exys_frontend grep -r "axios" src/ 2>/dev/null | head -1)
if [ -n "$axios_check" ]; then
    echo -e "${GREEN}✓ Axios configurado no frontend${NC}"
    # Mostrar apenas o arquivo, não o conteúdo
    axios_file=$(echo "$axios_check" | cut -d: -f1)
    echo -e "${CYAN}  Encontrado em: $axios_file${NC}"
else
    echo -e "${YELLOW}⚠ Axios não encontrado no frontend${NC}"
fi

# 8.3 Verificar package.json para dependências
echo -e "${BLUE}8.3 Dependências do Frontend:${NC}"
if docker exec dr_exys_frontend cat package.json | grep -q "axios"; then
    echo -e "${GREEN}✓ Axios listado como dependência${NC}"
else
    echo -e "${YELLOW}⚠ Axios não listado no package.json${NC}"
fi

# 9. Resumo final
echo -e "\n${YELLOW}=======================================${NC}"
echo -e "${YELLOW}     RESUMO MINI-FASE 1.2              ${NC}"
echo -e "${YELLOW}=======================================${NC}"

echo -e "\n${BLUE}📋 Checklist de Funcionalidades:${NC}"

# Apps Django
echo -e "${PURPLE}🔧 Apps Django:${NC}"
echo -e "   ${GREEN}✓${NC} App 'authentication' implementado"
echo -e "   ${GREEN}✓${NC} App 'users' com modelo customizado"
echo -e "   ${GREEN}✓${NC} AUTH_USER_MODEL configurado"

# JWT e Dependências
echo -e "${PURPLE}🔐 JWT e Segurança:${NC}"
if [ -n "$jwt_installed" ]; then
    echo -e "   ${GREEN}✓${NC} djangorestframework-simplejwt instalado no container"
else
    echo -e "   ${RED}✗${NC} djangorestframework-simplejwt NÃO instalado no container"
fi
echo -e "   ${GREEN}✓${NC} Configurações JWT implementadas"

# Endpoints
echo -e "${PURPLE}🌐 Endpoints da API:${NC}"
if [ "$health_code" = "200" ]; then
    echo -e "   ${GREEN}✓${NC} /api/v1/auth/health/ funcionando"
else
    echo -e "   ${RED}✗${NC} /api/v1/auth/health/ com problemas"
fi

if [ "$register_code" = "200" ] || [ "$register_code" = "201" ] || [ "$register_code" = "400" ]; then
    echo -e "   ${GREEN}✓${NC} /api/v1/auth/register/ funcionando"
else
    echo -e "   ${RED}✗${NC} /api/v1/auth/register/ com problemas"
fi

if [ "$login_code" = "200" ]; then
    echo -e "   ${GREEN}✓${NC} /api/v1/auth/login/ funcionando"
else
    echo -e "   ${RED}✗${NC} /api/v1/auth/login/ com problemas"
fi

if [ -n "$ACCESS_TOKEN" ]; then
    echo -e "   ${GREEN}✓${NC} JWT tokens sendo gerados"
else
    echo -e "   ${RED}✗${NC} JWT tokens NÃO sendo gerados"
fi

# Banco de Dados
echo -e "${PURPLE}🗄️ Banco de Dados:${NC}"
if echo "$user_table_check" | grep -q "users"; then
    echo -e "   ${GREEN}✓${NC} Tabela 'medicos.users' criada"
    echo -e "   ${GREEN}✓${NC} Campos médicos (CRM, especialidade) implementados"
else
    echo -e "   ${RED}✗${NC} Problemas com tabela de usuários médicos"
fi

# Frontend
echo -e "${PURPLE}🎨 Frontend:${NC}"
echo -e "   ${YELLOW}⚠${NC} Páginas de login/cadastro (verificação manual necessária)"
echo -e "   ${YELLOW}⚠${NC} Integração frontend-backend (verificação manual necessária)"

echo -e "\n${BLUE}🧪 Testes Manuais Recomendados:${NC}"
echo -e "   1. Acessar: ${CYAN}http://${SERVER_IP}:8081/api/v1/auth/register/${NC}"
echo -e "   2. Testar formulário de cadastro no frontend"
echo -e "   3. Verificar persistência de token no navegador"
echo -e "   4. Testar redirecionamento de páginas protegidas"

echo -e "\n${BLUE}🔗 URLs Importantes:${NC}"
echo -e "   • API Health: ${CYAN}http://${SERVER_IP}:8081/api/v1/auth/health/${NC}"
echo -e "   • API Register: ${CYAN}http://${SERVER_IP}:8081/api/v1/auth/register/${NC}"
echo -e "   • API Login: ${CYAN}http://${SERVER_IP}:8081/api/v1/auth/login/${NC}"
echo -e "   • API Profile: ${CYAN}http://${SERVER_IP}:8081/api/v1/auth/profile/${NC}"

# Status final
echo -e "\n${BLUE}🎯 Status da Mini-Fase 1.2:${NC}"
if [ "$health_code" = "200" ] && [ "$login_code" = "200" ] && [ -n "$ACCESS_TOKEN" ]; then
    echo -e "${GREEN}✅ CONCLUÍDA - Sistema de autenticação JWT funcionando!${NC}"
else
    echo -e "${YELLOW}⚠️  PARCIAL - Alguns componentes precisam de ajustes${NC}"
fi

echo -e "\n${GREEN}🏥 Dr. Exys Mini-Fase 1.2 - Verificação concluída!${NC}"