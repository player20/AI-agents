'use client'

import { Check } from 'lucide-react'
import { useState } from 'react'

const plans = [
  {
    name: 'Starter',
    price: { monthly: 29, annual: 24 },
    description: 'Perfect for small teams getting started',
    features: [
      'Up to 5 team members',
      '10GB storage',
      'Basic analytics',
      'Email support',
      'API access',
    ],
    popular: false,
  },
  {
    name: 'Pro',
    price: { monthly: 79, annual: 66 },
    description: 'For growing teams that need more power',
    features: [
      'Up to 25 team members',
      '100GB storage',
      'Advanced analytics',
      'Priority support',
      'API access',
      'Custom integrations',
      'SSO authentication',
    ],
    popular: true,
  },
  {
    name: 'Enterprise',
    price: { monthly: 199, annual: 166 },
    description: 'For large organizations with custom needs',
    features: [
      'Unlimited team members',
      'Unlimited storage',
      'Enterprise analytics',
      '24/7 dedicated support',
      'API access',
      'Custom integrations',
      'SSO & SAML',
      'Custom contracts',
      'SLA guarantee',
    ],
    popular: false,
  },
]

export function Pricing() {
  const [annual, setAnnual] = useState(true)

  return (
    <section id="pricing" className="py-20 bg-surface-muted">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-12">
          <h2 className="text-sm font-semibold text-brand-primary uppercase tracking-wide mb-3">
            Pricing
          </h2>
          <p className="text-3xl md:text-4xl font-bold text-content mb-4">
            Simple, transparent pricing
          </p>
          <p className="text-xl text-content-muted mb-8">
            Choose the plan that works best for your team. All plans include a 14-day free trial.
          </p>

          {/* Billing Toggle */}
          <div className="flex items-center justify-center gap-3">
            <span className={`text-sm ${!annual ? 'text-content font-medium' : 'text-content-muted'}`}>
              Monthly
            </span>
            <button
              onClick={() => setAnnual(!annual)}
              className={`relative w-14 h-7 rounded-full transition-colors ${
                annual ? 'bg-brand-primary' : 'bg-gray-300'
              }`}
            >
              <div
                className={`absolute w-5 h-5 bg-white rounded-full top-1 transition-transform ${
                  annual ? 'translate-x-8' : 'translate-x-1'
                }`}
              />
            </button>
            <span className={`text-sm ${annual ? 'text-content font-medium' : 'text-content-muted'}`}>
              Annual <span className="text-brand-secondary">(Save 20%)</span>
            </span>
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-8">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`relative bg-white rounded-2xl p-8 ${
                plan.popular
                  ? 'border-2 border-brand-primary shadow-xl scale-105'
                  : 'border border-gray-200'
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-brand-primary text-white text-sm font-medium rounded-full">
                  Most Popular
                </div>
              )}

              <h3 className="text-xl font-semibold text-content mb-2">{plan.name}</h3>
              <p className="text-content-muted mb-6">{plan.description}</p>

              <div className="mb-6">
                <span className="text-4xl font-bold text-content">
                  ${annual ? plan.price.annual : plan.price.monthly}
                </span>
                <span className="text-content-muted">/month</span>
              </div>

              <button
                className={`w-full py-3 rounded-lg font-medium transition-colors mb-8 ${
                  plan.popular
                    ? 'bg-brand-primary text-white hover:bg-brand-primary/90'
                    : 'bg-surface-muted text-content hover:bg-gray-200'
                }`}
              >
                Get Started
              </button>

              <ul className="space-y-3">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex items-center gap-3 text-content-muted">
                    <Check className="w-5 h-5 text-brand-secondary flex-shrink-0" />
                    {feature}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
