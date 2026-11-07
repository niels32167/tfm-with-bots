import { useId, useState } from "react";

import { useCardsById } from "../cards/catalog";
import { PLAYER_COLOURS } from "../players";
import {
  cardsWithASpecialTile,
  changePlayer,
  type CardPile,
  putCard,
  placeTile,
  removeTile,
  setCorporation,
  takeOutCard,
  tileFrom,
} from "../scenario";
import { MAX_OXYGEN, MAX_TEMPERATURE, MIN_TEMPERATURE, TEMPERATURE_STEP } from "../tracks";
import {
  type Area,
  type Card,
  RESOURCES,
  type Scenario,
  type ScenarioPlayer,
  type ScenarioTile,
} from "../types";
import { RESOURCE_NAMES } from "./PlayerBoards";

// The Temperature track's steps and the Oxygen track's, as printed.
const TEMPERATURES = Array.from(
  { length: (MAX_TEMPERATURE - MIN_TEMPERATURE) / TEMPERATURE_STEP + 1 },
  (_, step) => MIN_TEMPERATURE + TEMPERATURE_STEP * step,
);
const OXYGEN_LEVELS = Array.from({ length: MAX_OXYGEN + 1 }, (_, step) => step);

/** The Players of a Scenario, as the Options of a select. */
function PlayerOptions({ scenario }: { scenario: Scenario }) {
  return (
    <>
      {scenario.players.map((_, index) => (
        <option key={index} value={index}>
          Player {index + 1}
        </option>
      ))}
    </>
  );
}

interface Props {
  /** The card catalog. */
  cards: Card[];
  edited: Scenario;
  /** The Areas, as printed. */
  board: Area[];
  /** The step the position was read from. */
  readFromStep: number;
  /** Whether it has something under way that a Scenario can't describe. */
  underWay: boolean;
  onChange: (edited: Scenario) => void;
  /** Reads the position shown again, dropping the edits. */
  onRead: () => void;
  onStart: () => void;
}

/** Edits a position as a Scenario, and starts a Game from it in place of the current one. Save Replay
 * then saves it like any Replay, and it can start a scenario test. The engine says if it refuses it. */
export function StateEditor({ cards, edited, board, readFromStep, underWay, onChange, onRead, onStart }: Props) {
  // A Scenario can name only the cards a Game can hold: those of the base box, and with Prelude its
  // Project Cards. Prelude Cards and Prelude's Corporations aren't offered here yet.
  const isProjectCard = (card: Card) => ["automated", "active", "event"].includes(card.type);
  const inGame = cards.filter((card) => card.expansion === "base" || (edited.prelude && isProjectCard(card)));
  const projectCards = inGame.filter(isProjectCard);
  const listId = useId();
  return (
    <div className="state-editor">
      <p className="dev-panel-note">Read from step {readFromStep}.</p>
      {underWay && (
        <p className="dev-panel-note">
          A Scenario starts at an Action: what is under way now, such as cards being bought, a Draft or a card being
          played, is dropped, and those cards go into the deck.
        </p>
      )}
      <datalist id={listId}>
        {projectCards.map((card) => (
          <option key={card.id} value={card.name} />
        ))}
      </datalist>
      <GlobalFields edited={edited} onChange={onChange} />
      {edited.players.map((_, player) => (
        <PlayerFields
          key={player}
          cards={inGame}
          edited={edited}
          player={player}
          listId={listId}
          onChange={onChange}
        />
      ))}
      <TileFields cards={cards} edited={edited} board={board} onChange={onChange} />
      <div className="dev-panel-buttons">
        <button className="option" onClick={onStart}>
          Start from this position
        </button>
        <button className="link-button" onClick={onRead}>
          Read the position shown again
        </button>
      </div>
      <p className="dev-panel-note">
        Starting replaces the current Game. Save Replay in the top bar then saves this position, to load again or to
        start a scenario test with <code>load_game</code>.
      </p>
    </div>
  );
}

interface NumberFieldProps {
  label: string;
  value: number;
  min?: number;
  onChange: (value: number) => void;
}

