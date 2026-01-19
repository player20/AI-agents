import Header from '@/components/layout/header';
import Footer from '@/components/layout/footer';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Rocket, Globe, Zap } from 'lucide-react';

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main className="flex-1 overflow-hidden">
        {/* Hero Section */}
        <section className="relative py-20 overflow-hidden bg-gradient-to-r from-primary via-secondary to-primary/50 dark:from-primary/70 dark:via-secondary/70 dark:to-primary/40">
          <div className="absolute inset-0 opacity-10">
            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmZmZmYiIGZpbGwtb3BhY2l0eT0iMC40Ij48cGF0aCBkPSJNMzYgMzRjMCAxIDEgMiAyIDJoMnYtNGgtMmMtMSAwLTIgMS0yIDJ6TTMwIDRDMTMuNDMxIDQgMCAxNy40MzEgMCAzNHMxMy40MzEgMzAgMzAgMzAgMzAtMTMuNDMxIDMwLTMwUzQ2LjU2OSA0IDMwIDR6TTEwLjIyNSA0Mi42OGMtNS41NTYtOS45NDItMi4zLTIyLjUyNyA3LjY0MS0yOC4wODJDMjcuODA5IDkuMDQyIDQwLjM5NSAxMi4yOTcgNDUuOTUgMjIuMjM5YzUuNTU2IDkuOTQzIDIuMyAyMi41MjgtNy42NDEgMjguMDgyLTkuOTQyIDUuNTU1LTIyLjUyNyAyLjMtMjguMDg0LTcuNjQxeiIvPjwvZz48L2c+PC9zdmc+')] bg-repeat" />
          </div>
          <div className="container relative z-10 px-4 mx-auto text-center">
            <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl md:text-6xl lg:text-7xl">
              Mira News
            </h1>
            <p className="mt-6 text-xl leading-8 text-white/90 max-w-3xl mx-auto">
              AI-powered, unbiased news summaries from multiple sources. Fact-first reporting without political spin or emotional framing.
            </p>
            <div className="mt-10 flex justify-center gap-4">
              <Button size="lg" className="bg-white text-primary hover:bg-white/90 text-lg px-8 py-6 rounded-xl shadow-xl transition-all duration-300 hover:scale-105">
                Get Started
              </Button>
              <Button variant="outline" size="lg" className="border-white text-white hover:bg-white/10 text-lg px-8 py-6 rounded-xl shadow-xl transition-all duration-300 hover:scale-105">
                Learn More
              </Button>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-20 bg-background dark:bg-background/90">
          <div className="container px-4 mx-auto">
            <div className="text-center mb-16">
              <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                Why Choose Mira News?
              </h2>
              <p className="mt-4 text-lg leading-6 text-muted-foreground max-w-2xl mx-auto">
                We deliver news as it should be—clear, concise, and without agenda.
              </p>
            </div>
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
              <Card className="shadow-xl rounded-2xl overflow-hidden transition-all duration-300 hover:scale-105 dark:bg-background/50 border-0">
                <CardHeader className="pb-2">
                  <div className="w-12 h-12 rounded-full bg-primary/20 dark:bg-primary/10 flex items-center justify-center mb-4">
                    <Rocket className="w-6 h-6 text-primary" />
                  </div>
                  <CardTitle className="text-xl">Fact-First Summaries</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-muted-foreground">
                    Our AI aggregates multiple sources to provide concise, neutral summaries of current events.
                  </CardDescription>
                </CardContent>
              </Card>
              <Card className="shadow-xl rounded-2xl overflow-hidden transition-all duration-300 hover:scale-105 dark:bg-background/50 border-0">
                <CardHeader className="pb-2">
                  <div className="w-12 h-12 rounded-full bg-primary/20 dark:bg-primary/10 flex items-center justify-center mb-4">
                    <Globe className="w-6 h-6 text-primary" />
                  </div>
                  <CardTitle className="text-xl">Regional Editions</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-muted-foreground">
                    Personalized news based on your location, covering global and local stories that matter to you.
                  </CardDescription>
                </CardContent>
              </Card>
              <Card className="shadow-xl rounded-2xl overflow-hidden transition-all duration-300 hover:scale-105 dark:bg-background/50 border-0">
                <CardHeader className="pb-2">
                  <div className="w-12 h-12 rounded-full bg-primary/20 dark:bg-primary/10 flex items-center justify-center mb-4">
                    <Zap className="w-6 h-6 text-primary" />
                  </div>
                  <CardTitle className="text-xl">Instant Updates</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-muted-foreground">
                    Real-time news delivery so you’re always informed about what’s happening right now.
                  </CardDescription>
                </CardContent>
              </Card>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  );
}