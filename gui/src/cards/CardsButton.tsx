/** Opens the card gallery; it sits in the top bar and on the setup screen. */
export function CardsButton({ onClick }: { onClick: () => void }) {
  return (
    <button className="link-button" title="Browse every card" onClick={onClick}>
      Cards
    </button>
  );
}
