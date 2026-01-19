import { Header } from '@/components/Header';
import { HeroSection } from '@/components/HeroSection';
import { FeatureHighlights } from '@/components/FeatureHighlights';
import { Footer } from '@/components/Footer';

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main className="flex-1">
        <HeroSection
          title="Welcome to Test App"
          subtitle="A modern web application built with Next.js and Tailwind CSS"
          primaryCTA="Get Started"
          secondaryCTA="Learn More"
        />
        <FeatureHighlights />
      </main>
      <Footer />
    </div>
  );
}