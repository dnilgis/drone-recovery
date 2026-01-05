#!/usr/bin/env node
/**
 * US Drone Map - Sitemap Generator
 * 
 * This script reads pilots.json and generates a complete sitemap.xml
 * including all pilot profile pages.
 * 
 * Usage: node build-sitemap.js
 */

const fs = require('fs');
const path = require('path');

const DOMAIN = 'https://usdronemap.com';
const TODAY = new Date().toISOString().split('T')[0];

// Main pages with their priorities
const mainPages = [
    { path: '/', changefreq: 'daily', priority: '1.0' },
    { path: '/directory.html', changefreq: 'daily', priority: '0.9' },
    { path: '/privacy.html', changefreq: 'monthly', priority: '0.3' },
    { path: '/terms.html', changefreq: 'monthly', priority: '0.3' }
];

function generateSitemap() {
    // Read pilots.json
    const pilotsPath = path.join(__dirname, 'pilots.json');
    
    if (!fs.existsSync(pilotsPath)) {
        console.error('Error: pilots.json not found');
        process.exit(1);
    }
    
    const data = JSON.parse(fs.readFileSync(pilotsPath, 'utf8'));
    const pilots = data.pilots || [];
    
    // Filter out honeypot entries
    const realPilots = pilots.filter(p => !p._honeypot);
    
    // Start building XML
    let xml = '<?xml version="1.0" encoding="UTF-8"?>\n';
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n';
    
    // Add main pages
    mainPages.forEach(page => {
        xml += '    <url>\n';
        xml += `        <loc>${DOMAIN}${page.path}</loc>\n`;
        xml += `        <lastmod>${TODAY}</lastmod>\n`;
        xml += `        <changefreq>${page.changefreq}</changefreq>\n`;
        xml += `        <priority>${page.priority}</priority>\n`;
        xml += '    </url>\n';
    });
    
    // Add pilot pages
    realPilots.forEach(pilot => {
        const isVerified = pilot.v === true;
        xml += '    <url>\n';
        xml += `        <loc>${DOMAIN}/pilot.html?id=${pilot.id}</loc>\n`;
        xml += `        <lastmod>${TODAY}</lastmod>\n`;
        xml += `        <changefreq>${isVerified ? 'weekly' : 'monthly'}</changefreq>\n`;
        xml += `        <priority>${isVerified ? '0.8' : '0.5'}</priority>\n`;
        xml += '    </url>\n';
    });
    
    xml += '</urlset>\n';
    
    // Write sitemap
    const sitemapPath = path.join(__dirname, 'sitemap.xml');
    fs.writeFileSync(sitemapPath, xml);
    
    console.log(`✅ Sitemap generated: ${sitemapPath}`);
    console.log(`   - ${mainPages.length} main pages`);
    console.log(`   - ${realPilots.length} pilot pages`);
    console.log(`   - ${realPilots.filter(p => p.v).length} verified pilots`);
}

// Run
generateSitemap();
