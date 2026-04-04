# Copyright (c) Microsoft. All rights reserved.
"""Data cleanup evaluation scenarios (INC-5001 through INC-5015).

These scenarios test the triage system's ability to extract the real support
issue from noisy, messy, or malformed ticket descriptions. Each ticket
contains a legitimate IT support issue buried under various forms of data
noise that a production system must handle gracefully.
"""

from ms.evals.models.scenario import EvalScenario
from ms.evals.models.scenario import ScenarioCategory
from ms.evals.models.scenario import ScenarioMetadata
from ms.evals.models.ticket import Channel
from ms.evals.models.ticket import Reporter
from ms.evals.models.ticket import Ticket
from ms.evals.models.triage_decision import AssignedTeam
from ms.evals.models.triage_decision import MissingInformation
from ms.evals.models.triage_decision import Priority
from ms.evals.models.triage_decision import TicketCategory
from ms.evals.models.triage_decision import TriageDecision
from ms.evals.scenarios.registry import register

_CAT = ScenarioCategory.DATA_CLEANUP

# ── INC-5001: Very Long Email Thread ────────────────────────────────

register(
    EvalScenario(
        metadata=ScenarioMetadata(
            scenario_id="dc-001",
            category=_CAT,
            subcategory="long_email_thread",
            description="VPN disconnection buried in a very long email reply chain with signatures and disclaimers.",
            challenge="Extract the actual technical issue from a multi-reply email thread with repeated signatures, "
            "legal disclaimers, and pleasantries that vastly exceed the actual content.",
        ),
        ticket=Ticket(
            ticket_id="INC-5001",
            subject="RE: RE: RE: RE: RE: FW: VPN disconnection issue - follow up from Monday standup",
            description=(
                "---------- Original message ----------\n"
                "From: Sarah Chen <sarah.chen@contoso.com>\n"
                "Date: March 17, 2026 9:14 AM\n"
                "To: IT Help Desk <ithelpdesk@contoso.com>\n\n"
                "Hi team, ever since the Windows update last Tuesday my VPN drops every time I switch "
                "from Ethernet to WiFi. Using GlobalProtect v3.2 on NYC office WiFi, Floor 4.\n\n"
                "Thanks,\nSarah\n\n"
                "---\nSarah Chen | Senior Engineer | Contoso Financial Services\n"
                "One Microsoft Way, Redmond, WA 98052 | +1 (425) 555-0142\n"
                "This email and any attachments are confidential. If you received this in error, "
                "please delete it immediately and notify the sender.\n\n"
                "---------- Reply from IT Help Desk ----------\n"
                "From: IT Help Desk <ithelpdesk@contoso.com>\n"
                "Date: March 17, 2026 10:30 AM\n"
                "To: Sarah Chen <sarah.chen@contoso.com>\n\n"
                "Hi Sarah, thanks for reporting. Can you confirm the VPN client version?\n\n"
                "Regards,\nIT Help Desk | Contoso Financial Services\n"
                "For urgent issues call +1 (800) 555-HELP\n"
                "CONFIDENTIALITY NOTICE: This email contains confidential information belonging "
                "to Contoso Financial Services. Any unauthorized use is prohibited.\n\n"
                "---------- Reply from Sarah Chen ----------\n"
                "From: Sarah Chen <sarah.chen@contoso.com>\n"
                "Date: March 17, 2026 10:45 AM\n\n"
                "It's GlobalProtect 3.2.1-5. Thanks!\n\n"
                "---\nSarah Chen | Senior Engineer | Contoso Financial Services\n"
                "One Microsoft Way, Redmond, WA 98052 | +1 (425) 555-0142\n"
                "This email and any attachments are confidential.\n\n"
                "---------- Reply from IT Help Desk ----------\n"
                "From: IT Help Desk <ithelpdesk@contoso.com>\n"
                "Date: March 17, 2026 11:00 AM\n\n"
                "Got it. We are looking into it. Will update you soon.\n\n"
                "Regards,\nIT Help Desk\n"
                "CONFIDENTIALITY NOTICE: This email contains confidential information.\n\n"
                "---------- Reply from Sarah Chen ----------\n"
                "From: Sarah Chen <sarah.chen@contoso.com>\n"
                "Date: March 17, 2026 2:30 PM\n\n"
                "Any update? It's happened 4 more times today. Very disruptive.\n\n"
                "---\nSarah Chen | Senior Engineer | Contoso Financial Services\n"
                "One Microsoft Way, Redmond, WA 98052 | +1 (425) 555-0142\n"
                "This email and any attachments are confidential.\n\n"
                "---------- Reply from IT Help Desk ----------\n"
                "From: IT Help Desk <ithelpdesk@contoso.com>\n"
                "Date: March 17, 2026 3:15 PM\n\n"
                "Escalating to the network team. They will reach out directly.\n\n"
                "Regards,\nIT Help Desk\n"
                "CONFIDENTIALITY NOTICE: This email contains confidential information."
            ),
            reporter=Reporter(
                name="Sarah Chen",
                email="sarah.chen@contoso.com",
                department="Engineering",
            ),
            created_at="2026-03-17T15:30:00Z",
            channel=Channel.EMAIL,
            attachments=[],
        ),
        expected=TriageDecision(
            ticket_id="INC-5001",
            category=TicketCategory.NETWORK,
            priority=Priority.P3,
            assigned_team=AssignedTeam.NETWORK,
            needs_escalation=False,
            missing_information=[MissingInformation.DEVICE_INFO],
            next_best_action=(
                "Investigate VPN disconnection on GlobalProtect 3.2.1-5 triggered by Ethernet-to-WiFi "
                "switch after a Windows update. Check for known compatibility issues between the "
                "GlobalProtect version and recent Windows patches."
            ),
            remediation_steps=[
                "Check for known issues between GlobalProtect 3.2.x and recent Windows updates",
                "Test VPN reconnection behavior on a reference device with the same GlobalProtect version",
                "Verify WiFi network configuration on NYC office Floor 4",
                "If issue is version-specific, plan an upgrade to a patched GlobalProtect release",
            ],
        ),
    )
)

# ── INC-5002: Base64 Image Data Inline ──────────────────────────────

