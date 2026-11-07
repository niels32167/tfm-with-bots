import { playersAreBuying } from "../cards/BuyingPanel";
import { useCardsById } from "../cards/catalog";
import { signed } from "../format";
import { controllerLabel, isYou, PLAYER_COLOURS, playerTitle } from "../players";
import { type Card, type CountedTag, type DraftPass, type PlayerBoard, RESOURCES, type Resource, TAGS } from "../types";
import type { GameUpdate } from "../useGameServer";

export const RESOURCE_NAMES: Record<Resource, string> = {
  megacredits: "MegaCredits",
  steel: "Steel",
  titanium: "Titanium",
  plants: "Plants",
  energy: "Energy",
  heat: "Heat",
};

// As the game log names each Production: "MegaCredit Production", "plant Production".
const PRODUCTION_NAMES: Record<Resource, string> = {
  megacredits: "MegaCredit Production",
  steel: "steel Production",
  titanium: "titanium Production",
  plants: "plant Production",
  energy: "energy Production",
  heat: "heat Production",
};

// The Tags a player board counts: every Tag but the Event Tag, which never counts once played, and,
// so far, the wild Tag.
const COUNTED_TAGS = TAGS.filter((tag): tag is CountedTag => tag !== "event" && tag !== "wild");

interface Props {
  game: GameUpdate;
  /** The card catalog. */
  cards: Card[];
}

/** One board per Player, as on Board Game Arena: Terraform Rating, Hand size, the first-player marker
 * and Turn state, their Corporation and its ability, each Resource over its Production, the Tags in
 * play, and the cards they passed in the Draft where the view shows them. */
export function PlayerBoards({ game, cards }: Props) {
  const { view } = game;
  const catalog = useCardsById(cards);
  return (
    <section className="player-boards" aria-label="Player boards">
      {view.players.map((board, index) => {
        const isCurrent = view.current_player === index;
        return (
          <article key={index} className={`player-board ${isCurrent ? "current" : ""}`}>
            <header className="player-board-header">
              <span className="player-name" style={{ color: PLAYER_COLOURS[index] }}>
                {board.name}
              </span>
              <span className="player-controller">
                {isYou(game, index) ? "You" : controllerLabel(game, index)}
              </span>
              {isCurrent && <span className="badge turn">{turnBadge(game)}</span>}
              {board.passed && view.phase === "action" && <span className="badge passed">Passed</span>}
            </header>
            <div className="player-tokens">
              <TerraformRating value={board.terraform_rating} />
              <span className="hand-size" title="Cards in hand">
                <img src="/card-list/images/resources/card.png" alt="Cards in hand" />
                {board.hand_size}
              </span>
              {view.first_player === index && (
                <span className="first-player-token" title="First player: takes the first Turn of this Generation">
                  1
                </span>
              )}
              {board.next_card && (
                <span className="badge next-card" title={`${catalog.get(board.next_card)?.name}: the next card they play this Generation`}>
                  Next card: {nextCardEffect(catalog.get(board.next_card))}
                </span>
              )}
            </div>
            <CorporationLine game={game} player={index} catalog={catalog} />
            <ResourceCells board={board} />
            <TagCounts board={board} />
            {board.passed_in_draft && board.passed_in_draft.length > 0 && (
              <PassedInDraft
                game={game}
                passes={board.passed_in_draft}
                name={(id) => catalog.get(id)?.name ?? id}
              />
            )}
          </article>
        );
      })}
    </section>
  );
}

/** A Player's Terraform Rating, in an orange token. */
export function TerraformRating({ value }: { value: number }) {
  return (
    <span className="terraform-rating" title="Terraform Rating">
      {value}
    </span>
  );
}

const RESOURCE_ICONS: Record<Resource, string> = {
  megacredits: "megacredits/megacredit",
  steel: "resources/steel",
  titanium: "resources/titanium",
  plants: "resources/plant",
  energy: "resources/power",
  heat: "resources/heat",
};

/** The six Resources in a row, each with its icon and count over its Production. */
export function ResourceCells({ board }: { board: PlayerBoard }) {
  return (
    <dl className="resource-cells">
      {RESOURCES.map((resource) => (
        <div
          key={resource}
          className={`resource-cell ${resource}`}
          title={`${RESOURCE_NAMES[resource]} (${PRODUCTION_NAMES[resource]})`}
        >
          <dt>
            <img src={`/card-list/images/${RESOURCE_ICONS[resource]}.png`} alt={RESOURCE_NAMES[resource]} />
          </dt>
          <dd>
            <span className="resource-count">{board.resources[resource]}</span>
            <span className="resource-production">{signed(board.production[resource])}</span>
          </dd>
        </div>
      ))}
    </dl>
  );
}