function NumberField({ label, value, min, onChange }: NumberFieldProps) {
  return (
    <label className="state-editor-field">
      {label}
      <input type="number" value={value} min={min} onChange={(event) => onChange(Number(event.target.value))} />
    </label>
  );
}

interface GlobalFieldsProps {
  edited: Scenario;
  onChange: (edited: Scenario) => void;
}

/** The Generation, Global Parameters, and who holds the first-player marker and takes the Turn. */
function GlobalFields({ edited, onChange }: GlobalFieldsProps) {
  const oceans = edited.tiles.filter((tile) => tile.tile === "ocean").length;
  return (
    <fieldset className="state-editor-group">
      <legend>The Game</legend>
      <NumberField label="Generation" value={edited.generation} min={1} onChange={(generation) => onChange({ ...edited, generation })} />
      <label className="state-editor-field">
        Temperature
        <select value={edited.temperature} onChange={(event) => onChange({ ...edited, temperature: Number(event.target.value) })}>
          {TEMPERATURES.map((temperature) => (
            <option key={temperature} value={temperature}>
              {temperature} °C
            </option>
          ))}
        </select>
      </label>
      <label className="state-editor-field">
        Oxygen
        <select value={edited.oxygen} onChange={(event) => onChange({ ...edited, oxygen: Number(event.target.value) })}>
          {OXYGEN_LEVELS.map((oxygen) => (
            <option key={oxygen} value={oxygen}>
              {oxygen} %
            </option>
          ))}
        </select>
      </label>
      <span className="state-editor-field">
        Oceans <output>{oceans}</output>
      </span>
      <label className="state-editor-field">
        First player
        <select
          value={edited.first_player}
          onChange={(event) => onChange({ ...edited, first_player: Number(event.target.value) })}
        >
          <PlayerOptions scenario={edited} />
        </select>
      </label>
      <label className="state-editor-field">
        Whose Turn
        <select
          value={edited.current_player ?? edited.first_player}
          onChange={(event) => onChange({ ...edited, current_player: Number(event.target.value), actions_this_turn: 0 })}
        >
          <PlayerOptions scenario={edited} />
        </select>
      </label>
    </fieldset>
  );
}

interface PlayerFieldsProps {
  cards: Card[];
  edited: Scenario;
  player: number;
  listId: string;
  onChange: (edited: Scenario) => void;
}

