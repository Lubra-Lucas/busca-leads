import { createClient } from '@supabase/supabase-js'

// Chave publicável (pode ficar no navegador). O acesso aos dados é controlado
// pelas regras RLS do banco: só e-mails em public.usuarios_permitidos leem/escrevem.
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL ?? 'https://papaicnydbcajkfghwem.supabase.co'
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_KEY ?? 'sb_publishable_RPFXNIMe-jQeGUVpCi4UYQ_J0lDgfcA'

export const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)