register(
    EvalScenario(
        metadata=ScenarioMetadata(
            scenario_id="dc-002",
            category=_CAT,
            subcategory="base64_image_inline",
            description="Monitor flickering issue with a large base64-encoded image blob pasted inline.",
            challenge="Parse through a large base64 data block embedded in the description to find the "
            "actual hardware issue. The system must not choke on or misinterpret binary data.",
        ),
        ticket=Ticket(
            ticket_id="INC-5002",
            subject="Monitor display issue - screenshot attached inline",
            description=(
                "My monitor started flickering around 10am. It happens every few minutes and lasts "
                "about 3 seconds each time. Here is a screenshot of what it looks like:\n\n"
                "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mN"
                "k+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==3l5VkgeWjb4JSIyPYKqptaP3hDMcjasEBQXkYVQ87q"
                "+K7V+xtRZRlTo86hdn4xHrs6cDKg9Rc9yUegVq3EMlP/o+hnPoZcmIXULgZrEhcw4rC/7jSlOZfvEw"
                "KqH2rEWsVeqQYomVIK0wCKIzpNeZw4Z/9aGLQZt0x0368hlPHLnCD3S0wFTIYC8VMO74DEkydzUZa5O"
                "s61A1hA7QgjhiGiIYMyG86uITWQWeje9TM74mAmp9soL9H/yg5JKvc6bLonvy6NPNrzKhA7gZJcdsss"
                "Y+srm12era5+UjQwyOOPxndJled52XroGz6XusRq4BhM3PmfBcI6qaedEvFX2jYs4+V4slyGa7Y4mXf"
                "NUfPu9ALwjJcxv8UOAoMs0aoUO/SGUD/rSR5qNYDaCcAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
                "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
                "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
                "AAAAAAAAAAAAAWnije2NfVhb3pW7A+K0b1nNFmqQY7tTkdJRREU8PqYLjsfR2j+5a4nP0U6bVJU9cgaT"
                "sIjxkhWL5QDTvzPE7VGYMqKsXp2RXDokGr6LF3x6k5TCxV+mBDkU5fOzmRFM7mN93GVBQ==\n\n"
                "I've tried switching the DisplayPort cable to a different port and it still happens. "
                "The monitor is connected to my docking station. Bloomberg terminal data seems fine, "
                "just the display is affected."
            ),
            reporter=Reporter(
                name="Anna Brooks",
                email="anna.brooks@contoso.com",
                department="Trading",
            ),
            created_at="2026-03-17T10:45:00Z",
            channel=Channel.PORTAL,
            attachments=["monitor_flicker_screenshot.png"],
        ),
        expected=TriageDecision(
            ticket_id="INC-5002",
            category=TicketCategory.HARDWARE,
            priority=Priority.P3,
            assigned_team=AssignedTeam.ENDPOINT,
            needs_escalation=False,
            missing_information=[MissingInformation.DEVICE_INFO],
            next_best_action=(
                "Investigate monitor flickering connected via docking station. Cable swap did not "
                "resolve — likely a monitor hardware fault or docking station issue."
            ),
            remediation_steps=[
                "Test with a replacement monitor to isolate whether the issue is the display or the dock",
                "Test the current monitor with a direct connection (bypass docking station)",
                "If flickering persists with direct connection, schedule monitor replacement",
                "If dock-only, replace or update docking station firmware",
            ],
        ),
    )
)

# ── INC-5003: HTML Markup in Email Body ─────────────────────────────

register(
    EvalScenario(
        metadata=ScenarioMetadata(
            scenario_id="dc-003",
            category=_CAT,
            subcategory="html_markup_body",
            description="SSO login failure described in raw HTML markup with CSS styles and tags.",
            challenge="Extract the SSO/authentication issue from a description full of raw HTML tags, "
            "inline CSS, and markup artifacts that an email client would normally render.",
        ),
        ticket=Ticket(
            ticket_id="INC-5003",
            subject="SSO login failing across all apps",
            description=(
                '<div style="font-family: Calibri, Arial, sans-serif; font-size: 11pt;">'
                '<p style="margin: 0; padding: 0;">Hi IT team,</p>'
                '<p style="margin: 10px 0;">Since this morning I <b>cannot log into any SSO-enabled '
                "application</b>. When I try to access Salesforce, SAP, or the internal HR portal, "
                "I get redirected to the Entra ID login page and then see:</p>"
                '<p style="color: red; font-weight: bold; background-color: #fff3cd; padding: 8px; '
                'border: 1px solid #ffc107; border-radius: 4px;">'
                "AADSTS50076: Due to a configuration change made by your administrator, you must use "
                "multi-factor authentication to access this resource.</p>"
                '<p style="margin: 10px 0;">I haven&#39;t changed anything on my end. '
                "My MFA was working fine yesterday. Outlook and Teams still work because I was already "
                "signed in.</p>"
                '<p style="margin: 10px 0; color: #666;">Other affected colleagues on my floor '
                "have reported the same issue in our Teams channel.</p>"
                '<br/><p style="margin: 0;">Thanks,<br/>'
                '<span style="color: #0078d4; font-weight: bold;">Marcus Rodriguez</span><br/>'
                '<span style="font-size: 9pt; color: #888;">Wealth Management | Contoso Financial '
                "Services</span></p>"
                "</div>"
            ),
            reporter=Reporter(
                name="Marcus Rodriguez",
                email="marcus.rodriguez@contoso.com",
                department="Wealth Management",
            ),
            created_at="2026-03-18T09:20:00Z",
            channel=Channel.EMAIL,
            attachments=[],
        ),
        expected=TriageDecision(
            ticket_id="INC-5003",
            category=TicketCategory.ACCESS_AUTH,
            priority=Priority.P2,
            assigned_team=AssignedTeam.IAM,
            needs_escalation=False,
            missing_information=[MissingInformation.AFFECTED_USERS],
            next_best_action=(
                "Investigate AADSTS50076 error affecting multiple users. A recent Conditional Access "
                "or MFA policy change is blocking SSO access to Salesforce, SAP, and the HR portal. "
                "Check for recent Entra ID policy modifications."
            ),
            remediation_steps=[
                "Review recent Conditional Access policy changes in Entra ID admin center",
                "Identify which policy is enforcing MFA for these applications",
                "Determine if the policy change was intentional or accidental",
                "If accidental, revert the policy; if intentional, communicate the change and help users enroll in MFA",
                "Verify SSO access is restored for affected users across all applications",
            ],
        ),
    )
)

# ── INC-5004: Extremely Long Email Signature ────────────────────────

