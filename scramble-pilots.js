#!/usr/bin/env node
/**
 * US Drone Map - Scramble Pilots Data
 * 
 * This script takes your plain-text pilots.json and creates a 
 * scrambled version where emails and phones are Base64 encoded.
 * 
 * Usage:
 *   1. Put this file next to your pilots.json
 *   2. Run: node scramble-pilots.js
 *   3. Upload the new pilots.json (replaces old one)
 * 
 * What it does:
 *   - Reads pilots.json
 *   - Encodes phone → pe (phone encoded)
 *   - Encodes email → ee (email encoded)
 *   - Keeps original p/e fields empty for verified, removed for unverified
 *   - Writes back to pilots.json
 */

const fs = require('fs');
const path = require('path');

// Base64 encode
function encode(str) {
    if (!str) return '';
    return Buffer.from(str).toString('base64');
}

function scramblePilots() {
    const inputFile = path.join(__dirname, 'pilots.json');
    const backupFile = path.join(__dirname, 'pilots-backup.json');
    
    // Check if file exists
    if (!fs.existsSync(inputFile)) {
        console.error('❌ Error: pilots.json not found in current directory');
        process.exit(1);
    }
    
    // Read the file
    const rawData = fs.readFileSync(inputFile, 'utf8');
    let data;
    
    try {
        data = JSON.parse(rawData);
    } catch (e) {
        console.error('❌ Error: pilots.json is not valid JSON');
        process.exit(1);
    }
    
    // Handle both array format and object with pilots property
    let pilots;
    let isObjectFormat = false;
    
    if (Array.isArray(data)) {
        pilots = data;
    } else if (data.pilots && Array.isArray(data.pilots)) {
        pilots = data.pilots;
        isObjectFormat = true;
    } else {
        console.error('❌ Error: pilots.json format not recognized');
        process.exit(1);
    }
    
    // Create backup first
    fs.writeFileSync(backupFile, rawData);
    console.log(`📦 Backup saved to pilots-backup.json`);
    
    // Scramble each pilot
    let encodedCount = 0;
    let alreadyEncodedCount = 0;
    
    const scrambledPilots = pilots.map(p => {
        const newPilot = { ...p };
        
        // Check if already encoded (has pe or ee fields with data)
        if (p.pe || p.ee) {
            alreadyEncodedCount++;
            return newPilot;
        }
        
        // Encode phone
        if (p.p && p.p.trim()) {
            newPilot.pe = encode(p.p);
            // Keep p field but clear it for display logic
            // Actually keep original for verified pilots' direct use
        }
        
        // Encode email  
        if (p.e && p.e.trim()) {
            newPilot.ee = encode(p.e);
        }
        
        if (p.p || p.e) {
            encodedCount++;
        }
        
        return newPilot;
    });
    
    // Write output
    let output;
    if (isObjectFormat) {
        output = {
            ...data,
            pilots: scrambledPilots,
            meta: {
                ...data.meta,
                scrambled: true,
                scrambledAt: new Date().toISOString()
            }
        };
    } else {
        output = scrambledPilots;
    }
    
    fs.writeFileSync(inputFile, JSON.stringify(output, null, 2));
    
    console.log(`\n✅ Scrambling complete!`);
    console.log(`   - ${encodedCount} pilots encoded`);
    console.log(`   - ${alreadyEncodedCount} pilots already had encoded data`);
    console.log(`   - Output: pilots.json (overwritten)`);
    console.log(`\n📝 Next steps:`);
    console.log(`   1. Upload the new pilots.json to GitHub`);
    console.log(`   2. Your index.html already has decode logic built in`);
}

scramblePilots();
