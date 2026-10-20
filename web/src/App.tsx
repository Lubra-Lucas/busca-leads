import { useEffect, useState } from 'react'
import { HashRouter, Navigate, Route, Routes } from 'react-router-dom'
import { ShieldAlert } from 'lucide-react'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Leads from './pages/Leads'
import Login from './pages/Login'
import { AuthProvider, useAuth } from './lib/auth'
import { DataProvider } from './lib/data'
import { supabase } from './lib/supabase'

function Portao() {
  const { session, carregando } = useAuth()
  const [permitido, setPermitido] = useState<boolean | null>(null)

  useEffect(() => {
    if (!session) return setPermitido(null)
    // a regra de quem tem acesso fica no banco (função usuario_permitido)
    supabase.rpc('usuario_permitido').then(({ data }) => setPermitido(data === true))
  }, [session])

  if (carregando || (session && permitido === null)) return <div className="min-h-screen bg-plane" />
  if (!session) return <Login />
  if (!permitido) return <SemAcesso email={session.user.email ?? ''} />

  return (
    <DataProvider>
      <HashRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="leads" element={<Leads />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </HashRouter>
    </DataProvider>
  )
}

function SemAcesso({ email }: { email: string }) {
  return (
    <div className="bg-grid flex min-h-screen items-center justify-center px-4">
      <div className="card max-w-sm p-8 text-center">
        <ShieldAlert className="mx-auto text-garnet" />
        <h1 className="mt-3 font-semibold">Acesso não liberado</h1>
        <p className="mt-2 text-sm text-ink-muted">{email} ainda não tem acesso liberado.</p>
        <button onClick={() => supabase.auth.signOut()} className="btn-ghost mt-6">Sair</button>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <Portao />
    </AuthProvider>
  )
}
