import { Link, NavLink, Outlet } from 'react-router-dom'
import { LayoutDashboard, LogIn, LogOut, RefreshCw, Search, Users } from 'lucide-react'
import { supabase } from '../lib/supabase'
import { useAuth } from '../lib/auth'
import { useData } from '../lib/data'

const NAV = [
  { to: '/', nome: 'Visão geral', icone: LayoutDashboard },
  { to: '/leads', nome: 'Leads', icone: Users },
]

export default function Layout() {
  const { session } = useAuth()
  const { recarregar, carregando } = useData()

  return (
    <div className="bg-grid min-h-screen">
      <header className="sticky top-0 z-30 border-b border-white/10 bg-plane/80 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-7xl items-center gap-6 px-4">
          <div className="flex items-center gap-2 font-semibold">
            <span className="grid h-7 w-7 place-items-center rounded-lg bg-garnet/15 text-garnet"><Search size={15} /></span>
            <span className="hidden sm:inline">Busca Leads</span>
          </div>
          <nav className="flex gap-1">
            {NAV.map(({ to, nome, icone: Icone }) => (
              <NavLink key={to} to={to} end title={nome}
                className={({ isActive }) =>
                  `flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm transition ${
                    isActive ? 'bg-white/10 text-ink' : 'text-ink-muted hover:text-ink'}`}>
                <Icone size={15} /><span className="hidden whitespace-nowrap sm:inline">{nome}</span>
              </NavLink>
            ))}
          </nav>
          <div className="ml-auto flex items-center gap-2">
            <button onClick={recarregar} title="Atualizar dados" className="btn-ghost px-2.5">
              <RefreshCw size={15} className={carregando ? 'animate-spin' : ''} />
            </button>
            {session ? (
              <>
                <span className="hidden text-xs text-ink-muted md:inline">{session.user.email}</span>
                <button onClick={() => supabase.auth.signOut()} title="Sair" className="btn-ghost px-2.5">
                  <LogOut size={15} />
                </button>
              </>
            ) : (
              <Link to="/entrar" title="Entrar para editar" className="btn-ghost gap-1.5 px-2.5 text-xs">
                <LogIn size={15} /><span className="hidden sm:inline">Entrar</span>
              </Link>
            )}
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-8">
        <Outlet />
      </main>
    </div>
  )
}
