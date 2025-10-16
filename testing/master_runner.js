const fs = require('fs');
const { execSync } = require('child_process');
const path = require('path');

// Path to bots directory (relative to this script)
const botsDir = './bots';

// Scan for bot folders
const botFolders = fs.readdirSync(botsDir).filter(f => 
    fs.statSync(path.join(botsDir, f)).isDirectory()
);

let allResults = [];

for (const bot of botFolders) {
    const botPath = path.join(botsDir, bot);
    const scriptPath = path.join(botPath, 'simulation.js');
    if (fs.existsSync(scriptPath)) {
        console.log(`Running simulation for ${bot}...`);
        // Run simulation script (e.g., node simulation.js local)
        execSync(`node ${scriptPath} ${bot}`, { cwd: botPath, stdio: 'inherit' });

        // Collect results (assuming output file is named results_{instance}_{BOT_NAME}.json)
        const resultsFiles = fs.readdirSync(botPath).filter(file => file.startsWith('results_') && file.endsWith('.json'));
        for (const file of resultsFiles) {
            const filePath = path.join(botPath, file);
            const resultData = JSON.parse(fs.readFileSync(filePath));
            allResults.push({ bot, file, resultData });
        }
    } else {
        console.warn(`No simulation.js found in ${botPath}`);
    }
}

// Save aggregated results
fs.writeFileSync(path.join(botsDir, 'all_bots_results.json'), JSON.stringify(allResults, null, 2));
console.log('All bot results aggregated in bots/all_bots_results.json');
