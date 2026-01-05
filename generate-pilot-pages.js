#!/usr/bin/env node
/**
 * US Drone Map - Pilot Page Generator
 * 
 * Generates individual HTML profile pages for each pilot with:
 * - Correct canonical URL (usdronemap.com)
 * - Proper Open Graph tags
 * - JSON-LD LocalBusiness schema
 * - Click-to-reveal contact for unverified
 * 
 * Usage:
 *   1. Put this file next to your pilots.json
 *   2. Run: node generate-pilot-pages.js
 *   3. Upload the /pilots/ folder to GitHub
 */

const fs = require('fs');
const path = require('path');

const DOMAIN = 'https://usdronemap.com';
const OUTPUT_DIR = path.join(__dirname, 'pilots');

// Slug generator
function slugify(text) {
    return (text || '')
        .toLowerCase()
        .replace(/[^\w\s-]/g, '')
        .replace(/\s+/g, '-')
        .replace(/-+/g, '-')
        .trim();
}

// Base64 decode
function decode(str) {
    if (!str) return '';
    try {
        return Buffer.from(str, 'base64').toString('utf8');
    } catch (e) {
        return str;
    }
}

// Format phone number
function formatPhone(phone) {
    if (!phone) return '';
    const digits = phone.replace(/\D/g, '');
    if (digits.length === 10) {
        return `(${digits.slice(0,3)}) ${digits.slice(3,6)}-${digits.slice(6)}`;
    }
    return phone;
}

// Generate HTML for a single pilot
function generatePilotHTML(p) {
    const slug = slugify(`${p.company}-${p.city}-${p.state}`);
    const url = `${DOMAIN}/pilots/${slug}.html`;
    const phone = p.pe ? decode(p.pe) : p.p || '';
    const email = p.ee ? decode(p.ee) : p.e || '';
    const industry = Array.isArray(p.i) ? p.i.join(', ') : (p.i || '');
    
    // JSON-LD Schema
    const schema = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": p.company,
        "description": `Professional drone services${industry ? ' - ' + industry : ''}`,
        "url": url,
        "address": {
            "@type": "PostalAddress",
            "addressLocality": p.city,
            "addressRegion": p.state,
            "addressCountry": "US"
        }
    };
    
    if (p.la && p.lo) {
        schema.geo = {
            "@type": "GeoCoordinates",
            "latitude": p.la,
            "longitude": p.lo
        };
    }
    
    if (p.v && phone) schema.telephone = phone;
    if (p.v && email) schema.email = email;
    if (p.v && p.w) schema.sameAs = p.w.startsWith('http') ? p.w : `https://${p.w}`;
    
    // Contact HTML
    let contactHTML = '';
    if (p.v && (phone || email || p.w)) {
        if (phone) {
            contactHTML += `
                <div class="contact-item">
                    <span class="contact-label">Phone</span>
                    <a href="tel:${phone}" class="contact-value">${formatPhone(phone)}</a>
                </div>`;
        }
        if (email) {
            contactHTML += `
                <div class="contact-item">
                    <span class="contact-label">Email</span>
                    <a href="mailto:${email}" class="contact-value">${email}</a>
                </div>`;
        }
        if (p.w) {
            const website = p.w.startsWith('http') ? p.w : `https://${p.w}`;
            contactHTML += `
                <div class="contact-item">
                    <span class="contact-label">Website</span>
                    <a href="${website}" target="_blank" rel="noopener" class="contact-value">${p.w.replace(/^https?:\/\//, '')}</a>
                </div>`;
        }
    } else {
        contactHTML = `
            <div class="contact-locked">
                <div class="lock-icon">🔒</div>
                <p>Contact information is hidden for unverified listings.</p>
                <a href="${DOMAIN}/verify.html?claim=${slug}&company=${encodeURIComponent(p.company)}" class="claim-btn">Claim This Listing</a>
            </div>`;
    }
    
    // Equipment HTML
    let equipmentHTML = '';
    if (p.mf) equipmentHTML += `<div class="equipment-item"><span class="label">Manufacturer:</span> ${p.mf}</div>`;
    if (p.m) equipmentHTML += `<div class="equipment-item"><span class="label">Model:</span> ${p.m}</div>`;
    if (p.f) equipmentHTML += `<div class="equipment-item"><span class="label">Fleet Size:</span> ${p.f} drone${p.f > 1 ? 's' : ''}</div>`;
    
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${p.company} - Drone Services in ${p.city}, ${p.state} | US Drone Map</title>
    <meta name="description" content="${p.company} provides professional drone services in ${p.city}, ${p.state}.${industry ? ' Specializing in ' + industry + '.' : ''}">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="${url}">
    
    <!-- Open Graph -->
    <meta property="og:type" content="business.business">
    <meta property="og:url" content="${url}">
    <meta property="og:title" content="${p.company} - Drone Services | US Drone Map">
    <meta property="og:description" content="Professional drone services in ${p.city}, ${p.state}">
    <meta property="og:image" content="${DOMAIN}/og-image.png">
    <meta property="og:site_name" content="US Drone Map">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="${p.company} - Drone Services">
    <meta name="twitter:description" content="Professional drone services in ${p.city}, ${p.state}">
    
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    
    <script type="application/ld+json">
