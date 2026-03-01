-- Este archivo corre automáticamente cuando Docker crea la base de datos por primera vez.
-- Solo necesita correr una vez.

-- Habilita la generación de UUIDs dentro de PostgreSQL
-- gen_random_uuid() que usamos en el schema requiere esto
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Habilita búsqueda de texto completo (útil para buscar receptores por nombre)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
