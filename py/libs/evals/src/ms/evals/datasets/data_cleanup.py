# Copyright (c) Microsoft. All rights reserved.
"""Data cleanup evaluation cases — tests robustness against noisy, oversized, and malformed input.

Each case represents a realistic edge case that enterprise IT ticket systems encounter:
excessive email chains, embedded base64 content, HTML markup, garbled encodings,
extremely long descriptions, and other forms of input noise. The triage system
must extract the actual IT issue and classify correctly despite the noise.
"""

import base64

from ms.evals.models import EvalCase
from ms.evals.models import EvalGoldAnswer
from ms.evals.models import EvalSuite
from ms.evals.models import EvalTicket
from ms.evals.models import EvalTicketReporter

_SUITE = EvalSuite.DATA_CLEANUP

# ── Helpers for generating noisy content ─────────────────────────────

_CORPORATE_DISCLAIMER = (
    "\n\n---\nCONFIDENTIALITY NOTICE: This email and any attachments are for the "
    "exclusive and confidential use of the intended recipient. If you are not the "
    "intended recipient, please do not read, distribute, or take action based on "
    "this message. If you have received this in error, please notify the sender "
    "immediately and delete this message from your system. Contoso Financial "
    "Services accepts no liability for the content of this email, or for the "
    "consequences of any actions taken on the basis of the information provided. "
    "Any views or opinions presented are solely those of the author and do not "
    "necessarily represent those of Contoso Financial Services.\n"
)

_LONG_EMAIL_SIGNATURE = (
    "\n\n--\nBest regards,\n"
    "Jennifer Walsh\n"
    "Senior Vice President, Institutional Trading\n"
    "Contoso Financial Services\n"
    "One Financial Plaza, 42nd Floor\n"
    "New York, NY 10004\n"
    "Tel: +1 (212) 555-0147 | Fax: +1 (212) 555-0148\n"
    "Mobile: +1 (917) 555-0192\n"
    "jennifer.walsh@contoso.com\n"
    "www.contoso.com\n"
    "\nPlease consider the environment before printing this email.\n"
    "\nRegistered in the State of New York. Company No. 12345678.\n"
    "\nMember FINRA | SIPC | NFA\n"
)

_QUOTED_REPLY_CHAIN = "\n".join(
    [
        "",
        "--- Original Message ---",
        "From: helpdesk@contoso.com",
        "Sent: Monday, March 16, 2026 3:45 PM",
        "To: Jennifer Walsh <jennifer.walsh@contoso.com>",
        "Subject: RE: RE: RE: RE: Ticket INC-3847 Update",
        "",
        "> Thank you for your patience. We are still investigating.",
        ">",
        "> --- Original Message ---",
        "> From: Jennifer Walsh <jennifer.walsh@contoso.com>",
        "> Sent: Monday, March 16, 2026 2:10 PM",
        "> To: helpdesk@contoso.com",
        "> Subject: RE: RE: RE: Ticket INC-3847 Update",
        ">",
        ">> Any update on this? It's been three days now.",
        ">>",
        ">> --- Original Message ---",
        ">> From: helpdesk@contoso.com",
        ">> Sent: Friday, March 13, 2026 5:00 PM",
        ">> Subject: RE: RE: Ticket INC-3847 Update",
        ">>",
        ">>> We have escalated this to the networking team.",
        ">>>",
        ">>>> Original ticket: VPN keeps disconnecting when I switch floors.",
        ">>>> Started on Tuesday. Using GlobalProtect on my laptop.",
        ">>>> Floor 12 and Floor 8 both affected.",
    ]
)


