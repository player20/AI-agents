import { Zap, Shield, BarChart, Users, Globe, Layers } from 'lucide-react'

const features = [
  {
    name: 'Lightning Fast',
    description: 'Optimized for speed with sub-100ms response times. Your users will love the instant experience.',
    icon: Zap,
  },
  {
    name: 'Enterprise Security',
    description: 'SOC2 compliant with end-to-end encryption. Your data is safe with us.',
    icon: Shield,
  },
  {
    name: 'Advanced Analytics',
    description: 'Get deep insights into user behavior with our real-time analytics dashboard.',
    icon: BarChart,
  },
  {
    name: 'Team Collaboration',
    description: 'Work together seamlessly with real-time collaboration and commenting.',
    icon: Users,
  },
  {
    name: 'Global CDN',
    description: 'Content delivered from 200+ edge locations worldwide for optimal performance.',
    icon: Globe,
  },
  {
    name: 'Integrations',
    description: 'Connect with 100+ tools you already use. Slack, GitHub, Jira, and more.',
    icon: Layers,
  },
]

export function Features() {
  return (
    <section id="features" className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-sm font-semibold text-brand-primary uppercase tracking-wide mb-3">
            Features
          </h2>
          <p className="text-3xl md:text-4xl font-bold text-content mb-4">
            Everything you need to scale
          </p>
          <p className="text-xl text-content-muted">
            Powerful features to help you manage, analyze, and grow your business.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature) => (
            <div
              key={feature.name}
              className="p-6 rounded-xl border border-gray-200 hover:border-brand-primary hover:shadow-lg transition-all group"
            >
              <div className="w-12 h-12 bg-brand-primary/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-brand-primary/20 transition-colors">
                <feature.icon className="w-6 h-6 text-brand-primary" />
              </div>
              <h3 className="text-lg font-semibold text-content mb-2">
                {feature.name}
              </h3>
              <p className="text-content-muted">
                {feature.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
