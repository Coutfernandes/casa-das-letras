/** Lugar provisório de uma tela que ainda será construída. */

type ComingSoonProps = {
  title: string;
  part: number;
};

export function ComingSoon({ title, part }: ComingSoonProps) {
  return (
    <section className="space-y-3">
      <h1 className="font-serif text-4xl font-bold">{title}</h1>
      <p className="text-muted">Esta tela será construída na parte {part}.</p>
    </section>
  );
}
