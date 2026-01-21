import { Sidebar } from '@/components/Sidebar'
import { Header } from '@/components/Header'
import { Bell, Check, Trash2, MessageSquare, UserPlus, AlertTriangle, CheckCircle } from 'lucide-react'

const notifications = [
  {
    id: 1,
    type: 'message',
    icon: MessageSquare,
    title: 'New comment on your post',
    description: 'Sarah Chen commented on "Q4 Marketing Strategy"',
    time: '5 minutes ago',
    read: false,
  },
  {
    id: 2,
    type: 'user',
    icon: UserPlus,
    title: 'New team member',
    description: 'Marcus Johnson joined the Engineering team',
    time: '1 hour ago',
    read: false,
  },
  {
    id: 3,
    type: 'alert',
    icon: AlertTriangle,
    title: 'Server usage high',
    description: 'Production server CPU usage exceeded 85%',
    time: '2 hours ago',
    read: true,
  },
  {
    id: 4,
    type: 'success',
    icon: CheckCircle,
    title: 'Deployment successful',
    description: 'v2.4.0 was deployed to production',
    time: '3 hours ago',
    read: true,
  },
]

const iconColors = {
  message: 'bg-blue-100 text-blue-600',
  user: 'bg-green-100 text-green-600',
  alert: 'bg-yellow-100 text-yellow-600',
  success: 'bg-emerald-100 text-emerald-600',
}

export default function NotificationsPage() {
  return (
    <div className="min-h-screen" style={{ minHeight: '100vh', background: '#f8fafc', color: '#1e293b' }}>
      <Sidebar />
      <main className="lg:ml-64">
        <Header title="Notifications" />

        <div className="p-6 max-w-3xl">
          {/* Actions */}
          <div className="flex justify-between items-center mb-6">
            <p className="text-sm text-content-muted">
              You have <span className="font-medium text-content">2 unread</span> notifications
            </p>
            <button className="text-sm text-brand-primary font-medium hover:underline">
              Mark all as read
            </button>
          </div>

          {/* Notifications List */}
          <div className="bg-surface rounded-xl border border-gray-200 overflow-hidden">
            <div className="divide-y divide-gray-200">
              {notifications.map((notification) => (
                <div
                  key={notification.id}
                  className={`px-6 py-4 flex items-start gap-4 ${!notification.read ? 'bg-brand-primary/5' : 'hover:bg-surface-muted'}`}
                >
                  <div className={`p-2 rounded-lg ${iconColors[notification.type as keyof typeof iconColors]}`}>
                    <notification.icon className="w-5 h-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between">
                      <div>
                        <p className="font-medium">{notification.title}</p>
                        <p className="text-sm text-content-muted mt-0.5">{notification.description}</p>
                        <p className="text-xs text-content-muted mt-2">{notification.time}</p>
                      </div>
                      {!notification.read && (
                        <div className="w-2 h-2 bg-brand-primary rounded-full flex-shrink-0 mt-2" />
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    <button className="p-1.5 text-content-muted hover:text-brand-primary rounded-lg hover:bg-surface-muted">
                      <Check className="w-4 h-4" />
                    </button>
                    <button className="p-1.5 text-content-muted hover:text-red-500 rounded-lg hover:bg-surface-muted">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Load More */}
          <div className="mt-4 text-center">
            <button className="text-sm text-brand-primary font-medium hover:underline">
              Load older notifications
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}