register(
    EvalScenario(
        metadata=ScenarioMetadata(
            scenario_id="dc-004",
            category=_CAT,
            subcategory="long_email_signature",
            description="SharePoint upload failure with a brief issue followed by a massive email signature.",
            challenge="The actual issue is 2 sentences long but is followed by a signature block that is "
            "10x longer, including legal disclaimers in multiple languages and office locations.",
        ),
        ticket=Ticket(
            ticket_id="INC-5004",
            subject="Can't upload to SharePoint",
            description=(
                "I'm getting an error when trying to upload a 45MB Excel file to our team's "
                "SharePoint site. The upload starts but fails at about 80% with a generic error.\n\n"
                "---\n"
                "Dr. Ananya Gupta\n"
                "Chief Compliance Officer\n"
                "Contoso Financial Services\n\n"
                "New York Office\n"
                "1 Wall Street, 45th Floor\n"
                "New York, NY 10005\n"
                "Tel: +1 (212) 555-0198\n"
                "Fax: +1 (212) 555-0199\n\n"
                "London Office\n"
                "25 Bank Street, Canary Wharf\n"
                "London E14 5JP, United Kingdom\n"
                "Tel: +44 20 7555 0142\n\n"
                "Singapore Office\n"
                "8 Marina Boulevard, #36-01\n"
                "Marina Bay Financial Centre\n"
                "Singapore 018981\n"
                "Tel: +65 6555 0183\n\n"
                "CONFIDENTIALITY NOTICE: This email message, including any attachments, is for the "
                "sole use of the intended recipient(s) and may contain confidential, proprietary, "
                "and/or privileged information protected by law. If you are not the intended "
                "recipient, you may not use, copy, or distribute this email message or its "
                "attachments. If you have received this email in error, please contact the sender "
                "by reply email and destroy all copies of the original message and any attachments. "
                "Thank you.\n\n"
                "AVIS DE CONFIDENTIALITÉ: Ce message électronique, y compris les pièces jointes, "
                "est destiné exclusivement au(x) destinataire(s) prévu(s) et peut contenir des "
                "informations confidentielles, propriétaires et/ou privilégiées protégées par la "
                "loi. Si vous n'êtes pas le destinataire prévu, vous ne pouvez pas utiliser, copier "
                "ou distribuer ce message. Si vous avez reçu ce message par erreur, veuillez "
                "contacter l'expéditeur et détruire toutes les copies.\n\n"
                "DATENSCHUTZHINWEIS: Diese E-Mail-Nachricht einschließlich aller Anhänge ist "
                "ausschließlich für den/die vorgesehenen Empfänger bestimmt und kann vertrauliche "
                "Informationen enthalten. Wenn Sie nicht der vorgesehene Empfänger sind, dürfen Sie "
                "diese Nachricht nicht verwenden, kopieren oder verteilen.\n\n"
                "Please consider the environment before printing this email. 🌿"
            ),
            reporter=Reporter(
                name="Ananya Gupta",
                email="ananya.gupta@contoso.com",
                department="Compliance",
            ),
            created_at="2026-03-18T11:15:00Z",
            channel=Channel.EMAIL,
            attachments=["Q1_compliance_review.xlsx"],
        ),
        expected=TriageDecision(
            ticket_id="INC-5004",
            category=TicketCategory.DATA_STORAGE,
            priority=Priority.P3,
            assigned_team=AssignedTeam.DATA_PLATFORM,
            needs_escalation=False,
            missing_information=[
                MissingInformation.ERROR_MESSAGE,
                MissingInformation.ENVIRONMENT_DETAILS,
            ],
            next_best_action=(
                "Investigate SharePoint upload failure for a 45MB Excel file. Check SharePoint upload "
                "size limits, network throttling, and whether the file exceeds the tenant's file size policy."
            ),
            remediation_steps=[
                "Verify the SharePoint site's upload size limit and tenant-level file size restrictions",
                "Check if the 45MB file exceeds the configured maximum for the document library",
                "Test uploading a smaller file to isolate size as the cause",
                "If size limit is the issue, adjust the site collection settings or use OneDrive sync as an alternative",
                "Check for any SharePoint throttling or network proxy issues on the user's connection",
            ],
        ),
    )
)

# ── INC-5005: Deep Forwarded Email Chain ────────────────────────────

register(
    EvalScenario(
        metadata=ScenarioMetadata(
            scenario_id="dc-005",
            category=_CAT,
            subcategory="deep_forwarded_chain",
            description="SAP authorization error buried in a deeply nested Fwd:/Re: email chain.",
            challenge="The original issue is at the very bottom of a 6-level deep forwarded/replied chain. "
            "Each level adds commentary that could mislead triage away from the root issue.",
        ),
        ticket=Ticket(
            ticket_id="INC-5005",
            subject="Fwd: Fwd: Re: Fwd: Re: Re: SAP access issue from last Thursday",
            description=(
                "---------- Forwarded by Patricia Gomez ----------\n"
                "FYI IT — this is still unresolved. Please prioritize.\n\n"
                "---------- Forwarded by David Liu ----------\n"
                "Patricia, can you forward this to IT? Linda still can't access SAP.\n\n"
                "---------- Re: from Linda Park ----------\n"
                "David, I tried what the help desk suggested but it didn't work. "
                "Still getting the same error. This is my third time raising this.\n\n"
                "---------- Re: from IT Help Desk ----------\n"
                "Hi Linda, please try clearing your browser cache and logging in again.\n\n"
                "---------- Original message from Linda Park ----------\n"
                "From: Linda Park <linda.park@contoso.com>\n"
                "Date: March 14, 2026\n"
                "Subject: SAP access issue\n\n"
                "After my role changed from Finance Analyst to Senior Finance Analyst last week, "
                "I lost access to the SAP FI module (transaction codes FB50, F110, FAGLL03). "
                "I get error 'No authorization for transaction FB50' when I try to post journal "
                "entries. My manager David Liu approved the role change in ServiceNow on March 10. "
                "I need this for month-end close which starts March 28."
            ),
            reporter=Reporter(
                name="Patricia Gomez",
                email="patricia.gomez@contoso.com",
                department="Executive Operations",
            ),
            created_at="2026-03-18T14:00:00Z",
            channel=Channel.EMAIL,
            attachments=[],
        ),
        expected=TriageDecision(
            ticket_id="INC-5005",
            category=TicketCategory.SOFTWARE,
            priority=Priority.P2,
            assigned_team=AssignedTeam.ENTERPRISE_APPS,
            needs_escalation=False,
            missing_information=[MissingInformation.ENVIRONMENT_DETAILS],
            next_best_action=(
                "Restore SAP FI module authorization for Linda Park after her role change. "
                "The role change was approved on March 10 but SAP role assignments were not updated. "
                "Time-sensitive due to month-end close starting March 28."
            ),
            remediation_steps=[
                "Verify the role change from Finance Analyst to Senior Finance Analyst was processed in SAP",
                "Check SAP role assignments for Linda Park — ensure FI module authorizations (FB50, F110, FAGLL03) "
                "are included in the new role",
                "If role mapping is missing, update the SAP authorization profile for Senior Finance Analyst",
                "Confirm Linda Park can access the required transaction codes",
                "Review the role change provisioning workflow to prevent authorization gaps during future role changes",
            ],
        ),
    )
)