def _make_base64_image_block(size_bytes: int = 4096) -> str:
    """Generate a realistic base64-encoded image block of approximately the given size."""
    raw_bytes = bytes(range(256)) * (size_bytes // 256 + 1)
    return base64.b64encode(raw_bytes[:size_bytes]).decode("ascii")


def _make_html_heavy_body(core_text: str) -> str:
    """Wrap core text in verbose HTML email markup."""
    return (
        '<!DOCTYPE html><html xmlns="http://www.w3.org/1999/xhtml">'
        "<head><meta charset='UTF-8'/>"
        "<style>"
        "body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; "
        "font-size: 11pt; color: #333333; margin: 0; padding: 20px; }"
        ".container { max-width: 600px; margin: 0 auto; }"
        ".header { background-color: #0078D4; color: white; padding: 15px; }"
        ".content { padding: 20px; line-height: 1.6; }"
        ".footer { font-size: 8pt; color: #999999; border-top: 1px solid #dddddd; "
        "padding-top: 10px; margin-top: 20px; }"
        "table { border-collapse: collapse; width: 100%; }"
        "td, th { border: 1px solid #dddddd; text-align: left; padding: 8px; }"
        "</style></head><body>"
        '<div class="container">'
        '<div class="header"><h2>Contoso IT Support</h2></div>'
        f'<div class="content"><p>{core_text}</p></div>'
        '<div class="footer">'
        "<p>This is an automated message from Contoso IT ServiceNow.</p>"
        "<p>Do not reply to this email. To update your ticket, "
        "visit the self-service portal at https://contoso.service-now.com</p>"
        '<table><tr><th>Ticket</th><th>Status</th><th>Priority</th></tr>'
        "<tr><td>--</td><td>Open</td><td>Unassigned</td></tr></table>"
        "</div></div></body></html>"
    )


# ── Data Cleanup Evaluation Cases ────────────────────────────────────

_VERY_LONG_EMAIL_CHAIN = EvalCase(
    suite=_SUITE,
    case_id="dc-001",
    description="Extremely long email with nested reply chain, multiple signatures, and disclaimers",
    ticket=EvalTicket(
        ticket_id="EVAL-DC-001",
        subject="RE: RE: RE: RE: RE: VPN disconnects when switching floors",
        description=(
            "LATEST UPDATE: The VPN is still dropping. It happens every time I walk "
            "from Floor 12 to Floor 8 for meetings. I have to reconnect manually each "
            "time. This has been going on for a week. GlobalProtect client v3.2 on my "
            "Dell Latitude 5540, Windows 11."
            + _LONG_EMAIL_SIGNATURE
            + _CORPORATE_DISCLAIMER
            + _QUOTED_REPLY_CHAIN
            + _LONG_EMAIL_SIGNATURE
            + _CORPORATE_DISCLAIMER
            + _QUOTED_REPLY_CHAIN
            + _LONG_EMAIL_SIGNATURE
            + _CORPORATE_DISCLAIMER
        ),
        reporter=EvalTicketReporter(
            name="Jennifer Walsh",
            email="jennifer.walsh@contoso.com",
            department="Institutional Trading",
        ),
        created_at="2026-03-18T09:22:00Z",
        channel="email",
    ),
    gold=EvalGoldAnswer(
        ticket_id="EVAL-DC-001",
        category="Network & Connectivity",
        priority="P3",
        assigned_team="Network Operations",
        needs_escalation=False,
        missing_information=["network_location"],
    ),
)

_BASE64_IMAGE_IN_DESCRIPTION = EvalCase(
    suite=_SUITE,
    case_id="dc-002",
    description="Ticket body contains large base64-encoded image data inline",
    ticket=EvalTicket(
        ticket_id="EVAL-DC-002",
        subject="Monitor displays distorted colors after docking",
        description=(
            "When I connect my laptop to the docking station, my external monitor "
            "(Dell U2722D) shows distorted colors — everything has a green tint. "
            "Here's a screenshot of what I'm seeing:\n\n"
            f"data:image/png;base64,{_make_base64_image_block(8192)}\n\n"
            "This started after the Intune update last night. "
            "The laptop display itself is fine. Tried two different USB-C cables."
        ),
        reporter=EvalTicketReporter(
            name="Robert Kim",
            email="robert.kim@contoso.com",
            department="Finance",
        ),
        created_at="2026-03-18T08:15:00Z",
        channel="portal",
        attachments=["monitor_screenshot.png"],
    ),
    gold=EvalGoldAnswer(
        ticket_id="EVAL-DC-002",
        category="Hardware & Peripherals",
        priority="P3",
        assigned_team="Endpoint Engineering",
        needs_escalation=False,
        missing_information=["device_info"],
    ),
)

_HTML_HEAVY_EMAIL = EvalCase(
    suite=_SUITE,
    case_id="dc-003",
    description="Ticket is an HTML-formatted email with heavy markup obscuring the actual issue",
    ticket=EvalTicket(
        ticket_id="EVAL-DC-003",
        subject="Outlook keeps crashing on launch",
        description=_make_html_heavy_body(
            "Outlook crashes immediately on launch — about 3 seconds after the splash "
            "screen. Error: &quot;OUTLOOK.EXE has stopped working&quot;. I&#x27;ve "
            "tried running in safe mode (outlook.exe /safe) and it works fine there, "
            "so it&#x27;s probably an add-in. But I don&#x27;t know which one. "
            "This started after IT pushed the new M365 update yesterday. "
            "I&#x27;m on Build 16.0.17928.20114."
        ),
        reporter=EvalTicketReporter(
            name="Amanda Torres",
            email="amanda.torres@contoso.com",
            department="Compliance",
        ),
        created_at="2026-03-18T07:48:00Z",
        channel="email",
    ),
    gold=EvalGoldAnswer(
        ticket_id="EVAL-DC-003",
        category="Software & Applications",
        priority="P3",
        assigned_team="Endpoint Engineering",
        needs_escalation=False,
        missing_information=["device_info"],
    ),
)

_GARBLED_ENCODING = EvalCase(
    suite=_SUITE,
    case_id="dc-004",
    description="Ticket with corrupted/garbled character encoding mixed into real content",
    ticket=EvalTicket(
        ticket_id="EVAL-DC-004",
        subject="Can\u2019t access SharePoint â€" permission denied",
        description=(
            "Iâ€\u2122m trying to access the Q1 Financial Reports folder on "
            "SharePoint but I keep getting â€œAccess Deniedâ€\u009d. I had access "
            "last week â€\" my manager confirmed I should still have it. "
            "The URL is https://contoso.sharepoint.com/sites/finance/Q1Reports. "
            "Iâ€\u2122ve tried clearing my browser cache and using InPrivate mode. "
            "Still the same error. Other SharePoint sites work fine for me."
        ),
        reporter=EvalTicketReporter(
            name="Michael Chang",
            email="michael.chang@contoso.com",
            department="Finance",
        ),
        created_at="2026-03-17T14:30:00Z",
        channel="portal",
    ),
    gold=EvalGoldAnswer(
        ticket_id="EVAL-DC-004",
        category="Data & Storage",
        priority="P3",
        assigned_team="Data Platform",
        needs_escalation=False,
        missing_information=["error_message"],
    ),
)

_MASSIVE_LOG_DUMP = EvalCase(
    suite=_SUITE,
    case_id="dc-005",
    description="Ticket with an enormous log dump pasted inline — real issue buried in noise",
    ticket=EvalTicket(
        ticket_id="EVAL-DC-005",
        subject="SAP connection timeout - full error log attached",
        description=(
            "SAP GUI keeps timing out when I try to connect to the production server "
            "(PRD-100). Here's the full log output:\n\n"
            + "\n".join(
                [
                    f"[2026-03-17T{8 + i // 60:02d}:{i % 60:02d}:00.{i:03d}Z] "
                    f"TRACE sapgui.connection: Attempting connection to appserver "
                    f"sap-prd-100.contoso.internal:3200 (attempt {i + 1}/100)... "
                    f"timeout after 5000ms. errno=ETIMEDOUT. "
                    f"Stack: at SAPConnection.connect (sapgui.dll:0x7ff{i:04x}) "
                    f"-> at NetworkLayer.tcpHandshake (network.dll:0x{i * 3:06x}) "
                    f"-> at Socket.waitForResponse (ws2_32.dll:0x{i * 7:06x})"
                    for i in range(150)
                ]
            )
            + "\n\nThis has been happening since about 8 AM. Other colleagues in "
            "London can connect fine. I'm in the NYC office."
        ),
        reporter=EvalTicketReporter(
            name="Karen Liu",
            email="karen.liu@contoso.com",
            department="Finance",
        ),
        created_at="2026-03-17T10:45:00Z",
        channel="portal",
        attachments=["sap_connection.log"],
    ),
    gold=EvalGoldAnswer(
        ticket_id="EVAL-DC-005",
        category="Software & Applications",
        priority="P2",
        assigned_team="Enterprise Applications",
        needs_escalation=False,
        missing_information=["environment_details"],
    ),
)

_FORWARDED_THREAD_NOISE = EvalCase(
    suite=_SUITE,
    case_id="dc-006",
    description="Forwarded email thread with multiple unrelated conversations — actual issue is brief",
    ticket=EvalTicket(
        ticket_id="EVAL-DC-006",
        subject="FW: FW: FW: Team lunch Thursday / also my printer is broken",
        description=(
            "Hey IT, my printer (HP LaserJet Pro on Floor 3, near the break room) "
            "won't print — paper jam error but there's no paper stuck. Can someone "
            "come take a look?\n\n"
            "---------- Forwarded message ----------\n"
            "From: Alex Wu <alex.wu@contoso.com>\n"
            "Date: March 17, 2026\n"
            "Subject: Re: Team lunch Thursday\n\n"
            "Sounds great! I'll order from that Thai place.\n\n"
            "> On Mar 17, 2026, Lisa Park wrote:\n"
            "> Hey team, should we do Thai or Italian for Thursday lunch?\n"
            "> Also @David, did you finish the quarterly report?\n\n"
            "---------- Forwarded message ----------\n"
            "From: David Okonkwo <david.okonkwo@contoso.com>\n"
            "Date: March 16, 2026\n"
            "Subject: Quarterly report draft\n\n"
            "Report is attached. Review by EOD Friday please.\n\n"
            "---------- Forwarded message ----------\n"
            "From: IT Announcements <it-announce@contoso.com>\n"
            "Date: March 15, 2026\n"
            "Subject: Planned maintenance - March 22\n\n"
            "Please note: SharePoint and OneDrive will be unavailable "
            "Saturday March 22 from 2 AM - 6 AM EST for scheduled maintenance.\n"
        ),
        reporter=EvalTicketReporter(
            name="Lisa Park",
            email="lisa.park@contoso.com",
            department="Human Resources",
        ),
        created_at="2026-03-17T11:20:00Z",
        channel="email",
    ),
    gold=EvalGoldAnswer(
        ticket_id="EVAL-DC-006",
        category="Hardware & Peripherals",
        priority="P3",
        assigned_team="Endpoint Engineering",
        needs_escalation=False,
        missing_information=["device_info"],
    ),
)

_MULTIPLE_BASE64_ATTACHMENTS = EvalCase(
    suite=_SUITE,
    case_id="dc-007",
    description="Ticket with multiple base64-encoded file attachments inline, burying the actual request",
    ticket=EvalTicket(
        ticket_id="EVAL-DC-007",
        subject="Need new laptop — current one is failing",
        description=(
            "My laptop (Dell Latitude 5530, asset tag CT-4892) is overheating and "
            "shutting down randomly. Battery also only lasts about 30 minutes. "
            "I've had it for 4 years. Hardware diagnostics show failing SSD. "
            "Requesting a replacement.\n\n"
            "Diagnostic report (embedded):\n"
            f"data:application/pdf;base64,{_make_base64_image_block(6144)}\n\n"
            "Battery health report:\n"
            f"data:text/html;base64,{_make_base64_image_block(4096)}\n\n"
            "Asset management screenshot:\n"
            f"data:image/jpeg;base64,{_make_base64_image_block(8192)}\n\n"
            "Please process this as soon as possible — I have client meetings "
            "all next week and can't risk the laptop dying mid-presentation."
        ),
        reporter=EvalTicketReporter(
            name="David Okonkwo",
            email="david.okonkwo@contoso.com",
            department="Wealth Management",
        ),
        created_at="2026-03-17T15:00:00Z",
        channel="portal",
        attachments=["diagnostic_report.pdf", "battery_health.html", "asset_screenshot.jpg"],
    ),
    gold=EvalGoldAnswer(
        ticket_id="EVAL-DC-007",
        category="Hardware & Peripherals",
        priority="P2",
        assigned_team="Endpoint Engineering",
        needs_escalation=False,
        missing_information=[],
    ),
)

_EXCESSIVE_WHITESPACE = EvalCase(
    suite=_SUITE,
    case_id="dc-008",
    description="Ticket with excessive blank lines, tabs, and irregular whitespace",
    ticket=EvalTicket(
        ticket_id="EVAL-DC-008",
        subject="   Password    reset    not    working   ",
        description=(
            "\n\n\n\n\n"
            "   Hi,   \n\n\n"
            "\t\tI tried to reset my password using the self-service portal   \n"
            "\n\n\n\n"
            "   but it says \t\"account not found\"  \t  \n"
            "\n\n"
            "   \tI can log into my email fine but   \n"
            "\t  the password reset page just doesn't recognize    \n"
            "   my username (jlee@contoso.com)   \n"
            "\n\n\n\n\n\n\n\n"
            "   please help    \n"
            "\n\n\n\n\n"
        ),
        reporter=EvalTicketReporter(
            name="Jordan Lee",
            email="jordan.lee@contoso.com",
            department="Marketing",
        ),
        created_at="2026-03-18T10:05:00Z",
        channel="portal",
    ),
    gold=EvalGoldAnswer(
        ticket_id="EVAL-DC-008",
        category="Access & Authentication",
        priority="P3",
        assigned_team="Identity & Access Management",
        needs_escalation=False,
        missing_information=["error_message"],
    ),
)

_MIXED_LANGUAGES = EvalCase(
    suite=_SUITE,
    case_id="dc-009",
    description="Ticket mixing English with other languages — Singapore office user",
    ticket=EvalTicket(
        ticket_id="EVAL-DC-009",
        subject="WiFi 很慢 / very slow in Singapore office",
        description=(
            "Hi IT team,\n\n"
            "WiFi在新加坡办公室非常慢 (WiFi is very slow in Singapore office). "
            "从今天早上开始的 (started this morning). "
            "I'm on Floor 2, near the trading desks. "
            "做speed test只有2 Mbps，平时有100+ Mbps "
            "(speed test shows only 2 Mbps, usually 100+ Mbps). "
            "同事们也有同样的问题 (colleagues have the same issue). "
            "这影响了我们的Bloomberg terminal连接 "
            "(this is affecting our Bloomberg terminal connections).\n\n"
            "谢谢 (Thanks),\nWei Chen"
        ),
        reporter=EvalTicketReporter(
            name="Wei Chen",
            email="wei.chen@contoso.com",
            department="Trading",
        ),
        created_at="2026-03-18T02:30:00Z",
        channel="chat",
    ),
    gold=EvalGoldAnswer(
        ticket_id="EVAL-DC-009",
        category="Network & Connectivity",
        priority="P2",
        assigned_team="Network Operations",
        needs_escalation=False,
        missing_information=[],
    ),
)

_PHONE_TRANSCRIPTION_NOISE = EvalCase(
    suite=_SUITE,
    case_id="dc-010",
    description="Garbled phone transcription with speech-to-text errors",
    ticket=EvalTicket(
        ticket_id="EVAL-DC-010",
        subject="Phone call transcription - unable to access application",
        description=(
            "[Auto-transcribed from phone call, March 17 2026, 2:15 PM EST]\n\n"
            "Hi this is uh mark from the uh wealth management team. I'm calling "
            "because I can't get into cells force... Salesforce... the CRM thing. "
            "It keeps saying... [inaudible] ...forbidden error four oh three. "
            "I need to pull up client records for a meeting in... [pause] "
            "...about an hour. My login is mark dot johnson at can toss oh dot com... "
            "contoso dot com sorry. I tried clearing my cash... cache... and "
            "also tried on my phone with the same [inaudible] result. "
            "It was working fine yesterday. Can someone please [inaudible] "
            "...look into this urgently? Thank you. [End of call, duration 1:42]"
        ),
        reporter=EvalTicketReporter(
            name="Mark Johnson",
            email="mark.johnson@contoso.com",
            department="Wealth Management",
        ),
        created_at="2026-03-17T14:15:00Z",
        channel="phone",
    ),
    gold=EvalGoldAnswer(
        ticket_id="EVAL-DC-010",
        category="Software & Applications",
        priority="P2",
        assigned_team="Enterprise Applications",
        needs_escalation=False,
        missing_information=["error_message"],
    ),
)

_EMOJI_HEAVY_CHAT = EvalCase(
    suite=_SUITE,
    case_id="dc-011",
    description="Teams chat message heavily laden with emojis and informal language",
    ticket=EvalTicket(
        ticket_id="EVAL-DC-011",
        subject="🚨🚨🚨 HELP computer frozen 🥶💻",
        description=(
            "OMG 😱😱😱 my computer just completely froze!!! 💀\n"
            "I was in the middle of a Teams call with a client 📞 and the "
            "whole screen went 🧊 FROZEN 🧊\n"
            "Can't move mouse 🖱️❌ can't type ⌨️❌ nothing works!!! 😤\n"
            "I tried Ctrl+Alt+Del 🤞 but nothing happened 😭😭😭\n"
            "This is the THIRD time this week 😡🤬\n"
            "I have another client call in 30 mins ⏰ PLEASE HELP 🙏🙏🙏\n"
            "Laptop is a ThinkPad T14s, about 2 years old 💻\n"
            "Running Windows 11 🪟"
        ),
        reporter=EvalTicketReporter(
            name="Jessica Huang",
            email="jessica.huang@contoso.com",
            department="Wealth Management",
        ),
        created_at="2026-03-18T14:32:00Z",
        channel="chat",
    ),
    gold=EvalGoldAnswer(
        ticket_id="EVAL-DC-011",
        category="Hardware & Peripherals",
        priority="P2",
        assigned_team="Endpoint Engineering",
        needs_escalation=False,
        missing_information=["error_message"],
    ),
)

_EMBEDDED_JSON_LOGS = EvalCase(
    suite=_SUITE,
    case_id="dc-012",
    description="Ticket with large embedded JSON diagnostic data mixed with the issue description",
    ticket=EvalTicket(
        ticket_id="EVAL-DC-012",
        subject="Intune enrollment failing for new hire devices",
        description=(
            "We onboarded 5 new hires today and 3 of their devices won't enroll "
            "in Intune. The enrollment wizard gets to the 'Connecting to your "
            "organization' step and then fails.\n\n"
            "Device enrollment diagnostic output:\n"
            "```json\n"
            '{"diagnostic": {"enrollmentId": "ENR-2026-0317-001", '
            '"deviceId": "DEV-44821", "os": "Windows 11 23H2", '
            '"enrollmentType": "UserDriven", "mdmAuthority": "Intune", '
            '"aadJoinStatus": "Pending", "steps": ['
            '{"step": "DevicePreparation", "status": "Complete", "duration": 12400}, '
            '{"step": "DeviceSetup", "status": "Complete", "duration": 34200}, '
            '{"step": "AccountSetup", "status": "Failed", "duration": 60000, '
            '"error": {"code": "0x800700b7", "message": "Cannot create a file when '
            'that file already exists", "source": "EnrollmentPlugin.dll", '
            '"innerException": {"code": "AADSTS50076", "message": "MFA claim '
            'challenge required but not satisfied"}}}, '
            '{"step": "PostEnrollment", "status": "Skipped"}], '
            '"policies": {"applied": 12, "failed": 3, "pending": 8}, '
            '"apps": {"installed": 0, "failed": 0, "pending": 15}, '
            '"compliance": {"status": "NotEvaluated"}, '
            '"lastSync": null, "enrollmentTimestamp": "2026-03-17T09:00:00Z", '
            '"retryCount": 3, "maxRetries": 5}}\n'
            "```\n\n"
            "Same error on all 3 devices. The other 2 enrolled fine. "
            "All new hires are in the same OU (WealthMgmt-NewHires)."
        ),
        reporter=EvalTicketReporter(
            name="Patricia Gomez",
            email="patricia.gomez@contoso.com",
            department="IT",
        ),
        created_at="2026-03-17T11:30:00Z",
        channel="portal",
        attachments=["enrollment_diagnostic.json"],
    ),
    gold=EvalGoldAnswer(
        ticket_id="EVAL-DC-012",
        category="Hardware & Peripherals",
        priority="P2",
        assigned_team="Endpoint Engineering",
        needs_escalation=False,
        missing_information=["affected_users", "device_info"],
    ),
)

_URL_AND_PATH_HEAVY = EvalCase(
    suite=_SUITE,
    case_id="dc-013",
    description="Ticket filled with long URLs, file paths, and registry keys obscuring the issue",
    ticket=EvalTicket(
        ticket_id="EVAL-DC-013",
        subject="OneDrive sync stuck — files not uploading",
        description=(
            "OneDrive for Business won't sync my files. Stuck on 'Processing changes' "
            "for 2 days.\n\n"
            "Affected paths:\n"
            "C:\\Users\\nwilliams\\OneDrive - Contoso Financial Services\\Documents\\"
            "Client Portfolios\\2026\\Q1\\Wealth Management\\High Net Worth\\"
            "Portfolio Reviews\\March\\Final Versions\\\n"
            "C:\\Users\\nwilliams\\OneDrive - Contoso Financial Services\\Documents\\"
            "Client Portfolios\\2026\\Q1\\Wealth Management\\High Net Worth\\"
            "Investment Proposals\\Pending Approval\\\n"
            "C:\\Users\\nwilliams\\OneDrive - Contoso Financial Services\\Documents\\"
            "Compliance\\Regulatory Filings\\2026\\SEC\\Form ADV\\Part 2A\\\n\n"
            "Registry checked:\n"
            "HKEY_CURRENT_USER\\Software\\Microsoft\\OneDrive\\Accounts\\Business1\\"
            "ScopeIdToMountPointPathCache\n"
            "HKEY_LOCAL_MACHINE\\SOFTWARE\\Policies\\Microsoft\\OneDrive\\"
            "AllowTenantList\n"
            "HKEY_CURRENT_USER\\Software\\Microsoft\\Office\\16.0\\Common\\"
            "Identity\\Identities\n\n"
            "OneDrive version: 24.045.0310.0002\n"
            "Total files stuck: ~340 files, ~2.8 GB\n"
            "Error in OneDrive activity center: 'We couldn't merge the changes "
            "in [filename]. Both copies have been kept.'"
        ),
        reporter=EvalTicketReporter(
            name="Nathan Williams",
            email="nathan.williams@contoso.com",
            department="Wealth Management",
        ),
        created_at="2026-03-17T16:15:00Z",
        channel="portal",
    ),
    gold=EvalGoldAnswer(
        ticket_id="EVAL-DC-013",
        category="Data & Storage",
        priority="P3",
        assigned_team="Data Platform",
        needs_escalation=False,
        missing_information=[],
    ),
)

_EMPTY_DESCRIPTION_TICKET = EvalCase(
    suite=_SUITE,
    case_id="dc-014",
    description="Ticket with an essentially empty description — subject is the only signal",
    ticket=EvalTicket(
        ticket_id="EVAL-DC-014",
        subject="MFA not working",
        description=".",
        reporter=EvalTicketReporter(
            name="Carlos Rivera",
            email="carlos.rivera@contoso.com",
            department="Trading",
        ),
        created_at="2026-03-18T11:00:00Z",
        channel="chat",
    ),
    gold=EvalGoldAnswer(
        ticket_id="EVAL-DC-014",
        category="Access & Authentication",
        priority="P3",
        assigned_team="Identity & Access Management",
        needs_escalation=False,
        missing_information=[
            "error_message",
            "affected_system",
            "authentication_method",
            "device_info",
        ],
    ),
)

_REPEATED_TEXT_TICKET = EvalCase(
    suite=_SUITE,
    case_id="dc-015",
    description="Ticket with text copy-pasted many times, possibly from a frustrated user mashing send",
    ticket=EvalTicket(
        ticket_id="EVAL-DC-015",
        subject="CANNOT PRINT CANNOT PRINT CANNOT PRINT",
        description=(
            "I CANNOT PRINT TO THE FLOOR 5 PRINTER. " * 25
            + "\n\nSeriously, I've been trying for an hour. Print jobs go to the queue "
            "and then just disappear. HP Color LaserJet Pro on Floor 5 east wing. "
            "Other people on Floor 5 say they can print fine so it might be just me."
        ),
        reporter=EvalTicketReporter(
            name="Greg Novak",
            email="greg.novak@contoso.com",
            department="Legal",
        ),
        created_at="2026-03-18T15:45:00Z",
        channel="portal",
    ),
    gold=EvalGoldAnswer(
        ticket_id="EVAL-DC-015",
        category="Hardware & Peripherals",
        priority="P3",
        assigned_team="Endpoint Engineering",
        needs_escalation=False,
        missing_information=["device_info", "error_message"],
    ),
)


DATA_CLEANUP_CASES: tuple[EvalCase, ...] = (
    _VERY_LONG_EMAIL_CHAIN,
    _BASE64_IMAGE_IN_DESCRIPTION,
    _HTML_HEAVY_EMAIL,
    _GARBLED_ENCODING,
    _MASSIVE_LOG_DUMP,
    _FORWARDED_THREAD_NOISE,
    _MULTIPLE_BASE64_ATTACHMENTS,
    _EXCESSIVE_WHITESPACE,
    _MIXED_LANGUAGES,
    _PHONE_TRANSCRIPTION_NOISE,
    _EMOJI_HEAVY_CHAT,
    _EMBEDDED_JSON_LOGS,
    _URL_AND_PATH_HEAVY,
    _EMPTY_DESCRIPTION_TICKET,
    _REPEATED_TEXT_TICKET,
)
