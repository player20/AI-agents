"""
Current App Prototype Generator
===============================

Generates an interactive HTML prototype showing the CURRENT state of an app's UX flows.
This is used alongside the proposed improvements prototype to show before/after comparisons.
"""


def generate_juicenet_current_prototype() -> str:
    """
    Generate an interactive prototype of the CURRENT JuiceNet app flows.

    This shows:
    - Current signup flow (no role selection, generic welcome)
    - Current guest onboarding (email verification blocker)
    - Current host onboarding (4 steps without privacy explanations)
    - Current pain points highlighted

    Returns complete HTML/CSS/JS for the interactive prototype.
    """
    return '''
    <!-- Current JuiceNet App Prototype -->
    <style>
        /* Current App Prototype Styles - JuiceNet Exact Colors */
        .current-prototype-container {
            background: #e8e8e8;
            padding: 30px 20px;
            border-radius: 16px;
            margin: 20px 0 40px;
        }

        .current-prototype-header {
            text-align: center;
            margin-bottom: 20px;
        }

        .current-prototype-header h3 {
            font-size: 1.4rem;
            font-weight: 600;
            color: #102441;
            margin-bottom: 8px;
        }

        .current-prototype-header p {
            color: #5c6c82;
            font-size: 13px;
        }

        .current-tabs {
            display: flex;
            justify-content: center;
            gap: 8px;
            margin-bottom: 25px;
            flex-wrap: wrap;
        }

        .current-tab {
            padding: 10px 16px;
            background: #fff;
            border: 1px solid #d8e8ff;
            border-radius: 0px 12px;
            color: #102441;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.2s;
            font-family: 'Poppins', sans-serif;
        }

        .current-tab:hover {
            background: #f3f8ff;
        }

        .current-tab.active {
            background: #5c6c82;
            color: #fff;
            border-color: #5c6c82;
        }

        /* Phone Frame - Current App */
        .current-phone {
            width: 320px;
            height: 680px;
            background: #000;
            border-radius: 42px;
            padding: 10px;
            position: relative;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
            margin: 0 auto;
        }

        .current-phone-screen {
            width: 100%;
            height: 100%;
            background: #fff;
            border-radius: 34px;
            overflow: hidden;
            position: relative;
        }

        .current-notch {
            position: absolute;
            top: 0;
            left: 50%;
            transform: translateX(-50%);
            width: 120px;
            height: 28px;
            background: #000;
            border-radius: 0 0 16px 16px;
            z-index: 10;
        }

        .current-app-content {
            height: 100%;
            display: flex;
            flex-direction: column;
            background: #fff;
            color: #102441;
            padding-top: 40px;
            font-family: 'Poppins', sans-serif;
        }

        .current-app-header {
            padding: 10px 14px;
            display: flex;
            align-items: center;
            position: relative;
            border-bottom: 1px solid #f3f8ff;
        }

        .current-back-btn {
            width: 20px;
            height: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            color: #102441;
            position: absolute;
            left: 14px;
            font-size: 18px;
        }

        .current-header-title {
            flex: 1;
            text-align: center;
            font-size: 15px;
            font-weight: 500;
            color: #102441;
        }

        .current-app-body {
            flex: 1;
            padding: 14px;
            overflow-y: auto;
        }

        .current-h3 {
            font-weight: 600;
            font-size: 20px;
            line-height: 26px;
            color: #102441;
            margin-bottom: 6px;
        }

        .current-subtitle {
            font-size: 12px;
            color: #5c6c82;
            margin-bottom: 16px;
            line-height: 16px;
        }

        .current-input-container {
            margin-bottom: 12px;
        }

        .current-input-container label {
            color: #102441;
            font-size: 12px;
            display: block;
            margin-bottom: 6px;
        }

        .current-input {
            width: 100%;
            padding: 13px 16px;
            background: #f3f8ff;
            border: 1px solid #f3f8ff;
            border-radius: 8px;
            color: #102441;
            font-size: 14px;
        }

        .current-input-message {
            color: #5c6c82;
            font-size: 12px;
            margin-top: 4px;
        }

        .current-btn-primary {
            width: 100%;
            padding: 16px;
            background: #26a45a;
            border: 1px solid #26a45a;
            border-radius: 0px 12px;
            color: #fff;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 12px;
        }

        .current-btn-secondary {
            width: 100%;
            padding: 12px 16px;
            background: #fff;
            border: 1px solid #26a45a;
            border-radius: 0px 12px;
            color: #26a45a;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            margin-top: 8px;
        }

        .current-checkbox-container {
            color: #5c6c82;
            display: flex;
            gap: 10px;
            align-items: flex-start;
            margin-bottom: 10px;
            font-size: 12px;
        }

        .current-checkbox {
            width: 16px;
            height: 16px;
            min-width: 16px;
            background: #102441;
            border-radius: 3px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 10px;
            margin-top: 2px;
        }

        .current-checkbox.unchecked {
            background: #f3f8ff;
            border: 1px solid #d8e8ff;
        }

        .current-link {
            color: #26a45a;
            font-weight: 500;
            cursor: pointer;
        }

        .current-reddot {
            color: #c30000;
        }

        /* Pain point highlight */
        .current-pain-point {
            background: #FEE2E2;
            border: 1px solid #FCA5A5;
            border-radius: 6px;
            padding: 10px;
            margin: 12px 0;
            position: relative;
        }

        .current-pain-point::before {
            content: '⚠️';
            position: absolute;
            top: -10px;
            left: 10px;
            background: #FEE2E2;
            padding: 0 4px;
            font-size: 14px;
        }

        .current-pain-point p {
            font-size: 11px;
            color: #DC2626;
            margin: 0;
        }

        .current-progress-bar {
            display: flex;
            gap: 4px;
            padding: 10px 14px;
            background: #f3f8ff;
        }

        .current-progress-dot {
            flex: 1;
            height: 3px;
            background: #d8e8ff;
            border-radius: 2px;
        }

        .current-progress-dot.active {
            background: #26a45a;
        }

        .current-blocker-modal {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            z-index: 20;
        }

        .current-blocker-content {
            background: #fff;
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            max-width: 280px;
        }

        .current-blocker-icon {
            font-size: 48px;
            margin-bottom: 12px;
        }

        .current-blocker-title {
            font-size: 16px;
            font-weight: 600;
            color: #102441;
            margin-bottom: 8px;
        }

        .current-blocker-desc {
            font-size: 12px;
            color: #5c6c82;
            margin-bottom: 16px;
        }

        .current-section-content {
            display: none;
        }

        .current-section-content.active {
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .current-screen {
            display: none;
        }

        .current-screen.active {
            display: flex;
            flex-direction: column;
        }

        .current-screen-nav {
            display: flex;
            justify-content: center;
            gap: 5px;
            margin-top: 12px;
            flex-wrap: wrap;
        }

        .current-screen-nav button {
            padding: 6px 10px;
            background: #fff;
            border: 1px solid #d8e8ff;
            border-radius: 0px 8px;
            color: #102441;
            cursor: pointer;
            font-size: 11px;
            font-weight: 400;
        }

        .current-screen-nav button:hover {
            background: #f3f8ff;
        }

        .current-screen-nav button.active {
            background: #5c6c82;
            color: #fff;
            border-color: #5c6c82;
        }

        .current-footer-link {
            text-align: center;
            margin-top: 12px;
            font-size: 13px;
            color: #102441;
        }

        .current-form-row {
            display: flex;
            gap: 10px;
        }

        .current-form-row .current-input-container {
            flex: 1;
        }

        .current-role-cards {
            display: flex;
            flex-direction: column;
            gap: 12px;
            margin: 16px 0;
        }

        .current-role-card {
            padding: 16px;
            background: #f3f8ff;
            border: 1px solid #d8e8ff;
            border-radius: 8px;
            cursor: pointer;
        }

        .current-role-card.selected {
            border-color: #26a45a;
            background: rgba(38, 164, 90, 0.08);
        }

        .current-role-title {
            font-size: 14px;
            font-weight: 600;
            color: #102441;
            margin-bottom: 4px;
        }

        .current-role-desc {
            font-size: 12px;
            color: #5c6c82;
        }

        .current-social-login {
            display: flex;
            gap: 8px;
            margin-top: 12px;
        }

        .current-social-btn {
            flex: 1;
            padding: 10px;
            background: #f3f8ff;
            border: 1px solid #d8e8ff;
            border-radius: 8px;
            text-align: center;
            font-size: 12px;
            color: #102441;
        }

        .current-divider {
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 14px 0;
        }

        .current-divider-line {
            flex: 1;
            height: 1px;
            background: #d8e8ff;
        }

        .current-divider-text {
            color: #9fa8b6;
            font-size: 12px;
        }
    </style>

    <div class="current-prototype-container">
        <div class="current-prototype-header">
            <h3>Current JuiceNet App Flow</h3>
            <p>How the app works today - click tabs to navigate through current screens</p>
        </div>

        <div class="current-tabs">
            <button class="current-tab active" onclick="showCurrentSection('current-signup')">Signup</button>
            <button class="current-tab" onclick="showCurrentSection('current-email-block')">Email Blocker</button>
            <button class="current-tab" onclick="showCurrentSection('current-role')">Role Select</button>
            <button class="current-tab" onclick="showCurrentSection('current-guest-setup')">Guest Setup</button>
            <button class="current-tab" onclick="showCurrentSection('current-host-setup')">Host Setup</button>
        </div>

        <!-- CURRENT SIGNUP -->
        <div id="current-signup" class="current-section-content active">
            <div class="current-phone">
                <div class="current-phone-screen">
                    <div class="current-notch"></div>
                    <div class="current-app-content">
                        <div class="current-app-header">
                            <div class="current-back-btn">&larr;</div>
                            <span class="current-header-title">Sign up</span>
                        </div>
                        <div class="current-app-body">
                            <div class="current-h3">Create Account</div>
                            <p class="current-subtitle">Join JuiceNet today</p>

                            <div class="current-pain-point">
                                <p>No clear value proposition - users don't know what they're signing up for</p>
                            </div>

                            <div class="current-input-container">
                                <label>Email</label>
                                <input type="text" class="current-input" placeholder="Email">
                            </div>

                            <div class="current-input-container">
                                <label>Password</label>
                                <input type="password" class="current-input" placeholder="Password">
                                <p class="current-input-message">8+ characters, 1 capital letter, 1 special character</p>
                            </div>

                            <div class="current-input-container">
                                <label>Confirm Password</label>
                                <input type="password" class="current-input" placeholder="Confirm password">
                            </div>

                            <div class="current-checkbox-container">
                                <div class="current-checkbox unchecked"></div>
                                <span>I'd like to receive marketing emails & texts</span>
                            </div>

                            <div class="current-checkbox-container">
                                <div class="current-checkbox">&#10003;</div>
                                <span>I agree to the <span class="current-link">Terms</span> and <span class="current-link">Privacy Policy</span><span class="current-reddot">*</span></span>
                            </div>

                            <button class="current-btn-primary">Continue</button>

                            <div class="current-divider">
                                <div class="current-divider-line"></div>
                                <span class="current-divider-text">or sign up with</span>
                                <div class="current-divider-line"></div>
                            </div>

                            <div class="current-social-login">
                                <div class="current-social-btn">&#63743; Apple</div>
                                <div class="current-social-btn">f Facebook</div>
                                <div class="current-social-btn">G Google</div>
                            </div>

                            <p class="current-footer-link">Already a member? <span class="current-link">Log in</span></p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- CURRENT EMAIL BLOCKER -->
        <div id="current-email-block" class="current-section-content">
            <div class="current-phone">
                <div class="current-phone-screen">
                    <div class="current-notch"></div>
                    <div class="current-app-content">
                        <div class="current-app-header">
                            <span class="current-header-title">Verify Email</span>
                        </div>
                        <div class="current-app-body" style="display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 20px;">
                            <div style="font-size: 48px; margin-bottom: 16px;">&#9993;</div>
                            <div class="current-h3">Check your email</div>
                            <p class="current-subtitle" style="margin-bottom: 24px;">We sent a verification link to your email. Please verify before continuing.</p>

                            <div class="current-pain-point" style="width: 100%;">
                                <p><strong>BLOCKER:</strong> Users cannot proceed until email is verified. 23% drop off here!</p>
                            </div>

                            <button class="current-btn-primary" style="opacity: 0.5; cursor: not-allowed;">Continue</button>
                            <p style="font-size: 10px; color: #DC2626; margin-top: 8px;">Button disabled until verified</p>

                            <p style="margin-top: 16px; color: #5c6c82; font-size: 12px;">Didn't get it? <span class="current-link">Resend link</span></p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- CURRENT ROLE SELECTION -->
        <div id="current-role" class="current-section-content">
            <div class="current-phone">
                <div class="current-phone-screen">
                    <div class="current-notch"></div>
                    <div class="current-app-content">
                        <div class="current-app-header">
                            <div class="current-back-btn">&larr;</div>
                            <span class="current-header-title">Select Role</span>
                        </div>
                        <div class="current-app-body">
                            <div class="current-h3">How will you use JuiceNet?</div>
                            <p class="current-subtitle">Choose your primary role</p>

                            <div class="current-pain-point">
                                <p>Role selection happens AFTER signup - users don't see host earnings potential before committing</p>
                            </div>

                            <div class="current-role-cards">
                                <div class="current-role-card">
                                    <div class="current-role-title">Guest</div>
                                    <div class="current-role-desc">Find and book EV chargers near you</div>
                                </div>
                                <div class="current-role-card selected">
                                    <div class="current-role-title">Host</div>
                                    <div class="current-role-desc">Share your charger and earn money</div>
                                </div>
                            </div>

                            <button class="current-btn-primary">Continue</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- CURRENT GUEST SETUP -->
        <div id="current-guest-setup" class="current-section-content">
            <div class="current-phone" id="current-guest-phone">
                <div class="current-phone-screen">
                    <div class="current-notch"></div>

                    <!-- Guest Step 1 -->
                    <div class="current-app-content current-screen active" id="current-guest-step-1">
                        <div class="current-app-header">
                            <div class="current-back-btn">&larr;</div>
                            <span class="current-header-title">Account Setup</span>
                        </div>
                        <div class="current-progress-bar">
                            <div class="current-progress-dot active"></div>
                            <div class="current-progress-dot"></div>
                            <div class="current-progress-dot"></div>
                        </div>
                        <div class="current-app-body">
                            <div class="current-h3">Create Profile</div>
                            <p class="current-subtitle">Tell us about yourself</p>

                            <div style="text-align: center; margin-bottom: 12px;">
                                <div style="width: 60px; height: 60px; background: #f3f8ff; border: 2px dashed #d8e8ff; border-radius: 50%; margin: 0 auto 8px; display: flex; align-items: center; justify-content: center; font-size: 20px; color: #9fa8b6;">+</div>
                                <p style="font-size: 10px; color: #5c6c82;">Add profile photo</p>
                            </div>

                            <div class="current-form-row">
                                <div class="current-input-container">
                                    <label>First Name</label>
                                    <input type="text" class="current-input" placeholder="First Name">
                                </div>
                                <div class="current-input-container">
                                    <label>Last Name</label>
                                    <input type="text" class="current-input" placeholder="Last Name">
                                </div>
                            </div>

                            <div class="current-input-container">
                                <label>Address</label>
                                <input type="text" class="current-input" placeholder="Address">
                            </div>

                            <div class="current-input-container">
                                <label>Phone Number</label>
                                <input type="text" class="current-input" placeholder="Phone Number">
                            </div>

                            <button class="current-btn-primary" onclick="showCurrentGuestStep(2)">Next</button>
                            <button class="current-btn-secondary">Back</button>
                        </div>
                    </div>

                    <!-- Guest Step 2 -->
                    <div class="current-app-content current-screen" id="current-guest-step-2">
                        <div class="current-app-header">
                            <div class="current-back-btn" onclick="showCurrentGuestStep(1)">&larr;</div>
                            <span class="current-header-title">Account Setup</span>
                        </div>
                        <div class="current-progress-bar">
                            <div class="current-progress-dot active"></div>
                            <div class="current-progress-dot active"></div>
                            <div class="current-progress-dot"></div>
                        </div>
                        <div class="current-app-body">
                            <div class="current-h3">Add Your Vehicle</div>
                            <p class="current-subtitle">Help us find compatible chargers</p>

                            <div style="text-align: center; margin-bottom: 12px;">
                                <div style="width: 100%; height: 80px; background: #f3f8ff; border: 2px dashed #d8e8ff; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 24px; color: #9fa8b6;">&#128663; +</div>
                                <p style="font-size: 10px; color: #5c6c82; margin-top: 4px;">Add car photo</p>
                            </div>

                            <div class="current-input-container">
                                <label>Make</label>
                                <select class="current-input">
                                    <option>Select make...</option>
                                    <option>Tesla</option>
                                    <option>Chevrolet</option>
                                    <option>Ford</option>
                                </select>
                            </div>

                            <div class="current-input-container">
                                <label>Model</label>
                                <select class="current-input">
                                    <option>Select model...</option>
                                </select>
                            </div>

                            <div class="current-input-container">
                                <label>Connection Type</label>
                                <select class="current-input">
                                    <option>Select connector...</option>
                                </select>
                            </div>

                            <button class="current-btn-primary" onclick="showCurrentGuestStep(3)">Next</button>
                            <button class="current-btn-secondary" onclick="showCurrentGuestStep(1)">Back</button>
                        </div>
                    </div>

                    <!-- Guest Step 3 -->
                    <div class="current-app-content current-screen" id="current-guest-step-3">
                        <div class="current-app-header">
                            <div class="current-back-btn" onclick="showCurrentGuestStep(2)">&larr;</div>
                            <span class="current-header-title">Account Setup</span>
                        </div>
                        <div class="current-progress-bar">
                            <div class="current-progress-dot active"></div>
                            <div class="current-progress-dot active"></div>
                            <div class="current-progress-dot active"></div>
                        </div>
                        <div class="current-app-body">
                            <div class="current-h3">Payment Method</div>
                            <p class="current-subtitle">Add a card to book chargers</p>

                            <div style="padding: 20px; background: #f3f8ff; border-radius: 8px; text-align: center; margin: 20px 0;">
                                <div style="font-size: 32px; margin-bottom: 8px;">&#128179;</div>
                                <p style="font-size: 14px; color: #102441; font-weight: 500;">Add Credit Card</p>
                                <p style="font-size: 11px; color: #5c6c82;">Powered by Stripe</p>
                            </div>

                            <button class="current-btn-primary">Add Payment Method</button>
                            <button class="current-btn-secondary" onclick="showCurrentGuestStep(2)">Back</button>
                        </div>
                    </div>
                </div>
            </div>
            <div class="current-screen-nav">
                <button onclick="showCurrentGuestStep(1)" class="active">Profile</button>
                <button onclick="showCurrentGuestStep(2)">Vehicle</button>
                <button onclick="showCurrentGuestStep(3)">Payment</button>
            </div>
        </div>

        <!-- CURRENT HOST SETUP -->
        <div id="current-host-setup" class="current-section-content">
            <div class="current-phone" id="current-host-phone">
                <div class="current-phone-screen">
                    <div class="current-notch"></div>

                    <!-- Host Step 1 -->
                    <div class="current-app-content current-screen active" id="current-host-step-1">
                        <div class="current-app-header">
                            <div class="current-back-btn">&larr;</div>
                            <span class="current-header-title">Account Setup</span>
                        </div>
                        <div class="current-progress-bar">
                            <div class="current-progress-dot active"></div>
                            <div class="current-progress-dot"></div>
                            <div class="current-progress-dot"></div>
                            <div class="current-progress-dot"></div>
                        </div>
                        <div class="current-app-body">
                            <div class="current-h3">Create Profile</div>
                            <p class="current-subtitle">Tell us about yourself</p>

                            <div class="current-form-row">
                                <div class="current-input-container">
                                    <label>First Name</label>
                                    <input type="text" class="current-input" placeholder="First Name">
                                </div>
                                <div class="current-input-container">
                                    <label>Last Name</label>
                                    <input type="text" class="current-input" placeholder="Last Name">
                                </div>
                            </div>

                            <div class="current-input-container">
                                <label>Date of Birth</label>
                                <input type="date" class="current-input">
                                <div class="current-pain-point" style="margin-top: 4px;">
                                    <p>No explanation why DOB is needed - causes trust issues</p>
                                </div>
                            </div>

                            <div class="current-input-container">
                                <label>Address</label>
                                <input type="text" class="current-input" placeholder="Address">
                                <div class="current-pain-point" style="margin-top: 4px;">
                                    <p>Users worry their address will be shared publicly</p>
                                </div>
                            </div>

                            <div class="current-input-container">
                                <label>Phone Number</label>
                                <input type="text" class="current-input" placeholder="Phone Number">
                            </div>

                            <button class="current-btn-primary" onclick="showCurrentHostStep(2)">Next</button>
                        </div>
                    </div>

                    <!-- Host Step 2 -->
                    <div class="current-app-content current-screen" id="current-host-step-2">
                        <div class="current-app-header">
                            <div class="current-back-btn" onclick="showCurrentHostStep(1)">&larr;</div>
                            <span class="current-header-title">Account Setup</span>
                        </div>
                        <div class="current-progress-bar">
                            <div class="current-progress-dot active"></div>
                            <div class="current-progress-dot active"></div>
                            <div class="current-progress-dot"></div>
                            <div class="current-progress-dot"></div>
                        </div>
                        <div class="current-app-body">
                            <div class="current-h3">Add Charger</div>
                            <p class="current-subtitle">Charger details</p>

                            <div class="current-pain-point">
                                <p>Long form with required + optional fields mixed together - overwhelming</p>
                            </div>

                            <div style="text-align: center; margin-bottom: 8px;">
                                <div style="width: 100%; height: 60px; background: #f3f8ff; border: 2px dashed #d8e8ff; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 20px; color: #9fa8b6;">&#128247; +</div>
                            </div>

                            <div class="current-input-container">
                                <label>Charger Name</label>
                                <input type="text" class="current-input" placeholder="Charger name">
                            </div>

                            <div class="current-input-container">
                                <label>Charger Type</label>
                                <select class="current-input">
                                    <option>Select type...</option>
                                </select>
                            </div>

                            <div class="current-input-container">
                                <label>Address</label>
                                <input type="text" class="current-input" placeholder="Charger address">
                            </div>

                            <div class="current-input-container">
                                <label>Amenities</label>
                                <input type="text" class="current-input" placeholder="WiFi, Restroom, etc.">
                            </div>

                            <div class="current-input-container">
                                <label>Host Instructions</label>
                                <textarea class="current-input" style="min-height: 60px; resize: none;" placeholder="Instructions for guests..."></textarea>
                            </div>

                            <button class="current-btn-primary" onclick="showCurrentHostStep(3)">Next</button>
                            <button class="current-btn-secondary" onclick="showCurrentHostStep(1)">Back</button>
                        </div>
                    </div>

                    <!-- Host Step 3 -->
                    <div class="current-app-content current-screen" id="current-host-step-3">
                        <div class="current-app-header">
                            <div class="current-back-btn" onclick="showCurrentHostStep(2)">&larr;</div>
                            <span class="current-header-title">Account Setup</span>
                            <span style="position: absolute; right: 14px; color: #26a45a; font-size: 12px; cursor: pointer;">Skip</span>
                        </div>
                        <div class="current-progress-bar">
                            <div class="current-progress-dot active"></div>
                            <div class="current-progress-dot active"></div>
                            <div class="current-progress-dot active"></div>
                            <div class="current-progress-dot"></div>
                        </div>
                        <div class="current-app-body">
                            <div class="current-h3">Payment Method</div>
                            <p class="current-subtitle">How would you like to receive payments?</p>

                            <div class="current-role-cards">
                                <div class="current-role-card">
                                    <div class="current-role-title">&#128179; Credit Card</div>
                                    <div class="current-role-desc">Receive payouts to your card</div>
                                </div>
                                <div class="current-role-card selected">
                                    <div class="current-role-title">&#127974; Bank Account</div>
                                    <div class="current-role-desc">Direct deposit to your bank</div>
                                </div>
                            </div>

                            <button class="current-btn-primary" onclick="showCurrentHostStep(4)">Next</button>
                            <button class="current-btn-secondary" onclick="showCurrentHostStep(2)">Back</button>
                        </div>
                    </div>

                    <!-- Host Step 4 -->
                    <div class="current-app-content current-screen" id="current-host-step-4">
                        <div class="current-app-header">
                            <div class="current-back-btn" onclick="showCurrentHostStep(3)">&larr;</div>
                            <span class="current-header-title">Account Setup</span>
                            <span style="position: absolute; right: 14px; color: #26a45a; font-size: 12px; cursor: pointer;">Skip</span>
                        </div>
                        <div class="current-progress-bar">
                            <div class="current-progress-dot active"></div>
                            <div class="current-progress-dot active"></div>
                            <div class="current-progress-dot active"></div>
                            <div class="current-progress-dot active"></div>
                        </div>
                        <div class="current-app-body">
                            <div class="current-h3">Bank Account</div>
                            <p class="current-subtitle">Enter your bank details</p>

                            <div class="current-pain-point">
                                <p>Asking for sensitive info (SSN, bank details) without building trust first</p>
                            </div>

                            <div class="current-form-row">
                                <div class="current-input-container">
                                    <label>First Name</label>
                                    <input type="text" class="current-input" placeholder="First Name">
                                </div>
                                <div class="current-input-container">
                                    <label>Last Name</label>
                                    <input type="text" class="current-input" placeholder="Last Name">
                                </div>
                            </div>

                            <div class="current-input-container">
                                <label>Date of Birth</label>
                                <input type="date" class="current-input">
                            </div>

                            <div class="current-input-container">
                                <label>Last 4 SSN</label>
                                <input type="text" class="current-input" placeholder="****">
                            </div>

                            <div class="current-input-container">
                                <label>Account Number</label>
                                <input type="text" class="current-input" placeholder="Account Number">
                            </div>

                            <div class="current-input-container">
                                <label>Routing Number</label>
                                <input type="text" class="current-input" placeholder="Routing Number">
                            </div>

                            <button class="current-btn-primary">Confirm</button>
                            <button class="current-btn-secondary" onclick="showCurrentHostStep(3)">Back</button>
                        </div>
                    </div>
                </div>
            </div>
            <div class="current-screen-nav">
                <button onclick="showCurrentHostStep(1)" class="active">Profile</button>
                <button onclick="showCurrentHostStep(2)">Charger</button>
                <button onclick="showCurrentHostStep(3)">Payment</button>
                <button onclick="showCurrentHostStep(4)">Bank</button>
            </div>
        </div>
    </div>

    <script>
        function showCurrentSection(sectionId) {
            document.querySelectorAll('.current-section-content').forEach(section => {
                section.classList.remove('active');
            });
            document.getElementById(sectionId).classList.add('active');

            document.querySelectorAll('.current-tabs .current-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            if (event && event.target) {
                event.target.classList.add('active');
            }
        }

        function showCurrentGuestStep(step) {
            document.querySelectorAll('#current-guest-phone .current-screen').forEach(screen => {
                screen.classList.remove('active');
            });
            document.getElementById('current-guest-step-' + step).classList.add('active');

            document.querySelectorAll('#current-guest-setup .current-screen-nav button').forEach((btn, i) => {
                btn.classList.remove('active');
                if (i === step - 1) btn.classList.add('active');
            });
        }

        function showCurrentHostStep(step) {
            document.querySelectorAll('#current-host-phone .current-screen').forEach(screen => {
                screen.classList.remove('active');
            });
            document.getElementById('current-host-step-' + step).classList.add('active');

            document.querySelectorAll('#current-host-setup .current-screen-nav button').forEach((btn, i) => {
                btn.classList.remove('active');
                if (i === step - 1) btn.classList.add('active');
            });
        }
    </script>
    '''


if __name__ == "__main__":
    # Generate standalone HTML file
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JuiceNet Current App - Interactive Prototype</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body {{
            font-family: 'Poppins', sans-serif;
            background: #f5f5f5;
            min-height: 100vh;
            padding: 20px;
        }}
        h1 {{
            text-align: center;
            color: #102441;
            margin-bottom: 10px;
        }}
        .header-subtitle {{
            text-align: center;
            color: #5c6c82;
            margin-bottom: 30px;
        }}
    </style>
</head>
<body>
    <h1>JuiceNet Current App Flow</h1>
    <p class="header-subtitle">Interactive prototype showing the current user experience</p>

    {generate_juicenet_current_prototype()}
</body>
</html>"""

    with open("JUICENET_CURRENT_FLOW_PROTOTYPE.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Current app prototype saved to JUICENET_CURRENT_FLOW_PROTOTYPE.html")
