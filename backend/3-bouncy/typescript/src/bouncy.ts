/**
 * Bouncy numbers — TypeScript implementation.
 */

/**
 * Returns true if n is a bouncy number.
 * A number is bouncy if it is neither increasing nor decreasing.
 */
export function isBouncy(n: number): boolean {
  const digits = String(n).split("").map(Number);
  const increasing = digits.every((d, i) => i === 0 || d >= digits[i - 1]);
  const decreasing = digits.every((d, i) => i === 0 || d <= digits[i - 1]);
  return !increasing && !decreasing;
}

/**
 * Returns the least number for which bouncy numbers represent exactly `percent`%.
 * Uses integer arithmetic to avoid floating-point errors:
 *   bouncyCount * 100 === percent * current
 *
 * @throws {Error} If percent is outside the range 1–99.
 */
export function leastNumberWithBouncyRatio(percent: number): number {
  if (percent < 1 || percent > 99) {
    throw new Error(`percent must be between 1 and 99, got ${percent}`);
  }

  let bouncyCount = 0;
  let current = 1;

  while (true) {
    current++;
    if (isBouncy(current)) bouncyCount++;
    if (bouncyCount * 100 === percent * current) return current;
  }
}

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

const args = process.argv.slice(2);

if (args.length === 1) {
  const percent = parseInt(args[0], 10);
  if (isNaN(percent)) {
    console.error("Error: percent must be an integer.");
    process.exit(1);
  }
  try {
    console.log(leastNumberWithBouncyRatio(percent));
  } catch (err) {
    console.error(`Error: ${(err as Error).message}`);
    process.exit(1);
  }
}
