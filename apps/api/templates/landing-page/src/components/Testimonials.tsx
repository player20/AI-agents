import { Star } from 'lucide-react'

const testimonials = [
  {
    quote: "Acme has transformed how our team works. We've cut our development time in half and our customers are happier than ever.",
    author: 'Sarah Chen',
    title: 'CTO at TechStart',
    avatar: 'SC',
  },
  {
    quote: "The analytics alone are worth the price. We finally understand what our users want and can act on it immediately.",
    author: 'Michael Rodriguez',
    title: 'Product Lead at ScaleUp',
    avatar: 'MR',
  },
  {
    quote: "Best investment we made this year. The team collaboration features have made remote work actually enjoyable.",
    author: 'Emily Johnson',
    title: 'CEO at RemoteFirst',
    avatar: 'EJ',
  },
]

export function Testimonials() {
  return (
    <section id="testimonials" className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-sm font-semibold text-brand-primary uppercase tracking-wide mb-3">
            Testimonials
          </h2>
          <p className="text-3xl md:text-4xl font-bold text-content mb-4">
            Loved by teams worldwide
          </p>
          <p className="text-xl text-content-muted">
            See what our customers have to say about their experience with Acme.
          </p>
        </div>

        {/* Testimonials Grid */}
        <div className="grid md:grid-cols-3 gap-8">
          {testimonials.map((testimonial) => (
            <div
              key={testimonial.author}
              className="bg-surface-muted rounded-2xl p-8"
            >
              {/* Stars */}
              <div className="flex gap-1 mb-4">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-5 h-5 fill-brand-accent text-brand-accent" />
                ))}
              </div>

              {/* Quote */}
              <p className="text-content mb-6">
                "{testimonial.quote}"
              </p>

              {/* Author */}
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-brand-primary flex items-center justify-center">
                  <span className="text-white font-medium">{testimonial.avatar}</span>
                </div>
                <div>
                  <p className="font-semibold text-content">{testimonial.author}</p>
                  <p className="text-sm text-content-muted">{testimonial.title}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
