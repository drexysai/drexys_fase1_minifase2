#!/bin/bash

echo "======================================="
echo "   VERIFICAÇÃO DE REQUISITOS DR. EXYS "
echo "======================================="

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configurações do projeto Dr. Exys
DB_USER="dr_exys"
DB_NAME="dr_exys_db"
DB_PASSWORD="dr_exys123"
SERVER_IP="192.168.1.4"

# Função para verificar se um container está rodando
check_container() {
    local container_name=$1
    if docker ps --format "{{.Names}}" | grep -q "^${container_name}$"; then
        echo -e "${GREEN}✓ $container_name${NC}"
        return 0
    else
        echo -e "${RED}✗ $container_name${NC}"
        return 1
    fi
}

# Função para fazer requisição HTTP com timeout
http_check() {
    local url=$1
    local expected_code=$2
    local timeout=${3:-10}
    
    local response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout $timeout "$url" 2>/dev/null)
    
    if [ "$response" = "$expected_code" ]; then
        return 0
    else
        echo "$response"
        return 1
    fi
}

echo -e "\n${BLUE}🏥 Dr. Exys - Sistema Médico Inteligente${NC}"
echo -e "${BLUE}Verificando infraestrutura Docker...${NC}\n"

# 1. Verificar containers Dr. Exys
echo -e "${YELLOW}1. Containers Dr. Exys (4 containers):${NC}"
containers=("dr_exys_nginx" "dr_exys_backend" "dr_exys_frontend" "dr_exys_db")
running_containers=0

for container in "${containers[@]}"; do
    if check_container "$container"; then
        ((running_containers++))
    fi
done

if [ "$running_containers" -eq 4 ]; then
    echo -e "\n${GREEN}✓ Todos os 4 containers estão rodando${NC}"
    echo -e "\n${BLUE}Status detalhado:${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep dr_exys
else
    echo -e "\n${RED}✗ Apenas $running_containers/4 containers rodando${NC}"
    echo -e "${YELLOW}Containers que deveriam estar rodando:${NC}"
    for container in "${containers[@]}"; do
        echo "  - $container"
    done
fi

# 2. Verificar Nginx servindo página principal
echo -e "\n${YELLOW}2. Nginx servindo página Hello Medical World:${NC}"
if response=$(http_check "http://${SERVER_IP}:8081/" "200" 15); then
    echo -e "${GREEN}✓ Nginx respondendo (HTTP 200)${NC}"
    
    # Verificar se contém conteúdo esperado
    content=$(curl -s "http://${SERVER_IP}:8081/" 2>/dev/null)
    if echo "$content" | grep -q "Dr. Exys funcionando"; then
        echo -e "${GREEN}✓ Página 'Hello Medical World' carregada${NC}"
        echo -e "${BLUE}Conteúdo encontrado:${NC}"
        echo "$content" | grep -i "dr.*exys" | head -2
    else
        echo -e "${YELLOW}⚠ Nginx responde, mas conteúdo pode não estar correto${NC}"
        echo -e "${BLUE}Preview do conteúdo:${NC}"
        echo "$content" | head -3
    fi
else
    echo -e "${RED}✗ Nginx não está respondendo (HTTP $response)${NC}"
    echo -e "${YELLOW}Verificando se o container está acessível...${NC}"
    if docker exec dr_exys_nginx curl -s http://localhost >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠ Nginx responde internamente, problema pode ser de rede${NC}"
    else
        echo -e "${RED}✗ Nginx não responde nem internamente${NC}"
    fi
fi

# 3. Verificar Django Admin
echo -e "\n${YELLOW}3. Django Admin via Nginx:${NC}"
admin_response=$(http_check "http://${SERVER_IP}:8081/admin/" "200" 10)
if [ $? -eq 0 ] || [ "$admin_response" = "302" ]; then
    echo -e "${GREEN}✓ Django admin acessível (HTTP $admin_response)${NC}"
else
    echo -e "${RED}✗ Django admin não acessível (HTTP $admin_response)${NC}"
    
    # Testar Django direto
    echo -e "${YELLOW}Testando Django direto na porta 8007...${NC}"
    direct_response=$(http_check "http://${SERVER_IP}:8007/admin/" "200" 10)
    if [ $? -eq 0 ] || [ "$direct_response" = "302" ]; then
        echo -e "${YELLOW}⚠ Django funciona direto, problema no roteamento Nginx${NC}"
    else
        echo -e "${RED}✗ Django não responde nem diretamente (HTTP $direct_response)${NC}"
    fi
fi

# 4. Verificar Frontend Astro
echo -e "\n${YELLOW}4. Frontend Astro:${NC}"
if response=$(http_check "http://${SERVER_IP}:8008/" "200" 10); then
    echo -e "${GREEN}✓ Astro respondendo diretamente (HTTP 200)${NC}"
    
    # Verificar conteúdo específico do Astro
    astro_content=$(curl -s "http://${SERVER_IP}:8008/" 2>/dev/null)
    if echo "$astro_content" | grep -q "Dr. Exys funcionando"; then
        echo -e "${GREEN}✓ Página Astro carregada corretamente${NC}"
    else
        echo -e "${YELLOW}⚠ Astro responde, mas conteúdo pode estar incorreto${NC}"
    fi
else
    echo -e "${RED}✗ Astro não está respondendo (HTTP $response)${NC}"
fi

