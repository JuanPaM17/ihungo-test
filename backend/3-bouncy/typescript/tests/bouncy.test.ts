import { describe, it, expect } from "vitest";
import { isBouncy, leastNumberWithBouncyRatio } from "../src/bouncy";

// ---------------------------------------------------------------------------
// isBouncy
// ---------------------------------------------------------------------------

describe("isBouncy", () => {
  it("returns false for an increasing number (134468)", () => {
    expect(isBouncy(134468)).toBe(false);
  });

  it("returns false for a decreasing number (66420)", () => {
    expect(isBouncy(66420)).toBe(false);
  });

  it("returns true for bouncy example from problem (155349)", () => {
    expect(isBouncy(155349)).toBe(true);
  });

  it("returns false for all numbers below 100", () => {
    for (let n = 1; n < 100; n++) {
      expect(isBouncy(n), `${n} should not be bouncy`).toBe(false);
    }
  });

  it("returns false for numbers with all same digits", () => {
    expect(isBouncy(111)).toBe(false);
    expect(isBouncy(999)).toBe(false);
  });

  it("returns false for 100 (decreasing)", () => {
    expect(isBouncy(100)).toBe(false);
  });

  it("returns true for 101 (first bouncy number)", () => {
    expect(isBouncy(101)).toBe(true);
  });
});

// ---------------------------------------------------------------------------
// leastNumberWithBouncyRatio
// ---------------------------------------------------------------------------

describe("leastNumberWithBouncyRatio", () => {
  it("returns 538 for 50%", () => {
    expect(leastNumberWithBouncyRatio(50)).toBe(538);
  });

  it("returns 21780 for 90%", () => {
    expect(leastNumberWithBouncyRatio(90)).toBe(21780);
  });

  it("returns a positive integer", () => {
    const result = leastNumberWithBouncyRatio(50);
    expect(typeof result).toBe("number");
    expect(result).toBeGreaterThan(0);
  });

  it("throws for 0%", () => {
    expect(() => leastNumberWithBouncyRatio(0)).toThrow();
  });

  it("throws for 100%", () => {
    expect(() => leastNumberWithBouncyRatio(100)).toThrow();
  });

  it("throws for negative values", () => {
    expect(() => leastNumberWithBouncyRatio(-1)).toThrow();
  });

  it("throws for values above 99", () => {
    expect(() => leastNumberWithBouncyRatio(101)).toThrow();
  });
});
