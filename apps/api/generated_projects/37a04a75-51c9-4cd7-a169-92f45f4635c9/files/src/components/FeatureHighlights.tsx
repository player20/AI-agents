import { CheckCircle } from 'lucide-react';

const features = [
  {
    title: 'Responsive Design',
    description: 'Looks great on any device, from mobile to desktop.',
  },
  {
    title: 'Dark Mode',
    description: 'Switch between light and dark themes effortlessly.',
  },
  {
    title: 'Accessible',
    description: 'Built with accessibility in mind for all users.',
  },
  {
    title: 'Fast Performance',
    description: 'Optimized for speed with Next.js and modern techniques.',
  },
];

export function FeatureHighlights() {
  return (
    <section className="py-16 md:py-24 bg-background">
      <div className="container mx-auto px-4">
        <h2 className="text-3xl md:text-4xl font-bold text-center mb-12 text-foreground animate-fadeIn">Key Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-7xl mx-auto">
          {features.map((feature, index) => (
            <div
              key={index}
              className="p-6 rounded-lg border bg-card shadow-md hover:shadow-lg transition-shadow duration-300 animate-slideIn"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className="flex items-center gap-3 mb-3">
                <CheckCircle className="h-6 w-6 text-primary" aria-hidden="true" />
                <h3 className="text-xl font-semibold text-card-foreground">{feature.title}</h3>
              </div>
              <p className="text-muted-foreground">{feature.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}