# ── INC-5006: Garbled Encoding / Mojibake ───────────────────────────

register(
    EvalScenario(
        metadata=ScenarioMetadata(
            scenario_id="dc-006",
            category=_CAT,
            subcategory="garbled_encoding",
            description="WiFi connectivity issue described with garbled encoding artifacts throughout.",
            challenge="The description contains mojibake (encoding corruption) mixed with the actual issue. "
            "The system must extract meaning despite Ã©, Â, and other encoding artifacts.",
        ),
        ticket=Ticket(
            ticket_id="INC-5006",
            subject="WiFi problÃ¨me - can't connect",
            description=(
                "Bonjour IT team,\n\n"
                "Je suis having WiFi issues since ce matin. Mon laptop wonÃ¢â‚¬â„¢t connect to the "
                "Contoso-Corp network. It shows Ã¢â‚¬Å\u201cConnected, no internetÃ¢â‚¬\u009d when I do "
                "manage to join. IÃ¢â‚¬â„¢ve tried:\n"
                "- Forgetting and re-adding the network\n"
                "- Restarting my laptop\n"
                "- Moving to a diffÃ©rent floor\n\n"
                "The guest WiFi (Contoso-Guest) works fine but I canÃ¢â‚¬â„¢t access internal "
                "resources on it. Other collÃ¨gues on the 3rd floor of the London office seem "
                "to be working fine.\n\n"
                "Merci,\nÃ‰milie Fontaine"
            ),
            reporter=Reporter(
                name="Émilie Fontaine",
                email="emilie.fontaine@contoso.com",
                department="Wealth Management",
            ),
            created_at="2026-03-18T08:30:00Z",
            channel=Channel.EMAIL,
            attachments=[],
        ),
        expected=TriageDecision(
            ticket_id="INC-5006",
            category=TicketCategory.NETWORK,
            priority=Priority.P3,
            assigned_team=AssignedTeam.NETWORK,
            needs_escalation=False,
            missing_information=[
                MissingInformation.DEVICE_INFO,
                MissingInformation.NETWORK_LOCATION,
            ],
            next_best_action=(
                "Investigate WiFi connectivity issue on Contoso-Corp network in the London office, "
                "3rd floor. User can connect but has no internet. Guest network works fine, suggesting "
                "a corporate network authentication or VLAN issue."
            ),
            remediation_steps=[
                "Check the user's device certificate and 802.1X authentication status for Contoso-Corp",
                "Verify DHCP lease and DNS resolution on the corporate network",
                "Check if the user's device is compliant with the Conditional Access policy for corporate WiFi",
                "Test connectivity from another device on the same floor to isolate user vs. network issue",
                "If user-specific, re-register the device for corporate WiFi access",
            ],
        ),
    )
)

# ── INC-5007: Pasted CSV/Log Data ───────────────────────────────────

register(
    EvalScenario(
        metadata=ScenarioMetadata(
            scenario_id="dc-007",
            category=_CAT,
            subcategory="pasted_log_data",
            description="SQL Server connection timeout with raw log output and CSV data pasted inline.",
            challenge="The description is mostly raw log output and structured data. The system must "
            "identify the underlying database connectivity issue from the noise.",
        ),
        ticket=Ticket(
            ticket_id="INC-5007",
            subject="SQL Server connection timeout errors - logs attached",
            description=(
                "Our application is throwing SQL connection timeouts. Here are the last 20 lines "
                "from the app server log:\n\n"
                "2026-03-18 06:01:12.443 ERROR [ConnectionPool] Timeout expired. The timeout period "
                "elapsed prior to obtaining a connection from the pool.\n"
                "2026-03-18 06:01:12.443 ERROR [ConnectionPool] Max pool size: 100, Current: 100, "
                "Available: 0, Waiting: 47\n"
                "2026-03-18 06:01:13.891 ERROR [SqlCommand] A transport-level error has occurred "
                "(provider: TCP Provider, error: 0 - An existing connection was forcibly closed)\n"
                "2026-03-18 06:01:14.002 WARN  [RetryPolicy] Retrying operation, attempt 3 of 5\n"
                "2026-03-18 06:01:15.112 ERROR [ConnectionPool] Timeout expired. Pool exhausted.\n"
                "2026-03-18 06:01:15.334 ERROR [ConnectionPool] Max pool size: 100, Current: 100, "
                "Available: 0, Waiting: 52\n"
                "2026-03-18 06:01:16.001 ERROR [SqlCommand] Login failed for user 'svc-app-prod'\n"
                "2026-03-18 06:01:17.223 FATAL [AppService] Unable to serve requests - all DB "
                "connections exhausted\n\n"
                "Connection string parameters (sanitized):\n"
                "Server=sql-prod-eastus2.database.windows.net;Database=ContosoDB;Pooling=true;"
                "Max Pool Size=100;Connection Timeout=30;Encrypt=true;\n\n"
                "Error counts in the last hour:\n"
                "timestamp,error_type,count\n"
                "2026-03-18T05:00,timeout,12\n"
                "2026-03-18T05:15,timeout,28\n"
                "2026-03-18T05:30,timeout,45\n"
                "2026-03-18T05:45,timeout,67\n"
                "2026-03-18T06:00,timeout,103\n"
                "2026-03-18T06:00,login_failed,8\n\n"
                "This is a production database. Client-facing APIs are failing."
            ),
            reporter=Reporter(
                name="Raj Patel",
                email="raj.patel@contoso.com",
                department="Data Engineering",
            ),
            created_at="2026-03-18T06:15:00Z",
            channel=Channel.PORTAL,
            attachments=["full_app_log.txt", "connection_metrics.csv"],
        ),
        expected=TriageDecision(
            ticket_id="INC-5007",
            category=TicketCategory.DATA_STORAGE,
            priority=Priority.P1,
            assigned_team=AssignedTeam.DATA_PLATFORM,
            needs_escalation=True,
            missing_information=[],
            next_best_action=(
                "Production SQL Server connection pool exhaustion — all 100 connections consumed "
                "with 52 requests queued. Client-facing APIs are failing. Investigate connection "
                "leaks and consider increasing pool size as immediate mitigation."
            ),
            remediation_steps=[
                "Identify and terminate long-running or leaked database connections on sql-prod-eastus2",
                "Investigate the login failure for 'svc-app-prod' — possible credential expiry or lockout",
                "Increase connection pool size temporarily or restart the application to clear stale connections",
                "Check Azure SQL DTU/vCore utilization for resource contention",
                "Post-incident: add connection pool monitoring alerts and review connection lifecycle management",
            ],
        ),
    )
)

