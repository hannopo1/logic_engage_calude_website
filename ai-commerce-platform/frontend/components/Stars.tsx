"use client";

import { Star } from "lucide-react";
import { useState } from "react";

/**
 * Displays a read-only five-star rating.
 *
 * @param value - The rating used to determine how many stars appear filled.
 * @param size - The width and height of each star icon.
 * @returns A five-star rating visualization.
 */
export function Stars({ value, size = 16 }: { value: number; size?: number }) {
  const full = Math.round(value); // simple rounded display
  return (
    <span className="inline-flex items-center gap-0.5" aria-label={`${value} من 5`}>
      {[1, 2, 3, 4, 5].map((i) => (
        <Star
          key={i}
          style={{ width: size, height: size }}
          className={i <= full ? "fill-brand text-brand" : "fill-none text-line"}
        />
      ))}
    </span>
  );
}

/**
 * Provides an interactive five-star rating selector with hover preview.
 *
 * @param value - The currently selected rating.
 * @param onChange - Called with the selected star value.
 */
export function StarInput({
  value,
  onChange,
}: {
  value: number;
  onChange: (v: number) => void;
}) {
  const [hover, setHover] = useState(0);
  const shown = hover || value;
  return (
    <div className="flex items-center gap-1" role="radiogroup" aria-label="التقييم بالنجوم">
      {[1, 2, 3, 4, 5].map((i) => (
        <button
          key={i}
          type="button"
          role="radio"
          aria-checked={value === i}
          aria-label={`${i} نجوم`}
          onMouseEnter={() => setHover(i)}
          onMouseLeave={() => setHover(0)}
          onClick={() => onChange(i)}
          className="p-1"
        >
          <Star
            className={`h-7 w-7 ${i <= shown ? "fill-brand text-brand" : "fill-none text-line"}`}
          />
        </button>
      ))}
    </div>
  );
}
