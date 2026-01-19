export function Features() {
  return (
    <section className="py-16 px-4 md:py-24 md:px-8 bg-secondary/30 w-full flex flex-col items-center">
      <h3 className="text-2xl md:text-3xl font-bold text-center mb-12 bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary-foreground">Key Features</h3>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl">
        <div className="p-6 rounded-xl bg-card shadow-lg hover:shadow-xl transition-shadow duration-300" role="article">
          <h4 className="text-xl font-semibold mb-3 text-primary">Responsive Design</h4>
          <p className="text-muted-foreground">Works seamlessly on any device, from mobile to desktop.</p>
        </div>
        <div className="p-6 rounded-xl bg-card shadow-lg hover:shadow-xl transition-shadow duration-300" role="article">
          <h4 className="text-xl font-semibold mb-3 text-primary">Dark Mode</h4>
          <p className="text-muted-foreground">Switch between light and dark themes effortlessly.</p>
        </div>
        <div className="p-6 rounded-xl bg-card shadow-lg hover:shadow-xl transition-shadow duration-300" role="article">
          <h4 className="text-xl font-semibold mb-3 text-primary">Accessibility</h4>
          <p className="text-muted-foreground">Built with ARIA standards for inclusive user experience.</p>
        </div>
      </div>
    </section>
  );
}