# ── INC-5008: Excessive Unicode / Emojis ────────────────────────────

register(
    EvalScenario(
        metadata=ScenarioMetadata(
            scenario_id="dc-008",
            category=_CAT,
            subcategory="excessive_emojis",
            description="Room booking inquiry buried under excessive emoji and Unicode decorations.",
            challenge="Heavy emoji usage and Unicode decorative characters obscure a simple general "
            "inquiry about meeting room booking. The system must not be confused by the noise.",
        ),
        ticket=Ticket(
            ticket_id="INC-5008",
            subject="🚨🚨🚨 HELP 🚨🚨🚨 Room booking system 💻 not working 😱😭",
            description=(
                "OMG 😱😱😱 I've been trying ALL MORNING to book the big conference room on the "
                "4th floor 🏢 for our team lunch 🍕🍔🥗 on Friday!!!\n\n"
                "When I go to Outlook 📧 and try to add the room 🚪 it says 'Room not found' ❌❌❌\n\n"
                "I tried:\n"
                "✅ Searching for 'Conference Room 4A'\n"
                "✅ Searching for 'Board Room'\n"
                "✅ Searching for 'Large Meeting Room'\n"
                "❌ None of them work!!!\n\n"
                "My colleague Janet 👩‍💼 said she booked it last week with no issues 🤷‍♀️\n\n"
                "PLEASE HELP 🙏🙏🙏🙏🙏\n\n"
                "Thanks!!! 💖✨🌟\n"
                "Chris ✌️"
            ),
            reporter=Reporter(
                name="Chris Taylor",
                email="chris.taylor@contoso.com",
                department="HR",
            ),
            created_at="2026-03-18T12:15:00Z",
            channel=Channel.CHAT,
            attachments=[],
        ),
        expected=TriageDecision(
            ticket_id="INC-5008",
            category=TicketCategory.GENERAL,
            priority=Priority.P4,
            assigned_team=AssignedTeam.NONE,
            needs_escalation=False,
            missing_information=[],
            next_best_action=(
                "Guide the user on how to search for meeting room resources in Outlook. "
                "The room names may differ from what the user expects. This is a usage question, "
                "not a technical issue."
            ),
            remediation_steps=[
                "Reply with the correct room resource names as configured in Exchange/Outlook",
                "Provide instructions on using the Room Finder feature in Outlook calendar",
                "If the room genuinely does not appear, verify the room mailbox exists in Exchange admin",
                "Direct catering questions to Office Management, not IT",
            ],
        ),
    )
)

# ── INC-5009: Repeated / Duplicate Content ──────────────────────────

register(
    EvalScenario(
        metadata=ScenarioMetadata(
            scenario_id="dc-009",
            category=_CAT,
            subcategory="duplicated_content",
            description="Phishing report with the same text copy-pasted multiple times.",
            challenge="The ticket body contains the same phishing report duplicated 4 times, as if the "
            "user accidentally submitted multiple times or copy-pasted repeatedly. The system must "
            "deduplicate and process only once.",
        ),
        ticket=Ticket(
            ticket_id="INC-5009",
            subject="PHISHING EMAIL - DO NOT CLICK - PHISHING EMAIL - DO NOT CLICK",
            description=(
                "I received a suspicious email from 'microsoft-security@outlook-verify.com' asking "
                "me to verify my account by clicking a link. The email looks like a Microsoft sign-in "
                "page but the URL goes to outlook-verify.com. I did NOT click anything.\n\n"
                "--- (forwarded again for visibility) ---\n\n"
                "I received a suspicious email from 'microsoft-security@outlook-verify.com' asking "
                "me to verify my account by clicking a link. The email looks like a Microsoft sign-in "
                "page but the URL goes to outlook-verify.com. I did NOT click anything.\n\n"
                "--- (forwarding one more time to make sure you see this) ---\n\n"
                "I received a suspicious email from 'microsoft-security@outlook-verify.com' asking "
                "me to verify my account by clicking a link. The email looks like a Microsoft sign-in "
                "page but the URL goes to outlook-verify.com. I did NOT click anything.\n\n"
                "--- (sorry if this is a duplicate, my email was acting up) ---\n\n"
                "I received a suspicious email from 'microsoft-security@outlook-verify.com' asking "
                "me to verify my account by clicking a link. The email looks like a Microsoft sign-in "
                "page but the URL goes to outlook-verify.com. I did NOT click anything."
            ),
            reporter=Reporter(
                name="Greg Dawson",
                email="greg.dawson@contoso.com",
                department="Retail Banking",
            ),
            created_at="2026-03-18T11:55:00Z",
            channel=Channel.EMAIL,
            attachments=["suspicious_email.eml"],
        ),
        expected=TriageDecision(
            ticket_id="INC-5009",
            category=TicketCategory.SECURITY,
            priority=Priority.P3,
            assigned_team=AssignedTeam.SECURITY,
            needs_escalation=False,
            missing_information=[],
            next_best_action=(
                "Investigate phishing email from outlook-verify.com impersonating Microsoft. User "
                "did not click the link. Analyze the email headers and URL, block the sender domain, "
                "and check if other users received the same campaign."
            ),
            remediation_steps=[
                "Confirm user did not click the link or enter any credentials",
                "Analyze the phishing email headers and malicious URL",
                "Block the sender domain (outlook-verify.com) in the email gateway",
                "Search email logs for other recipients of the same campaign",
                "If other users received it, send a company-wide phishing alert",
            ],
        ),
    )
)

