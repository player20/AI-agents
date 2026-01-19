export function Hero() {
  return (
    <section className="flex flex-col items-center justify-center py-20 px-4 md:py-32 text-center animate-fadeIn max-w-4xl">
      <h2 className="text-4xl md:text-6xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary-foreground mb-6">Hello, World!</h2>
      <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mb-8">Welcome to our simple yet elegant web application. Start exploring the possibilities with us.</p>
      <button className="px-6 py-3 rounded-lg bg-primary text-primary-foreground font-medium hover:bg-primary/90 focus:ring-2 focus:ring-primary/50 focus:outline-none transition-all duration-200" aria-label="Get started with the app">Get Started</button>
    </section>
  );
}