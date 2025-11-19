#!/usr/bin/env python3
"""
Batch Plugin Generator
Generates ALL Windows AI plugins from the roadmap in one go
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from generate_plugin import generate_plugin

# Plugin definitions - categorized by type
# Format: (name, template_type, api_key_var, api_url, description)

AI_PROVIDERS = [
    ("Perplexity AI", "api", "PERPLEXITY_API_KEY", "https://api.perplexity.ai", "pplx-7b, pplx-70b models"),
    ("Together AI", "api", "TOGETHER_API_KEY", "https://api.together.xyz/v1", "RedPajama, Falcon, MPT"),
    ("Anyscale", "api", "ANYSCALE_API_KEY", "https://api.endpoints.anyscale.com/v1", "Llama, Mistral endpoints"),
    ("AI21 Labs", "api", "AI21_API_KEY", "https://api.ai21.com/studio/v1", "Jurassic-2, Contextual Answers"),
    ("Runway ML", "api", "RUNWAY_API_KEY", "https://api.runwayml.com/v1", "Gen-2, Gen-3 video"),
    ("Midjourney", "api", "MIDJOURNEY_API_KEY", "https://api.midjourney.com/v1", "AI image generation (unofficial)"),
    ("Alibaba Qwen", "api", "ALIBABA_API_KEY", "https://dashscope.aliyuncs.com/api/v1", "Qwen, Tongyi Qianwen"),
    ("Baidu ERNIE", "api", "BAIDU_API_KEY", "https://aip.baidubce.com/rpc/2.0", "ERNIE Bot, ERNIE 3.5"),
    ("Yandex YaLM", "api", "YANDEX_API_KEY", "https://api.yandex.com/v1", "YaLM 100B"),
]

LOCAL_AI = [
    ("Jan AI", "local", None, None, "Local AI with privacy focus"),
    ("KoboldAI", "local", None, None, "Local AI for creative writing"),
    ("Text Generation WebUI", "local", None, None, "oobabooga gradio interface"),
    ("vLLM", "local", None, None, "High-performance LLM serving"),
    ("ExLlama", "local", None, None, "Fast LLaMA inference"),
    ("AutoGPTQ", "local", None, None, "Quantized model inference"),
    ("PrivateGPT", "local", None, None, "Private document Q&A"),
    ("LocalGPT", "local", None, None, "Local document chat"),
    ("h2oGPT", "local", None, None, "H2O.ai local LLM"),
    ("FastChat", "local", None, None, "Vicuna model serving"),
]

CODE_ASSISTANTS = [
    ("Tabnine", "api", "TABNINE_API_KEY", "https://api.tabnine.com", "AI code completion"),
    ("Codeium", "api", "CODEIUM_API_KEY", "https://api.codeium.com", "Free code AI"),
    ("Replit Ghostwriter", "api", "REPLIT_API_KEY", "https://replit.com/api", "Replit AI assistant"),
    ("Amazon CodeWhisperer", "api", "AWS_ACCESS_KEY_ID", "https://codewhisperer.us-east-1.amazonaws.com", "AWS code AI"),
]

PRODUCTIVITY = [
    ("Jira", "storage", "JIRA_API_KEY", "https://your-domain.atlassian.net/rest/api/3", "Jira issue tracking"),
    ("Confluence", "storage", "CONFLUENCE_API_KEY", "https://your-domain.atlassian.net/wiki/rest/api", "Confluence wiki"),
    ("ClickUp", "storage", "CLICKUP_API_KEY", "https://api.clickup.com/api/v2", "ClickUp task management"),
    ("Linear", "storage", "LINEAR_API_KEY", "https://api.linear.app/graphql", "Linear project tracker"),
    ("Height", "storage", "HEIGHT_API_KEY", "https://api.height.app", "Height task manager"),
    ("Coda", "storage", "CODA_API_KEY", "https://coda.io/apis/v1", "Coda documents"),
    ("Obsidian", "local", None, None, "Obsidian notes (local)"),
    ("Roam Research", "storage", "ROAM_API_KEY", "https://api.roamresearch.com", "Roam networked notes"),
    ("RemNote", "storage", "REMNOTE_API_KEY", "https://api.remnote.com", "RemNote spaced repetition"),
    ("Bear", "storage", "BEAR_API_KEY", "https://bear-app.com/api", "Bear notes"),
]

COMMUNICATION = [
    ("Microsoft Outlook", "api", "OUTLOOK_API_KEY", "https://outlook.office.com/api/v2.0", "Outlook email/calendar"),
    ("Google Calendar", "api", "GOOGLE_CALENDAR_API_KEY", "https://www.googleapis.com/calendar/v3", "Google Calendar"),
    ("Apple Calendar", "local", None, None, "macOS Calendar via CalDAV"),
    ("Calendly", "api", "CALENDLY_API_KEY", "https://api.calendly.com", "Calendly scheduling"),
    ("Cal.com", "api", "CAL_API_KEY", "https://api.cal.com/v1", "Cal.com scheduling"),
]

CLOUD_STORAGE = [
    ("Box", "storage", "BOX_ACCESS_TOKEN", "https://api.box.com/2.0", "Box cloud storage"),
    ("pCloud", "storage", "PCLOUD_API_KEY", "https://api.pcloud.com", "pCloud storage"),
    ("MEGA", "storage", "MEGA_API_KEY", "https://g.api.mega.co.nz", "MEGA cloud"),
    ("Tresorit", "storage", "TRESORIT_API_KEY", "https://api.tresorit.com", "Secure cloud storage"),
]

DATABASES = [
    ("MongoDB", "storage", "MONGODB_URI", "mongodb://localhost:27017", "MongoDB database"),
    ("PostgreSQL", "storage", "POSTGRES_URI", "postgresql://localhost:5432", "PostgreSQL database"),
    ("MySQL", "storage", "MYSQL_URI", "mysql://localhost:3306", "MySQL database"),
    ("Redis", "storage", "REDIS_URI", "redis://localhost:6379", "Redis cache"),
    ("Elasticsearch", "storage", "ELASTICSEARCH_URL", "http://localhost:9200", "Elasticsearch search"),
    ("Supabase", "storage", "SUPABASE_KEY", "https://your-project.supabase.co", "Supabase backend"),
    ("Firebase", "storage", "FIREBASE_API_KEY", "https://your-project.firebaseio.com", "Firebase realtime DB"),
]

ANALYTICS = [
    ("Google Analytics", "api", "GA_API_KEY", "https://analyticsreporting.googleapis.com/v4", "Google Analytics"),
    ("Mixpanel", "api", "MIXPANEL_TOKEN", "https://api.mixpanel.com", "Mixpanel analytics"),
    ("Amplitude", "api", "AMPLITUDE_API_KEY", "https://api2.amplitude.com", "Amplitude analytics"),
    ("Segment", "api", "SEGMENT_WRITE_KEY", "https://api.segment.io/v1", "Segment CDP"),
    ("PostHog", "api", "POSTHOG_API_KEY", "https://app.posthog.com", "PostHog product analytics"),
    ("Plausible", "api", "PLAUSIBLE_API_KEY", "https://plausible.io/api/v1", "Privacy-friendly analytics"),
]

MONITORING = [
    ("Datadog", "api", "DATADOG_API_KEY", "https://api.datadoghq.com/api/v1", "Datadog monitoring"),
    ("New Relic", "api", "NEW_RELIC_API_KEY", "https://api.newrelic.com/v2", "New Relic APM"),
    ("Sentry", "api", "SENTRY_DSN", "https://sentry.io/api/0", "Sentry error tracking"),
    ("PagerDuty", "api", "PAGERDUTY_API_KEY", "https://api.pagerduty.com", "PagerDuty incident management"),
    ("Grafana", "api", "GRAFANA_API_KEY", "http://localhost:3000/api", "Grafana dashboards"),
    ("Prometheus", "api", None, "http://localhost:9090", "Prometheus metrics"),
]

PAYMENT = [
    ("Stripe", "api", "STRIPE_API_KEY", "https://api.stripe.com/v1", "Stripe payments"),
    ("PayPal", "api", "PAYPAL_CLIENT_ID", "https://api.paypal.com/v1", "PayPal payments"),
    ("Square", "api", "SQUARE_ACCESS_TOKEN", "https://connect.squareup.com/v2", "Square payments"),
    ("Braintree", "api", "BRAINTREE_PUBLIC_KEY", "https://api.braintreegateway.com", "Braintree payments"),
]

CRM = [
    ("Salesforce", "storage", "SALESFORCE_ACCESS_TOKEN", "https://your-instance.salesforce.com/services/data/v57.0", "Salesforce CRM"),
    ("HubSpot", "storage", "HUBSPOT_API_KEY", "https://api.hubapi.com", "HubSpot CRM"),
    ("Pipedrive", "storage", "PIPEDRIVE_API_KEY", "https://api.pipedrive.com/v1", "Pipedrive CRM"),
    ("Zoho CRM", "storage", "ZOHO_API_KEY", "https://www.zohoapis.com/crm/v3", "Zoho CRM"),
    ("Copper", "storage", "COPPER_API_KEY", "https://api.copper.com/developer_api/v1", "Copper CRM"),
]

UTILITIES = [
    ("Base64 Encoder", "utility", None, None, "Base64 encoding/decoding"),
    ("Hash Generator", "utility", None, None, "MD5/SHA hash generation"),
    ("UUID Generator", "utility", None, None, "UUID generation"),
    ("Timestamp Converter", "utility", None, None, "Unix timestamp conversion"),
    ("Color Converter", "utility", None, None, "RGB/HEX/HSL conversion"),
    ("Regex Tester", "utility", None, None, "Regular expression testing"),
    ("Markdown Preview", "utility", None, None, "Markdown to HTML"),
    ("YAML Parser", "utility", None, None, "YAML validation and parsing"),
    ("XML Parser", "utility", None, None, "XML validation and parsing"),
    ("CSV Parser", "utility", None, None, "CSV parsing and conversion"),
]

def generate_batch(category_name, plugins, template_type_override=None):
    """Generate a batch of plugins"""
    print(f"\n{'='*60}")
    print(f"Generating {category_name} ({len(plugins)} plugins)")
    print(f"{'='*60}")
    
    count = 0
    for plugin_def in plugins:
        try:
            if len(plugin_def) == 5:
                name, template, key, url, desc = plugin_def
            elif len(plugin_def) == 4:
                name, template, key, desc = plugin_def
                url = None
            else:
                name, template, desc = plugin_def
                key = url = None
            
            # Build kwargs
            kwargs = {"DESCRIPTION": desc} if desc else {}
            if key:
                kwargs["API_KEY_ENV_VAR"] = key
            if url:
                kwargs["API_BASE_URL"] = url
            
            # Use override if provided
            template = template_type_override or template
            
            generate_plugin(template, name, **kwargs)
            count += 1
            if count % 10 == 0:
                print(f"  Progress: {count}/{len(plugins)}")
        except Exception as e:
            print(f"  WARNING: Error generating {name}: {e}")
    
    print(f"COMPLETE: {category_name}: {count}/{len(plugins)} completed\n")
    return count

def main():
    print("\n" + "="*60)
    print("BATCH PLUGIN GENERATOR - FULL ROADMAP")
    print("="*60)
    
    total = 0
    
    # Generate all categories
    total += generate_batch("AI Providers", AI_PROVIDERS)
    total += generate_batch("Local AI Platforms", LOCAL_AI)
    total += generate_batch("Code Assistants", CODE_ASSISTANTS)
    total += generate_batch("Productivity Tools", PRODUCTIVITY)
    total += generate_batch("Communication", COMMUNICATION)
    total += generate_batch("Cloud Storage", CLOUD_STORAGE)
    total += generate_batch("Databases", DATABASES)
    total += generate_batch("Analytics", ANALYTICS)
    total += generate_batch("Monitoring", MONITORING)
    total += generate_batch("Payment Processing", PAYMENT)
    total += generate_batch("CRM Systems", CRM)
    total += generate_batch("Utilities", UTILITIES)
    
    print("\n" + "="*60)
    print(f"BATCH GENERATION COMPLETE!")
    print(f"Total plugins generated: {total}")
    print("="*60)

if __name__ == "__main__":
    main()
