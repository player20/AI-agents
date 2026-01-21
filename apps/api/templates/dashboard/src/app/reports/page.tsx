import { Sidebar } from '@/components/Sidebar'
import { Header } from '@/components/Header'
import { FileText, Download, Calendar, MoreHorizontal } from 'lucide-react'

const reports = [
  { name: 'Q4 2024 Revenue Report', date: 'Dec 15, 2024', type: 'Financial', size: '2.4 MB' },
  { name: 'User Growth Analysis', date: 'Dec 10, 2024', type: 'Analytics', size: '1.8 MB' },
  { name: 'Marketing Campaign Results', date: 'Dec 5, 2024', type: 'Marketing', size: '3.2 MB' },
  { name: 'Product Usage Metrics', date: 'Nov 30, 2024', type: 'Product', size: '1.5 MB' },
  { name: 'Customer Satisfaction Survey', date: 'Nov 25, 2024', type: 'Customer', size: '892 KB' },
]

export default function ReportsPage() {
  return (
    <div className="min-h-screen" style={{ minHeight: '100vh', background: '#f8fafc', color: '#1e293b' }}>
      <Sidebar />
      <main className="lg:ml-64">
        <Header title="Reports" />

        <div className="p-6">
          {/* Actions */}
          <div className="flex justify-between items-center mb-6">
            <div className="flex gap-3">
              <button className="flex items-center gap-2 px-3 py-2 bg-surface border border-gray-200 rounded-lg text-sm hover:bg-surface-muted">
                <Calendar className="w-4 h-4" />
                Last 30 days
              </button>
            </div>
            <button className="flex items-center gap-2 px-4 py-2 bg-brand-primary text-white rounded-lg text-sm font-medium hover:bg-brand-primary/90">
              <FileText className="w-4 h-4" />
              Generate Report
            </button>
          </div>

          {/* Reports List */}
          <div className="bg-surface rounded-xl border border-gray-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="font-semibold">Recent Reports</h3>
            </div>
            <div className="divide-y divide-gray-200">
              {reports.map((report, i) => (
                <div key={i} className="px-6 py-4 flex items-center justify-between hover:bg-surface-muted">
                  <div className="flex items-center gap-4">
                    <div className="p-2 bg-brand-primary/10 rounded-lg">
                      <FileText className="w-5 h-5 text-brand-primary" />
                    </div>
                    <div>
                      <p className="font-medium">{report.name}</p>
                      <p className="text-sm text-content-muted">{report.date} • {report.type} • {report.size}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button className="p-2 text-content-muted hover:text-brand-primary rounded-lg hover:bg-surface-muted">
                      <Download className="w-4 h-4" />
                    </button>
                    <button className="p-2 text-content-muted hover:text-content rounded-lg hover:bg-surface-muted">
                      <MoreHorizontal className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