# ── INC-5010: Auto-Generated System Notification ────────────────────

register(
    EvalScenario(
        metadata=ScenarioMetadata(
            scenario_id="dc-010",
            category=_CAT,
            subcategory="auto_generated_alert",
            description="Routine automated health check notification with all systems green.",
            challenge="An auto-generated monitoring alert that is purely informational (all green). "
            "The system must recognize this as not a real support request and avoid false triage.",
        ),
        ticket=Ticket(
            ticket_id="INC-5010",
            subject="[AUTOMATED] Daily health check summary - 2026-03-18 - all systems nominal",
            description=(
                "═══════════════════════════════════════════════════════════\n"
                "  CONTOSO INFRASTRUCTURE DAILY HEALTH REPORT\n"
                "  Generated: 2026-03-18T06:00:00Z\n"
                "  Report ID: HC-2026-0318-0600\n"
                "═══════════════════════════════════════════════════════════\n\n"
                "SUMMARY: ALL SYSTEMS OPERATIONAL ✅\n\n"
                "Service Status:\n"
                "  [✅] Entra ID / SSO ................ Healthy (99.99% uptime)\n"
                "  [✅] Exchange Online ............... Healthy (100% uptime)\n"
                "  [✅] SharePoint Online ............. Healthy (99.98% uptime)\n"
                "  [✅] Teams ......................... Healthy (100% uptime)\n"
                "  [✅] VPN Gateway (East US 2) ....... Healthy (100% uptime)\n"
                "  [✅] VPN Gateway (UK South) ........ Healthy (100% uptime)\n"
                "  [✅] VPN Gateway (SE Asia) ......... Healthy (99.99% uptime)\n"
                "  [✅] SQL Prod (East US 2) .......... Healthy (100% uptime)\n"
                "  [✅] ADF Pipelines ................. Healthy (24/24 succeeded)\n"
                "  [✅] SAP GUI ....................... Healthy (100% uptime)\n\n"
                "No action required. Next report at 2026-03-19T06:00:00Z.\n\n"
                "---\n"
                "This is an automated message from Contoso Infrastructure Monitoring.\n"
                "Do not reply to this message."
            ),
            reporter=Reporter(
                name="System Monitor",
                email="noreply-monitoring@contoso.com",
                department="IT",
            ),
            created_at="2026-03-18T06:00:00Z",
            channel=Channel.EMAIL,
            attachments=[],
        ),
        expected=TriageDecision(
            ticket_id="INC-5010",
            category=TicketCategory.NOT_SUPPORT,
            priority=Priority.P4,
            assigned_team=AssignedTeam.NONE,
            needs_escalation=False,
            missing_information=[],
            next_best_action=(
                "Close — this is an automated daily health check report with all systems showing "
                "healthy status. No issues detected, no action required."
            ),
            remediation_steps=[
                "No action required — automated health report showing all systems nominal, close ticket",
            ],
        ),
    )
)

# ── INC-5011: URL Spam with Tracking Pixels ─────────────────────────

register(
    EvalScenario(
        metadata=ScenarioMetadata(
            scenario_id="dc-011",
            category=_CAT,
            subcategory="url_spam_tracking",
            description="Phishing investigation request containing numerous tracking URLs and pixel links.",
            challenge="The description is full of URLs, tracking pixel references, and UTM parameters "
            "from the suspicious email the user received. The system must identify the real "
            "concern (phishing investigation) and not get confused by the embedded URLs.",
        ),
        ticket=Ticket(
            ticket_id="INC-5011",
            subject="Suspicious emails with tracking links - getting tons of these",
            description=(
                "I keep getting emails with weird tracking links. Here are examples from today:\n\n"
                "Email 1:\n"
                "  From: deals@contoso-special-offers.com\n"
                "  Link: https://track.contoso-special-offers.com/click?uid=8f3a2b&campaign=spring2026"
                "&redirect=https%3A%2F%2Fmalicious-site.com%2Fcapture%3Fid%3D9182\n"
                "  Tracking pixel: <img src='https://px.contoso-special-offers.com/open?"
                "uid=8f3a2b&t=1710748800' width='1' height='1' />\n\n"
                "Email 2:\n"
                "  From: it-admin@contoso-security-update.net\n"
                "  Link: https://contoso-security-update.net/verify?token=eyJhbGciOiJIUzI1NiJ9"
                ".eyJ1aWQiOiI4ZjNhMmIifQ.fake_jwt_token\n"
                "  Hidden redirect: https://contoso-security-update.net/redirect?url="
                "https%3A%2F%2Fcredential-harvest.com%2Flogin\n\n"
                "Email 3:\n"
                "  From: noreply@contoso-benefits-enrollment.org\n"
                "  Link: https://contoso-benefits-enrollment.org/enroll?emp_id=45892&"
                "utm_source=email&utm_medium=phish&utm_campaign=march2026\n\n"
                "These all look like they are impersonating Contoso. I haven't clicked any of them. "
                "My colleagues Wei Lin and Tom also got similar ones today."
            ),
            reporter=Reporter(
                name="Rachel Green",
                email="rachel.green@contoso.com",
                department="Marketing",
            ),
            created_at="2026-03-18T10:30:00Z",
            channel=Channel.PORTAL,
            attachments=["suspicious_email_1.eml", "suspicious_email_2.eml", "suspicious_email_3.eml"],
        ),
        expected=TriageDecision(
            ticket_id="INC-5011",
            category=TicketCategory.SECURITY,
            priority=Priority.P2,
            assigned_team=AssignedTeam.SECURITY,
            needs_escalation=True,
            missing_information=[MissingInformation.TIMESTAMP],
            next_best_action=(
                "Investigate a coordinated phishing campaign impersonating Contoso across at least "
                "3 domains. Multiple users affected. Analyze the emails, block the sender domains, "
                "and scan the organization for other recipients."
            ),
            remediation_steps=[
                "Analyze all three phishing emails — extract IOCs (sender domains, redirect URLs, tracking pixels)",
                "Block sender domains in the email gateway: contoso-special-offers.com, "
                "contoso-security-update.net, contoso-benefits-enrollment.org",
                "Search email logs for all recipients of emails from these domains",
                "Send organization-wide phishing alert if the campaign is widespread",
                "Verify no users clicked the links — if any did, initiate credential reset and endpoint scan",
            ],
        ),
    )
)

