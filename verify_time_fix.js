// This script can be pasted into the browser console to test the time formatting fix
console.log('🔍 Verifying Time Formatting Fix');

// Test the parseIsoDate function (similar to what's now in the frontend)
const parseIsoDate = (dateStr) => {
  if (!dateStr) return new Date();
  
  // Add Z suffix if missing for proper UTC parsing
  const normalizedDate = dateStr.includes('Z') || dateStr.includes('+') ? dateStr : dateStr + 'Z';
  const date = new Date(normalizedDate);
  return isNaN(date.getTime()) ? new Date() : date;
};

// Test with actual dates from the API
const testDates = [
  '2025-11-13T20:53:03.887904',
  '2025-11-13T20:51:51.514830',
  '2025-11-13T20:47:49.103951'
];

testDates.forEach((dateStr, i) => {
  console.log(`\nTest ${i + 1}: ${dateStr}`);
  
  // Test old parsing method (what was causing the issue)
  const oldDate = new Date(dateStr);
  console.log(`  Old method: ${oldDate}`);
  console.log(`  Old valid: ${!isNaN(oldDate.getTime())}`);
  
  // Test new parsing method
  const newDate = parseIsoDate(dateStr);
  console.log(`  New method: ${newDate}`);
  console.log(`  New valid: ${!isNaN(newDate.getTime())}`);
  
  // Test time difference
  const now = new Date();
  const diffMs = now.getTime() - newDate.getTime();
  console.log(`  Time diff: ${diffMs}ms (${diffMs < 0 ? 'NEGATIVE!' : 'positive'})`);
  
  // Test formatTimeAgo logic
  if (isNaN(diffMs) || diffMs < 0) {
    console.log(`  Would show: Unknown time ❌`);
  } else {
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    
    if (diffMinutes < 60) {
      console.log(`  Would show: ${diffMinutes} minutes ago ✅`);
    } else {
      console.log(`  Would show: ${diffHours} hours ago ✅`);
    }
  }
});

console.log('\n🎉 Time formatting fix verification complete!');