# 5. Verificar schemas PostgreSQL
echo -e "\n${YELLOW}5. Schemas PostgreSQL (medicos, ia_data):${NC}"
schemas_result=$(docker exec dr_exys_db psql -U $DB_USER -d $DB_NAME -t -c \
    "SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('medicos', 'ia_data');" 2>/dev/null)

if [ $? -eq 0 ]; then
    schema_count=$(echo "$schemas_result" | grep -E "medicos|ia_data" | wc -l)
    if [ "$schema_count" -eq 2 ]; then
        echo -e "${GREEN}✓ Schemas 'medicos' e 'ia_data' existem${NC}"
        echo -e "${BLUE}Schemas encontrados:${NC}"
        echo "$schemas_result" | grep -E "medicos|ia_data" | sed 's/^/ - /'
    else
        echo -e "${RED}✗ Faltam schemas (encontrados: $schema_count/2)${NC}"
        echo -e "${YELLOW}Tentando criar schemas em falta...${NC}"
        
        docker exec dr_exys_db psql -U $DB_USER -d $DB_NAME -c \
            "CREATE SCHEMA IF NOT EXISTS medicos; CREATE SCHEMA IF NOT EXISTS ia_data;" 2>/dev/null
        
        sleep 2
        
        # Verificar novamente
        new_schemas=$(docker exec dr_exys_db psql -U $DB_USER -d $DB_NAME -t -c \
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('medicos', 'ia_data');" 2>/dev/null)
        new_count=$(echo "$new_schemas" | grep -E "medicos|ia_data" | wc -l)
        
        if [ "$new_count" -eq 2 ]; then
            echo -e "${GREEN}✓ Schemas criados com sucesso${NC}"
        else
            echo -e "${RED}✗ Ainda faltam schemas após tentativa de criação${NC}"
        fi
    fi
else
    echo -e "${RED}✗ Erro ao conectar no PostgreSQL${NC}"
    echo -e "${YELLOW}Verificando se o container do banco está acessível...${NC}"
    if docker exec dr_exys_db pg_isready -U $DB_USER >/dev/null 2>&1; then
        echo -e "${YELLOW}⚠ PostgreSQL está rodando, problema pode ser de autenticação${NC}"
    else
        echo -e "${RED}✗ PostgreSQL não está respondendo${NC}"
    fi
fi

# 6. Verificar comunicação entre containers
echo -e "\n${YELLOW}6. Comunicação entre containers:${NC}"

# Nginx → Backend
echo -e "${BLUE}6.1 Nginx → Backend:${NC}"
nginx_to_backend=$(docker exec dr_exys_nginx curl -s -o /dev/null -w "%{http_code}" \
    http://backend:8000 2>/dev/null || echo "000")
if [ "$nginx_to_backend" != "000" ] && [ "$nginx_to_backend" != "" ]; then
    echo -e "${GREEN}✓ Nginx → Backend funcionando (HTTP $nginx_to_backend)${NC}"
else
    echo -e "${RED}✗ Problema na comunicação Nginx → Backend${NC}"
fi

# Nginx → Frontend
echo -e "${BLUE}6.2 Nginx → Frontend:${NC}"
nginx_to_frontend=$(docker exec dr_exys_nginx curl -s -o /dev/null -w "%{http_code}" \
    http://frontend:3000 2>/dev/null || echo "000")
if [ "$nginx_to_frontend" != "000" ] && [ "$nginx_to_frontend" != "" ]; then
    echo -e "${GREEN}✓ Nginx → Frontend funcionando (HTTP $nginx_to_frontend)${NC}"
else
    echo -e "${RED}✗ Problema na comunicação Nginx → Frontend${NC}"
fi

# Backend → Database
echo -e "${BLUE}6.3 Backend → Database:${NC}"
backend_to_db=$(docker exec dr_exys_backend python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()
from django.db import connection
try:
    cursor = connection.cursor()
    cursor.execute('SELECT 1')
    print('OK')
except Exception as e:
    print(f'ERROR: {e}')
" 2>/dev/null)

if [ "$backend_to_db" = "OK" ]; then
    echo -e "${GREEN}✓ Backend → Database funcionando${NC}"
else
    echo -e "${RED}✗ Problema na comunicação Backend → Database${NC}"
    echo -e "${YELLOW}Erro: $backend_to_db${NC}"
fi

# 7. Resumo final
echo -e "\n${YELLOW}=======================================${NC}"
echo -e "${YELLOW}           RESUMO FINAL                ${NC}"
echo -e "${YELLOW}=======================================${NC}"

echo -e "\n${BLUE}📋 Checklist Dr. Exys:${NC}"
echo -e "   ${GREEN}✓${NC} Containers rodando: $running_containers/4"

# URLs principais para teste
echo -e "\n${BLUE}🌐 URLs para teste:${NC}"
echo -e "   • Página principal: http://${SERVER_IP}:8081/"
echo -e "   • Django Admin: http://${SERVER_IP}:8081/admin/"
echo -e "   • Frontend direto: http://${SERVER_IP}:8008/"
echo -e "   • Backend direto: http://${SERVER_IP}:8007/admin/"

# Comandos úteis
echo -e "\n${BLUE}🔧 Comandos úteis:${NC}"
echo -e "   • Ver logs: ${YELLOW}docker-compose logs -f [service]${NC}"
echo -e "   • Restart: ${YELLOW}docker-compose restart [service]${NC}"
echo -e "   • Rebuild: ${YELLOW}docker-compose up --build${NC}"

echo -e "\n${GREEN}🏥 Dr. Exys - Verificação concluída!${NC}"