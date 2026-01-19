"""
JuiceNet Audit Report Generator
Pre-configured to generate reports in the exact style of JUICENET_COMPREHENSIVE_AUDIT_2026.md

This is a convenience wrapper around comprehensive_audit_report.py with JuiceNet-specific data.
"""

from comprehensive_audit_report import (
    ComprehensiveAuditData,
    ComprehensiveAuditReport,
    FunnelStage,
    RetentionCohort,
    RevenueData,
    FlowAnalysis,
    UXIssue,
    Recommendation,
    RoadmapPhase,
    DataSource,
    TechStackItem,
    CompetitorAnalysis,
    ROICalculator
)
from datetime import datetime
from pathlib import Path


def create_juicenet_audit_data(
    # Core metrics (provide your real data)
    total_guests: int = 2012,
    email_verified: int = 1543,
    profile_complete: int = 1035,
    made_reservation: int = 19,
    total_hosts: int = 330,
    hosts_with_chargers: int = 131,
    # Revenue data
    total_reservations: int = 19,
    avg_booking_value: float = 8.49,
    booking_fee: float = 2.25,
    # Testing info
    testing_date: str = None,
    screenshots_count: int = 117,
    screenshots_dir: str = "JuiceNet code/screenshots-manual/"
) -> ComprehensiveAuditData:
    """
    Create JuiceNet audit data from real metrics

    Args:
        total_guests: Total guest signups
        email_verified: Guests who verified email
        profile_complete: Guests who completed profile
        made_reservation: Guests who made at least one reservation
        total_hosts: Total host accounts
        hosts_with_chargers: Hosts with at least one charger listed
        total_reservations: Total reservations (all time)
        avg_booking_value: Average booking amount
        booking_fee: Platform fee per booking
        testing_date: Date of production testing (defaults to today)
        screenshots_count: Number of screenshots captured
        screenshots_dir: Path to screenshots directory
    """
    if testing_date is None:
        testing_date = datetime.now().strftime("%B %d, %Y")

    # Calculate derived metrics
    email_verified_pct = (email_verified / total_guests * 100) if total_guests > 0 else 0
    profile_complete_pct = (profile_complete / total_guests * 100) if total_guests > 0 else 0
    conversion_rate = (made_reservation / total_guests * 100) if total_guests > 0 else 0
    hosts_with_chargers_pct = (hosts_with_chargers / total_hosts * 100) if total_hosts > 0 else 0

    return ComprehensiveAuditData(
        app_name="JuiceNet",
        company_name="JuiceNet Inc.",
        business_model='EV charging marketplace ("Airbnb for EV chargers") - Connect EV drivers (Guests) with home charger owners (Hosts). Revenue from platform fees on bookings.',
        target_market="Corona, CA and surrounding areas",
        app_url="https://web.juicenet.ai",

        # Funnel
        funnel_stages=[
            FunnelStage(
                name="Total Guest Signups",
                label="SIGNUP",
                count=total_guests,
                description="Guest accounts created",
                route="/auth/signin"
            ),
            FunnelStage(
                name="Email Verified",
                label="EMAIL VERIFIED",
                count=email_verified,
                description=f"{email_verified_pct:.1f}% confirmed email"
            ),
            FunnelStage(
                name="Profile Complete",
                label="PROFILE COMPLETE",
                count=profile_complete,
                description=f"{profile_complete_pct:.1f}% filled in profile"
            ),
            FunnelStage(
                name="Made Reservation",
                label="MADE RESERVATION",
                count=made_reservation,
                description=f"Only {conversion_rate:.1f}% ever booked"
            ),
        ],
        funnel_title="GUEST SIGNUP FUNNEL",

        # Host metrics
        host_metrics={
            'total_hosts': {'name': 'Total Host Accounts', 'count': total_hosts, 'pct': '100%'},
            'address_verified': {'name': 'Address Verified', 'count': int(total_hosts * 0.794), 'pct': '79.4%'},
            'with_chargers': {'name': 'Have Chargers Listed', 'count': hosts_with_chargers, 'pct': f'{hosts_with_chargers_pct:.1f}%'},
            'no_chargers': {'name': 'No Chargers Listed', 'count': total_hosts - hosts_with_chargers, 'pct': f'{100 - hosts_with_chargers_pct:.1f}%'},
        },

        # Revenue
        revenue_data=RevenueData(
            total_transactions=total_reservations,
            avg_transaction_value=avg_booking_value,
            booking_fee=booking_fee,
            monthly_revenue=total_reservations * booking_fee,
            notes="This is critically low for a marketplace - indicates funnel problems"
        ),

        # Retention (example cohorts - replace with real data)
        retention_cohorts=[
            RetentionCohort(week="Recent cohorts", new_users=300, day_1=8, day_7=3, day_30=1),
        ],

        # Testing
        testing_date=testing_date,
        testing_url="https://web.juicenet.ai",
        device_viewport="iPhone 14 Pro (390x844)",
        screenshots_count=screenshots_count,
        screenshots_dir=screenshots_dir,

        # Flow Analysis
        flows_analyzed=[
            FlowAnalysis(
                flow_id="landing",
                flow_name="First Impression (Landing Page)",
                screenshots=["001-splash.png", "002-landing.png"],
                elements_checked={
                    "Brand Logo": {"present": True, "quality": "Clean, professional"},
                    "Tagline": {"present": True, "quality": '"Power sharing, switched on"'},
                    "Value Proposition": {"present": True, "quality": "Clear messaging"},
                    "Sign Up CTA": {"present": True, "quality": "Prominent green button"},
                    "Social Login": {"present": True, "quality": "Apple, Facebook, Google"},
                    "Map Preview": {"present": True, "quality": "Shows charger locations"},
                },
                score=8,
                notes="Strong first impression with clear CTAs."
            ),
            FlowAnalysis(
                flow_id="signup",
                flow_name="Signup Process",
                screenshots=["005-signup.png"],
                elements_checked={
                    "Email field": {"present": True, "quality": "Clear, standard"},
                    "Password field": {"present": True, "quality": "Requirements shown"},
                    "Social Options": {"present": True, "quality": "Reduces friction"},
                },
                score=7,
                notes="Good form with social login options. Password confirmation adds some friction."
            ),
            FlowAnalysis(
                flow_id="post-signup",
                flow_name="Post-Signup Experience",
                screenshots=["015-role-selection.png"],
                score=5,
                notes="Role selection timing is suboptimal + email verification creates massive friction."
            ),
            FlowAnalysis(
                flow_id="booking",
                flow_name="Booking Flow (Guest)",
                screenshots=["100-117"],
                elements_checked={
                    "Charger Details": {"present": True, "quality": "Excellent"},
                    "Time Selection": {"present": True, "quality": "Good"},
                    "Payment": {"present": True, "quality": "Excellent"},
                    "Confirmation": {"present": True, "quality": "Excellent"},
                },
                score=9,
                notes="Booking flow is well-designed once users get there."
            ),
        ],

        # UX Issues
        ux_issues=[
            UXIssue(
                id="1",
                title="Email verification forces app exit",
                description="Users leave app to verify email and never return",
                severity="critical",
                impact="23% drop-off",
                status="confirmed",
                fix_difficulty="medium"
            ),
            UXIssue(
                id="2",
                title="No auto-login after verification",
                description="Users must manually log back in after clicking email link",
                severity="critical",
                impact="33% additional drop-off",
                status="confirmed",
                fix_difficulty="medium"
            ),
            UXIssue(
                id="3",
                title="Verification page has no app redirect",
                description="Azure static page shows 'Account Activated' with no way back to app",
                severity="critical",
                impact="Users lost after verify",
                status="confirmed",
                fix_difficulty="easy"
            ),
            UXIssue(
                id="4",
                title="Role selection after signup",
                description="Users don't know if they're signing up as Host or Guest",
                severity="high",
                impact="Missed personalization opportunity",
                status="observed",
                fix_difficulty="easy"
            ),
            UXIssue(
                id="5",
                title="Too many host onboarding steps",
                description="9+ screens required to complete host setup",
                severity="high",
                impact="60% host drop-off",
                status="observed",
                fix_difficulty="medium"
            ),
        ],

        # Heuristics
        heuristics_scores={
            'visibility': 7,
            'match': 8,
            'control': 5,
            'consistency': 8,
            'prevention': 7,
            'recognition': 7,
            'flexibility': 5,
            'aesthetic': 8,
            'errors': 6,
            'help': 4
        },

        # Tech Stack
        tech_stack=[
            TechStackItem("Mobile App", "Angular 18 + Ionic 8 + Capacitor", "Modern, good choice"),
            TechStackItem("Admin Dashboard", "Angular 18 + PrimeNG", "Adequate"),
            TechStackItem("Backend API", ".NET 8 / ASP.NET Core", "Solid, enterprise-grade"),
            TechStackItem("Database", "Azure SQL Server", "Scalable"),
            TechStackItem("Push Notifications", "OneSignal", "Good integration"),
            TechStackItem("Payments", "Stripe", "Industry standard"),
            TechStackItem("Maps", "Google Maps API", "Good UX"),
            TechStackItem("Email", "SendGrid", "Reliable"),
        ],

        # Code Quality
        code_quality_notes={
            'positive': [
                "Clean separation of concerns",
                "TypeScript throughout frontend",
                "Proper service layer in backend",
                "Good use of dependency injection"
            ],
            'improvements': [
                "Email verification flow is rigid",
                "No unverified user state management",
                "Role selection not captured at signup"
            ]
        },

        # API Issues
        api_issues=[
            {"endpoint": "POST /identity/register", "function": "Create account", "issue": "No role field"},
            {"endpoint": "POST /registration-confirmation", "function": "Confirm email", "issue": "Returns empty, no tokens"},
            {"endpoint": "GET /verification-status", "function": "Check if verified", "issue": "Doesn't exist (needs creation)"},
        ],

        # Competitors
        competitors=[
            CompetitorAnalysis("ChargePoint", "Network size", "Local/personal touch"),
            CompetitorAnalysis("PlugShare", "Database/reviews", "Actual booking capability"),
            CompetitorAnalysis("Airbnb (model)", "Trust system", "Build host ratings"),
            CompetitorAnalysis("Turo (model)", "Insurance/trust", "Add charger insurance"),
        ],

        # Recommendations
        recommendations=[
            Recommendation(
                priority=1,
                title="Fix Email Verification Flow",
                problem="23.3% of users never verify email, 33% who verify still abandon",
                data_support=f"470 + 508 = {total_guests - profile_complete} users lost (48.6% of all signups)",
                confidence=95,
                implementation="""
1. Allow browsing while unverified
2. Add verification status polling in the app
3. Auto-login after email confirmation (return JWT tokens)
4. Redirect confirmation page TO the app with auth tokens
5. Add "Open JuiceNet App" button on confirmation page
""",
                expected_impact="Recover 50-70% of drop-off (+490-685 users completing signup). If 10% book: +49-69 additional reservations",
                files_to_modify=[
                    "API/src/Services/JuiceNet.Services.Identity/Services/IdentityService.cs",
                    "App/src/app/services/auth.service.ts",
                    "App/src/app/shared/components/success/success.component.ts"
                ]
            ),
            Recommendation(
                priority=2,
                title="Add Role Selection Before Signup",
                problem="Users don't know if they're signing up as Host or Guest",
                data_support="59% drop between signup and role selection page",
                confidence=85,
                implementation="""
Move role selection to BEFORE signup:
1. Landing Page shows two cards: "I'M A GUEST" / "I'M A HOST"
2. Store intended role, pass to signup
3. Personalize signup messaging based on role
4. Skip role selection page post-login
""",
                expected_impact="Personalized experience from start, higher completion rates for hosts, better segmentation",
                files_to_modify=[
                    "App/src/app/features/auth/components/landing/landing.component.ts",
                    "App/src/app/features/auth/components/signin/signin.component.ts",
                    "API - Add IntendedRole field to registration"
                ]
            ),
            Recommendation(
                priority=3,
                title="Streamline Host Onboarding",
                problem="60% of hosts never list a charger (9+ steps is too many)",
                data_support=f"{total_hosts - hosts_with_chargers} out of {total_hosts} hosts have no chargers listed",
                confidence=80,
                implementation="""
Reduce from 9 steps to 4:
1. Basic Info (name + address + charger type + one photo)
2. Pricing (smart defaults based on local rates)
3. Availability (preset templates: "Weekday evenings", "Weekends", "24/7")
4. Payment (Stripe Connect)

Move profile picture, amenities, bio to "Optional - Complete Later"
""",
                expected_impact="Increase host completion from 40% to 70%+, add 60-100 more charger listings",
                files_to_modify=[
                    "App/src/app/features/host/components/charger-add/",
                    "App/src/app/features/settings/components/account-host-setup/"
                ]
            ),
        ],

        # Roadmap
        roadmap=[
            RoadmapPhase(
                phase="Week 1-2",
                title="Critical Fixes",
                tasks=[
                    {"task": "Backend: Add IntendedRole to registration", "done": False},
                    {"task": "Backend: Return JWT tokens after email confirmation", "done": False},
                    {"task": "Backend: Add verification status endpoint", "done": False},
                    {"task": "Frontend: Allow browsing while unverified", "done": False},
                    {"task": "Frontend: Add verification polling", "done": False},
                    {"task": 'Frontend: Update success screen to "Explore Chargers"', "done": False},
                ]
            ),
            RoadmapPhase(
                phase="Week 3-4",
                title="UX Improvements",
                tasks=[
                    {"task": "Create role selection landing page", "done": False},
                    {"task": "Personalize signup based on role", "done": False},
                    {"task": "Streamline host onboarding (reduce steps)", "done": False},
                    {"task": "Add progress indicators", "done": False},
                ]
            ),
            RoadmapPhase(
                phase="Month 2",
                title="Growth Features",
                tasks=[
                    {"task": "Implement QR code scanning", "done": False},
                    {"task": "Add host earnings calculator", "done": False},
                    {"task": "Create Corona, CA targeted landing page", "done": False},
                    {"task": "Build referral program", "done": False},
                ]
            ),
        ],

        # KPIs
        kpis=[
            {"metric": "Signup -> Verified", "current": f"{email_verified_pct:.1f}%", "target_30": "85%", "target_90": "90%"},
            {"metric": "Verified -> Profile Complete", "current": f"{(profile_complete/email_verified*100) if email_verified > 0 else 0:.1f}%", "target_30": "80%", "target_90": "85%"},
            {"metric": "Profile -> First Booking", "current": f"{(made_reservation/profile_complete*100) if profile_complete > 0 else 0:.1f}%", "target_30": "5%", "target_90": "10%"},
            {"metric": "Overall Conversion", "current": f"{conversion_rate:.1f}%", "target_30": "3.4%", "target_90": "7.5%"},
            {"metric": "Day 30 Retention", "current": "~0%", "target_30": "10%", "target_90": "20%"},
            {"metric": "Monthly Reservations", "current": f"{total_reservations} (all time)", "target_30": "50", "target_90": "150"},
        ],

        # ROI
        roi_projection=ROICalculator.calculate(
            current_signups=total_guests,
            current_conversion_pct=conversion_rate,
            dropoff_recoverable_pct=50,  # 50% of lost users are recoverable
            avg_transaction_value=avg_booking_value,
            booking_fee=booking_fee
        ),

        # Data Sources
        data_sources=[
            DataSource("Guest Data", "guestsDocument-200.csv", total_guests),
            DataSource("Host Data", "hostsDocument-170.csv", total_hosts),
            DataSource("Page Views", "Pages and screens.csv", 0, "All routes"),
            DataSource("Retention", "Retention overview.csv", 0, "13 week cohorts"),
            DataSource("Push Users", "OneSignal export.csv", 9874),
        ],

        # Appendix
        appendix_content={
            "Email Verification Flow (Production Capture)": """
**Current Email Content**:
```
Subject: [JuiceNet Email Verification]

Hi,
To complete your JuiceNet registration, please confirm your email address.

[Confirm your email] <- Button

Didn't sign up for JuiceNet? Let us know
```

**Current Flow Issues**:
1. Email link goes to Azure Static Web App (wrong domain)
2. After clicking, shows static "Account Activated" page with NO app link
3. User must manually navigate back to app
4. User must manually log in again (no auto-login)
5. No deep link or app redirect

**Recommended Email Changes**:
```
Hi,
To complete your JuiceNet registration, please confirm your email address.

[Confirm your email]

After confirming, you'll be automatically logged in and ready to find chargers near you!
```
"""
        }
    )