/** A round counter for each Tag in play. */
export function TagCounts({ board }: { board: PlayerBoard }) {
  return (
    <div className="tag-counts">
      {COUNTED_TAGS.filter((tag) => board.tags[tag] > 0).map((tag) => (
        <span key={tag} className="tag-count" title={`${board.tags[tag]} ${tag} Tags in play`}>
          <img src={`/card-list/images/tags/${tag}.png`} alt={`${tag} Tags`} />
          {board.tags[tag]}
        </span>
      ))}
    </div>
  );
}

/** A revealed Corporation's name, which enlarges the card when pointed at. */
export function CorporationName({ id, catalog }: { id: string | null; catalog: Map<string, Card> }) {
  const corporation = id ? catalog.get(id) : undefined;
  if (!corporation) return null;
  return (
    <span className="corporation-name" tabIndex={0} data-zoom-card={corporation.id}>
      {corporation.name}
    </span>
  );
}

/** What a Corporation's card says it does, without what it starts with: "Effect: When playing an
 * Earth card, you pay 3 MC less for it." */
function corporationAbility(card: Card | undefined): string {
  const [ability] = (card?.text ?? "").split("\n");
  return ability.replace(/^\(|\)$/g, "");
}

interface CorporationLineProps {
  game: GameUpdate;
  player: number;
  catalog: Map<string, Card>;
}

/** A Player's Corporation and its ability, or at setup, that it is hidden. The one they chose shows
 * only to them: the human at the screen, or in the full view, while it is their Decision. Nothing
 * shows in a Game without Corporations, a Replay saved before they existed. */
function CorporationLine({ game, player, catalog }: CorporationLineProps) {
  const { view, viewer, decision } = game;
  const board = view.players[player];
  const dealtCorporations = view.players.some((each) => each.choosing_corporation !== null);
  if (!board.corporation && !dealtCorporations) return null;
  const seesTheirChoice = (viewer ?? decision?.player) === player;
  const picked = seesTheirChoice ? board.choosing_corporation?.picked : null;
  const corporation = catalog.get(board.corporation ?? picked ?? "");
  return (
    <div className="player-corporation">
      {corporation ? (
        <>
          <span className="player-corporation-name" tabIndex={0} data-zoom-card={corporation.id}>
            {corporation.name}
            {!board.corporation && " (hidden for now)"}
          </span>
          <span className="player-corporation-ability">{corporationAbility(corporation)}</span>
        </>
      ) : (
        <span className="player-corporation-name">Corporation hidden until every Player is done buying</span>
      )}
    </div>
  );
}

/** What an Event such as Indentured Workers changes about the next card played: "−8 MegaCredits",
 * "±2 steps on global Requirements". */
function nextCardEffect(card: Card | undefined): string {
  const effect = card?.effects?.next_card as { discount?: number; requirement_steps?: number } | undefined;
  const parts = [
    effect?.discount && `−${effect.discount} MegaCredits`,
    effect?.requirement_steps && `±${effect.requirement_steps} steps on global Requirements`,
  ];
  return parts.filter(Boolean).join(", ");
}

interface PassedInDraftProps {
  game: GameUpdate;
  passes: DraftPass[];
  /** A card's name, by its id. */
  name: (id: string) => string;
}

/** The cards a Player passed on in the Draft this Game, folded away: by Generation, whom they went
 * to and each set passed, latest first. */
function PassedInDraft({ game, passes, name }: PassedInDraftProps) {
  const generations = [...new Set(passes.map((pass) => pass.generation))].reverse();
  const count = passes.reduce((total, pass) => total + pass.cards.length, 0);
  return (
    <details className="passed-in-draft">
      <summary>Passed in the Draft ({count} cards)</summary>
      {generations.map((generation) => {
        const passed = passes.filter((pass) => pass.generation === generation);
        return (
          <div key={generation} className="passed-in-draft-generation">
            <h4>
              Generation {generation}, to {playerTitle(game, passed[0].to)}
            </h4>
            <ul>
              {passed.map((pass, index) => (
                <li key={index}>{pass.cards.map(name).join(", ")}</li>
              ))}
            </ul>
          </div>
        );
      })}
    </details>
  );
}

/** What the current Player is doing: their Turn (and which Action), the Draft, buying cards, playing
 * Prelude Cards, or the final Greenery conversion. */
function turnBadge(game: GameUpdate): string {
  const { view } = game;
  if (view.phase === "final_greenery") return "Final Greeneries";
  if (view.phase === "draft") return "Drafting";
  if (view.phase === "prelude_cards") return "Prelude Cards";
  if (playersAreBuying(view)) return "Buying cards";
  return `Turn${view.actions_this_turn > 0 ? ` · Action ${view.actions_this_turn + 1}` : ""}`;
}
