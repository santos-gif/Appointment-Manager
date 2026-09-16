const fs = require('fs');
const path = require('path');
require('dotenv').config({path:'../../.env', silent:true});

const baseTargetPath = path.join(__dirname, '../src/environments/environment.ts');
const devTargetPath = path.join(__dirname, '../src/environments/environment.development.ts');

const envConfigFile = `export const environment = {
  production: ${process.env.PRODUCTION || 'false'},
  apiUrl: '${process.env.API_URL || ''}'
};
`;

const writeFile = (targetPath) => {
  fs.writeFile(targetPath, envConfigFile, (err) => {
    if (err) {
      console.error(`Error writing environment file to ${targetPath}:`, err);
    } else {
      console.log(`Angular environment file generated successfully at ${targetPath}`);
    }
  });
};

// 3. Generate both files
writeFile(baseTargetPath);
writeFile(devTargetPath);