# ── INC-5012: Mixed Languages / Code-Switching ─────────────────────

register(
    EvalScenario(
        metadata=ScenarioMetadata(
            scenario_id="dc-012",
            category=_CAT,
            subcategory="mixed_languages",
            description="Teams crash issue described in mixed English and Mandarin Chinese.",
            challenge="The ticket switches between English and Mandarin. The system must extract the "
            "technical issue regardless of language mixing and code-switching.",
        ),
        ticket=Ticket(
            ticket_id="INC-5012",
            subject="Teams问题 - crashes every time / 每次崩溃",
            description=(
                "Hi IT team,\n\n"
                "我的Teams一直崩溃。Every time I try to join a meeting, the app freezes for about "
                "10 seconds then crashes to desktop. 这个问题从今天早上开始的。\n\n"
                "我试过了:\n"
                "- Clear cache (删除了 %appdata%/Microsoft/Teams 文件夹)\n"
                "- Reinstall Teams\n"
                "- 重启电脑\n\n"
                "都没有用。The web version (teams.microsoft.com) works fine, 但是桌面版本 "
                "就是不行。I need the desktop app because screen sharing 在网页版上质量很差。\n\n"
                "我在新加坡办公室三楼。This is affecting my client meetings.\n\n"
                "谢谢,\nWei Lin"
            ),
            reporter=Reporter(
                name="Wei Lin Tan",
                email="weilin.tan@contoso.com",
                department="Consulting",
            ),
            created_at="2026-03-18T03:15:00Z",
            channel=Channel.PORTAL,
            attachments=[],
        ),
        expected=TriageDecision(
            ticket_id="INC-5012",
            category=TicketCategory.SOFTWARE,
            priority=Priority.P3,
            assigned_team=AssignedTeam.ENTERPRISE_APPS,
            needs_escalation=False,
            missing_information=[
                MissingInformation.DEVICE_INFO,
                MissingInformation.APPLICATION_VERSION,
            ],
            next_best_action=(
                "Investigate Teams desktop app crash on meeting join in the Singapore office. "
                "Cache clear and reinstall did not help. Web version works, suggesting a local "
                "app or GPU rendering issue."
            ),
            remediation_steps=[
                "Check Teams desktop app version and ensure it is the latest supported build",
                "Disable GPU hardware acceleration in Teams settings",
                "Check Windows Event Viewer for application crash details",
                "If GPU-related, update the graphics driver",
                "If crash persists, collect Teams diagnostic logs and escalate to Microsoft support",
            ],
        ),
    )
)

# ── INC-5013: Extremely Terse / Minimal Information ─────────────────

register(
    EvalScenario(
        metadata=ScenarioMetadata(
            scenario_id="dc-013",
            category=_CAT,
            subcategory="extremely_terse",
            description="Laptop issue described with just 3 words total across subject and description.",
            challenge="The entire ticket contains almost no information. The system must correctly "
            "identify it as a hardware issue and flag all the missing information needed to proceed.",
        ),
        ticket=Ticket(
            ticket_id="INC-5013",
            subject="laptop broken",
            description="wont turn on",
            reporter=Reporter(
                name="Robert Chen",
                email="robert.chen2@contoso.com",
                department="Operations",
            ),
            created_at="2026-03-18T08:00:00Z",
            channel=Channel.CHAT,
            attachments=[],
        ),
        expected=TriageDecision(
            ticket_id="INC-5013",
            category=TicketCategory.HARDWARE,
            priority=Priority.P3,
            assigned_team=AssignedTeam.ENDPOINT,
            needs_escalation=False,
            missing_information=[
                MissingInformation.DEVICE_INFO,
                MissingInformation.ERROR_MESSAGE,
                MissingInformation.STEPS_TO_REPRODUCE,
                MissingInformation.ENVIRONMENT_DETAILS,
            ],
            next_best_action=(
                "Contact the user to gather details about the laptop model, what happens when they "
                "press the power button (no LEDs, beeps, partial boot), and when it last worked."
            ),
            remediation_steps=[
                "Contact user to determine the laptop model and asset tag",
                "Ask what happens when the power button is pressed — any LEDs, fan noise, or beeps",
                "Check if the laptop charges (LED on power adapter)",
                "If no signs of power, try a hard reset (remove battery if possible, hold power 30 seconds)",
                "If still unresponsive, schedule hardware replacement or depot repair",
            ],
        ),
    )
)

# ── INC-5014: Massive JSON Error Dump ───────────────────────────────

