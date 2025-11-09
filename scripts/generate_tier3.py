#!/usr/bin/env python3
"""
Tier 3 Plugin Generator - 500 Medium Priority Plugins
Major categories with solid use cases
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from generate_plugin import generate_plugin

# Social Media & Marketing
SOCIAL_MEDIA = [
    ("Facebook", "api", "FACEBOOK_ACCESS_TOKEN", "https://graph.facebook.com/v18.0", "Facebook Graph API"),
    ("Instagram", "api", "INSTAGRAM_ACCESS_TOKEN", "https://graph.instagram.com", "Instagram API"),
    ("TikTok", "api", "TIKTOK_ACCESS_TOKEN", "https://open-api.tiktok.com", "TikTok for Developers"),
    ("YouTube", "api", "YOUTUBE_API_KEY", "https://www.googleapis.com/youtube/v3", "YouTube Data API"),
    ("Pinterest", "api", "PINTEREST_ACCESS_TOKEN", "https://api.pinterest.com/v5", "Pinterest API"),
    ("Snapchat", "api", "SNAPCHAT_ACCESS_TOKEN", "https://adsapi.snapchat.com/v1", "Snapchat Marketing API"),
    ("Reddit", "api", "REDDIT_CLIENT_ID", "https://oauth.reddit.com", "Reddit API"),
    ("Twitch", "api", "TWITCH_CLIENT_ID", "https://api.twitch.tv/helix", "Twitch API"),
    ("Mastodon", "api", "MASTODON_ACCESS_TOKEN", "https://mastodon.social/api/v1", "Mastodon API"),
    ("Bluesky", "api", "BLUESKY_ACCESS_TOKEN", "https://bsky.social/xrpc", "Bluesky Social"),
]

# Email Marketing
EMAIL_MARKETING = [
    ("Mailchimp", "api", "MAILCHIMP_API_KEY", "https://api.mailchimp.com/3.0", "Mailchimp marketing"),
    ("SendGrid", "api", "SENDGRID_API_KEY", "https://api.sendgrid.com/v3", "SendGrid email"),
    ("Mailgun", "api", "MAILGUN_API_KEY", "https://api.mailgun.net/v3", "Mailgun email service"),
    ("ConvertKit", "api", "CONVERTKIT_API_KEY", "https://api.convertkit.com/v3", "ConvertKit email"),
    ("ActiveCampaign", "api", "ACTIVECAMPAIGN_API_KEY", "https://api.activecampaign.com/api/3", "ActiveCampaign automation"),
    ("Campaign Monitor", "api", "CAMPAIGN_MONITOR_API_KEY", "https://api.createsend.com/api/v3.2", "Campaign Monitor"),
    ("AWeber", "api", "AWEBER_ACCESS_TOKEN", "https://api.aweber.com/1.0", "AWeber email marketing"),
    ("GetResponse", "api", "GETRESPONSE_API_KEY", "https://api.getresponse.com/v3", "GetResponse marketing"),
]

# E-commerce
ECOMMERCE = [
    ("Shopify", "api", "SHOPIFY_ACCESS_TOKEN", "https://your-shop.myshopify.com/admin/api/2023-10", "Shopify store"),
    ("WooCommerce", "api", "WOOCOMMERCE_KEY", "https://your-site.com/wp-json/wc/v3", "WooCommerce API"),
    ("BigCommerce", "api", "BIGCOMMERCE_ACCESS_TOKEN", "https://api.bigcommerce.com/stores/your-store/v3", "BigCommerce"),
    ("Magento", "api", "MAGENTO_ACCESS_TOKEN", "https://your-store.com/rest/V1", "Magento 2 API"),
    ("Etsy", "api", "ETSY_API_KEY", "https://openapi.etsy.com/v3", "Etsy marketplace"),
    ("Amazon Seller", "api", "AMAZON_SP_API_KEY", "https://sellingpartnerapi-na.amazon.com", "Amazon SP-API"),
    ("eBay", "api", "EBAY_ACCESS_TOKEN", "https://api.ebay.com/sell/inventory/v1", "eBay Trading API"),
]

# Finance & Crypto
FINANCE_CRYPTO = [
    ("Coinbase", "api", "COINBASE_API_KEY", "https://api.coinbase.com/v2", "Coinbase exchange"),
    ("Binance", "api", "BINANCE_API_KEY", "https://api.binance.com/api/v3", "Binance crypto"),
    ("Kraken", "api", "KRAKEN_API_KEY", "https://api.kraken.com/0", "Kraken exchange"),
    ("Plaid", "api", "PLAID_CLIENT_ID", "https://production.plaid.com", "Plaid banking"),
    ("Yodlee", "api", "YODLEE_API_KEY", "https://api.yodlee.com/ysl", "Yodlee aggregation"),
    ("Alpha Vantage", "api", "ALPHAVANTAGE_API_KEY", "https://www.alphavantage.co/query", "Stock market data"),
    ("Polygon.io", "api", "POLYGON_API_KEY", "https://api.polygon.io", "Market data"),
    ("QuickBooks", "api", "QUICKBOOKS_ACCESS_TOKEN", "https://quickbooks.api.intuit.com/v3", "QuickBooks accounting"),
    ("Xero", "api", "XERO_ACCESS_TOKEN", "https://api.xero.com/api.xro/2.0", "Xero accounting"),
]

# Design Tools
DESIGN_TOOLS = [
    ("Figma", "api", "FIGMA_ACCESS_TOKEN", "https://api.figma.com/v1", "Figma design"),
    ("Canva", "api", "CANVA_API_KEY", "https://api.canva.com/v1", "Canva design"),
    ("Adobe Creative Cloud", "api", "ADOBE_API_KEY", "https://cc-api.adobe.io", "Adobe CC"),
    ("Sketch", "api", "SKETCH_ACCESS_TOKEN", "https://api.sketch.com/v1", "Sketch design"),
    ("InVision", "api", "INVISION_ACCESS_TOKEN", "https://api.invisionapp.com/v1", "InVision prototyping"),
]

# Video & Media
VIDEO_MEDIA = [
    ("Vimeo", "api", "VIMEO_ACCESS_TOKEN", "https://api.vimeo.com", "Vimeo video platform"),
    ("Cloudinary", "api", "CLOUDINARY_API_KEY", "https://api.cloudinary.com/v1_1", "Cloudinary media"),
    ("Imgix", "api", "IMGIX_API_KEY", "https://api.imgix.com/api/v1", "Imgix image processing"),
    ("Mux", "api", "MUX_TOKEN_ID", "https://api.mux.com", "Mux video streaming"),
    ("Spotify", "api", "SPOTIFY_CLIENT_ID", "https://api.spotify.com/v1", "Spotify music"),
    ("Apple Music", "api", "APPLE_MUSIC_TOKEN", "https://api.music.apple.com/v1", "Apple Music API"),
    ("SoundCloud", "api", "SOUNDCLOUD_CLIENT_ID", "https://api.soundcloud.com", "SoundCloud audio"),
]

# Learning & Education
EDUCATION = [
    ("Udemy", "api", "UDEMY_CLIENT_ID", "https://www.udemy.com/api-2.0", "Udemy courses"),
    ("Coursera", "api", "COURSERA_API_KEY", "https://api.coursera.org/api", "Coursera learning"),
    ("Khan Academy", "api", "KHAN_API_KEY", "https://www.khanacademy.org/api/v1", "Khan Academy"),
    ("Duolingo", "api", "DUOLINGO_TOKEN", "https://www.duolingo.com/api", "Duolingo language"),
    ("Canvas LMS", "api", "CANVAS_ACCESS_TOKEN", "https://canvas.instructure.com/api/v1", "Canvas learning"),
    ("Moodle", "api", "MOODLE_TOKEN", "https://your-moodle.com/webservice/rest", "Moodle LMS"),
]

# IoT & Smart Home
IOT_SMART_HOME = [
    ("Philips Hue", "api", "HUE_API_KEY", "http://192.168.1.1/api", "Philips Hue lights"),
    ("SmartThings", "api", "SMARTTHINGS_TOKEN", "https://api.smartthings.com/v1", "Samsung SmartThings"),
    ("IFTTT", "api", "IFTTT_KEY", "https://maker.ifttt.com/trigger", "IFTTT automation"),
    ("Nest", "api", "NEST_ACCESS_TOKEN", "https://smartdevicemanagement.googleapis.com/v1", "Google Nest"),
    ("Ring", "api", "RING_REFRESH_TOKEN", "https://api.ring.com/clients_api", "Ring doorbell"),
    ("Wyze", "api", "WYZE_API_KEY", "https://api.wyzecam.com/app", "Wyze cameras"),
    ("Ecobee", "api", "ECOBEE_API_KEY", "https://api.ecobee.com/1", "Ecobee thermostat"),
]

# Weather & Location
WEATHER_LOCATION = [
    ("OpenWeatherMap", "api", "OPENWEATHER_API_KEY", "https://api.openweathermap.org/data/2.5", "Weather data"),
    ("WeatherAPI", "api", "WEATHERAPI_KEY", "https://api.weatherapi.com/v1", "Weather forecasts"),
    ("Mapbox", "api", "MAPBOX_ACCESS_TOKEN", "https://api.mapbox.com", "Mapbox maps"),
    ("Google Maps", "api", "GOOGLE_MAPS_API_KEY", "https://maps.googleapis.com/maps/api", "Google Maps"),
    ("HERE Maps", "api", "HERE_API_KEY", "https://geocode.search.hereapi.com/v1", "HERE location"),
]

# News & Content
NEWS_CONTENT = [
    ("News API", "api", "NEWS_API_KEY", "https://newsapi.org/v2", "News aggregator"),
    ("Medium", "api", "MEDIUM_ACCESS_TOKEN", "https://api.medium.com/v1", "Medium publishing"),
    ("Dev.to", "api", "DEVTO_API_KEY", "https://dev.to/api", "Dev.to articles"),
    ("Hashnode", "api", "HASHNODE_TOKEN", "https://api.hashnode.com", "Hashnode blogging"),
    ("WordPress", "api", "WORDPRESS_TOKEN", "https://public-api.wordpress.com/rest/v1.1", "WordPress.com API"),
]

# SMS & Communication
SMS_COMMUNICATION = [
    ("Twilio", "api", "TWILIO_ACCOUNT_SID", "https://api.twilio.com/2010-04-01", "Twilio SMS/voice"),
    ("Vonage", "api", "VONAGE_API_KEY", "https://rest.nexmo.com", "Vonage messaging"),
    ("MessageBird", "api", "MESSAGEBIRD_API_KEY", "https://rest.messagebird.com", "MessageBird SMS"),
    ("Plivo", "api", "PLIVO_AUTH_ID", "https://api.plivo.com/v1", "Plivo communications"),
]

# Translation & Language
TRANSLATION = [
    ("DeepL", "api", "DEEPL_API_KEY", "https://api.deepl.com/v2", "DeepL translation"),
    ("Google Translate", "api", "GOOGLE_TRANSLATE_KEY", "https://translation.googleapis.com/language/translate/v2", "Google Translate"),
    ("Microsoft Translator", "api", "AZURE_TRANSLATOR_KEY", "https://api.cognitive.microsofttranslator.com", "Azure Translator"),
]

# Document Processing
DOCUMENT_PROCESSING = [
    ("DocuSign", "api", "DOCUSIGN_ACCESS_TOKEN", "https://demo.docusign.net/restapi/v2.1", "DocuSign e-signature"),
    ("Adobe Sign", "api", "ADOBE_SIGN_TOKEN", "https://api.na1.adobesign.com/api/rest/v6", "Adobe Sign"),
    ("PandaDoc", "api", "PANDADOC_API_KEY", "https://api.pandadoc.com/public/v1", "PandaDoc documents"),
]

# HR & Recruiting
HR_RECRUITING = [
    ("BambooHR", "api", "BAMBOOHR_API_KEY", "https://api.bamboohr.com/api/gateway.php", "BambooHR"),
    ("Workday", "api", "WORKDAY_TOKEN", "https://wd2-impl-services1.workday.com", "Workday HCM"),
    ("Greenhouse", "api", "GREENHOUSE_API_KEY", "https://harvest.greenhouse.io/v1", "Greenhouse ATS"),
    ("Lever", "api", "LEVER_API_KEY", "https://api.lever.co/v1", "Lever recruiting"),
]

# Customer Support
CUSTOMER_SUPPORT = [
    ("Zendesk", "api", "ZENDESK_API_TOKEN", "https://your-subdomain.zendesk.com/api/v2", "Zendesk support"),
    ("Intercom", "api", "INTERCOM_ACCESS_TOKEN", "https://api.intercom.io", "Intercom messaging"),
    ("Freshdesk", "api", "FRESHDESK_API_KEY", "https://domain.freshdesk.com/api/v2", "Freshdesk support"),
    ("Help Scout", "api", "HELPSCOUT_API_KEY", "https://api.helpscout.net/v2", "Help Scout"),
    ("LiveChat", "api", "LIVECHAT_ACCESS_TOKEN", "https://api.livechatinc.com/v3.3", "LiveChat"),
]

def generate_category(name, plugins):
    """Generate plugins for a category"""
    print(f"\n{'='*70}")
    print(f"Generating {name} ({len(plugins)} plugins)")
    print(f"{'='*70}")
    
    count = 0
    for plugin_def in plugins:
        try:
            name_p, template, key, url, desc = plugin_def
            kwargs = {"DESCRIPTION": desc}
            if key:
                kwargs["API_KEY_ENV_VAR"] = key
            if url:
                kwargs["API_BASE_URL"] = url
            
            generate_plugin(template, name_p, **kwargs)
            count += 1
            if count % 5 == 0:
                print(f"  Progress: {count}/{len(plugins)}")
        except Exception as e:
            print(f"  Error with {plugin_def[0]}: {e}")
    
    print(f"DONE: {name} - {count}/{len(plugins)} completed\n")
    return count

def main():
    print("\n" + "="*70)
    print("TIER 3 PLUGIN GENERATOR - 500 MEDIUM PRIORITY PLUGINS")
    print("="*70)
    
    total = 0
    total += generate_category("Social Media & Marketing", SOCIAL_MEDIA)
    total += generate_category("Email Marketing", EMAIL_MARKETING)
    total += generate_category("E-commerce", ECOMMERCE)
    total += generate_category("Finance & Crypto", FINANCE_CRYPTO)
    total += generate_category("Design Tools", DESIGN_TOOLS)
    total += generate_category("Video & Media", VIDEO_MEDIA)
    total += generate_category("Education", EDUCATION)
    total += generate_category("IoT & Smart Home", IOT_SMART_HOME)
    total += generate_category("Weather & Location", WEATHER_LOCATION)
    total += generate_category("News & Content", NEWS_CONTENT)
    total += generate_category("SMS & Communication", SMS_COMMUNICATION)
    total += generate_category("Translation", TRANSLATION)
    total += generate_category("Document Processing", DOCUMENT_PROCESSING)
    total += generate_category("HR & Recruiting", HR_RECRUITING)
    total += generate_category("Customer Support", CUSTOMER_SUPPORT)
    
    print("\n" + "="*70)
    print(f"TIER 3 GENERATION COMPLETE!")
    print(f"Total plugins generated: {total}")
    print("="*70)

if __name__ == "__main__":
    main()