/** One Player's Resources and Production, Terraform Rating, Corporation, hand and played cards. */
function PlayerFields({ cards, edited, player, listId, onChange }: PlayerFieldsProps) {
  const catalog = useCardsById(cards);
  const own = edited.players[player];
  const change = (fields: Partial<ScenarioPlayer>) => onChange(changePlayer(edited, player, fields));
  const corporation = own.corporation ? catalog.get(own.corporation) : undefined;
  const addTo = (pile: CardPile) => (card: string) => onChange(putCard(edited, card, player, pile));
  return (
    <fieldset className="state-editor-group" style={{ borderLeftColor: PLAYER_COLOURS[player] }}>
      <legend>Player {player + 1}</legend>
      <table className="state-editor-resources">
        <thead>
          <tr>
            <th />
            <th>Held</th>
            <th>Production</th>
          </tr>
        </thead>
        <tbody>
          {RESOURCES.map((resource) => (
            <tr key={resource}>
              <th scope="row">{RESOURCE_NAMES[resource]}</th>
              <td>
                <input
                  type="number"
                  aria-label={`Player ${player + 1} ${RESOURCE_NAMES[resource]}`}
                  value={own.resources[resource]}
                  onChange={(event) => change({ resources: { ...own.resources, [resource]: Number(event.target.value) } })}
                />
              </td>
              <td>
                <input
                  type="number"
                  aria-label={`Player ${player + 1} ${RESOURCE_NAMES[resource]} Production`}
                  value={own.production[resource]}
                  onChange={(event) => change({ production: { ...own.production, [resource]: Number(event.target.value) } })}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <NumberField label="Terraform Rating" value={own.terraform_rating} onChange={(terraform_rating) => change({ terraform_rating })} />
      <label className="state-editor-field">
        <input
          type="checkbox"
          checked={own.terraform_rating_raised}
          onChange={(event) => change({ terraform_rating_raised: event.target.checked })}
        />
        Terraform Rating raised this Generation
      </label>
      <label className="state-editor-field">
        <input type="checkbox" checked={own.passed} onChange={(event) => change({ passed: event.target.checked })} />
        Passed
      </label>
      <label className="state-editor-field">
        Corporation
        <select
          aria-label={`Player ${player + 1} Corporation`}
          value={own.corporation ?? ""}
          onChange={(event) => onChange(setCorporation(edited, player, event.target.value || null))}
        >
          <option value="">None</option>
          {cards
            .filter((card) => card.type === "corporation")
            .map((card) => (
              <option key={card.id} value={card.id}>
                {card.name}
              </option>
            ))}
        </select>
      </label>
      {corporation?.effects?.first_action !== undefined && (
        <label className="state-editor-field">
          <input
            type="checkbox"
            checked={own.first_action_due}
            onChange={(event) => change({ first_action_due: event.target.checked })}
          />
          First action still due
        </label>
      )}
      {corporation?.effects?.action !== undefined && (
        <ActionUsed card={corporation.id} used={own.used_actions} onChange={(used_actions) => change({ used_actions })} />
      )}
      <h4>Hand</h4>
      <ul className="state-editor-cards">
        {own.hand.map((id) => (
          <li key={id}>
            {catalog.get(id)?.name ?? id}
            <RemoveButton label={`Take ${catalog.get(id)?.name} out of the hand`} onClick={() => onChange(takeOutCard(edited, id))} />
          </li>
        ))}
      </ul>
      <AddCard label={`Add to Player ${player + 1}'s hand`} cards={cards} listId={listId} onAdd={addTo("hand")} />
      <h4>Played cards</h4>
      <ul className="state-editor-cards">
        {own.played_cards.map((id) => {
          const card = catalog.get(id);
          return (
            <li key={id}>
              {card?.name ?? id}
              {card?.effects?.holds !== undefined && (
                <label>
                  {String(card.effects.holds)}
                  <input
                    type="number"
                    min={0}
                    aria-label={`Card Resources on ${card.name}`}
                    value={own.card_resources[id] ?? 0}
                    onChange={(event) =>
                      change({ card_resources: { ...own.card_resources, [id]: Number(event.target.value) } })
                    }
                  />
                </label>
              )}
              {card?.effects?.action !== undefined && (
                <ActionUsed card={id} used={own.used_actions} onChange={(used_actions) => change({ used_actions })} />
              )}
              {card?.effects?.next_card !== undefined && (
                <label>
                  <input
                    type="checkbox"
                    checked={own.next_card === id}
                    onChange={(event) => change({ next_card: event.target.checked ? id : null })}
                  />
                  waits on the next card
                </label>
              )}
              <RemoveButton label={`Take ${card?.name} out of the played cards`} onClick={() => onChange(takeOutCard(edited, id))} />
            </li>
          );
        })}
      </ul>
      <AddCard label={`Add to Player ${player + 1}'s played cards`} cards={cards} listId={listId} onAdd={addTo("played_cards")} />
    </fieldset>
  );
}

interface ActionUsedProps {
  card: string;
  used: string[];
  onChange: (used: string[]) => void;
}

/** Whether a card's action was used this Generation. */
function ActionUsed({ card, used, onChange }: ActionUsedProps) {
  return (
    <label className="state-editor-used">
      <input
        type="checkbox"
        checked={used.includes(card)}
        onChange={(event) => onChange(event.target.checked ? [...used, card] : used.filter((each) => each !== card))}
      />
      action used
    </label>
  );
}

function RemoveButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button className="link-button state-editor-remove" aria-label={label} title={label} onClick={onClick}>
      ×
    </button>
  );
}

interface AddCardProps {
  label: string;
  cards: Card[];
  listId: string;
  onAdd: (card: string) => void;
}

/** A card named by typing, as the list of Project Cards suggests, and added from wherever it is. */
function AddCard({ label, cards, listId, onAdd }: AddCardProps) {
  const [name, setName] = useState("");
  const card = cards.find((each) => each.type !== "corporation" && each.name.toLowerCase() === name.trim().toLowerCase());
  const add = () => {
    if (!card) return;
    onAdd(card.id);
    setName("");
  };
  return (
    <div className="state-editor-add">
      <input
        type="text"
        list={listId}
        aria-label={label}
        placeholder="Card name"
        value={name}
        onChange={(event) => setName(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === "Enter") {
            event.preventDefault();
            add();
          }
        }}
      />
      <button className="link-button" disabled={!card} aria-label={label} onClick={add}>
        Add
      </button>
    </div>
  );
}