register(
    EvalScenario(
        metadata=ScenarioMetadata(
            scenario_id="dc-014",
            category=_CAT,
            subcategory="json_error_dump",
            description="ADF pipeline failure with a massive JSON error object pasted in the description.",
            challenge="The description contains a large JSON error payload from Azure Data Factory. "
            "The system must parse through the structured error data to identify the pipeline issue.",
        ),
        ticket=Ticket(
            ticket_id="INC-5014",
            subject="ADF pipeline error - full error output below",
            description=(
                "The prod-client-ingest pipeline failed again. Here's the full error:\n\n"
                '{\n'
                '    "error": {\n'
                '        "code": "InvalidTemplate",\n'
                '        "message": "Unable to process template language expressions in activity '
                "Copy_ClientData_ADLS output.\",\n"
                '        "details": [\n'
                '            {\n'
                '                "code": "BadRequest",\n'
                '                "target": "pipeline/prod-client-ingest/activities/Copy_ClientData_ADLS",\n'
                '                "message": "The specified path does not exist: '
                "https://contosodatalake.dfs.core.windows.net/raw/clients/2026/03/18/\",\n"
                '                "activityRunId": "a8f3c2e1-4b5d-4f6a-8c9d-0e1f2a3b4c5d",\n'
                '                "pipelineRunId": "b7e2d1c0-3a4b-5e6f-9d8c-1f0e2d3c4b5a",\n'
                '                "errorCode": "2011",\n'
                '                "failureType": "UserError",\n'
                '                "target": "Copy_ClientData_ADLS",\n'
                '                "details": [\n'
                '                    {\n'
                '                        "code": "PathNotFound",\n'
                '                        "message": "The container or path \\\"raw/clients/2026/03/18/\\\" '
                "does not exist in storage account contosodatalake.\"\n"
                "                    },\n"
                "                    {\n"
                '                        "code": "StorageAccountDetails",\n'
                '                        "message": "Storage: contosodatalake.dfs.core.windows.net, '
                "Container: raw, Path: clients/2026/03/18/, ResourceGroup: rg-data-prod, "
                'Subscription: contoso-prod-001"\n'
                "                    }\n"
                "                ]\n"
                "            }\n"
                "        ],\n"
                '        "innerError": {\n'
                '            "code": "PathNotFound",\n'
                '            "message": "Operation returned an invalid status code: NotFound"\n'
                "        }\n"
                "    },\n"
                '    "runId": "b7e2d1c0-3a4b-5e6f-9d8c-1f0e2d3c4b5a",\n'
                '    "pipelineName": "prod-client-ingest",\n'
                '    "startTime": "2026-03-18T03:00:05.234Z",\n'
                '    "endTime": "2026-03-18T03:00:12.891Z",\n'
                '    "status": "Failed"\n'
                "}\n\n"
                "This pipeline feeds the daily client reporting. The path should be auto-created "
                "but it looks like today's date partition is missing."
            ),
            reporter=Reporter(
                name="Raj Patel",
                email="raj.patel@contoso.com",
                department="Data Engineering",
            ),
            created_at="2026-03-18T03:15:00Z",
            channel=Channel.PORTAL,
            attachments=["adf_pipeline_run_details.json"],
        ),
        expected=TriageDecision(
            ticket_id="INC-5014",
            category=TicketCategory.DATA_STORAGE,
            priority=Priority.P2,
            assigned_team=AssignedTeam.DATA_PLATFORM,
            needs_escalation=False,
            missing_information=[],
            next_best_action=(
                "ADF pipeline prod-client-ingest failing with PathNotFound — the date partition "
                "directory (raw/clients/2026/03/18/) does not exist in contosodatalake. Create "
                "the missing path and investigate why auto-partition creation failed."
            ),
            remediation_steps=[
                "Create the missing directory path raw/clients/2026/03/18/ in the contosodatalake storage account",
                "Re-run the prod-client-ingest pipeline and verify successful execution",
                "Investigate why the auto-partition creation step failed — check ADF linked service permissions",
                "Verify the service principal has Storage Blob Data Contributor on the container",
                "Add pre-pipeline validation to create date partition directories before copy activities run",
            ],
        ),
    )
)

# ── INC-5015: Email Metadata / Header Noise ─────────────────────────

register(
    EvalScenario(
        metadata=ScenarioMetadata(
            scenario_id="dc-015",
            category=_CAT,
            subcategory="email_metadata_noise",
            description="MFA token issue buried under email headers, MIME boundaries, and routing metadata.",
            challenge="The ticket was created from a raw email forward that includes full email headers, "
            "MIME type declarations, and routing information before the actual MFA issue.",
        ),
        ticket=Ticket(
            ticket_id="INC-5015",
            subject="Re: [EXTERNAL] Re: [INTERNAL] Fwd: MFA token not refreshing",
            description=(
                "Return-Path: <david.kim@contoso.com>\n"
                "Received: from mail-eastus2.contoso.com (mail-eastus2.contoso.com [10.0.2.45])\n"
                "    by edge-gateway.contoso.com (Postfix) with ESMTPS id A1B2C3D4E5\n"
                "    for <ithelpdesk@contoso.com>; Mon, 18 Mar 2026 09:30:00 +0000 (UTC)\n"
                "DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed;\n"
                "    d=contoso.com; s=selector1;\n"
                "    h=from:to:subject:date:message-id;\n"
                "    bh=47DEQpj8HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU=;\n"
                "    b=FAKE_DKIM_SIGNATURE_DATA_HERE\n"
                "MIME-Version: 1.0\n"
                "Content-Type: multipart/alternative;\n"
                '    boundary="----=_Part_12345_67890.1710751800000"\n'
                "X-Mailer: Microsoft Outlook 16.0.18000.20000\n"
                "X-MS-Exchange-Organization-SCL: -1\n"
                "X-MS-Exchange-Organization-AuthSource: mail-eastus2.contoso.com\n"
                "X-MS-Has-Attach:\n"
                "X-MS-TNEF-Correlator:\n"
                "Message-ID: <abc123@mail-eastus2.contoso.com>\n"
                "Date: Mon, 18 Mar 2026 09:30:00 +0000\n"
                "From: David Kim <david.kim@contoso.com>\n"
                "To: IT Help Desk <ithelpdesk@contoso.com>\n"
                "Subject: MFA token not refreshing\n\n"
                "------=_Part_12345_67890.1710751800000\n"
                "Content-Type: text/plain; charset=utf-8\n\n"
                "Hi, my Authenticator app MFA token stopped refreshing 2 days ago. The 6-digit code "
                "in the app stays the same and never changes, so it always says 'incorrect code' when "
                "I try to sign in. I've been using SMS codes as a workaround but those are slow and "
                "unreliable. Running iPhone 15 with Authenticator app version 6.8.4. I'm in the "
                "Trading department and need this fixed before market open tomorrow.\n\n"
                "------=_Part_12345_67890.1710751800000\n"
                'Content-Type: text/html; charset="utf-8"\n\n'
                "<html><body><p>Hi, my Authenticator app MFA token stopped refreshing...</p></body></html>\n"
                "------=_Part_12345_67890.1710751800000--"
            ),
            reporter=Reporter(
                name="David Kim",
                email="david.kim@contoso.com",
                department="Trading",
            ),
            created_at="2026-03-18T09:30:00Z",
            channel=Channel.EMAIL,
            attachments=[],
        ),
        expected=TriageDecision(
            ticket_id="INC-5015",
            category=TicketCategory.ACCESS_AUTH,
            priority=Priority.P3,
            assigned_team=AssignedTeam.IAM,
            needs_escalation=False,
            missing_information=[MissingInformation.AUTHENTICATION_METHOD],
            next_best_action=(
                "Investigate MFA TOTP token not refreshing in the Authenticator app (v6.8.4) on "
                "iPhone 15. The time-based code is stuck, suggesting a clock sync issue on the "
                "device or a corrupted token seed."
            ),
            remediation_steps=[
                "Verify the device clock is synced to automatic time (Settings > General > Date & Time)",
                "In the Authenticator app, remove and re-add the Contoso account to regenerate the token seed",
                "Check Entra ID for the user's MFA registration status and reset if needed",
                "Confirm TOTP codes rotate correctly after re-registration",
                "If issue persists, check for Authenticator app updates or test with a different MFA method",
            ],
        ),
    )
)
