/**
 * quoteApi.js
 * Returns random health & wellness quotes from a curated static library.
 * No external API calls — instant, no CORS issues, never fails.
 */

const HEALTH_QUOTES = [
  { content: 'The greatest wealth is health.', author: 'Virgil' },
  { content: 'To keep the body in good health is a duty, otherwise we shall not be able to keep our mind strong and clear.', author: 'Buddha' },
  { content: 'Take care of your body. It\'s the only place you have to live.', author: 'Jim Rohn' },
  { content: 'Health is not valued till sickness comes.', author: 'Thomas Fuller' },
  { content: 'An ounce of prevention is worth a pound of cure.', author: 'Benjamin Franklin' },
  { content: 'A healthy outside starts from the inside.', author: 'Robert Urich' },
  { content: 'The first wealth is health.', author: 'Ralph Waldo Emerson' },
  { content: 'It is health that is real wealth and not pieces of gold and silver.', author: 'Mahatma Gandhi' },
  { content: 'Physical fitness is not only one of the most important keys to a healthy body, it is the basis of dynamic and creative intellectual activity.', author: 'John F. Kennedy' },
  { content: 'Early to bed and early to rise makes a man healthy, wealthy, and wise.', author: 'Benjamin Franklin' },
  { content: 'He who has health has hope, and he who has hope has everything.', author: 'Arabian Proverb' },
  { content: 'The human body is the best picture of the human soul.', author: 'Ludwig Wittgenstein' },
  { content: 'Health is the greatest gift, contentment the greatest wealth, faithfulness the best relationship.', author: 'Buddha' },
  { content: 'A good laugh and a long sleep are the best cures in the doctor\'s book.', author: 'Irish Proverb' },
  { content: 'Let food be thy medicine and medicine be thy food.', author: 'Hippocrates' },
  { content: 'In order to change, we must be sick and tired of being sick and tired.', author: 'Unknown' },
  { content: 'The secret of health for both mind and body is not to mourn for the past, worry about the future, or anticipate troubles, but to live the present moment wisely.', author: 'Buddha' },
  { content: 'Laughter is the best medicine.', author: 'Proverb' },
  { content: 'Walking is the best possible exercise. Habituate yourself to walk very far.', author: 'Thomas Jefferson' },
  { content: 'Your body hears everything your mind says.', author: 'Naomi Judd' },
];

let lastIndex = -1;

/**
 * Returns a random health/motivational quote from the curated list.
 * Avoids repeating the last shown quote.
 * @returns {{ content: string, author: string, tags: string[] }}
 */
export async function fetchHealthQuote() {
  let idx;
  do {
    idx = Math.floor(Math.random() * HEALTH_QUOTES.length);
  } while (idx === lastIndex && HEALTH_QUOTES.length > 1);
  lastIndex = idx;

  const q = HEALTH_QUOTES[idx];
  return { content: q.content, author: q.author, tags: ['health'] };
}