${JSON.stringify(schema, null, 4)}
    </script>
    
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Inter', -apple-system, sans-serif;
            background: #f5f5f5;
            color: #1a1a1a;
            line-height: 1.6;
        }
        header {
            background: white;
            border-bottom: 1px solid #e5e5e5;
            padding: 1rem 2rem;
        }
        .header-inner {
            max-width: 900px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .logo {
            font-size: 1.25rem;
            font-weight: 700;
            color: #1a1a1a;
            text-decoration: none;
        }
        .logo span { color: #f97316; }
        nav a {
            color: #666;
            text-decoration: none;
            margin-left: 1.5rem;
            font-size: 0.9rem;
        }
        nav a:hover { color: #f97316; }
        main {
            max-width: 900px;
            margin: 2rem auto;
            padding: 0 1rem;
        }
        .back-link {
            display: inline-block;
            color: #666;
            text-decoration: none;
            margin-bottom: 1.5rem;
            font-size: 0.9rem;
        }
        .back-link:hover { color: #f97316; }
        .profile-card {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .profile-header {
            padding: 2rem;
            border-bottom: 1px solid #e5e5e5;
        }
        .profile-title {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 1rem;
            margin-bottom: 0.5rem;
        }
        .company-name {
            font-size: 1.75rem;
            font-weight: 700;
        }
        .verified-badge {
            background: #f97316;
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .unverified-badge {
            background: #e5e5e5;
            color: #666;
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            font-size: 0.75rem;
        }
        .location {
            color: #666;
            margin-bottom: 1rem;
        }
        .industry-tag {
            display: inline-block;
            background: #fff7ed;
            color: #c2410c;
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            font-size: 0.85rem;
        }
        .profile-body {
            display: grid;
            grid-template-columns: 1fr 1fr;
        }
        .contact-section, .equipment-section {
            padding: 2rem;
        }
        .contact-section {
            border-right: 1px solid #e5e5e5;
        }
        .section-title {
            font-size: 0.75rem;
            font-weight: 600;
            color: #999;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 1rem;
        }
        .contact-item {
            margin-bottom: 1rem;
        }
        .contact-label {
            display: block;
            font-size: 0.75rem;
            color: #999;
            margin-bottom: 0.25rem;
        }
        .contact-value {
            color: #f97316;
            text-decoration: none;
        }
        .contact-value:hover { text-decoration: underline; }
        .contact-locked {
            text-align: center;
            padding: 1rem;
            background: #fafafa;
            border-radius: 8px;
        }
        .lock-icon { font-size: 2rem; margin-bottom: 0.5rem; }
        .contact-locked p { color: #666; font-size: 0.9rem; margin-bottom: 1rem; }
        .claim-btn {
            display: inline-block;
            background: #f97316;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 500;
            font-size: 0.9rem;
        }
        .claim-btn:hover { background: #ea580c; }
        .equipment-item {
            margin-bottom: 0.75rem;
            color: #444;
        }
        .equipment-item .label {
            color: #999;
        }
        footer {
            max-width: 900px;
            margin: 2rem auto;
            padding: 1rem;
            text-align: center;
            color: #999;
            font-size: 0.85rem;
        }
        footer a { color: #666; text-decoration: none; margin: 0 0.5rem; }
        footer a:hover { color: #f97316; }
        @media (max-width: 768px) {
            .profile-body { grid-template-columns: 1fr; }
            .contact-section { border-right: none; border-bottom: 1px solid #e5e5e5; }
            .profile-title { flex-direction: column; }
        }
    </style>
</head>
<body>
    <header>
        <div class="header-inner">
            <a href="${DOMAIN}/" class="logo">US <span>Drone Map</span></a>
            <nav>
                <a href="${DOMAIN}/">Map</a>
                <a href="${DOMAIN}/directory.html">Directory</a>
                <a href="${DOMAIN}/verify.html">Get Verified</a>
            </nav>
        </div>
    </header>
    
    <main>
        <a href="${DOMAIN}/directory.html" class="back-link">← Back to Directory</a>
        
        <div class="profile-card">
            <div class="profile-header">
                <div class="profile-title">
                    <h1 class="company-name">${p.company}</h1>
                    ${p.v ? '<span class="verified-badge">✓ VERIFIED</span>' : '<span class="unverified-badge">Unverified</span>'}
                </div>
                <p class="location">📍 ${p.city}, ${p.state}</p>
                ${industry ? `<span class="industry-tag">${industry}</span>` : ''}
            </div>
            
            <div class="profile-body">
                <div class="contact-section">
                    <div class="section-title">Contact Information</div>
                    ${contactHTML}
                </div>
                <div class="equipment-section">
                    <div class="section-title">Equipment</div>
                    ${equipmentHTML || '<p style="color:#999">No equipment information</p>'}
                </div>
            </div>
        </div>
    </main>
    
    <footer>
        <p>© ${new Date().getFullYear()} US Drone Map</p>
        <p>
            <a href="${DOMAIN}/">Map</a>
            <a href="${DOMAIN}/directory.html">Directory</a>
            <a href="${DOMAIN}/privacy.html">Privacy</a>
            <a href="${DOMAIN}/terms.html">Terms</a>
        </p>
    </footer>
</body>
</html>`;
}

// Main function
function generateAllPages() {
    console.log('🚀 Starting pilot page generation...\n');
    
    // Read pilots.json
    const pilotsFile = path.join(__dirname, 'pilots.json');
    if (!fs.existsSync(pilotsFile)) {
        console.error('❌ Error: pilots.json not found');
        process.exit(1);
    }
    
    const rawData = JSON.parse(fs.readFileSync(pilotsFile, 'utf8'));
    const pilots = Array.isArray(rawData) ? rawData : (rawData.pilots || []);
    
    // Filter out honeypots
    const realPilots = pilots.filter(p => !p._honeypot);
    
    console.log(`📊 Found ${realPilots.length} pilots\n`);
    
    // Create output directory
    if (!fs.existsSync(OUTPUT_DIR)) {
        fs.mkdirSync(OUTPUT_DIR, { recursive: true });
    }
    
    // Generate pages
    let created = 0;
    const slugs = [];
    
    realPilots.forEach(rawPilot => {
        // Normalize field names
        const p = {
            company: rawPilot.c || rawPilot.company || 'Unknown',
            city: rawPilot.ct || rawPilot.city || '',
            state: rawPilot.st || rawPilot.state || '',
            la: rawPilot.la || rawPilot.latitude,
            lo: rawPilot.lo || rawPilot.longitude,
            i: rawPilot.i || rawPilot.industry || '',
            v: rawPilot.v === true || rawPilot.verified === true,
            p: rawPilot.p || rawPilot.phone || '',
            pe: rawPilot.pe || rawPilot.phoneEncoded || '',
            e: rawPilot.e || rawPilot.email || '',
            ee: rawPilot.ee || rawPilot.emailEncoded || '',
            w: rawPilot.w || rawPilot.website || '',
            mf: rawPilot.mf || rawPilot.manufacturer || '',
            m: rawPilot.m || rawPilot.model || '',
            f: rawPilot.f || rawPilot.fleet || ''
        };
        
        const slug = slugify(`${p.company}-${p.city}-${p.state}`);
        
        if (!slug) {
            console.log(`⚠️  Skipping pilot with no slug: ${p.company}`);
            return;
        }
        
        const html = generatePilotHTML(p);
        const filename = `${slug}.html`;
        const filepath = path.join(OUTPUT_DIR, filename);
        
        fs.writeFileSync(filepath, html);
        slugs.push(slug);
        created++;
    });
    
    console.log(`✅ Generated ${created} pilot pages in /pilots/\n`);
    
    // Generate sitemap entries
    const sitemapEntries = slugs.map(slug => 
        `    <url>\n        <loc>${DOMAIN}/pilots/${slug}.html</loc>\n        <changefreq>weekly</changefreq>\n        <priority>0.7</priority>\n    </url>`
    ).join('\n');
    
    const sitemapFile = path.join(__dirname, 'sitemap-pilots.txt');
    fs.writeFileSync(sitemapFile, sitemapEntries);
    console.log(`📝 Sitemap entries saved to sitemap-pilots.txt`);
    console.log(`   Copy these into your sitemap.xml\n`);
    
    console.log('✨ Done!');
    console.log('\n📝 Next steps:');
    console.log('   1. Upload the /pilots/ folder to GitHub');
    console.log('   2. Add sitemap-pilots.txt entries to your sitemap.xml');
}

generateAllPages();
