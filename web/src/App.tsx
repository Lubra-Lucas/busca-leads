import { HashRouter, Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Leads from './pages/Leads'
import Login from './pages/Login'
import { AuthProvider, useAuth } from './lib/auth'
import { DataProvider } from './lib/data'

// sem tela de login na entrada: o site abre direto em modo leitura; "Entrar" fica no topo para quem edita
function Portao() {
  const { session, carregando } = useAuth()

  if (carregando) return <div className="min-h-screen bg-plane" />

  return (
    <DataProvider>
      <HashRouter>
        <Routes>
          <Route path="entrar" element={session ? <Navigate to="/" replace /> : <Login />} />
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

export default function App() {
  return (
    <AuthProvider>
      <Portao />
    </AuthProvider>
  )
}
