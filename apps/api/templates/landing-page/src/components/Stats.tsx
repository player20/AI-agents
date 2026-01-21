const stats = [
  { value: '10,000+', label: 'Active Companies' },
  { value: '99.99%', label: 'Uptime SLA' },
  { value: '50M+', label: 'API Requests/Day' },
  { value: '24/7', label: 'Support' },
]

export function Stats() {
  return (
    <section className="py-16 bg-brand-primary">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <p className="text-3xl md:text-4xl font-bold text-white mb-2">
                {stat.value}
              </p>
              <p className="text-blue-100">
                {stat.label}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
