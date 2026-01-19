import Header from '@/components/layout/header';
import Footer from '@/components/layout/footer';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Rocket, Globe, Zap } from 'lucide-react';

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen bg-background text-foreground">
      <Header />
      <main className="flex-1">
        {/* Hero Section */}
        <section className="py-20 px-4 bg-gradient-to-r from-primary to-secondary text-white text-center">
          <div className="container mx-auto max-w-5xl">
            <h1 className="text-4xl md:text-6xl font-bold mb-6">Unbiased News, Powered by AI</h1>
            <p className="text-xl md:text-2xl mb-8 max-w-3xl mx-auto">
              Mira News delivers clear, fact-first summaries of current events without political spin.
            </p>
            <Button
              variant="outline"
              className="bg-transparent border-white text-white hover:bg-white hover:text-primary rounded-full px-8 py-2 text-lg transition-all duration-300 hover:scale-105"
            >
              Explore Now
            </Button>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-16 px-4">
          <div className="container mx-auto max-w-5xl">
            <h2 className="text-3xl md:text-4xl font-bold text-center mb-12 text-primary dark:text-primary-dark">
              Why Choose Mira News?
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card className="shadow-xl dark:bg-card-dark rounded-2xl transition-all duration-300 hover:scale-105 border-0">
                <CardHeader>
                  <Rocket className="h-12 w-12 text-primary mb-2" />
                  <CardTitle className="text-xl">Fact-First Reporting</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>
                    AI-driven summaries that prioritize facts over opinions or emotional framing.
                  </CardDescription>
                </CardContent>
              </Card>
              <Card className="shadow-xl dark:bg-card-dark rounded-2xl transition-all duration-300 hover:scale-105 border-0">
                <CardHeader>
                  <Globe className="h-12 w-12 text-primary mb-2" />
                  <CardTitle className="text-xl">Global & Local Editions</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>
                    Stay informed with news tailored to your region alongside global perspectives.
                  </CardDescription>
                </CardContent>
              </Card>
              <Card className="shadow-xl dark:bg-card-dark rounded-2xl transition-all duration-300 hover:scale-105 border-0">
                <CardHeader>
                  <Zap className="h-12 w-12 text-primary mb-2" />
                  <CardTitle className="text-xl">Concise & Clear</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription>
                    Get the essence of every story in minutes with our streamlined summaries.
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