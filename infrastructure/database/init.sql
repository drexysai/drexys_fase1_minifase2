-- Database dr_exys_db já é criado automaticamente via POSTGRES_DB
-- Criar apenas os schemas necessários:

CREATE SCHEMA IF NOT EXISTS medicos;
CREATE SCHEMA IF NOT EXISTS ia_data;

-- Opcional: Confirmar que schemas foram criados
SELECT 'Schemas médicos criados com sucesso!' as status;