interface TileFieldsProps {
  cards: Card[];
  edited: Scenario;
  board: Area[];
  onChange: (edited: Scenario) => void;
}

/** The Tiles on the board, a Tile to place, and the Area claimed with Land Claim. */
function TileFields({ cards, edited, board, onChange }: TileFieldsProps) {
  const catalog = useCardsById(cards);
  const [area, setArea] = useState(board[0]?.area ?? "");
  const [kind, setKind] = useState("ocean");
  const [owner, setOwner] = useState(0);
  const areaLabel = (each: Area) => (each.name ? `${each.area} (${each.name})` : each.area);
  const tileName = (tile: ScenarioTile) => (tile.card ? `${catalog.get(tile.card)?.name} Tile` : tile.tile);
  const claimable = board.filter((each) => each.row !== null && each.reserved === null);
  return (
    <fieldset className="state-editor-group">
      <legend>Tiles</legend>
      <ul className="state-editor-cards">
        {edited.tiles.map((tile) => (
          <li key={tile.area}>
            {tile.area}: {tileName(tile)}
            {tile.owner !== null && ` of Player ${tile.owner + 1}`}
            <RemoveButton label={`Remove the Tile on ${tile.area}`} onClick={() => onChange(removeTile(edited, tile.area))} />
          </li>
        ))}
      </ul>
      <div className="state-editor-add">
        <select aria-label="Area" value={area} onChange={(event) => setArea(event.target.value)}>
          {board.map((each) => (
            <option key={each.area} value={each.area}>
              {areaLabel(each)}
            </option>
          ))}
        </select>
        <select aria-label="Tile" value={kind} onChange={(event) => setKind(event.target.value)}>
          <option value="ocean">Ocean</option>
          <option value="greenery">Greenery</option>
          <option value="city">City</option>
          {cardsWithASpecialTile(cards).map((card) => (
            <option key={card.id} value={card.id}>
              {card.name}
            </option>
          ))}
        </select>
        {kind !== "ocean" && (
          <select aria-label="Owner" value={owner} onChange={(event) => setOwner(Number(event.target.value))}>
            <PlayerOptions scenario={edited} />
          </select>
        )}
        <button className="link-button" onClick={() => onChange(placeTile(edited, tileFrom(kind, area, owner)))}>
          Place
        </button>
      </div>
      <h4>Land Claim</h4>
      <div className="state-editor-add">
        <select
          aria-label="Area claimed with Land Claim"
          value={edited.land_claim?.area ?? ""}
          onChange={(event) =>
            onChange({
              ...edited,
              land_claim: event.target.value ? { area: event.target.value, player: edited.land_claim?.player ?? 0 } : null,
            })
          }
        >
          <option value="">No Area claimed</option>
          {claimable.map((each) => (
            <option key={each.area} value={each.area}>
              {areaLabel(each)}
            </option>
          ))}
        </select>
        {edited.land_claim && (
          <select
            aria-label="Player who claimed it"
            value={edited.land_claim.player}
            onChange={(event) => onChange({ ...edited, land_claim: { ...edited.land_claim!, player: Number(event.target.value) } })}
          >
            <PlayerOptions scenario={edited} />
          </select>
        )}
      </div>
    </fieldset>
  );
}
