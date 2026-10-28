import { useState, type FormEvent } from 'react'
import { motion } from 'framer-motion'
import { Search } from 'lucide-react'
import { supabase } from '../lib/supabase'

export default function Login() {
  const [modo, setModo] = useState<'entrar' | 'criar'>('entrar')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [msg, setMsg] = useState<{ tipo: 'erro' | 'ok'; texto: string } | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function enviar(e: FormEvent) {
    e.preventDefault()
    setEnviando(true)
    setMsg(null)
    if (modo === 'entrar') {
      const { error } = await supabase.auth.signInWithPassword({ email, password: senha })
      if (error) setMsg({ tipo: 'erro', texto: traduzir(error.message) })
    } else {
      const { data, error } = await supabase.auth.signUp({
        email,
        password: senha,
        options: { emailRedirectTo: window.location.href.split('#')[0] },
      })
      if (error) setMsg({ tipo: 'erro', texto: traduzir(error.message) })
      else if (!data.session)
        setMsg({ tipo: 'ok', texto: 'Conta criada. Confirme pelo link enviado ao seu e-mail e depois entre aqui.' })
    }
    setEnviando(false)
  }

  return (
    <div className="bg-grid flex min-h-screen items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: 'easeOut' }}
        className="card w-full max-w-sm p-8"
      >
        <div className="mb-8 flex items-center gap-3">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-garnet/15 text-garnet">
            <Search size={20} />
          </div>
          <div>
            <h1 className="text-lg font-semibold">Busca Leads</h1>
            <p className="text-sm text-ink-muted">Prospecção · Garnet Cosméticos</p>
          </div>
        </div>

        <form onSubmit={enviar} className="space-y-3">
          <input className="input" type="email" placeholder="E-mail" value={email}
            onChange={(e) => setEmail(e.target.value)} required autoComplete="email" />
          <input className="input" type="password" placeholder="Senha (mín. 6 caracteres)" value={senha}
            onChange={(e) => setSenha(e.target.value)} required minLength={6}
            autoComplete={modo === 'entrar' ? 'current-password' : 'new-password'} />
          <button className="btn-primary w-full" disabled={enviando}>
            {enviando ? 'Aguarde…' : modo === 'entrar' ? 'Entrar' : 'Criar conta'}
          </button>
        </form>

        {msg && (
          <p className={`mt-4 text-sm ${msg.tipo === 'erro' ? 'text-red-400' : 'text-emerald-400'}`}>{msg.texto}</p>
        )}

        <button
          onClick={() => { setModo(modo === 'entrar' ? 'criar' : 'entrar'); setMsg(null) }}
          className="mt-6 text-sm text-ink-muted transition hover:text-ink"
        >
          {modo === 'entrar' ? 'Primeiro acesso? Criar conta' : 'Já tenho conta. Entrar'}
        </button>
        <a href="#/" className="mt-2 block text-sm text-ink-muted transition hover:text-ink">Voltar sem entrar</a>
      </motion.div>
    </div>
  )
}

function traduzir(m: string) {
  if (/invalid login/i.test(m)) return 'E-mail ou senha incorretos.'
  if (/not confirmed/i.test(m)) return 'Confirme seu e-mail pelo link que enviamos antes de entrar.'
  if (/already registered/i.test(m)) return 'Este e-mail já tem conta. Use "Entrar".'
  return m
}