def generate_juicenet_report(
    output_path: str = None,
    output_format: str = 'markdown',
    **kwargs
) -> str:
    """
    Generate a JuiceNet audit report

    Args:
        output_path: Path to save the report (optional)
        output_format: 'markdown', 'html', or 'json'
        **kwargs: Override default metrics (see create_juicenet_audit_data)

    Returns:
        Report content as string
    """
    data = create_juicenet_audit_data(**kwargs)

    report = ComprehensiveAuditReport(config={
        'company_name': 'Weaver Pro',
        'company_tagline': 'AI-Powered UX Analysis',
        'contact_email': 'audit@weaverpro.ai',
        'contact_phone': ''
    })

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d")
        ext = 'md' if output_format == 'markdown' else output_format
        output_path = f"JUICENET_AUDIT_{timestamp}.{ext}"

    return report.generate(data, output_format=output_format, output_path=output_path)


def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Generate JuiceNet comprehensive audit report'
    )
    parser.add_argument('--output', type=str, help='Output file path')
    parser.add_argument('--format', type=str, default='markdown',
                        choices=['markdown', 'html', 'json'])

    # Metric overrides
    parser.add_argument('--guests', type=int, default=2012, help='Total guest signups')
    parser.add_argument('--verified', type=int, default=1543, help='Email verified count')
    parser.add_argument('--profiles', type=int, default=1035, help='Profile complete count')
    parser.add_argument('--reservations', type=int, default=19, help='Reservations made')
    parser.add_argument('--hosts', type=int, default=330, help='Total hosts')
    parser.add_argument('--chargers', type=int, default=131, help='Hosts with chargers')

    args = parser.parse_args()

    output = generate_juicenet_report(
        output_path=args.output,
        output_format=args.format,
        total_guests=args.guests,
        email_verified=args.verified,
        profile_complete=args.profiles,
        made_reservation=args.reservations,
        total_hosts=args.hosts,
        hosts_with_chargers=args.chargers
    )

    print(f"JuiceNet audit report generated!")
    if args.output:
        print(f"Saved to: {args.output}")


if __name__ == "__main__":
    main()
