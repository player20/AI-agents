import { Header } from '@/components/Header'
import { Hero } from '@/components/Hero'
import { Features } from '@/components/Features'
import { Stats } from '@/components/Stats'
import { Pricing } from '@/components/Pricing'
import { Testimonials } from '@/components/Testimonials'
import { CTA } from '@/components/CTA'
import { Footer } from '@/components/Footer'

export default function Home() {
  return (
    <div className="min-h-screen" style={{ minHeight: '100vh', background: '#ffffff', color: '#1e293b' }}>
      <Header />
      <main>
        <Hero />
        <Features />
        <Stats />
        <Pricing />
        <Testimonials />
        <CTA />
      </main>
      <Footer />
    </div>
  )
}
