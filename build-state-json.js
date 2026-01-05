#!/usr/bin/env node
/**
 * US Drone Map - State-Level JSON Splitter
 * 
 * This script reads pilots.json and creates individual state files:
 * - pilots-tx.json, pilots-ca.json, pilots-wi.json, etc.
 * - Also creates a states-index.json with counts per state
 * 
 * Benefits:
 * - Anti-scraping: Can't grab all data in one request
 * - Performance: Load only the states user is viewing
 * - CDN-friendly: Smaller files cache better
 * 
 * Usage: node build-state-json.js
 */

const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = path.join(__dirname, 'data');

// US State codes for validation
const VALID_STATES = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
];

function buildStateJson() {
    console.log('🚀 Starting state-level JSON build...\n');
    
    // Read main pilots.json
    const pilotsPath = path.join(__dirname, 'pilots.json');
    
    if (!fs.existsSync(pilotsPath)) {
        console.error('❌ Error: pilots.json not found');
        process.exit(1);
    }
    
    const data = JSON.parse(fs.readFileSync(pilotsPath, 'utf8'));
    const pilots = data.pilots || [];
    
    // Filter out honeypots for state files (keep them only in main file)
    const realPilots = pilots.filter(p => !p._honeypot);
    
    console.log(`📊 Found ${realPilots.length} pilots (excluding honeypots)\n`);
    
    // Group pilots by state
    const byState = {};
    const invalidState = [];
    
    realPilots.forEach(pilot => {
        const state = (pilot.st || '').toUpperCase();
        
        if (!VALID_STATES.includes(state)) {
            invalidState.push({ id: pilot.id, company: pilot.c, state: pilot.st });
            return;
        }
        
        if (!byState[state]) {
            byState[state] = [];
        }
        byState[state].push(pilot);
    });
    
    // Warn about invalid states
    if (invalidState.length > 0) {
        console.log('⚠️  Pilots with invalid/missing states:');
        invalidState.forEach(p => {
            console.log(`   - ${p.company} (${p.id}): "${p.state}"`);
        });
        console.log('');
    }
    
    // Create output directory
    if (!fs.existsSync(OUTPUT_DIR)) {
        fs.mkdirSync(OUTPUT_DIR, { recursive: true });
    }
    
    // Generate state files
    const stateIndex = {
        generated: new Date().toISOString(),
        totalPilots: realPilots.length,
        states: {}
    };
    
    Object.keys(byState).sort().forEach(state => {
        const statePilots = byState[state];
        const filename = `pilots-${state.toLowerCase()}.json`;
        const filepath = path.join(OUTPUT_DIR, filename);
        
        // Create state file
        const stateData = {
            state: state,
            count: statePilots.length,
            verified: statePilots.filter(p => p.v).length,
            pilots: statePilots
        };
        
        fs.writeFileSync(filepath, JSON.stringify(stateData, null, 2));
        
        // Add to index
        stateIndex.states[state] = {
            count: statePilots.length,
            verified: statePilots.filter(p => p.v).length,
            file: filename
        };
        
        console.log(`✅ ${state}: ${statePilots.length} pilots → ${filename}`);
    });
    
    // Write state index
    const indexPath = path.join(OUTPUT_DIR, 'states-index.json');
    fs.writeFileSync(indexPath, JSON.stringify(stateIndex, null, 2));
    
    console.log(`\n📁 State index → states-index.json`);
    console.log(`\n✨ Done! Generated ${Object.keys(byState).length} state files in /data/`);
    
    // Summary
    console.log('\n--- Summary ---');
    console.log(`Total pilots: ${realPilots.length}`);
    console.log(`States covered: ${Object.keys(byState).length}`);
    console.log(`Verified pilots: ${realPilots.filter(p => p.v).length}`);
    
    // Top 5 states
    const sorted = Object.entries(byState)
        .sort((a, b) => b[1].length - a[1].length)
        .slice(0, 5);
    
    console.log('\nTop 5 states:');
    sorted.forEach(([state, pilots], i) => {
        console.log(`  ${i + 1}. ${state}: ${pilots.length} pilots`);
    });
}

// Run
buildStateJson();
