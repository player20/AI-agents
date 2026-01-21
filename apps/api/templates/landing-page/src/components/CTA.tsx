import { ArrowRight } from 'lucide-react'

export function CTA() {
  return (
    <section id="contact" className="py-20 bg-gradient-to-br from-brand-primary to-blue-700">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
          Ready to get started?
        </h2>
        <p className="text-xl text-blue-100 mb-8 max-w-2xl mx-auto">
          Join thousands of companies already using Acme to build better products.
          Start your free 14-day trial today.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <a
            href="#"
            className="flex items-center gap-2 px-8 py-4 bg-white text-brand-primary rounded-lg font-semibold hover:bg-blue-50 transition-colors"
          >
            Start Free Trial
            <ArrowRight className="w-5 h-5" />
          </a>
          <a
            href="#"
            className="flex items-center gap-2 px-8 py-4 bg-transparent border-2 border-white text-white rounded-lg font-semibold hover:bg-white/10 transition-colors"
          >
            Contact Sales
          </a>
        </div>

        <p className="mt-6 text-blue-200 text-sm">
          No credit card required. Cancel anytime.
        </p>
      </div>
    </section>
  )
}
