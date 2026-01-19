"""
Rich Screen Templates for Business Digitizer
Creates realistic, industry-specific app screens with real content.
"""

from typing import Dict, List
import random


class ScreenTemplates:
    """Generate rich, industry-specific screen content"""

    # Industry-specific content
    INDUSTRY_CONTENT = {
        'restaurant': {
            'menu_items': [
                {'name': 'Avocado Toast', 'desc': 'Sourdough, poached eggs, microgreens', 'price': 14.95, 'time': '10 min', 'rating': 4.8, 'orders': '2.3k'},
                {'name': 'Acai Bowl', 'desc': 'Organic acai, granola, fresh berries', 'price': 12.95, 'time': '5 min', 'rating': 4.9, 'orders': '1.8k'},
                {'name': 'Oat Milk Latte', 'desc': 'Double shot espresso, oat milk', 'price': 5.95, 'time': '3 min', 'rating': 4.7, 'orders': '5.2k'},
                {'name': 'Breakfast Burrito', 'desc': 'Scrambled eggs, bacon, cheese, salsa', 'price': 11.95, 'time': '12 min', 'rating': 4.6, 'orders': '980'},
            ],
            'categories': ['Popular', 'Breakfast', 'Lunch', 'Drinks', 'Desserts'],
            'rewards': {'points': 450, 'next_reward': 'Free Coffee', 'progress': 75},
            'promo': '20% OFF your first order!',
            'hero_text': 'Start your day\nthe right way',
        },
        'fitness': {
            'classes': [
                {'name': 'Power Yoga', 'instructor': 'Sarah M.', 'time': '7:00 AM', 'duration': '60 min', 'spots': 8, 'level': 'All Levels'},
                {'name': 'HIIT Burn', 'instructor': 'Mike T.', 'time': '8:30 AM', 'duration': '45 min', 'spots': 3, 'level': 'Advanced'},
                {'name': 'Spin Class', 'instructor': 'Jessica L.', 'time': '12:00 PM', 'duration': '45 min', 'spots': 12, 'level': 'Intermediate'},
                {'name': 'Evening Flow', 'instructor': 'David K.', 'time': '6:00 PM', 'duration': '75 min', 'spots': 15, 'level': 'Beginner'},
            ],
            'stats': {'workouts': 24, 'streak': 7, 'calories': '12.4k', 'hours': 18},
            'promo': 'First class FREE for new members!',
            'hero_text': 'Find your\ninner strength',
        },
        'retail': {
            'products': [
                {'name': 'Classic White Tee', 'brand': 'Essential', 'price': 34.99, 'original': 49.99, 'rating': 4.8, 'reviews': 234},
                {'name': 'Slim Fit Jeans', 'brand': 'Denim Co', 'price': 79.99, 'original': None, 'rating': 4.6, 'reviews': 156},
                {'name': 'Canvas Sneakers', 'brand': 'StreetWear', 'price': 64.99, 'original': 89.99, 'rating': 4.9, 'reviews': 412},
                {'name': 'Leather Belt', 'brand': 'Heritage', 'price': 44.99, 'original': None, 'rating': 4.7, 'reviews': 89},
            ],
            'categories': ['New Arrivals', 'Sale', 'Men', 'Women', 'Accessories'],
            'promo': 'Free shipping on orders $50+',
            'hero_text': 'New Season\nNew Style',
        },
        'service': {
            'services': [
                {'name': 'Emergency Repair', 'desc': '24/7 emergency service', 'price': 'From $99', 'time': '1-2 hrs', 'rating': 4.9},
                {'name': 'Routine Maintenance', 'desc': 'Preventive checkup', 'price': 'From $79', 'time': 'Same day', 'rating': 4.8},
                {'name': 'Installation', 'desc': 'Professional installation', 'price': 'Free quote', 'time': 'Scheduled', 'rating': 4.7},
                {'name': 'Inspection', 'desc': 'Full system inspection', 'price': '$49', 'time': '30-45 min', 'rating': 4.8},
            ],
            'stats': {'jobs_completed': '2,450+', 'avg_rating': 4.9, 'response_time': '< 1 hour'},
            'promo': '$25 off your first service!',
            'hero_text': 'Expert help\nwhen you need it',
        },
        'beauty': {
            'services': [
                {'name': 'Haircut & Style', 'stylist': 'Emma', 'price': 65, 'duration': '45 min', 'rating': 4.9},
                {'name': 'Balayage Color', 'stylist': 'Sophia', 'price': 185, 'duration': '2.5 hrs', 'rating': 4.8},
                {'name': 'Manicure', 'stylist': 'Lily', 'price': 35, 'duration': '30 min', 'rating': 4.7},
                {'name': 'Facial Treatment', 'stylist': 'Ava', 'price': 95, 'duration': '60 min', 'rating': 4.9},
            ],
            'stylists': ['Emma', 'Sophia', 'Lily', 'Ava', 'Mia'],
            'promo': 'Refer a friend, get 20% off!',
            'hero_text': 'Treat yourself\nto beautiful',
        },
        'healthcare': {
            'services': [
                {'name': 'General Checkup', 'type': 'In-Person', 'duration': '30 min', 'price': '$75'},
                {'name': 'Video Consultation', 'type': 'Telehealth', 'duration': '15 min', 'price': '$45'},
                {'name': 'Lab Work', 'type': 'In-Person', 'duration': '15 min', 'price': 'Varies'},
                {'name': 'Follow-up Visit', 'type': 'Either', 'duration': '15 min', 'price': '$50'},
            ],
            'stats': {'next_appt': 'Mar 15, 2:30 PM', 'prescriptions': 2, 'messages': 1},
            'promo': 'Same-day appointments available',
            'hero_text': 'Your health,\nyour way',
        },
        'education': {
            'courses': [
                {'name': 'Piano Basics', 'instructor': 'Prof. Chen', 'level': 'Beginner', 'sessions': 12, 'price': 299},
                {'name': 'Advanced Guitar', 'instructor': 'James M.', 'level': 'Advanced', 'sessions': 8, 'price': 249},
                {'name': 'Music Theory', 'instructor': 'Dr. Smith', 'level': 'All Levels', 'sessions': 10, 'price': 199},
                {'name': 'Voice Training', 'instructor': 'Maria L.', 'level': 'Intermediate', 'sessions': 6, 'price': 179},
            ],
            'progress': {'completed': 8, 'in_progress': 2, 'certificates': 3},
            'promo': 'First lesson FREE!',
            'hero_text': 'Learn something\nnew today',
        },
        'realestate': {
            'listings': [
                {'name': '3BR Modern Home', 'location': 'Brooklyn Heights', 'price': 1250000, 'beds': 3, 'baths': 2, 'sqft': 1850},
                {'name': 'Luxury Condo', 'location': 'Manhattan', 'price': 2100000, 'beds': 2, 'baths': 2, 'sqft': 1200},
                {'name': 'Family House', 'location': 'Park Slope', 'price': 1850000, 'beds': 4, 'baths': 3, 'sqft': 2400},
                {'name': 'Studio Apartment', 'location': 'Williamsburg', 'price': 450000, 'beds': 0, 'baths': 1, 'sqft': 550},
            ],
            'saved': 5,
            'promo': 'Virtual tours available 24/7',
            'hero_text': 'Find your\ndream home',
        },
    }

    # SVG Icons (inline, no external dependencies)
    ICONS = {
        'home': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z"/></svg>',
        'search': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>',
        'cart': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 18c-1.1 0-1.99.9-1.99 2S5.9 22 7 22s2-.9 2-2-.9-2-2-2zM1 2v2h2l3.6 7.59-1.35 2.45c-.16.28-.25.61-.25.96 0 1.1.9 2 2 2h12v-2H7.42c-.14 0-.25-.11-.25-.25l.03-.12.9-1.63h7.45c.75 0 1.41-.41 1.75-1.03l3.58-6.49c.08-.14.12-.31.12-.48 0-.55-.45-1-1-1H5.21l-.94-2H1zm16 16c-1.1 0-1.99.9-1.99 2s.89 2 1.99 2 2-.9 2-2-.9-2-2-2z"/></svg>',
        'user': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>',
        'calendar': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.11 0-1.99.9-1.99 2L3 19c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11zM9 10H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2z"/></svg>',
        'star': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>',
        'clock': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/></svg>',
        'location': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/></svg>',
        'heart': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>',
        'check': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>',
        'arrow_right': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M10 6L8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z"/></svg>',
        'fire': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M13.5.67s.74 2.65.74 4.8c0 2.06-1.35 3.73-3.41 3.73-2.07 0-3.63-1.67-3.63-3.73l.03-.36C5.21 7.51 4 10.62 4 14c0 4.42 3.58 8 8 8s8-3.58 8-8C20 8.61 17.41 3.8 13.5.67zM11.71 19c-1.78 0-3.22-1.4-3.22-3.14 0-1.62 1.05-2.76 2.81-3.12 1.77-.36 3.6-1.21 4.62-2.58.39 1.29.59 2.65.59 4.04 0 2.65-2.15 4.8-4.8 4.8z"/></svg>',
        'gift': '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 6h-2.18c.11-.31.18-.65.18-1 0-1.66-1.34-3-3-3-1.05 0-1.96.54-2.5 1.35l-.5.67-.5-.68C10.96 2.54 10.05 2 9 2 7.34 2 6 3.34 6 5c0 .35.07.69.18 1H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-5-2c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zM9 4c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm11 15H4v-2h16v2zm0-5H4V8h5.08L7 10.83 8.62 12 11 8.76l1-1.36 1 1.36L15.38 12 17 10.83 14.92 8H20v6z"/></svg>',
    }

    @classmethod
    def get_icon(cls, name: str, size: int = 24, color: str = 'currentColor') -> str:
        """Get an SVG icon"""
        icon = cls.ICONS.get(name, cls.ICONS['home'])
        return f'<span style="display:inline-flex;width:{size}px;height:{size}px;color:{color}">{icon}</span>'

    @classmethod
    def generate_home_screen(cls, plan, content: Dict) -> str:
        """Generate a rich home screen"""
        promo = content.get('promo', 'Special offer today!')
        hero = content.get('hero_text', 'Welcome').replace('\n', '<br>')

        return f"""
        <div style="background: linear-gradient(180deg, {plan.primary_color} 0%, {plan.secondary_color} 100%); padding: 50px 20px 30px; color: white;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <div style="font-size: 13px; opacity: 0.9;">Good morning</div>
                <div style="width: 36px; height: 36px; background: rgba(255,255,255,0.2); border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                    {cls.get_icon('user', 20, 'white')}
                </div>
            </div>
            <h1 style="font-size: 32px; font-weight: 700; line-height: 1.2; margin-bottom: 20px;">{hero}</h1>
            <div style="background: rgba(255,255,255,0.15); backdrop-filter: blur(10px); border-radius: 12px; padding: 12px 16px; display: flex; align-items: center; gap: 10px;">
                {cls.get_icon('gift', 20, 'white')}
                <span style="font-size: 14px;">{promo}</span>
            </div>
        </div>
        <div style="padding: 20px; margin-top: -20px;">
            <div style="background: white; border-radius: 16px; padding: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); margin-bottom: 20px;">
                <div style="display: flex; align-items: center; gap: 12px; background: #F8FAFC; border-radius: 12px; padding: 14px;">
                    {cls.get_icon('search', 20, '#94A3B8')}
                    <span style="color: #94A3B8; font-size: 15px;">What are you looking for?</span>
                </div>
            </div>
            <div style="display: flex; gap: 12px; overflow-x: auto; padding-bottom: 10px; margin-bottom: 20px;">
                <div style="background: {plan.primary_color}; color: white; padding: 10px 20px; border-radius: 20px; font-size: 14px; font-weight: 500; white-space: nowrap;">All</div>
                <div style="background: #F1F5F9; color: #64748B; padding: 10px 20px; border-radius: 20px; font-size: 14px; white-space: nowrap;">Popular</div>
                <div style="background: #F1F5F9; color: #64748B; padding: 10px 20px; border-radius: 20px; font-size: 14px; white-space: nowrap;">New</div>
                <div style="background: #F1F5F9; color: #64748B; padding: 10px 20px; border-radius: 20px; font-size: 14px; white-space: nowrap;">Nearby</div>
            </div>
            <h3 style="font-size: 18px; font-weight: 600; color: #1E293B; margin-bottom: 16px;">Featured</h3>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                <div style="background: linear-gradient(135deg, #667EEA, #764BA2); border-radius: 16px; padding: 20px; color: white; aspect-ratio: 1;">
                    <div style="font-size: 12px; opacity: 0.8; margin-bottom: 8px;">TRENDING</div>
                    <div style="font-size: 16px; font-weight: 600;">Most Popular</div>
                </div>
                <div style="background: linear-gradient(135deg, #F093FB, #F5576C); border-radius: 16px; padding: 20px; color: white; aspect-ratio: 1;">
                    <div style="font-size: 12px; opacity: 0.8; margin-bottom: 8px;">NEW</div>
                    <div style="font-size: 16px; font-weight: 600;">Just Added</div>
                </div>
            </div>
        </div>
        {cls._generate_nav(plan, 'home')}
        """

    @classmethod
    def generate_menu_screen(cls, plan, content: Dict) -> str:
        """Generate a rich menu/browse screen"""
        items = content.get('menu_items', content.get('products', content.get('services', content.get('classes', []))))

        items_html = ""
        for item in items[:4]:
            name = item.get('name', 'Item')
            desc = item.get('desc', item.get('description', ''))
            price = item.get('price', '')
            rating = item.get('rating', 4.5)

            if isinstance(price, (int, float)):
                price_str = f"${price:.2f}"
            else:
                price_str = str(price)

            items_html += f"""
            <div style="display: flex; gap: 14px; padding: 16px 0; border-bottom: 1px solid #F1F5F9;">
                <div style="width: 80px; height: 80px; background: linear-gradient(135deg, #E2E8F0, #CBD5E1); border-radius: 12px; flex-shrink: 0;"></div>
                <div style="flex: 1; min-width: 0;">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 4px;">
                        <h4 style="font-size: 15px; font-weight: 600; color: #1E293B; margin: 0;">{name}</h4>
                        <span style="font-weight: 600; color: {plan.primary_color}; font-size: 15px;">{price_str}</span>
                    </div>
                    <p style="font-size: 13px; color: #64748B; margin: 0 0 8px 0; line-height: 1.4;">{desc}</p>
                    <div style="display: flex; align-items: center; gap: 4px;">
                        {cls.get_icon('star', 14, '#FBBF24')}
                        <span style="font-size: 13px; color: #1E293B; font-weight: 500;">{rating}</span>
                    </div>
                </div>
            </div>
            """

        return f"""
        <div style="padding: 50px 20px 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h1 style="font-size: 28px; font-weight: 700; color: #1E293B; margin: 0;">Browse</h1>
                <div style="width: 40px; height: 40px; background: #F1F5F9; border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                    {cls.get_icon('search', 20, '#64748B')}
                </div>
            </div>
            <div style="display: flex; gap: 8px; overflow-x: auto; padding-bottom: 16px;">
                <div style="background: {plan.primary_color}; color: white; padding: 10px 18px; border-radius: 20px; font-size: 13px; font-weight: 500; white-space: nowrap;">All</div>
                <div style="background: #F1F5F9; color: #64748B; padding: 10px 18px; border-radius: 20px; font-size: 13px; white-space: nowrap;">Popular</div>
                <div style="background: #F1F5F9; color: #64748B; padding: 10px 18px; border-radius: 20px; font-size: 13px; white-space: nowrap;">New</div>
                <div style="background: #F1F5F9; color: #64748B; padding: 10px 18px; border-radius: 20px; font-size: 13px; white-space: nowrap;">Deals</div>
            </div>
        </div>
        <div style="padding: 0 20px 100px;">
            {items_html}
        </div>
        {cls._generate_nav(plan, 'browse')}
        """

    @classmethod
    def generate_booking_screen(cls, plan, content: Dict) -> str:
        """Generate a booking/cart screen"""
        return f"""
        <div style="padding: 50px 20px 20px;">
            <h1 style="font-size: 24px; font-weight: 700; color: #1E293B; margin-bottom: 24px;">Confirm Booking</h1>

            <div style="background: #F8FAFC; border-radius: 16px; padding: 20px; margin-bottom: 20px;">
                <div style="display: flex; gap: 16px; margin-bottom: 16px;">
                    <div style="width: 60px; height: 60px; background: linear-gradient(135deg, {plan.primary_color}, {plan.secondary_color}); border-radius: 12px;"></div>
                    <div>
                        <h3 style="font-size: 16px; font-weight: 600; color: #1E293B; margin: 0 0 4px 0;">Selected Service</h3>
                        <p style="font-size: 14px; color: #64748B; margin: 0;">Premium Package</p>
                    </div>
                </div>
                <div style="display: flex; gap: 12px;">
                    <div style="flex: 1; background: white; border-radius: 10px; padding: 12px; text-align: center;">
                        <div style="font-size: 12px; color: #64748B; margin-bottom: 4px;">Date</div>
                        <div style="font-size: 14px; font-weight: 600; color: #1E293B;">Mar 15</div>
                    </div>
                    <div style="flex: 1; background: white; border-radius: 10px; padding: 12px; text-align: center;">
                        <div style="font-size: 12px; color: #64748B; margin-bottom: 4px;">Time</div>
                        <div style="font-size: 14px; font-weight: 600; color: #1E293B;">2:30 PM</div>
                    </div>
                    <div style="flex: 1; background: white; border-radius: 10px; padding: 12px; text-align: center;">
                        <div style="font-size: 12px; color: #64748B; margin-bottom: 4px;">Duration</div>
                        <div style="font-size: 14px; font-weight: 600; color: #1E293B;">60 min</div>
                    </div>
                </div>
            </div>

            <div style="background: white; border: 1px solid #E2E8F0; border-radius: 16px; padding: 20px; margin-bottom: 20px;">
                <h3 style="font-size: 15px; font-weight: 600; color: #1E293B; margin: 0 0 16px 0;">Price Details</h3>
                <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                    <span style="color: #64748B;">Service</span>
                    <span style="color: #1E293B;">$85.00</span>
                </div>
                <div style="display: flex; justify-content: space-between; margin-bottom: 12px;">
                    <span style="color: #64748B;">Booking fee</span>
                    <span style="color: #1E293B;">$5.00</span>
                </div>
                <div style="display: flex; justify-content: space-between; padding-top: 12px; border-top: 1px solid #E2E8F0;">
                    <span style="font-weight: 600; color: #1E293B;">Total</span>
                    <span style="font-weight: 700; color: {plan.primary_color}; font-size: 18px;">$90.00</span>
                </div>
            </div>

            <button style="width: 100%; background: {plan.primary_color}; color: white; border: none; padding: 18px; border-radius: 14px; font-size: 16px; font-weight: 600; cursor: pointer; box-shadow: 0 4px 14px {plan.primary_color}40;">
                Confirm & Pay
            </button>
            <p style="text-align: center; font-size: 13px; color: #94A3B8; margin-top: 12px;">Free cancellation up to 24 hours before</p>
        </div>
        {cls._generate_nav(plan, 'activity')}
        """

    @classmethod
    def generate_profile_screen(cls, plan, content: Dict) -> str:
        """Generate a rich profile screen"""
        stats = content.get('stats', {})
        rewards = content.get('rewards', {'points': 450, 'next_reward': 'Free Item', 'progress': 75})

        return f"""
        <div style="padding: 50px 20px 20px;">
            <div style="text-align: center; margin-bottom: 24px;">
                <div style="width: 90px; height: 90px; background: linear-gradient(135deg, {plan.primary_color}, {plan.secondary_color}); border-radius: 50%; margin: 0 auto 16px; display: flex; align-items: center; justify-content: center; color: white; font-size: 32px; font-weight: 600;">JD</div>
                <h2 style="font-size: 22px; font-weight: 700; color: #1E293B; margin: 0 0 4px 0;">John Doe</h2>
                <p style="font-size: 14px; color: #64748B; margin: 0;">Member since Jan 2024</p>
            </div>

            <div style="background: linear-gradient(135deg, {plan.primary_color}, {plan.secondary_color}); border-radius: 20px; padding: 24px; color: white; margin-bottom: 24px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                    <div>
                        <div style="font-size: 13px; opacity: 0.9;">Reward Points</div>
                        <div style="font-size: 32px; font-weight: 700;">{rewards['points']}</div>
                    </div>
                    {cls.get_icon('gift', 40, 'rgba(255,255,255,0.3)')}
                </div>
                <div style="background: rgba(255,255,255,0.2); border-radius: 8px; height: 8px; margin-bottom: 8px;">
                    <div style="background: white; border-radius: 8px; height: 100%; width: {rewards['progress']}%;"></div>
                </div>
                <div style="font-size: 13px; opacity: 0.9;">{100 - rewards['progress']} points to {rewards['next_reward']}</div>
            </div>

            <div style="background: #F8FAFC; border-radius: 16px; overflow: hidden;">
                <div style="display: flex; align-items: center; gap: 14px; padding: 16px 20px; border-bottom: 1px solid #E2E8F0; cursor: pointer;">
                    <div style="width: 40px; height: 40px; background: {plan.primary_color}15; border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                        {cls.get_icon('calendar', 20, plan.primary_color)}
                    </div>
                    <div style="flex: 1;">
                        <div style="font-size: 15px; font-weight: 500; color: #1E293B;">My Bookings</div>
                        <div style="font-size: 13px; color: #64748B;">View history</div>
                    </div>
                    {cls.get_icon('arrow_right', 20, '#94A3B8')}
                </div>
                <div style="display: flex; align-items: center; gap: 14px; padding: 16px 20px; border-bottom: 1px solid #E2E8F0; cursor: pointer;">
                    <div style="width: 40px; height: 40px; background: {plan.primary_color}15; border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                        {cls.get_icon('heart', 20, plan.primary_color)}
                    </div>
                    <div style="flex: 1;">
                        <div style="font-size: 15px; font-weight: 500; color: #1E293B;">Favorites</div>
                        <div style="font-size: 13px; color: #64748B;">Saved items</div>
                    </div>
                    {cls.get_icon('arrow_right', 20, '#94A3B8')}
                </div>
                <div style="display: flex; align-items: center; gap: 14px; padding: 16px 20px; cursor: pointer;">
                    <div style="width: 40px; height: 40px; background: {plan.primary_color}15; border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                        {cls.get_icon('user', 20, plan.primary_color)}
                    </div>
                    <div style="flex: 1;">
                        <div style="font-size: 15px; font-weight: 500; color: #1E293B;">Account Settings</div>
                        <div style="font-size: 13px; color: #64748B;">Edit profile</div>
                    </div>
                    {cls.get_icon('arrow_right', 20, '#94A3B8')}
                </div>
            </div>
        </div>
        {cls._generate_nav(plan, 'profile')}
        """

    @classmethod
    def generate_activity_screen(cls, plan, content: Dict) -> str:
        """Generate an activity/tracking screen"""
        return f"""
        <div style="padding: 50px 20px 20px;">
            <h1 style="font-size: 24px; font-weight: 700; color: #1E293B; margin-bottom: 24px;">Activity</h1>

            <div style="background: linear-gradient(135deg, {plan.primary_color}, {plan.secondary_color}); border-radius: 20px; padding: 24px; color: white; margin-bottom: 24px;">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
                    <div style="width: 50px; height: 50px; background: rgba(255,255,255,0.2); border-radius: 12px;"></div>
                    <div>
                        <div style="font-size: 14px; opacity: 0.9;">Current Order</div>
                        <div style="font-size: 18px; font-weight: 600;">#ORD-2847</div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
                    <div style="width: 10px; height: 10px; background: #4ADE80; border-radius: 50%;"></div>
                    <span style="font-size: 14px;">In Progress</span>
                </div>
                <div style="background: rgba(255,255,255,0.2); border-radius: 8px; height: 6px;">
                    <div style="background: white; border-radius: 8px; height: 100%; width: 65%;"></div>
                </div>
                <div style="font-size: 13px; opacity: 0.9; margin-top: 8px;">Estimated: 15 min remaining</div>
            </div>

            <h3 style="font-size: 16px; font-weight: 600; color: #1E293B; margin-bottom: 16px;">Recent Activity</h3>

            <div style="space-y: 12px;">
                <div style="display: flex; gap: 14px; padding: 16px; background: #F8FAFC; border-radius: 14px; margin-bottom: 12px;">
                    <div style="width: 44px; height: 44px; background: #D1FAE5; border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                        {cls.get_icon('check', 22, '#10B981')}
                    </div>
                    <div style="flex: 1;">
                        <div style="font-size: 15px; font-weight: 500; color: #1E293B;">Order Completed</div>
                        <div style="font-size: 13px; color: #64748B;">Mar 12 at 2:30 PM</div>
                    </div>
                    <div style="font-size: 15px; font-weight: 600; color: #1E293B;">$42.50</div>
                </div>
                <div style="display: flex; gap: 14px; padding: 16px; background: #F8FAFC; border-radius: 14px; margin-bottom: 12px;">
                    <div style="width: 44px; height: 44px; background: #D1FAE5; border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                        {cls.get_icon('check', 22, '#10B981')}
                    </div>
                    <div style="flex: 1;">
                        <div style="font-size: 15px; font-weight: 500; color: #1E293B;">Points Earned</div>
                        <div style="font-size: 13px; color: #64748B;">Mar 12 at 2:30 PM</div>
                    </div>
                    <div style="font-size: 15px; font-weight: 600; color: {plan.primary_color};">+42 pts</div>
                </div>
            </div>
        </div>
        {cls._generate_nav(plan, 'activity')}
        """

    @classmethod
    def _generate_nav(cls, plan, active: str = 'home') -> str:
        """Generate bottom navigation"""
        items = [
            ('home', 'Home'),
            ('browse', 'Browse'),
            ('activity', 'Activity'),
            ('profile', 'Profile'),
        ]

        nav_items = ""
        for item_id, label in items:
            is_active = item_id == active
            color = plan.primary_color if is_active else '#94A3B8'
            weight = '600' if is_active else '400'

            nav_items += f"""
            <div style="flex: 1; text-align: center; padding: 8px 0; cursor: pointer;">
                <div style="margin-bottom: 4px;">{cls.get_icon(item_id if item_id != 'browse' else 'search', 24, color)}</div>
                <div style="font-size: 11px; font-weight: {weight}; color: {color};">{label}</div>
            </div>
            """

        return f"""
        <nav style="position: absolute; bottom: 0; left: 0; right: 0; background: white; border-top: 1px solid #E2E8F0; display: flex; padding: 8px 0 20px 0; z-index: 100;">
            {nav_items}
        </nav>
        """

    @classmethod
    def get_screen_content(cls, screen: Dict, plan) -> str:
        """Get appropriate screen content based on screen type and industry"""
        screen_id = screen.get('id', '').lower()
        industry = plan.industry

        # Get industry-specific content
        content = cls.INDUSTRY_CONTENT.get(industry, cls.INDUSTRY_CONTENT['service'])

        # Match screen type to template
        if 'home' in screen_id:
            return cls.generate_home_screen(plan, content)
        elif any(x in screen_id for x in ['menu', 'shop', 'browse', 'service', 'class', 'course', 'search', 'listing']):
            return cls.generate_menu_screen(plan, content)
        elif any(x in screen_id for x in ['cart', 'book', 'checkout', 'order', 'confirm']):
            return cls.generate_booking_screen(plan, content)
        elif any(x in screen_id for x in ['profile', 'account', 'settings', 'me']):
            return cls.generate_profile_screen(plan, content)
        elif any(x in screen_id for x in ['activity', 'history', 'track', 'schedule', 'progress']):
            return cls.generate_activity_screen(plan, content)
        else:
            # Fallback to home-style screen
            return cls.generate_home_screen(plan, content)
