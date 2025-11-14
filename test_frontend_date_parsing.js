// Test script to run in browser console to debug date parsing
console.log('🔍 Testing Frontend Date Parsing');

// Test the actual dates from API
const testDates = [
  '2025-11-13T20:53:03.887904',
  '2025-11-13T20:51:51.514830'
];

testDates.forEach((dateStr, i) => {
  console.log(`\nTest ${i + 1}: ${dateStr}`);
  
  // Test JavaScript Date parsing
  const jsDate = new Date(dateStr);
  console.log(`  new Date(): ${jsDate}`);
  console.log(`  isValid: ${!isNaN(jsDate.getTime())}`);
  console.log(`  getTime(): ${jsDate.getTime()}`);
  
  // Test time ago calculation
  const now = new Date();
  const diffMs = now.getTime() - jsDate.getTime();
  console.log(`  diffMs: ${diffMs}`);
  console.log(`  diffMs < 0: ${diffMs < 0}`);
  
  // Test formatTimeAgo logic
  if (isNaN(diffMs) || diffMs < 0) {
    console.log(`  Would return: Unknown time`);
  } else {
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    console.log(`  diffMinutes: ${diffMinutes}`);
    console.log(`  diffHours: ${diffHours}`);
    console.log(`  diffDays: ${diffDays}`);
    
    let timeString = '';
    if (diffMinutes < 1) {
      timeString = 'Just now';
    } else if (diffMinutes < 60) {
      timeString = `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
      timeString = `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else if (diffDays === 1) {
      timeString = 'Yesterday';
    } else if (diffDays < 7) {
      timeString = `${diffDays} days ago`;
    } else {
      timeString = jsDate.toLocaleDateString();
    }
    
    console.log(`  Would return: ${timeString}`);
  }
});

console.log('\n🔍 Testing messageCount impact');
[0, 1, 5].forEach(count => {
  console.log(`  messageCount=${count}: ${count > 0 ? `${count} messages` : 'Unknown time'}`);
});