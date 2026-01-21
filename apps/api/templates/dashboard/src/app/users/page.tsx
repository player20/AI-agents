import { Sidebar } from '@/components/Sidebar'
import { Header } from '@/components/Header'
import { DataTable } from '@/components/DataTable'
import { Plus, Search, Filter } from 'lucide-react'
import mockData from '@/data/mock.json'

// Extended user list for the users page
const allUsers = [
  ...mockData.users,
  {
    id: '6',
    name: 'Alex Thompson',
    email: 'alex.t@company.com',
    role: 'Backend Developer',
    status: 'Active' as const,
    lastActive: '1 hour ago',
    avatar: 'AT'
  },
  {
    id: '7',
    name: 'Sophia Martinez',
    email: 'sophia.m@company.com',
    role: 'Data Analyst',
    status: 'Active' as const,
    lastActive: '30 minutes ago',
    avatar: 'SM'
  },
  {
    id: '8',
    name: 'Ryan Lee',
    email: 'ryan.lee@company.com',
    role: 'DevOps Engineer',
    status: 'Pending' as const,
    lastActive: '5 hours ago',
    avatar: 'RL'
  },
]

export default function UsersPage() {
  return (
    <div className="min-h-screen" style={{ minHeight: '100vh', background: '#f8fafc', color: '#1e293b' }}>
      <Sidebar />
      <main className="lg:ml-64">
        <Header title="Users" />

        <div className="p-6">
          {/* Actions bar */}
          <div className="flex flex-col sm:flex-row gap-4 justify-between mb-6">
            <div className="flex gap-3">
              <div className="flex items-center gap-2 px-3 py-2 bg-surface border border-gray-200 rounded-lg">
                <Search className="w-4 h-4 text-content-muted" />
                <input
                  type="text"
                  placeholder="Search users..."
                  className="bg-transparent border-none outline-none text-sm w-48"
                />
              </div>
              <button className="flex items-center gap-2 px-3 py-2 bg-surface border border-gray-200 rounded-lg text-sm hover:bg-surface-muted">
                <Filter className="w-4 h-4" />
                Filters
              </button>
            </div>
            <button className="flex items-center gap-2 px-4 py-2 bg-brand-primary text-white rounded-lg text-sm font-medium hover:bg-brand-primary/90">
              <Plus className="w-4 h-4" />
              Add User
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            <div className="bg-surface rounded-xl border border-gray-200 p-4">
              <p className="text-sm text-content-muted">Total Users</p>
              <p className="text-2xl font-bold mt-1">2,420</p>
            </div>
            <div className="bg-surface rounded-xl border border-gray-200 p-4">
              <p className="text-sm text-content-muted">Active Now</p>
              <p className="text-2xl font-bold mt-1 text-brand-secondary">184</p>
            </div>
            <div className="bg-surface rounded-xl border border-gray-200 p-4">
              <p className="text-sm text-content-muted">Pending Invites</p>
              <p className="text-2xl font-bold mt-1 text-brand-accent">23</p>
            </div>
          </div>

          {/* Users table */}
          <DataTable users={allUsers} />
        </div>
      </main>
    </div>
  )
}
