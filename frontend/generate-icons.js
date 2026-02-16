// PWA Icon Generator Script
// Bu script SVG'yi farklı boyutlarda PNG'lere dönüştürür

const fs = require('fs');
const path = require('path');

const sizes = [72, 96, 128, 144, 152, 192, 384, 512];
const iconDir = path.join(__dirname, 'public', 'icons');

// SVG template with dynamic size
function generateSVG(size) {
  const padding = Math.round(size * 0.15);
  const barWidth = Math.round((size - padding * 2) * 0.18);
  const gap = Math.round(barWidth * 0.5);
  const startX = padding;
  
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="0 0 ${size} ${size}">
  <defs>
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#3b82f6" />
      <stop offset="100%" style="stop-color:#1d4ed8" />
    </linearGradient>
  </defs>
  <rect width="${size}" height="${size}" rx="${Math.round(size * 0.2)}" fill="url(#bgGrad)"/>
  <g transform="translate(${padding}, ${padding})">
    <rect x="${startX}" y="${Math.round((size - padding * 2) * 0.55)}" width="${barWidth}" height="${Math.round((size - padding * 2) * 0.35)}" rx="${Math.round(barWidth * 0.15)}" fill="white" opacity="0.9"/>
    <rect x="${startX + barWidth + gap}" y="${Math.round((size - padding * 2) * 0.4)}" width="${barWidth}" height="${Math.round((size - padding * 2) * 0.5)}" rx="${Math.round(barWidth * 0.15)}" fill="white" opacity="0.9"/>
    <rect x="${startX + (barWidth + gap) * 2}" y="${Math.round((size - padding * 2) * 0.2)}" width="${barWidth}" height="${Math.round((size - padding * 2) * 0.7)}" rx="${Math.round(barWidth * 0.15)}" fill="white" opacity="0.9"/>
  </g>
</svg>`;
}

// Create icons directory if not exists
if (!fs.existsSync(iconDir)) {
  fs.mkdirSync(iconDir, { recursive: true });
}

// Generate SVG files for each size
sizes.forEach(size => {
  const svg = generateSVG(size);
  const fileName = `icon-${size}x${size}.svg`;
  fs.writeFileSync(path.join(iconDir, fileName), svg);
  console.log(`Created ${fileName}`);
});

// Create badge icon
const badgeSVG = `<svg xmlns="http://www.w3.org/2000/svg" width="72" height="72" viewBox="0 0 72 72">
  <circle cx="36" cy="36" r="32" fill="#3b82f6"/>
  <text x="36" y="44" font-family="Arial, sans-serif" font-size="28" font-weight="bold" fill="white" text-anchor="middle">H</text>
</svg>`;
fs.writeFileSync(path.join(iconDir, 'badge-72x72.svg'), badgeSVG);
console.log('Created badge-72x72.svg');

// Create shortcut icons
const analysisSVG = `<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96">
  <rect width="96" height="96" rx="19" fill="#3b82f6"/>
  <path d="M24 72 L24 48 L40 32 L56 48 L72 24" stroke="white" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="24" cy="72" r="4" fill="white"/>
  <circle cx="40" cy="32" r="4" fill="white"/>
  <circle cx="56" cy="48" r="4" fill="white"/>
  <circle cx="72" cy="24" r="4" fill="#22c55e"/>
</svg>`;
fs.writeFileSync(path.join(iconDir, 'analysis-icon.svg'), analysisSVG);
console.log('Created analysis-icon.svg');

const portfolioSVG = `<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96">
  <rect width="96" height="96" rx="19" fill="#8b5cf6"/>
  <rect x="20" y="36" width="56" height="40" rx="4" fill="white" opacity="0.9"/>
  <rect x="32" y="28" width="32" height="16" rx="2" fill="white" opacity="0.7"/>
  <line x1="20" y1="52" x2="76" y2="52" stroke="#8b5cf6" stroke-width="2"/>
</svg>`;
fs.writeFileSync(path.join(iconDir, 'portfolio-icon.svg'), portfolioSVG);
console.log('Created portfolio-icon.svg');

const watchlistSVG = `<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 96 96">
  <rect width="96" height="96" rx="19" fill="#f59e0b"/>
  <polygon points="48,20 54,38 74,38 58,50 64,68 48,56 32,68 38,50 22,38 42,38" fill="white"/>
</svg>`;
fs.writeFileSync(path.join(iconDir, 'watchlist-icon.svg'), watchlistSVG);
console.log('Created watchlist-icon.svg');

console.log('\n✅ All icons generated successfully!');
console.log('\n📝 Note: For production, convert these SVG files to PNG using a tool like:');
console.log('   - sharp (Node.js)');
console.log('   - ImageMagick');
console.log('   - Online converter');
console.log('\nFor now, you can use the SVG files directly by updating manifest.json');
