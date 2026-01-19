interface HeroSectionProps {
  title: string;
  subtitle: string;
  primaryCTA: string;
  secondaryCTA: string;
}

export function HeroSection({ title, subtitle, primaryCTA, secondaryCTA }: HeroSectionProps) {
  return (
    <section className="relative py-20 overflow-hidden bg-gradient-to-r from-primary/20 to-secondary/20 dark:from-primary/10 dark:to-secondary/10">
      <div className="absolute inset-0 opacity-30">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmZmZmYiIGZpbGwtb3BhY2l0eT0iMC40Ij48cGF0aCBkPSJNMzYgMzRjMCAxIDEgMiAyIDJoMnYtNGgtMmMtMSAwLTIgMS0yIDJ6TTMwIDRDMTMuNDMxIDQgMCAxNy40MzEgMCAzNHMxMy40MzEgMzAgMzAgMzAgMzAtMTMuNDMxIDMwLTMwUzQ2LjU2OSA0IDMwIDR6TTEwLjIyNSA0Mi42OGMtNS41NTYtOS45NDItMi4zLTIyLjUyNyA3LjY0MS0yOC4wODJDMjcuODA5IDkuMDQyIDQwLjM5NSAxMi4yOTcgNDUuOTUgMjIuMjM5YzUuNTU2IDkuOTQzIDIuMyAyMi41MjgtNy42NDEgMjguMDgyLTkuOTQyIDUuNTU1LTIyLjUyNyAyLjMtMjguMDg0LTcuNjQxeiIvPjwvZz48L2c+PC9zdmc+')] bg-repeat" />
      </div>
      <div className="container relative z-10 mx-auto px-4 text-center">
        <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight text-foreground animate-fadeIn">
          {title}
        </h1>
        <p className="mt-6 text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto animate-slideIn">
          {subtitle}
        </p>
        <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
          <button className="px-8 py-3 rounded-lg bg-primary text-primary-foreground font-medium hover:bg-primary/90 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background shadow-lg shadow-primary/20 hover:shadow-primary/30">
            {primaryCTA}
          </button>
          <button className="px-8 py-3 rounded-lg bg-transparent border border-foreground/20 text-foreground font-medium hover:bg-foreground/5 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background">
            {secondaryCTA}
          </button>
        </div>
      </div>
    </section>
  );
}