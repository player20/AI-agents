'use client'

import { MoreHorizontal, ChevronLeft, ChevronRight } from 'lucide-react'

interface User {
  id: string
  name: string
  email: string
  role: string
  status: 'Active' | 'Inactive' | 'Pending'
  lastActive: string
  avatar: string
}

interface DataTableProps {
  users: User[]
}

const statusStyles = {
  Active: 'bg-green-100 text-green-700',
  Inactive: 'bg-gray-100 text-gray-700',
  Pending: 'bg-yellow-100 text-yellow-700',
}

export function DataTable({ users }: DataTableProps) {
  return (
    <div className="bg-surface rounded-xl border border-gray-200 overflow-hidden">
      {/* Table header */}
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <h3 className="font-heading font-semibold">Recent Users</h3>
        <button className="text-sm text-brand-primary font-medium hover:underline">
          View all
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200 bg-surface-muted">
              <th className="text-left text-xs font-medium text-content-muted uppercase tracking-wider px-6 py-3">
                User
              </th>
              <th className="text-left text-xs font-medium text-content-muted uppercase tracking-wider px-6 py-3">
                Role
              </th>
              <th className="text-left text-xs font-medium text-content-muted uppercase tracking-wider px-6 py-3">
                Status
              </th>
              <th className="text-left text-xs font-medium text-content-muted uppercase tracking-wider px-6 py-3">
                Last Active
              </th>
              <th className="text-right text-xs font-medium text-content-muted uppercase tracking-wider px-6 py-3">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {users.map((user) => (
              <tr key={user.id} className="hover:bg-surface-muted transition-colors">
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-brand-primary flex items-center justify-center">
                      <span className="text-white text-sm font-medium">{user.avatar}</span>
                    </div>
                    <div>
                      <p className="font-medium">{user.name}</p>
                      <p className="text-sm text-content-muted">{user.email}</p>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 text-sm">{user.role}</td>
                <td className="px-6 py-4">
                  <span className={`inline-flex px-2.5 py-1 rounded-full text-xs font-medium ${statusStyles[user.status]}`}>
                    {user.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-content-muted">{user.lastActive}</td>
                <td className="px-6 py-4 text-right">
                  <button className="p-1.5 text-content-muted hover:text-content rounded-lg hover:bg-surface-muted">
                    <MoreHorizontal className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
        <p className="text-sm text-content-muted">
          Showing <span className="font-medium">1-10</span> of <span className="font-medium">48</span> users
        </p>
        <div className="flex items-center gap-2">
          <button className="p-2 text-content-muted hover:text-content rounded-lg hover:bg-surface-muted disabled:opacity-50" disabled>
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button className="px-3 py-1.5 bg-brand-primary text-white rounded-lg text-sm font-medium">1</button>
          <button className="px-3 py-1.5 text-content-muted hover:bg-surface-muted rounded-lg text-sm">2</button>
          <button className="px-3 py-1.5 text-content-muted hover:bg-surface-muted rounded-lg text-sm">3</button>
          <button className="p-2 text-content-muted hover:text-content rounded-lg hover:bg-surface-muted">
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
