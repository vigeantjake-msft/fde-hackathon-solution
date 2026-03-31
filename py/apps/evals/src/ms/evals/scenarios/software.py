# Copyright (c) Microsoft. All rights reserved.
"""Software & Applications scenario templates.

Covers: SAP errors, Salesforce issues, Bloomberg terminal, Microsoft 365
(Teams, Outlook, Word, Excel), internal web apps, application licensing,
software installation, app crashes, browser issues, and email problems.
"""

from ms.evals.constants import Category
from ms.evals.constants import MissingInfo
from ms.evals.constants import Priority
from ms.evals.constants import Team
from ms.evals.models import ScenarioTemplate
from ms.evals.scenarios.registry import register

register(ScenarioTemplate(
    scenario_id="sw-001",
    category=Category.SOFTWARE,
    priority=Priority.P2,
    assigned_team=Team.ENTERPRISE_APPS,
    needs_escalation=False,
    missing_information=[MissingInfo.ERROR_MESSAGE, MissingInfo.STEPS_TO_REPRODUCE],
    subjects=[
        "SAP GUI freezing during transaction processing",
        "SAP hangs every time I run a report",
        "SAP application unresponsive — can't complete transactions",
    ],
    descriptions=[
        "SAP GUI freezes for 30-60 seconds every time I try to run a financial report or post a "
        "transaction. It started yesterday afternoon. I'm using SAP GUI 7.70 on Windows 11. The "
        "Finance team has quarter-end closing this week and this is blocking our work.",
        "When I open transaction code ME21N in SAP to create a purchase order, the entire GUI locks "
        "up and I have to force-close it. This has been happening since the SAP patch last weekend. "
        "Multiple people in Procurement are affected.",
    ],
    next_best_actions=[
        "Check SAP application server health and recent patch deployment logs. Verify if the issue "
        "is affecting specific transaction codes or all SAP operations.",
    ],
    remediation_steps=[
        [
            "Check SAP application server performance metrics and recent changes",
            "Review SAP patch deployment logs from last maintenance window",
            "Test the same transactions from a different workstation to isolate the issue",
            "If server-side, engage SAP Basis team for performance analysis",
            "If client-side, clear SAP GUI cache and verify version compatibility",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-002",
    category=Category.SOFTWARE,
    priority=Priority.P3,
    assigned_team=Team.ENTERPRISE_APPS,
    needs_escalation=False,
    missing_information=[MissingInfo.ERROR_MESSAGE, MissingInfo.SCREENSHOT_OR_ATTACHMENT],
    subjects=[
        "Salesforce reports not loading — spinning wheel",
        "Can't generate reports in Salesforce since this morning",
        "Salesforce dashboard stuck on loading",
    ],
    descriptions=[
        "Salesforce reports have been failing to load all morning. I click on any report and it "
        "just shows a spinning wheel indefinitely. Dashboards are also affected. I can still "
        "navigate to individual records but any report or dashboard is broken. My team in Client "
        "Services relies on these reports for daily client outreach.",
        "None of the custom reports in Salesforce are working. Standard reports seem fine but "
        "anything our team built just shows a blank page. This might be related to the Salesforce "
        "release update that happened over the weekend.",
    ],
    next_best_actions=[
        "Check Salesforce system status page for known issues. Review recent release update impact "
        "on custom report configurations.",
    ],
    remediation_steps=[
        [
            "Check Salesforce Trust status page for service degradation",
            "Verify if the issue affects standard reports or only custom reports",
            "Review recent Salesforce release notes for reporting changes",
            "Test reports in a Salesforce sandbox environment",
            "If custom report specific, check report type and field permissions",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-003",
    category=Category.SOFTWARE,
    priority=Priority.P1,
    assigned_team=Team.ENTERPRISE_APPS,
    needs_escalation=True,
    missing_information=[],
    subjects=[
        "Bloomberg terminal showing stale data — trades not updating",
        "CRITICAL: Bloomberg pricing feed frozen for 20+ minutes",
        "Bloomberg Terminal data lag — trading desk impacted",
    ],
    descriptions=[
        "Bloomberg Terminal on the NYC trading floor is showing stale market data. Prices haven't "
        "updated in over 20 minutes. The traders noticed when their execution prices diverged from "
        "what Bloomberg was showing. This is a live trading issue — we're exposed to price risk on "
        "open positions. Affects 8 terminals on Floor 5.",
        "All Bloomberg terminals in the Institutional Trading department are displaying frozen "
        "data feeds. Last update timestamp shows 09:42 but it's now 10:15. We've tried restarting "
        "individual terminals but the data feed itself appears stale. Multiple traders can't "
        "execute orders accurately.",
    ],
    next_best_actions=[
        "Immediately engage Bloomberg support and check network connectivity to Bloomberg data "
        "feed servers. This is revenue-critical — trading desk cannot operate with stale pricing.",
    ],
    remediation_steps=[
        [
            "Contact Bloomberg support hotline for data feed status",
            "Check network connectivity between trading floor and Bloomberg data feed endpoints",
            "Verify Bloomberg server-side service health",
            "If network issue, check firewall rules and proxy configuration for Bloomberg traffic",
            "If Bloomberg service issue, implement alternative data feed for critical trading",
            "Communicate status to trading desk management every 15 minutes",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-004",
    category=Category.SOFTWARE,
    priority=Priority.P3,
    assigned_team=Team.ENDPOINT,
    needs_escalation=False,
    missing_information=[MissingInfo.DEVICE_INFO, MissingInfo.APPLICATION_VERSION],
    subjects=[
        "Teams crashes on launch after the latest update",
        "Microsoft Teams keeps crashing — can't join meetings",
        "Teams white screen then closes immediately",
    ],
    descriptions=[
        "Since the Teams update that was pushed yesterday, the app shows a white screen for about "
        "5 seconds then crashes. I've tried reinstalling it twice. I can still use Teams in the "
        "browser but the desktop app won't work. I have client meetings all afternoon.",
        "Teams crashes every time I try to launch it. I get a brief flash of the loading screen "
        "then it closes. Event Viewer shows an application error in ms-teams.exe. This started "
        "after the auto-update last night.",
    ],
    next_best_actions=[
        "Clear Teams cache, verify app version, and check for known issues with the latest update. "
        "Suggest using Teams web as a workaround while the desktop app is being fixed.",
    ],
    remediation_steps=[
        [
            "Clear Teams application cache folder",
            "Verify Teams version matches the latest stable release",
            "Check Windows Event Viewer for specific crash details",
            "Uninstall and perform a clean reinstall of Teams",
            "If issue persists, check for known bugs in the latest Teams update",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-005",
    category=Category.SOFTWARE,
    priority=Priority.P3,
    assigned_team=Team.ENDPOINT,
    needs_escalation=False,
    missing_information=[MissingInfo.DEVICE_INFO, MissingInfo.ENVIRONMENT_DETAILS],
    subjects=[
        "Outlook calendar sync broken — showing old appointments",
        "Calendar not updating in Outlook desktop app",
        "Outlook shows meetings I deleted months ago",
    ],
    descriptions=[
        "My Outlook desktop calendar is showing meetings from months ago that I deleted. New "
        "meeting invites sometimes appear, sometimes don't. Outlook Web shows the correct "
        "calendar. This started after I got a new laptop last week — might be a profile migration "
        "issue.",
        "Calendar sync seems broken between Outlook desktop and Exchange. I created a meeting "
        "yesterday and my colleague says they never received the invite. But Outlook shows it as "
        "sent. My calendar has duplicate entries and missing entries.",
    ],
    next_best_actions=[
        "Rebuild the Outlook profile and verify Exchange connectivity. Check for OST file "
        "corruption from the recent laptop migration.",
    ],
    remediation_steps=[
        [
            "Check Outlook connectivity status in the system tray",
            "Verify Exchange Online mailbox health in admin portal",
            "Delete and recreate the Outlook profile to force fresh sync",
            "If OST file is corrupt, delete it and allow Outlook to rebuild",
            "Verify calendar sync is working by creating a test appointment",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-006",
    category=Category.SOFTWARE,
    priority=Priority.P2,
    assigned_team=Team.ENTERPRISE_APPS,
    needs_escalation=False,
    missing_information=[MissingInfo.CONFIGURATION_DETAILS],
    subjects=[
        "Excel macro security policy blocking critical business macro",
        "Can't run VBA macros in Excel — blocked by policy",
        "Excel macro disabled — breaking our trading reconciliation",
    ],
    descriptions=[
        "Our daily trading reconciliation spreadsheet uses VBA macros that were working fine until "
        "this morning. Now Excel shows 'Macros have been disabled' and there's no option to enable "
        "them. This macro is critical — it reconciles about $50M in daily trades and the Finance "
        "team needs results by 2pm.",
        "The macro security policy was changed and now none of our business-critical Excel macros "
        "work. These are signed macros that have been approved for years. Affects the entire "
        "Risk Management team.",
    ],
    next_best_actions=[
        "Review recent Group Policy changes affecting macro security settings. Verify the macro "
        "signing certificate is still trusted. Create an exception for business-critical macros.",
    ],
    remediation_steps=[
        [
            "Check Group Policy for recent changes to Office macro security settings",
            "Verify the code signing certificate for the macros is valid and trusted",
            "If policy was changed, coordinate with Security to create approved exception",
            "Add the file location to Trusted Locations as interim measure",
            "Test macro execution after policy adjustment",
            "Communicate resolution to affected teams",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-007",
    category=Category.SOFTWARE,
    priority=Priority.P4,
    assigned_team=Team.ENDPOINT,
    needs_escalation=False,
    missing_information=[MissingInfo.BUSINESS_IMPACT, MissingInfo.APPLICATION_VERSION],
    subjects=[
        "Software installation request — Python 3.12",
        "Need Python installed on my work laptop",
        "Request: install development tools (Python, VS Code)",
    ],
    descriptions=[
        "I need Python 3.12 installed on my work laptop for data analysis work. The Software "
        "Center doesn't have it available. I'm in the Data Science team and this is a standard "
        "tool for our work. No rush — I can use Jupyter notebooks in the cloud for now.",
        "Requesting installation of Python 3.12 and Visual Studio Code. These are standard "
        "development tools I need for my engineering work. Both should be on the approved "
        "software list. My current laptop doesn't have either.",
    ],
    next_best_actions=[
        "Verify Python 3.12 is on the approved software list and deploy via Intune or Software "
        "Center. If not approved, initiate software approval request.",
    ],
    remediation_steps=[
        [
            "Verify the requested software is on the approved list",
            "If approved, deploy via Intune or Software Center",
            "If not approved, submit software approval request with business justification",
            "Confirm installation and functionality with the user",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-008",
    category=Category.SOFTWARE,
    priority=Priority.P3,
    assigned_team=Team.ENDPOINT,
    needs_escalation=False,
    missing_information=[MissingInfo.ERROR_MESSAGE, MissingInfo.DEVICE_INFO],
    subjects=[
        "Browser crashing when opening internal portal",
        "Edge keeps crashing on our intranet site",
        "Chrome freezes every time I access the internal dashboard",
    ],
    descriptions=[
        "Microsoft Edge crashes every time I try to open the internal IT portal at "
        "portal.contoso.com. It loads partially, then the tab crashes with 'Aw, Snap!' error. "
        "I've cleared the cache and disabled extensions. Chrome works fine for the same site.",
        "Our internal expense reporting portal crashes Chrome every time I try to submit a report. "
        "The page freezes, then the browser becomes unresponsive. This only happens on this "
        "specific portal — other websites work fine.",
    ],
    next_best_actions=[
        "Check browser compatibility with the internal portal. Verify browser version and "
        "extensions. Test in InPrivate mode to isolate the issue.",
    ],
    remediation_steps=[
        [
            "Test the portal in InPrivate/Incognito mode to rule out extension conflicts",
            "Verify browser version is current and compatible with the portal requirements",
            "Clear browser cache, cookies, and site data for the portal domain",
            "Disable hardware acceleration in browser settings",
            "If issue persists, try an alternative browser and report to portal team",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-009",
    category=Category.SOFTWARE,
    priority=Priority.P2,
    assigned_team=Team.ENTERPRISE_APPS,
    needs_escalation=False,
    missing_information=[MissingInfo.TIMESTAMP, MissingInfo.ERROR_MESSAGE],
    subjects=[
        "Outlook not receiving external emails",
        "External emails not arriving — internal email works fine",
        "Missing emails from clients — not in spam folder either",
    ],
    descriptions=[
        "I've stopped receiving emails from external senders. Internal emails arrive fine. I "
        "checked my Junk folder — nothing there either. A client confirmed they sent me 3 emails "
        "today that I never received. No bounce-back on their end. This is critical — I'm missing "
        "trade confirmations from our counterparties.",
        "External emails haven't been arriving for the past few hours. I know because a vendor "
        "called to ask why I didn't reply to their urgent email. My internal email works perfectly. "
        "Nothing in Junk, nothing in Quarantine that I can see.",
    ],
    next_best_actions=[
        "Check Exchange Online mail flow rules and message trace for the missing emails. Verify "
        "there are no transport rules blocking external delivery.",
    ],
    remediation_steps=[
        [
            "Run message trace in Exchange admin center for the user's mailbox",
            "Check mail flow rules and transport rules for blocking conditions",
            "Verify anti-spam/anti-malware quarantine for false positives",
            "Check Exchange Online Protection logs for delivery status",
            "If systemic, check MX records and mail routing configuration",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-010",
    category=Category.SOFTWARE,
    priority=Priority.P2,
    assigned_team=Team.ENTERPRISE_APPS,
    needs_escalation=False,
    missing_information=[MissingInfo.AFFECTED_USERS],
    subjects=[
        "M365 license expired — lost access to all Office apps",
        "Microsoft 365 apps deactivated — 'Your subscription has expired'",
        "Office apps showing 'Unlicensed Product' banner",
    ],
    descriptions=[
        "All my Microsoft 365 apps are showing 'Unlicensed Product' and I can't edit any "
        "documents. Word, Excel, PowerPoint, and Outlook all have the red banner. I was working "
        "fine yesterday. I have a quarterly report due to the board tomorrow that I can't finish.",
        "My M365 license seems to have been removed. All Office apps went into read-only mode "
        "this morning. I can view documents but can't edit or save anything. Outlook is still "
        "receiving emails but I can't compose new ones.",
    ],
    next_best_actions=[
        "Check user's license assignment in M365 admin center. Verify no recent license "
        "reclamation or group-based licensing changes affected the user.",
    ],
    remediation_steps=[
        [
            "Check user's license assignments in M365 admin center",
            "Verify group-based licensing hasn't removed the user's license",
            "If license was revoked, identify the cause and reassign",
            "Have user sign out and sign back in to refresh license status",
            "Verify all Office apps activate successfully",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-011",
    category=Category.SOFTWARE,
    priority=Priority.P3,
    assigned_team=Team.ENTERPRISE_APPS,
    needs_escalation=False,
    missing_information=[MissingInfo.ERROR_MESSAGE, MissingInfo.CONFIGURATION_DETAILS],
    subjects=[
        "Power BI dashboard not refreshing — data is 3 days old",
        "Power BI scheduled refresh failing",
        "Executive dashboard showing stale data in Power BI",
    ],
    descriptions=[
        "Our executive KPI dashboard in Power BI hasn't refreshed since Friday. It's supposed to "
        "refresh daily at 6am. The dashboard shows 'Last refresh: March 28' but it's now March 31. "
        "The executive team relies on this for the Monday morning meeting.",
        "The Power BI dataset for our client analytics report is failing to refresh. I see a "
        "'credentials expired' error in the refresh history. This dataset connects to our Azure "
        "SQL database and was working until the database credentials were rotated last week.",
    ],
    next_best_actions=[
        "Check Power BI scheduled refresh history and update data source credentials if they "
        "were recently rotated.",
    ],
    remediation_steps=[
        [
            "Check Power BI Service for scheduled refresh error details",
            "Verify data source credentials are current after recent rotation",
            "Update gateway data source credentials if needed",
            "Trigger manual refresh and verify data freshness",
            "Confirm scheduled refresh resumes on next cycle",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-012",
    category=Category.SOFTWARE,
    priority=Priority.P3,
    assigned_team=Team.ENDPOINT,
    needs_escalation=False,
    missing_information=[MissingInfo.APPLICATION_VERSION, MissingInfo.DEVICE_INFO],
    subjects=[
        "Adobe Acrobat can't open encrypted PDFs from clients",
        "PDF documents showing 'This document is protected' error",
        "Can't view password-protected PDF files in Acrobat",
    ],
    descriptions=[
        "When I try to open encrypted PDF documents sent by our clients, Adobe Acrobat shows "
        "'This document cannot be opened with your current security settings.' I receive these "
        "PDFs daily as part of contract reviews. This started after the security policy update.",
        "Adobe Acrobat Reader can't open any PDF that has password protection or encryption. It "
        "worked fine until last week. I get an error about 'insufficient permissions' even though "
        "I have the correct passwords. Other people on my team have the same problem.",
    ],
    next_best_actions=[
        "Check recent security policy changes affecting PDF handling. Verify Adobe Acrobat version "
        "and security settings.",
    ],
    remediation_steps=[
        [
            "Check recent Group Policy changes for PDF security settings",
            "Verify Adobe Acrobat version is current",
            "Review Enhanced Security settings in Acrobat preferences",
            "Add trusted domains or certificates if policy requires it",
            "Test opening a sample encrypted PDF after adjustments",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-013",
    category=Category.SOFTWARE,
    priority=Priority.P2,
    assigned_team=Team.ENTERPRISE_APPS,
    needs_escalation=False,
    missing_information=[MissingInfo.ERROR_MESSAGE, MissingInfo.AFFECTED_USERS],
    subjects=[
        "Internal web app showing 502 Bad Gateway errors",
        "Client portal returning 502 errors intermittently",
        "Internal CRM tool unreachable — 502 errors",
    ],
    descriptions=[
        "Our internal client management portal at crm.contoso.com is returning 502 Bad Gateway "
        "errors intermittently. It works sometimes if you refresh a few times but it's unreliable. "
        "The Client Services team uses this all day and they're unable to log client interactions.",
        "The internal reporting tool at reports.contoso.com is showing 502 errors. I've tried "
        "different browsers and from different machines. Seems to be a server-side issue. The app "
        "team deployed an update last night — might be related.",
    ],
    next_best_actions=[
        "Check application server health and recent deployment logs. A recent update may have "
        "introduced instability.",
    ],
    remediation_steps=[
        [
            "Check application server health and resource utilization",
            "Review recent deployment logs for configuration changes",
            "Check reverse proxy / load balancer logs for upstream errors",
            "If recent deployment caused the issue, coordinate rollback with app team",
            "Monitor application stability after remediation",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-014",
    category=Category.SOFTWARE,
    priority=Priority.P2,
    assigned_team=Team.ENTERPRISE_APPS,
    needs_escalation=False,
    missing_information=[MissingInfo.DEVICE_INFO, MissingInfo.NETWORK_LOCATION],
    subjects=[
        "Teams screen sharing not working — black screen for attendees",
        "Can't share my screen in Teams meetings — participants see nothing",
        "Screen sharing shows black rectangle in Teams calls",
    ],
    descriptions=[
        "When I try to share my screen in Teams meetings, attendees see a black rectangle instead "
        "of my screen. I can see the sharing indicator on my end but nobody else can see the "
        "content. This is happening in every meeting. I have a client demo in 2 hours.",
        "Screen sharing in Teams is broken for me. I can share but participants see a completely "
        "black screen. Audio and video work fine. I've tried sharing the whole screen and "
        "individual windows — same result. Reinstalled Teams, still broken.",
    ],
    next_best_actions=[
        "Check GPU driver compatibility with Teams screen sharing. Verify hardware acceleration "
        "settings and try disabling GPU hardware acceleration in Teams.",
    ],
    remediation_steps=[
        [
            "Disable GPU hardware acceleration in Teams settings",
            "Update GPU drivers to the latest version",
            "Check if screen sharing works in Teams web client as a workaround",
            "Verify screen recording permissions in Windows privacy settings",
            "If issue persists, check for known Teams bugs with the GPU model",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-015",
    category=Category.SOFTWARE,
    priority=Priority.P2,
    assigned_team=Team.ENTERPRISE_APPS,
    needs_escalation=False,
    missing_information=[MissingInfo.ERROR_MESSAGE, MissingInfo.ENVIRONMENT_DETAILS],
    subjects=[
        "Citrix session disconnecting every 30 minutes",
        "Remote desktop via Citrix keeps timing out",
        "Citrix Workspace kicks me out repeatedly",
    ],
    descriptions=[
        "My Citrix virtual desktop session disconnects exactly every 30 minutes. I have to log "
        "back in and everything I was working on is lost if I didn't save. This started after the "
        "Citrix policy update on Friday. I'm working remotely and this is my only way to access "
        "the trading applications.",
        "Citrix Workspace app keeps disconnecting my session. It happens at random intervals, "
        "sometimes after 20 minutes, sometimes after an hour. When it reconnects, my session is "
        "still there but any unsaved work in the apps is gone.",
    ],
    next_best_actions=[
        "Review recent Citrix session timeout policy changes. Check Citrix Director for session "
        "disconnect patterns and server health.",
    ],
    remediation_steps=[
        [
            "Check Citrix Director for session disconnect reason codes",
            "Review recent Citrix policy changes for session timeout settings",
            "Verify network stability between user and Citrix infrastructure",
            "Check Citrix server resource utilization for overload",
            "If policy change caused the issue, adjust timeout settings",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-016",
    category=Category.SOFTWARE,
    priority=Priority.P2,
    assigned_team=Team.ENDPOINT,
    needs_escalation=False,
    missing_information=[MissingInfo.APPLICATION_VERSION, MissingInfo.AFFECTED_USERS],
    subjects=[
        "Application auto-update broke compatibility with our workflow",
        "Chrome auto-update breaking internal web apps",
        "Software update killed our internal tool compatibility",
    ],
    descriptions=[
        "Chrome auto-updated to version 124 last night and now our internal client management "
        "portal doesn't work. The app uses features that Chrome 124 apparently deprecated. We "
        "need to either roll back Chrome or get the app team to fix compatibility. About 30 people "
        "in Client Services are affected.",
        "The latest Windows update automatically updated Edge and now our internal compliance "
        "reporting tool shows rendering errors. Forms don't display correctly and we can't submit "
        "reports. The compliance deadline is this Friday.",
    ],
    next_best_actions=[
        "Identify the breaking change in the auto-update and coordinate between browser team and "
        "application team for a fix or rollback.",
    ],
    remediation_steps=[
        [
            "Identify the specific browser version and breaking change",
            "Test the internal app with the previous browser version for confirmation",
            "If possible, roll back the browser update via Intune policy",
            "Coordinate with application team to fix compatibility",
            "Configure auto-update policy to pause future updates until tested",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-017",
    category=Category.SOFTWARE,
    priority=Priority.P3,
    assigned_team=Team.ENTERPRISE_APPS,
    needs_escalation=False,
    missing_information=[MissingInfo.ERROR_MESSAGE, MissingInfo.CONFIGURATION_DETAILS],
    subjects=[
        "DocuSign integration failing with API errors",
        "Can't send documents for signature via DocuSign",
        "DocuSign connector returning authentication errors",
    ],
    descriptions=[
        "Our DocuSign integration in the contract management system stopped working. When I try "
        "to send a document for signature, I get an 'API Authentication Failed' error. This is "
        "blocking contract execution for the M&A team — we have 3 deals waiting for signatures.",
        "DocuSign isn't working from our internal system. The integration was fine last week but "
        "now every signature request fails with a timeout error. I can still log into DocuSign "
        "directly and send documents from there, so it seems like an integration issue.",
    ],
    next_best_actions=[
        "Check DocuSign API credentials and integration configuration. The API key or OAuth "
        "token may have expired.",
    ],
    remediation_steps=[
        [
            "Check DocuSign API credentials for expiration",
            "Verify OAuth token refresh is functioning correctly",
            "Review DocuSign API rate limits for throttling",
            "Test API connectivity from the integration server",
            "If credentials expired, rotate and update in the integration config",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-018",
    category=Category.SOFTWARE,
    priority=Priority.P2,
    assigned_team=Team.ENDPOINT,
    needs_escalation=False,
    missing_information=[MissingInfo.DEVICE_INFO, MissingInfo.STEPS_TO_REPRODUCE],
    subjects=[
        "Word documents corrupted when saving to network drive",
        "Files getting corrupted on save — losing work",
        "Document corruption when saving to shared folder",
    ],
    descriptions=[
        "I've lost work twice today because Word documents are getting corrupted when I save to "
        "the \\\\fs01\\legal-docs network share. The file saves but when I reopen it, Word says "
        "'The file is corrupt and cannot be opened.' I have a 40-page legal brief that I've been "
        "working on for a week and I'm terrified of losing it.",
        "Excel and Word files saved to the Finance shared drive are getting corrupted. Multiple "
        "people in the Finance department are affected. Saving locally works fine. This only "
        "happens with the network drive. We've lost several important documents already.",
    ],
    next_best_actions=[
        "Check network share health and connectivity. Verify SMB protocol version and test file "
        "operations from multiple clients.",
    ],
    remediation_steps=[
        [
            "Recover the corrupted files from backup or shadow copies",
            "Check file server health and disk integrity",
            "Verify SMB signing and protocol version compatibility",
            "Test saving files of various sizes from multiple machines",
            "If file server issue, check event logs for disk or network errors",
            "Recommend saving locally and syncing as interim workaround",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-019",
    category=Category.SOFTWARE,
    priority=Priority.P4,
    assigned_team=Team.ENDPOINT,
    needs_escalation=False,
    missing_information=[MissingInfo.CONFIGURATION_DETAILS, MissingInfo.STEPS_TO_REPRODUCE],
    subjects=[
        "Outlook rules not processing automatically",
        "Email rules stopped working in Outlook",
        "Auto-sort rules in Outlook not firing anymore",
    ],
    descriptions=[
        "My Outlook rules that auto-sort emails into folders stopped working. I have about 15 "
        "rules set up to organize emails from different clients into project folders. They were "
        "working fine until the Office update last week. Now I have to manually sort everything.",
        "The inbox rules I set up in Outlook aren't running automatically. Emails just pile up "
        "in my inbox instead of going to their assigned folders. If I run rules manually they "
        "work, but they don't trigger automatically on new mail.",
    ],
    next_best_actions=[
        "Check Outlook rules for client-only vs server-side configuration. Verify rules haven't "
        "been disabled by the recent Office update.",
    ],
    remediation_steps=[
        [
            "Check Outlook rules list for disabled or broken rules",
            "Verify rules are set as server-side (not client-only) for automatic processing",
            "Delete and recreate rules if they were corrupted by the update",
            "Check mailbox size limits that might be preventing rule execution",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-020",
    category=Category.SOFTWARE,
    priority=Priority.P3,
    assigned_team=Team.ENTERPRISE_APPS,
    needs_escalation=False,
    missing_information=[MissingInfo.ERROR_MESSAGE, MissingInfo.ENVIRONMENT_DETAILS],
    subjects=[
        "Azure DevOps pipeline build failures since this morning",
        "CI/CD pipeline broken — all builds failing",
        "Azure DevOps builds timing out on every commit",
    ],
    descriptions=[
        "All our Azure DevOps CI/CD pipelines started failing this morning. The build agents are "
        "timing out after 60 minutes and the queue is backed up. We have 20+ developers who can't "
        "deploy code. The self-hosted build agents might need attention.",
        "Our build pipeline in Azure DevOps is broken. Every commit triggers a build that fails "
        "with 'Agent offline' error. We use self-hosted agents running on Azure VMs. They might "
        "have gone down during last night's maintenance window.",
    ],
    next_best_actions=[
        "Check self-hosted build agent VM health and connectivity. Verify agent services are "
        "running and can communicate with Azure DevOps.",
    ],
    remediation_steps=[
        [
            "Check Azure VM health for self-hosted build agents",
            "Verify Azure DevOps agent service is running on each build VM",
            "Review agent pool status in Azure DevOps for offline agents",
            "Restart agent services and verify agent registration",
            "Clear the build queue backlog once agents are restored",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-021",
    category=Category.SOFTWARE,
    priority=Priority.P3,
    assigned_team=Team.ENDPOINT,
    needs_escalation=False,
    missing_information=[MissingInfo.APPLICATION_VERSION, MissingInfo.BUSINESS_IMPACT],
    subjects=[
        "Application requesting elevated permissions — UAC popup",
        "Software needs admin rights to run — can't use it",
        "UAC prompt blocks application that used to work",
    ],
    descriptions=[
        "An application I use daily for financial modeling is now requesting admin permissions "
        "every time I launch it. It used to work fine without UAC prompts. I don't have admin "
        "rights on my laptop. This started after the Intune policy update.",
        "My statistical analysis software (R Studio) now shows a UAC prompt requiring admin "
        "access. I can't proceed because I don't have local admin. This tool is essential for "
        "my daily quantitative analysis work.",
    ],
    next_best_actions=[
        "Check recent Intune or Group Policy changes that may have changed UAC behavior. "
        "Consider adding an exception for the specific application.",
    ],
    remediation_steps=[
        [
            "Identify the specific Intune or GPO change affecting UAC behavior",
            "Check if the application was recently updated and now requires elevated permissions",
            "Create an Intune policy exception for the specific application if appropriate",
            "Test running the application after policy adjustment",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-022",
    category=Category.SOFTWARE,
    priority=Priority.P3,
    assigned_team=Team.ENDPOINT,
    needs_escalation=False,
    missing_information=[MissingInfo.DEVICE_INFO, MissingInfo.APPLICATION_VERSION],
    subjects=[
        "Calendar invites not syncing between Teams and Outlook",
        "Teams meetings don't show up in my Outlook calendar",
        "Calendar discrepancy between Teams and Outlook",
    ],
    descriptions=[
        "When colleagues schedule Teams meetings, they appear in my Teams calendar but not in "
        "Outlook. I missed two meetings today because I only check my Outlook calendar. My "
        "Outlook calendar used to show all Teams meetings automatically.",
        "I created a Teams meeting yesterday but none of the invitees got Outlook calendar "
        "entries. They only see it if they open Teams. This used to sync perfectly. Outlook "
        "and Teams are clearly out of sync.",
    ],
    next_best_actions=[
        "Check Outlook-Teams calendar sync settings and verify Exchange Online connectivity. "
        "May need to reset the calendar sync configuration.",
    ],
    remediation_steps=[
        [
            "Verify Exchange Online mailbox calendar health",
            "Check Teams calendar sync settings and permissions",
            "Clear Teams cache and restart the application",
            "Verify the user's M365 license includes Exchange Online",
            "If issue persists, re-link the Teams calendar to Exchange",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-023",
    category=Category.SOFTWARE,
    priority=Priority.P1,
    assigned_team=Team.ENTERPRISE_APPS,
    needs_escalation=True,
    missing_information=[],
    subjects=[
        "SAP license count exceeded — users getting kicked out",
        "CRITICAL: SAP concurrent user limit reached — blocking operations",
        "SAP system refusing new logins — license exhaustion",
    ],
    descriptions=[
        "SAP is refusing new logins with 'Maximum number of named users exceeded' error. We have "
        "50 concurrent users trying to access the system but our license only covers 45. This is "
        "month-end closing and the entire Finance and Accounting teams need SAP access right now. "
        "Revenue recognition is blocked.",
        "SAP ERP is at license capacity. Users across Finance, Procurement, and Operations are "
        "being randomly kicked out when someone else logs in. This is causing data entry errors "
        "and lost work. We're in the middle of quarterly close.",
    ],
    next_best_actions=[
        "Immediately identify and terminate idle SAP sessions to free up licenses. Initiate "
        "emergency license procurement for additional concurrent users.",
    ],
    remediation_steps=[
        [
            "Identify and terminate idle or stale SAP sessions",
            "Check for service accounts consuming user licenses unnecessarily",
            "Initiate emergency license procurement or temporary expansion",
            "Implement session timeout policy to auto-close idle sessions",
            "Communicate capacity constraints to affected departments",
            "Plan permanent license count increase for next billing cycle",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-024",
    category=Category.SOFTWARE,
    priority=Priority.P4,
    assigned_team=Team.ENDPOINT,
    needs_escalation=False,
    missing_information=[MissingInfo.DEVICE_INFO, MissingInfo.REPRODUCTION_FREQUENCY],
    subjects=[
        "Visio crashes when opening large network diagrams",
        "Microsoft Visio very slow with complex diagrams",
        "Visio out of memory error on infrastructure diagrams",
    ],
    descriptions=[
        "Microsoft Visio crashes or runs out of memory when I try to open our network "
        "infrastructure diagram. The file is about 50MB with hundreds of shapes. Visio "
        "works fine for smaller files. Not urgent — I can export sections as images for now.",
        "Visio is extremely slow and eventually crashes when I work on our data center layout "
        "diagram. I think the file has just gotten too large. Is there a way to optimize it or "
        "increase the memory allocation?",
    ],
    next_best_actions=[
        "Check Visio memory allocation settings and system RAM. Consider breaking the large "
        "diagram into linked sub-diagrams.",
    ],
    remediation_steps=[
        [
            "Check available system RAM and Visio memory usage",
            "Verify Visio is the latest version with all patches",
            "Recommend splitting the large diagram into linked sub-diagrams",
            "Increase virtual memory allocation if system is constrained",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-025",
    category=Category.SOFTWARE,
    priority=Priority.P1,
    assigned_team=Team.ENTERPRISE_APPS,
    needs_escalation=True,
    missing_information=[],
    subjects=[
        "Internal trading platform showing wrong prices",
        "CRITICAL: Price display error on trading application",
        "Trading system displaying incorrect market data",
    ],
    descriptions=[
        "Our internal trading platform is displaying incorrect bid/ask prices. The prices shown "
        "diverge from Bloomberg and Reuters by up to 2%. We discovered this when a trader noticed "
        "a trade executed at a price significantly different from what was displayed. This is a "
        "potential regulatory issue — we need to halt trading on this platform immediately.",
        "The price feed in our custom trading application is showing wrong values. Multiple "
        "traders have confirmed that the prices don't match other data sources. We've already "
        "executed several trades that may be at incorrect prices. Compliance has been notified.",
    ],
    next_best_actions=[
        "Immediately halt trading on the affected platform. Investigate the price feed integration "
        "and coordinate with Compliance on potentially erroneous trades.",
    ],
    remediation_steps=[
        [
            "Halt all trading activity on the affected platform immediately",
            "Identify the root cause of price feed discrepancy",
            "Compare executed trades against correct market prices",
            "Notify Compliance team of potentially erroneous trade executions",
            "Fix the price feed integration and verify data accuracy",
            "Resume trading only after thorough validation",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-026",
    category=Category.SOFTWARE,
    priority=Priority.P3,
    assigned_team=Team.ENDPOINT,
    needs_escalation=False,
    missing_information=[MissingInfo.DEVICE_INFO, MissingInfo.REPRODUCTION_FREQUENCY],
    subjects=[
        "OneNote sync conflict losing my meeting notes",
        "OneNote showing sync errors — notes disappearing",
        "OneNote sections not syncing between devices",
    ],
    descriptions=[
        "OneNote keeps showing sync conflicts between my laptop and tablet. Some of my meeting "
        "notes from this week have disappeared or been replaced with older versions. I use "
        "OneNote for all my client meeting notes and I'm worried about data loss.",
        "My OneNote notebooks aren't syncing properly. I have notes on my laptop that don't "
        "appear on my phone, and vice versa. The sync icon shows a constant error. I've tried "
        "closing and reopening but it doesn't help.",
    ],
    next_best_actions=[
        "Check OneNote sync status and conflict resolution. Verify OneDrive storage isn't full "
        "and network connectivity is stable.",
    ],
    remediation_steps=[
        [
            "Check OneNote sync status for specific error messages",
            "Verify OneDrive storage quota isn't exceeded",
            "Force a manual sync and resolve any conflicts",
            "Check for OneNote updates that may fix sync issues",
            "If notes were lost, check OneDrive version history for recovery",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-027",
    category=Category.SOFTWARE,
    priority=Priority.P4,
    assigned_team=Team.ENTERPRISE_APPS,
    needs_escalation=False,
    missing_information=[MissingInfo.ERROR_MESSAGE, MissingInfo.DEVICE_INFO],
    subjects=[
        "Video playback not working in training portal",
        "Can't watch training videos — just shows a black screen",
        "E-learning platform videos won't play",
    ],
    descriptions=[
        "The videos on our internal training portal aren't playing. I click play and get a black "
        "screen with an error icon. I need to complete my compliance training by end of month. "
        "Audio plays fine but no video. This might be a codec or browser compatibility issue.",
        "Our e-learning platform at learn.contoso.com doesn't play videos properly. The video "
        "thumbnails load but when I click play, nothing happens. I've tried Edge and Chrome. "
        "Other websites' videos work fine.",
    ],
    next_best_actions=[
        "Check browser media codec support and training portal compatibility requirements. "
        "Verify content delivery network connectivity.",
    ],
    remediation_steps=[
        [
            "Verify browser version meets the training portal requirements",
            "Check if video format requires specific codecs not available",
            "Disable browser extensions that may block media playback",
            "Try accessing the portal in InPrivate mode",
            "If widespread, contact the training portal vendor for support",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-028",
    category=Category.SOFTWARE,
    priority=Priority.P3,
    assigned_team=Team.ENTERPRISE_APPS,
    needs_escalation=False,
    missing_information=[MissingInfo.ERROR_MESSAGE, MissingInfo.STEPS_TO_REPRODUCE],
    subjects=[
        "Workday self-service portal timeout errors",
        "Can't access Workday — keeps timing out",
        "Workday HR portal very slow and unresponsive",
    ],
    descriptions=[
        "Workday is timing out every time I try to submit my expense report. The page loads but "
        "when I click Submit, it spins for about 2 minutes then shows 'Request Timeout.' I've "
        "tried multiple times. My expense report is due tomorrow.",
        "The Workday self-service portal is extremely slow. Navigating between pages takes 30-60 "
        "seconds. Most actions result in timeout errors. I need to approve time-off requests for "
        "my team but can't get through the workflow.",
    ],
    next_best_actions=[
        "Check Workday service status and network connectivity. Verify if the issue is specific "
        "to certain Workday modules or affecting all functionality.",
    ],
    remediation_steps=[
        [
            "Check Workday community status page for known outages",
            "Verify network connectivity and DNS resolution for Workday",
            "Test Workday from a different network to isolate the issue",
            "If proxy related, check proxy configuration for Workday domains",
            "Contact Workday support if the issue is service-side",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-029",
    category=Category.SOFTWARE,
    priority=Priority.P4,
    assigned_team=Team.ENDPOINT,
    needs_escalation=False,
    missing_information=[MissingInfo.DEVICE_INFO, MissingInfo.APPLICATION_VERSION],
    subjects=[
        "Teams status stuck on 'In a meeting' permanently",
        "My Teams presence shows wrong status all the time",
        "Teams status doesn't change — always shows busy",
    ],
    descriptions=[
        "My Teams status has been stuck on 'In a meeting' for 3 days now even though I'm not in "
        "any meeting. I've tried manually changing it to Available but it reverts back within "
        "minutes. People think I'm always busy and aren't messaging me.",
        "My Teams presence indicator is permanently showing 'Busy' even when I'm idle. I've "
        "restarted Teams, cleared the cache, even signed out and back in. It still shows the "
        "wrong status. Colleagues have started calling my phone instead of Teams.",
    ],
    next_best_actions=[
        "Clear Teams presence cache and reset presence state. Check for stuck calendar events "
        "that may be keeping the status locked.",
    ],
    remediation_steps=[
        [
            "Sign out of Teams completely on all devices",
            "Clear Teams cache (including presence cache files)",
            "Check Outlook calendar for phantom or stuck meetings",
            "Sign back in and manually set status to Available",
            "If issue persists, reset presence via PowerShell admin tools",
        ],
    ],
))

register(ScenarioTemplate(
    scenario_id="sw-030",
    category=Category.SOFTWARE,
    priority=Priority.P2,
    assigned_team=Team.ENDPOINT,
    needs_escalation=False,
    missing_information=[MissingInfo.AFFECTED_USERS, MissingInfo.ENVIRONMENT_DETAILS],
    subjects=[
        "Multiple apps crashing after Windows update — widespread impact",
        "Windows update broke several applications",
        "Post-update chaos — Outlook, Teams, and SAP all broken",
    ],
    descriptions=[
        "After last night's Windows update (KB5035849), multiple applications are crashing on "
        "startup. Outlook, Teams, and our internal tools are all affected. I've talked to 5 "
        "colleagues and they all have the same problem. We're basically unable to work. The "
        "update was pushed to all machines overnight.",
        "The Windows update that was deployed last night has broken everything. Chrome crashes, "
        "Outlook won't start, and the VPN client errors out. This seems to be affecting everyone "
        "who received the update. Is there a way to roll it back?",
    ],
    next_best_actions=[
        "Identify the problematic Windows update and assess rollback options. Check for known "
        "issues with the specific KB number and coordinate a response for all affected users.",
    ],
    remediation_steps=[
        [
            "Identify the specific Windows update causing issues (KB number)",
            "Check Microsoft Known Issues dashboard for the KB",
            "Test uninstalling the update on a sample machine",
            "If rollback resolves the issue, prepare Intune policy to remove the update",
            "Pause the update deployment for machines that haven't received it yet",
            "Communicate workaround and timeline to all affected users",
        ],
    ],
))
