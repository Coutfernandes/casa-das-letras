import { useState } from "react";

/** As cores das capas do protótipo, para quando o livro não tem uma imagem. */
const BOOK_COLORS = ["#5B3A29", "#2F4A3A", "#6B2E2A", "#3A4660", "#1F3B4D", "#4A3B5C", "#5C4A2E"];

/** O mesmo título sempre ganha a mesma cor. */
function colorFor(title: string): string {
  let hash = 0;
  for (const char of title) {
    hash = (hash * 31 + char.charCodeAt(0)) % 1_000_003;
  }
  return BOOK_COLORS[hash % BOOK_COLORS.length];
}

const SIZES = {
  card: {
    shape: "h-[206px] w-38 rounded-[2px_5px_5px_2px]",
    spine: "shadow-[inset_6px_0_0_rgb(0_0_0/0.18),var(--shadow)]",
  },
  thumb: {
    shape: "h-15 w-11 rounded-[1px_3px_3px_1px]",
    spine: "shadow-[inset_3px_0_0_rgb(0_0_0/0.2)]",
  },
};

type LotCoverProps = {
  title: string;
  authors: string[];
  coverUrl: string | null;
  size?: keyof typeof SIZES;
};

/**
 * A capa do livro. Se não houver imagem, ou se ela não carregar,
 * mostra um livro desenhado, como no protótipo.
 */
export function LotCover({ title, authors, coverUrl, size = "card" }: LotCoverProps) {
  const [failedUrl, setFailedUrl] = useState<string | null>(null);
  const { shape, spine } = SIZES[size];
  const label = `Capa de ${title}`;

  if (coverUrl && coverUrl !== failedUrl) {
    return (
      <img
        src={coverUrl}
        alt={label}
        loading="lazy"
        onError={() => setFailedUrl(coverUrl)}
        className={`${shape} shrink-0 bg-line object-cover ${size === "card" ? "shadow-card" : ""}`}
      />
    );
  }

  if (size === "thumb") {
    return (
      <div role="img" aria-label={label} style={{ backgroundColor: colorFor(title) }}
        className={`${shape} ${spine} shrink-0`} />
    );
  }

  return (
    <div
      role="img"
      aria-label={label}
      style={{ backgroundColor: colorFor(title) }}
      className={`${shape} ${spine} flex shrink-0 flex-col justify-between py-4.5 pr-3.5 pl-4.5 text-[#F3EFE6]`}
    >
      <span className="line-clamp-5 font-serif text-[17px] leading-tight font-semibold">
        {title}
      </span>
      <span className="line-clamp-2 text-[10.5px] tracking-widest uppercase opacity-90">
        {authors.length > 0 ? authors.join(", ") : "Autor desconhecido"}
      </span>
    </div>
  );
}
