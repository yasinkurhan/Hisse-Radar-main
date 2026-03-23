const fs = require('fs');
const path = require('path');

const patterns = {
  'Ä±': 'ı',
  'Ä°': 'İ',
  'Ã§': 'ç',
  'Ã‡': 'Ç',
  'ÅŸ': 'ş',
  'Åž': 'Ş',
  'Ã¶': 'ö',
  'Ã–': 'Ö',
  'Ã¼': 'ü',
  'Ãœ': 'Ü',
  'ÄŸ': 'ğ',
  'Äž': 'Ğ',
  'ğŸ“¡': '📡',
  'ğŸš€': '🚀',
  'ğŸ’¼': '💼',
  'Ã¦': 'æ',
  'Ã¢': 'â'
};

function fixEncoding(filePath) {
  if (!fs.existsSync(filePath)) return;
  let content = fs.readFileSync(filePath, 'utf8');
  let original = content;
  
  for (const [bad, good] of Object.entries(patterns)) {
    content = content.split(bad).join(good);
  }
  
  if (content !== original) {
    fs.writeFileSync(filePath, content, 'utf8');
    console.log('Fixed:', filePath);
  }
}

function walk(dir) {
  if (!fs.existsSync(dir)) return;
  const files = fs.readdirSync(dir);
  for (const file of files) {
    const fullPath = path.join(dir, file);
    if (fs.statSync(fullPath).isDirectory()) {
      if (file !== 'node_modules' && file !== '.next') {
        walk(fullPath);
      }
    } else if (fullPath.endsWith('.tsx') || fullPath.endsWith('.ts')) {
      fixEncoding(fullPath);
    }
  }
}

walk('frontend/src');
